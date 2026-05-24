"""
API 调用工具
通用 HTTP 请求工具，支持 GET/POST/PUT/DELETE 等方法
"""
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTTPRequestInput(BaseModel):
    """HTTP 请求输入模型"""
    url: str = Field(description="请求 URL")
    method: str = Field(default="GET", description="HTTP 方法：GET, POST, PUT, DELETE, PATCH")
    headers: Optional[Dict[str, str]] = Field(default=None, description="请求头（JSON 格式）")
    params: Optional[Dict[str, Any]] = Field(default=None, description="查询参数（GET 请求使用）")
    body: Optional[Dict[str, Any]] = Field(default=None, description="请求体（POST/PUT 请求使用）")
    timeout: int = Field(default=30, description="请求超时时间（秒）")


class HTTPValidator:
    """HTTP 请求验证器"""
    
    ALLOWED_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
    
    @staticmethod
    def validate_url(url: str) -> tuple[bool, str]:
        """验证 URL"""
        if not url or not url.strip():
            return False, "URL 不能为空"
        
        # 检查协议
        if not (url.startswith('http://') or url.startswith('https://')):
            return False, "URL 必须以 http:// 或 https:// 开头"
        
        # 检查长度
        if len(url) > 2048:
            return False, "URL 过长"
        
        return True, ""
    
    @staticmethod
    def validate_method(method: str) -> tuple[bool, str]:
        """验证 HTTP 方法"""
        method_upper = method.upper()
        if method_upper not in HTTPValidator.ALLOWED_METHODS:
            return False, f"不支持的 HTTP 方法：{method}"
        return True, ""


def make_http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> str:
    """
    发送 HTTP 请求。
    支持 GET, POST, PUT, DELETE, PATCH 等方法
    
    Args:
        url: 请求 URL
        method: HTTP 方法（GET/POST/PUT/DELETE/PATCH）
        headers: 请求头字典
        params: 查询参数字典（GET 请求使用）
        body: 请求体字典（POST/PUT 请求使用）
        timeout: 超时时间（秒）
        
    Returns:
        响应内容（JSON 格式或文本）
    """
    try:
        import requests
        
        # 验证 URL
        is_valid, error_msg = HTTPValidator.validate_url(url)
        if not is_valid:
            return f"错误：{error_msg}"
        
        # 验证方法
        is_valid, error_msg = HTTPValidator.validate_method(method)
        if not is_valid:
            return f"错误：{error_msg}"
        
        method = method.upper()
        
        logger.info(f"发送 {method} 请求：{url}")
        
        # 发送请求
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params,
            json=body,
            timeout=timeout
        )
        
        # 记录响应信息
        logger.info(f"响应状态码：{response.status_code}")
        
        # 构建响应信息
        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "url": response.url,
        }
        
        # 尝试解析 JSON
        try:
            result["body"] = response.json()
            result["content_type"] = "application/json"
        except json.JSONDecodeError:
            result["body"] = response.text[:5000]  # 限制长度
            result["content_type"] = response.headers.get('Content-Type', 'text/plain')
        
        # 格式化输出
        output = f"状态码：{response.status_code}\n"
        output += f"URL: {response.url}\n"
        output += f"内容类型：{result['content_type']}\n"
        output += "-" * 50 + "\n"
        
        if isinstance(result["body"], dict):
            output += json.dumps(result["body"], ensure_ascii=False, indent=2)
        else:
            output += result["body"]
        
        return output
        
    except ImportError:
        return "错误：需要安装 requests 库，请运行：pip install requests"
    except requests.exceptions.Timeout:
        logger.error(f"请求超时：{url}")
        return f"错误：请求超时（{timeout}秒）"
    except requests.exceptions.ConnectionError as e:
        logger.error(f"连接错误：{e}")
        return f"错误：连接失败 - {str(e)}"
    except requests.exceptions.RequestException as e:
        logger.error(f"请求异常：{e}")
        return f"错误：请求失败 - {str(e)}"
    except Exception as e:
        logger.error(f"未知错误：{e}")
        return f"错误：{str(e)}"


def get_request(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> str:
    """
    发送 GET 请求。
    用于获取数据
    
    Args:
        url: 请求 URL
        headers: 请求头字典
        params: 查询参数字典
        timeout: 超时时间（秒）
        
    Returns:
        响应内容
    """
    return make_http_request(
        url=url,
        method="GET",
        headers=headers,
        params=params,
        timeout=timeout
    )


def post_request(
    url: str,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> str:
    """
    发送 POST 请求。
    用于提交数据
    
    Args:
        url: 请求 URL
        body: 请求体字典
        headers: 请求头字典
        timeout: 超时时间（秒）
        
    Returns:
        响应内容
    """
    return make_http_request(
        url=url,
        method="POST",
        headers=headers,
        body=body,
        timeout=timeout
    )


def put_request(
    url: str,
    body: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> str:
    """
    发送 PUT 请求。
    用于更新数据
    
    Args:
        url: 请求 URL
        body: 请求体字典
        headers: 请求头字典
        timeout: 超时时间（秒）
        
    Returns:
        响应内容
    """
    return make_http_request(
        url=url,
        method="PUT",
        headers=headers,
        body=body,
        timeout=timeout
    )


def delete_request(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = 30
) -> str:
    """
    发送 DELETE 请求。
    用于删除数据
    
    Args:
        url: 请求 URL
        headers: 请求头字典
        timeout: 超时时间（秒）
        
    Returns:
        响应内容
    """
    return make_http_request(
        url=url,
        method="DELETE",
        headers=headers,
        timeout=timeout
    )


# 创建工具实例
http_request_tool = FunctionTool.from_defaults(
    fn=make_http_request,
    name="http_request",
    description="发送通用 HTTP 请求（GET/POST/PUT/DELETE/PATCH）",
    fn_schema=HTTPRequestInput
)

get_tool = FunctionTool.from_defaults(
    fn=get_request,
    name="get_request",
    description="发送 GET 请求获取数据",
    fn_schema=HTTPRequestInput
)

post_tool = FunctionTool.from_defaults(
    fn=post_request,
    name="post_request",
    description="发送 POST 请求提交数据",
    fn_schema=HTTPRequestInput
)

put_tool = FunctionTool.from_defaults(
    fn=put_request,
    name="put_request",
    description="发送 PUT 请求更新数据",
    fn_schema=HTTPRequestInput
)

delete_tool = FunctionTool.from_defaults(
    fn=delete_request,
    name="delete_request",
    description="发送 DELETE 请求删除数据",
    fn_schema=HTTPRequestInput
)

# 汇总所有 API 工具
API_TOOLS = [
    http_request_tool,
    get_tool,
    post_tool,
    put_tool,
    delete_tool
]
