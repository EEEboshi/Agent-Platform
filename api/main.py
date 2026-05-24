# api/main.py
"""
API 服务模块
提供 RESTful API 接口，支持跨域访问和完善的错误处理
"""
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Optional
import uvicorn
import time
from datetime import datetime

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from core.agent import create_agent
from core.config import get_settings
from core.session_store import session_store
from core.logging_config import setup_logging, get_logger

# 初始化日志系统
setup_logging()
logger = get_logger(__name__)

# 创建 FastAPI 应用
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    description="多功能 AI 智能体平台的 RESTful API 接口",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置 CORS（跨域资源共享）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    """聊天请求模型"""
    session_id: str = Field(description="会话 ID，用于标识用户会话")
    message: str = Field(description="用户消息内容", min_length=1, max_length=2000)

class ChatResponse(BaseModel):
    """聊天响应模型"""
    session_id: str
    reply: str
    timestamp: Optional[str] = None

class ResetSessionRequest(BaseModel):
    """重置会话请求模型"""
    session_id: str = Field(description="要重置的会话 ID")

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: str
    session_count: int

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """请求日志中间件"""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
    
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常：{exc}", exc_info=True)
    
    return {
        "detail": f"服务器内部错误：{str(exc)}",
        "type": type(exc).__name__,
        "path": request.url.path
    }

@app.get("/api/health", response_model=HealthResponse, tags=["健康检查"])
async def health_check():
    """
    健康检查接口
    用于监控服务状态
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        session_count=session_store.count
    )

@app.post("/api/chat", response_model=ChatResponse, tags=["聊天"])
async def chat_endpoint(request: ChatRequest):
    """
    聊天接口
    处理用户的聊天请求，调用 Agent 进行回复
    
    Args:
        request: 包含 session_id 和 message 的请求体
        
    Returns:
        包含 session_id 和回复内容的响应
    """
    try:
        # 验证请求
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="消息内容不能为空")
        
        if not request.session_id:
            raise HTTPException(status_code=400, detail="session_id 不能为空")
        
        # 获取或创建 Agent
        agent = get_or_create_agent(request.session_id)
        
        # 调用 Agent（同步方法，FastAPI 会自动将其放入线程池执行）
        response = agent.chat(request.message)
        
        return ChatResponse(
            session_id=request.session_id,
            reply=str(response),
            timestamp=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"聊天处理错误：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"聊天处理失败：{str(e)}")

@app.post("/api/reset_session", tags=["会话管理"])
async def reset_session(request: ResetSessionRequest):
    """
    重置/清空指定 session 的记忆
    
    Args:
        request: 包含 session_id 的请求体
        
    Returns:
        操作结果消息
    """
    try:
        if session_store.exists(request.session_id):
            session_store.delete(request.session_id)
            logger.info(f"会话已重置：{request.session_id}")
            return {"message": f"会话 {request.session_id} 已成功重置", "success": True}
        else:
            logger.warning(f"尝试重置不存在的会话：{request.session_id}")
            return {"message": "会话不存在", "success": False}
            
    except Exception as e:
        logger.error(f"重置会话失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"重置会话失败：{str(e)}")

@app.get("/api/sessions", tags=["会话管理"])
async def list_sessions():
    """
    列出所有活跃会话
    """
    return {
        "count": session_store.count,
        "sessions": session_store.list_all()
    }

def get_or_create_agent(session_id: str):
    """获取现有 Agent 或创建新 Agent"""
    if not session_store.exists(session_id):
        logger.info(f"创建新的 agent 会话：{session_id}")
        session_store.set(session_id, create_agent(session_id))
    return session_store.get(session_id)

if __name__ == "__main__":
    logger.info(f"启动 API 服务器：http://{settings.server.host}:{settings.server.port}")
    logger.info(f"API 文档：http://{settings.server.host}:{settings.server.port}/api/docs")
    logger.info(f"Session 存储模式：{session_store.store_type}")
    
    uvicorn.run(
        app,
        host=settings.server.host,
        port=settings.server.port,
        log_level=settings.log_level.lower()
    )
