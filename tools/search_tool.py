# tools/search_tool.py
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field
from duckduckgo_search import DDGS
import logging
import time
from typing import List, Dict, Optional
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSearchInput(BaseModel):
    query: str = Field(description="The search query to look up on the internet. Should be concise and keyword-rich.")

class SearchConfig:
    """搜索配置类，支持环境变量和默认值"""
    MAX_RESULTS: int = int(os.getenv("SEARCH_MAX_RESULTS", "5"))
    TIMEOUT: int = int(os.getenv("SEARCH_TIMEOUT", "10"))
    MAX_RETRIES: int = int(os.getenv("SEARCH_MAX_RETRIES", "3"))
    RETRY_DELAY: float = float(os.getenv("SEARCH_RETRY_DELAY", "1.0"))
    PROXY: Optional[str] = os.getenv("SEARCH_PROXY")  # 可选的代理设置

def _format_search_results(results: List[Dict]) -> str:
    """格式化搜索结果，提高可读性"""
    if not results:
        return "未找到相关搜索结果。"
    
    formatted = []
    for i, r in enumerate(results, 1):
        title = r.get('title', '无标题')
        snippet = r.get('body', '无摘要')
        url = r.get('href', '无链接')
        
        formatted.append(f"[{i}] {title}")
        formatted.append(f"   摘要：{snippet}")
        formatted.append(f"   链接：{url}")
        formatted.append("")  # 空行分隔
    
    return "\n".join(formatted)

def web_search(query: str) -> str:
    """
    搜索互联网以获取实时信息、新闻或特定事实。
    当用户询问最新事件、天气、股票或知识库中不存在的客观事实时，必须使用此工具。
    
    特性：
    - 支持重试机制，提高网络请求成功率
    - 支持超时控制，防止长时间挂起
    - 支持代理配置，解决网络访问问题
    - 详细的错误信息和日志记录
    """
    if not query or not query.strip():
        return "搜索查询不能为空，请提供有效的搜索关键词。"
    
    query = query.strip()
    logger.info(f"开始搜索：{query}")
    
    last_error = None
    
    # 重试机制
    for attempt in range(SearchConfig.MAX_RETRIES):
        try:
            logger.info(f"搜索尝试 {attempt + 1}/{SearchConfig.MAX_RETRIES}")
            
            # 配置代理（如果需要）
            proxy = SearchConfig.PROXY
            if proxy:
                logger.info(f"使用代理：{proxy}")
            
            # 执行搜索，带超时控制
            with DDGS(timeout=SearchConfig.TIMEOUT) as ddgs:
                results = list(ddgs.text(query, max_results=SearchConfig.MAX_RESULTS))
            
            if not results:
                logger.warning(f"搜索 '{query}' 未返回结果")
                return "未找到相关搜索结果，请尝试使用不同的关键词。"
            
            logger.info(f"搜索成功，找到 {len(results)} 条结果")
            return _format_search_results(results)
            
        except Exception as e:
            last_error = e
            error_msg = f"搜索失败 (尝试 {attempt + 1}/{SearchConfig.MAX_RETRIES}): {str(e)}"
            logger.error(error_msg)
            
            # 如果是网络相关错误，等待后重试
            if any(keyword in str(e).lower() for keyword in ['timeout', 'connection', 'network', 'proxy']):
                if attempt < SearchConfig.MAX_RETRIES - 1:
                    wait_time = SearchConfig.RETRY_DELAY * (attempt + 1)  # 递增延迟
                    logger.info(f"等待 {wait_time:.1f} 秒后重试...")
                    time.sleep(wait_time)
                continue
            else:
                # 非网络错误，直接返回
                break
    
    # 所有重试失败
    error_str = str(last_error)
    logger.error(f"搜索完全失败：{error_str}")
    
    # 提供友好的错误提示
    if 'timeout' in error_str.lower():
        return "搜索超时，可能是网络连接问题。请检查网络或稍后重试。"
    elif 'proxy' in error_str.lower():
        return "代理配置错误。请检查代理设置或移除代理配置。"
    elif 'connection' in error_str.lower():
        return "无法连接到搜索服务。请检查网络连接。"
    else:
        return f"搜索失败：{error_str}。请尝试简化搜索关键词或稍后重试。"

# 导出 LlamaIndex 工具实例
search_tool = FunctionTool.from_defaults(
    fn=web_search,
    name="web_search",
    description="搜索互联网以获取实时信息、新闻或特定事实。当询问最新事件、未知事实或需要联网查询时使用。支持重试和超时保护。",
    fn_schema=WebSearchInput
)
