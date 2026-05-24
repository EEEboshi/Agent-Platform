# tools/search_tool.py
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field
import logging
import time
import re
from typing import List, Dict, Optional
import os
import requests
from urllib.parse import quote

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
    # 使用 Bing 搜索，国内可访问
    SEARCH_ENGINE: str = os.getenv("SEARCH_ENGINE", "bing")  # 支持 'bing' 或 'baidu'

def _optimize_weather_query(query: str) -> str:
    """
    智能优化天气查询语句
    例如："今天北京天气" -> "北京天气预报"
    """
    import re
    
    # 检查是否包含天气相关关键词
    weather_keywords = ['天气', '气温', '下雨', '晴天', '阴天', '雨', '雪', '风', '雾霾']
    has_weather_keyword = any(keyword in query for keyword in weather_keywords)
    
    if not has_weather_keyword:
        return query
    
    # 检查是否包含地点（简单的中国城市名）
    cities = [
        '北京', '上海', '广州', '深圳', '杭州', '南京', '成都', '重庆', '武汉', '西安',
        '天津', '苏州', '青岛', '长沙', '郑州', '沈阳', '哈尔滨', '济南', '合肥', '福州',
        '昆明', '贵阳', '南昌', '南宁', '海口', '拉萨', '乌鲁木齐', '呼和浩特', '银川',
        '西宁', '太原', '石家庄', '长春', '大连', '厦门', '宁波', '无锡', '常州', '南通'
    ]
    
    city = None
    for c in cities:
        if c in query:
            city = c
            break
    
    if not city:
        # 如果没有明确城市，添加"天气"关键词
        if '天气' not in query:
            return query + ' 天气'
        return query
    
    # 优化查询：城市 + 天气预报
    if '预报' not in query:
        return f"{city}天气预报"
    
    return query

def _format_search_results(results: List[Dict]) -> str:
    """格式化搜索结果，提高可读性"""
    if not results:
        return "未找到相关搜索结果。"
    
    formatted = []
    for i, r in enumerate(results, 1):
        title = r.get('title', '无标题')
        snippet = r.get('snippet', '无摘要')
        url = r.get('url', '无链接')
        
        formatted.append(f"[{i}] {title}")
        formatted.append(f"   摘要：{snippet}")
        formatted.append(f"   链接：{url}")
        formatted.append("")  # 空行分隔
    
    return "\n".join(formatted)

def _extract_weather_info(snippet: str) -> str:
    """
    从摘要中提取天气相关信息
    识别温度、天气状况、风力等关键信息
    """
    import re
    
    weather_info = []
    
    # 提取温度信息（如 15-25°C、20℃ 等）
    temp_patterns = [
        r'(\d+[-~]\d+)\s*[°℃℉]',
        r'(\d+)\s*[°℃℉]',
        r'气温[^，,。]*?(\d+[^，,。]*)',
    ]
    for pattern in temp_patterns:
        match = re.search(pattern, snippet)
        if match:
            weather_info.append(f"温度：{match.group(1)}")
            break
    
    # 提取天气状况
    weather_conditions = ['晴', '多云', '阴', '小雨', '中雨', '大雨', '暴雨', '雪', '小雪', '大雪', '雾', '霾', '雷阵雨', '阵雨']
    for condition in weather_conditions:
        if condition in snippet:
            weather_info.append(f"天气：{condition}")
            break
    
    # 提取风力信息
    wind_patterns = [
        r'([一二三四五六七八级]+\s*[东南西北]?风)',
        r'(\d+\s*[东南西北]?风)',
        r'(微风)',
        r'(风力[^，,。]*)',
    ]
    for pattern in wind_patterns:
        match = re.search(pattern, snippet)
        if match:
            weather_info.append(f"风力：{match.group(1)}")
            break
    
    return "，".join(weather_info) if weather_info else ""

