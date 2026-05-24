# core/agent.py
"""
Agent 核心模块
负责创建和配置 AI Agent 实例，包括大模型、记忆和工具集成
"""
import os
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.memory import ChatMemoryBuffer
from tools import ALL_TOOLS
import logging
import httpx

from core.config import get_settings
from core.logging_config import setup_logging, get_logger

# 初始化日志系统
setup_logging()
logger = get_logger(__name__)

# 加载环境变量
load_dotenv()

# 全局 httpx 客户端连接池
_http_client_pool = {}

def get_http_client() -> httpx.Client:
    """
    获取或创建 httpx 客户端（连接池复用）
    避免每次创建新连接，提升性能
    """
    client_key = "default"
    if client_key not in _http_client_pool:
        settings = get_settings()
        _http_client_pool[client_key] = httpx.Client(
            timeout=httpx.Timeout(settings.llm.timeout),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            follow_redirects=True,
        )
        logger.info("HTTP 客户端连接池已创建")
    return _http_client_pool[client_key]

def validate_environment() -> bool:
    """验证必要的环境变量是否已设置"""
    settings = get_settings()
    if not settings.llm.api_key:
        logger.error("DASHSCOPE_API_KEY 环境变量未设置")
        return False
    
    if not settings.llm.api_base:
        logger.warning("DASHSCOPE_API_BASE 未设置，将使用默认值")
    
    return True

def create_llm():
    """
    创建大语言模型实例
    使用 OpenAI 兼容模式调用阿里云通义千问
    """
    settings = get_settings()
    
    logger.info(
        f"初始化 LLM: model={settings.llm.model}, "
        f"temperature={settings.llm.temperature}"
    )
    
    http_client = get_http_client()
    
    return OpenAI(
        model="gpt-4",
        temperature=settings.llm.temperature,
        api_key=settings.llm.api_key,
        api_base=settings.llm.api_base,
        additional_kwargs={
            "model": settings.llm.model
        },
        timeout=float(settings.llm.timeout),
        max_retries=settings.llm.max_retries,
        http_client=http_client,
    )

def create_memory(token_limit: int = None):
    """
    创建对话记忆实例
    限制 token 数量防止上下文溢出
    """
    if token_limit is None:
        settings = get_settings()
        token_limit = settings.memory.token_limit
    
    logger.info(f"创建记忆缓冲区，token 限制：{token_limit}")
    return ChatMemoryBuffer.from_defaults(token_limit=token_limit)

# 系统提示词配置
SYSTEM_PROMPT = """你是一个强大且多功能的自动化 AI 智能体助手。
你的主要职责是准确理解用户意图，并合理调用提供的工具来完成任务。

核心规则：
1. 【工具使用优先】如果用户的问题需要实时信息、新闻、计算或外部数据，必须调用相应工具，严禁自己编造。
2. 【严禁编造】对于天气、新闻、股票等实时信息，绝对不可以自己编造数据，必须调用 web_search 工具获取。
3. 【参数准确性】调用工具时确保参数准确完整。如果工具返回错误，分析原因后调整参数重试。
4. 【操作确认】对于发送邮件等不可逆操作，执行前需向用户确认（除非用户明确说"直接发送"）。
5. 【错误处理】工具调用失败时，向用户清晰解释原因并提供替代方案。
6. 【专业回复】始终使用清晰、专业、友好的中文回答用户。
7. 【基于工具回答】必须严格根据工具返回的实际内容来回答用户，不要添加工具未提供的具体数据。

可用工具：
- web_search: 联网搜索实时信息、新闻、事实
- calculate_math: 数学表达式计算
- send_automated_email: 发送邮件

回答格式：
- 先给出直接答案或结论
- 如使用了工具，简要说明信息来源
- 必要时提供后续建议"""

def create_agent(session_id: str = "default") -> OpenAIAgent:
    """
    工厂函数：为每个 session 创建一个带有独立记忆的 Agent 实例。
    
    Args:
        session_id: 会话标识符，用于区分不同用户的记忆
        
    Returns:
        配置好的 OpenAIAgent 实例
    """
    settings = get_settings()
    
    if not validate_environment():
        raise ValueError("环境变量配置不完整，请检查 .env 文件")
    
    llm = create_llm()
    memory = create_memory()
    
    available_tools = ALL_TOOLS
    logger.info(f"加载 {len(available_tools)} 个工具")
    
    agent = OpenAIAgent.from_tools(
        tools=available_tools,
        llm=llm,
        memory=memory,
        verbose=settings.agent.verbose,
        system_prompt=SYSTEM_PROMPT,
        max_function_calls=settings.agent.max_function_calls
    )
    
    logger.info(f"Agent 创建成功，session_id={session_id}")
    return agent

# 测试入口
if __name__ == "__main__":
    print("=" * 60)
    print("多功能 AI Agent 平台 - 测试模式")
    print("=" * 60)
    
    try:
        test_agent = create_agent()
        print("\n✓ Agent 初始化成功")
        print("\n开始对话测试 (输入 'quit' 或 'exit' 退出):\n")
        
        while True:
            user_input = input("\n👤 用户：")
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n再见！")
                break
            
            if not user_input.strip():
                continue
                
            try:
                response = test_agent.chat(user_input)
                print(f"\n🤖 Agent: {response}")
            except Exception as e:
                print(f"\n❌ 错误：{str(e)}")
                
    except Exception as e:
        print(f"\n❌ Agent 初始化失败：{str(e)}")
        print("\n请检查:")
        print("1. .env 文件是否存在")
        print("2. DASHSCOPE_API_KEY 是否正确配置")
        print("3. 网络连接是否正常")