def _format_weather_results(results: List[Dict]) -> str:
    """
    专门格式化天气搜索结果
    展示天气信息摘要和查看链接，让智能体能根据摘要回答
    """
    if not results:
        return "未找到相关天气信息。"
    
    # 严格筛选天气相关结果
    weather_sources = []
    for r in results:
        title = r.get('title', '')
        url = r.get('url', '')
        snippet = r.get('snippet', '')
        
        # 严格筛选：必须包含天气相关关键词
        is_weather_related = False
        
        # 检查标题
        if any(keyword in title.lower() for keyword in ['天气', 'weather', '气象', '预报']):
            is_weather_related = True
        
        # 检查摘要中是否包含天气数据特征
        weather_indicators = ['℃', '°C', '度', '气温', '天气', '晴', '多云', '阴', '雨', '雪', '风力', '风向', '湿度']
        if any(indicator in snippet for indicator in weather_indicators):
            is_weather_related = True
        
        # 检查URL是否是知名天气网站
        weather_domains = ['weather.com', 'tianqi.com', 'nmc.cn', 'cma.cn', 'cma.gov.cn']
        if any(domain in url.lower() for domain in weather_domains):
            is_weather_related = True
        
        if is_weather_related:
            # 清理标题
            clean_title = title.replace('.com.cn', '').replace('.cn', '').replace('.com', '')
            clean_title = re.sub(r'^https?://', '', clean_title).split('/')[0]
            
            weather_sources.append({
                'title': clean_title,
                'url': url,
                'snippet': snippet
            })
    
    if not weather_sources:
        # 如果没有天气相关结果，返回提示
        return "未找到相关天气信息，请尝试使用不同的关键词搜索。"
    
    # 生成格式化输出
    formatted = []
    
    # 第一部分：天气信息来源摘要（供智能体参考）
    formatted.append("【天气信息来源】")
    formatted.append("以下是查询到的天气信息，请根据这些信息回答用户：\n")
    
    for i, source in enumerate(weather_sources, 1):
        formatted.append(f"来源{i}（{source['title']}）：")
        formatted.append(f"  {source['snippet']}")
        formatted.append("")
    
    # 第二部分：查看链接（供用户点击查看详情）
    formatted.append("【查看实时天气详情】")
    formatted.append("如需查看最新的温度、风力等详细数据，可访问以下网站：\n")
    
    for i, source in enumerate(weather_sources, 1):
        formatted.append(f"{i}. {source['title']}：{source['url']}")
    
    formatted.append("")
    formatted.append("提示：天气数据会实时更新，建议点击上方链接获取最新信息。")
    
    return "\n".join(formatted)

def _search_bing(query: str, max_results: int = 5, timeout: int = 10) -> List[Dict]:
    """
    使用 Bing 搜索获取结果
    通过解析 Bing 搜索结果页面获取信息
    """
    try:
        # Bing 搜索 URL
        search_url = f"https://www.bing.com/search?q={quote(query)}&count={max_results}"
        
        # 设置请求头，模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        
        # 配置代理（如果需要）
        proxies = None
        if SearchConfig.PROXY:
            proxies = {
                'http': SearchConfig.PROXY,
                'https': SearchConfig.PROXY,
            }
        
        response = requests.get(search_url, headers=headers, timeout=timeout, proxies=proxies)
        response.raise_for_status()
        
        import re
        from html import unescape
        
        results = []
        html_content = response.text
        
        # 使用更宽松的正则表达式提取 Bing 搜索结果
        # 匹配 <li class="b_algo"> 标签内的内容
        pattern = r'<li[^>]*class="[^"]*b_algo[^"]*"[^>]*>(.*?)</li>'
        matches = re.findall(pattern, html_content, re.DOTALL | re.IGNORECASE)
        
        for match in matches[:max_results]:
            # 提取标题和链接 - 改进正则
            title = None
            url = None
            snippet = None
            
            # 尝试多种模式匹配标题和链接
            patterns = [
                r'<h2[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',  # 模式 1: h2 > a
                r'<h2[^>]*>.*?<a[^>]*>([^<]+)</a>.*?href="([^"]+)"',  # 模式 2: 先标题后链接
                r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>',  # 模式 3: 通用 a 标签
            ]
            
            for p in patterns:
                match_result = re.search(p, match, re.DOTALL)
                if match_result:
                    url = match_result.group(1)
                    title = match_result.group(2).strip()
                    break
            
            # 提取摘要 - 尝试多种模式
            snippet_patterns = [
                r'<div[^>]*class="[^"]*b_caption[^"]*"[^>]*>(.*?)</div>',  # b_caption
                r'<p[^>]*>([^<]+)</p>',  # 通用 p 标签
                r'<span[^>]*>([^<]+)</span>',  # span 标签
            ]
            
            for p in snippet_patterns:
                snippet_match = re.search(p, match, re.DOTALL)
                if snippet_match:
                    snippet = re.sub(r'<[^>]+>', '', snippet_match.group(1)).strip()
                    if snippet and len(snippet) > 10:  # 确保摘要有一定长度
                        break
            
            # 如果标题是 None，尝试从整个 match 中提取
            if not title:
                title_match = re.search(r'>([^<]{10,100})<', match)
                if title_match:
                    title = title_match.group(1).strip()
            
            # 如果 URL 是 None，尝试提取
            if not url:
                url_match = re.search(r'href="(https?://[^"]+)"', match)
                if url_match:
                    url = url_match.group(1)
            
            # 清理文本
            if title:
                title = unescape(re.sub(r'\s+', ' ', title))
            if snippet:
                snippet = unescape(re.sub(r'\s+', ' ', snippet))
            
            # 只添加有效的结果
            if title and url:
                results.append({
                    'title': title,
                    'snippet': snippet or '无摘要',
                    'url': url,
                })
        
        return results
        
    except Exception as e:
        logger.error(f"Bing 搜索失败：{e}")
        logger.error(f"错误类型：{type(e).__name__}")
        raise

def _search_baidu(query: str, max_results: int = 5, timeout: int = 10) -> List[Dict]:
    """
    使用百度搜索获取结果
    通过解析百度搜索结果页面获取信息
    """
    try:
        # 百度搜索 URL
        search_url = f"https://www.baidu.com/s?wd={quote(query)}&rn={max_results}"
        
        # 设置请求头，模拟浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9',
        }
        
        # 配置代理（如果需要）
        proxies = None
        if SearchConfig.PROXY:
            proxies = {
                'http': SearchConfig.PROXY,
                'https': SearchConfig.PROXY,
            }
        
        response = requests.get(search_url, headers=headers, timeout=timeout, proxies=proxies)
        response.raise_for_status()
        
        import re
        
        results = []
        html_content = response.text
        
        # 使用正则表达式提取百度搜索结果
        # 百度搜索结果通常在 <div class="result c-container"> 标签中
        pattern = r'<div class="result[^"]*"[^>]*>(.*?)</div><!-- end of result -->'
        matches = re.findall(pattern, html_content, re.DOTALL)
        
        for match in matches[:max_results]:
            # 提取标题
            title_match = re.search(r'<h3[^>]*class="t"[^>]*>.*?<a[^>]*title="([^"]*)"', match, re.DOTALL)
            title = title_match.group(1).strip() if title_match else '无标题'
            
            # 提取链接
            url_match = re.search(r'<h3[^>]*class="t"[^>]*>.*?<a[^>]*href="([^"]*)"', match, re.DOTALL)
            url = url_match.group(1) if url_match else '无链接'
            
            # 提取摘要
            snippet_match = re.search(r'<span class="c-showtext"[^>]*>([^<]+)', match, re.DOTALL)
            snippet = snippet_match.group(1).strip() if snippet_match else '无摘要'
            
            # 清理 HTML 标签
            snippet = re.sub(r'<[^>]+>', '', snippet)
            title = re.sub(r'<[^>]+>', '', title)
            
            if title != '无标题' and url != '无链接':
                results.append({
                    'title': title,
                    'snippet': snippet,
                    'url': url,
                })
        
        return results
        
    except Exception as e:
        logger.error(f"百度搜索失败：{e}")
        raise

def web_search(query: str) -> str:
    """
    搜索互联网以获取实时信息、新闻或特定事实。
    当用户询问最新事件、天气、股票或知识库中不存在的客观事实时，必须使用此工具。
    
    特性：
    - 支持重试机制，提高网络请求成功率
    - 支持超时控制，防止长时间挂起
    - 支持代理配置，解决网络访问问题
    - 详细的错误信息和日志记录
    - 使用国内可访问的搜索引擎（Bing/百度）
    - 智能识别天气查询并优化搜索词
    """
    if not query or not query.strip():
        return "搜索查询不能为空，请提供有效的搜索关键词。"
    
    query = query.strip()
    logger.info(f"开始搜索：{query}")
    
    # 智能优化天气查询
    optimized_query = _optimize_weather_query(query)
    if optimized_query != query:
        logger.info(f"优化天气查询：'{query}' -> '{optimized_query}'")
    
    last_error = None
    
    # 重试机制
    for attempt in range(SearchConfig.MAX_RETRIES):
        try:
            logger.info(f"搜索尝试 {attempt + 1}/{SearchConfig.MAX_RETRIES}")
            
            # 根据配置选择搜索引擎
            if SearchConfig.SEARCH_ENGINE.lower() == 'baidu':
                logger.info(f"使用百度搜索")
                results = _search_baidu(optimized_query, SearchConfig.MAX_RESULTS, SearchConfig.TIMEOUT)
            else:
                # 默认使用 Bing
                logger.info(f"使用 Bing 搜索")
                results = _search_bing(optimized_query, SearchConfig.MAX_RESULTS, SearchConfig.TIMEOUT)
            
            if not results:
                logger.warning(f"搜索 '{optimized_query}' 未返回结果")
                return "未找到相关搜索结果，请尝试使用不同的关键词。"
            
            logger.info(f"搜索成功，找到 {len(results)} 条结果")
            
            # 天气查询使用专门的格式化函数
            weather_keywords = ['天气', '气温', '天气预报', '气象', '下雨', '晴天', '阴天', '雪', '风']
            is_weather_query = any(keyword in query.lower() for keyword in weather_keywords)
            
            if is_weather_query:
                return _format_weather_results(results)
            else:
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
