"""
通知工具
支持企业微信、钉钉、飞书消息推送
"""
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import json
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeComInput(BaseModel):
    """企业微信消息输入模型"""
    webhook_url: Optional[str] = Field(default=None, description="企业微信机器人 Webhook URL（未提供则使用 .env 配置）")
    content: str = Field(description="消息内容")
    mentioned_list: Optional[List[str]] = Field(default=None, description="需要提醒的成员 ID 列表")


class DingTalkInput(BaseModel):
    """钉钉消息输入模型"""
    webhook_url: Optional[str] = Field(default=None, description="钉钉机器人 Webhook URL（未提供则使用 .env 配置）")
    content: str = Field(description="消息内容")
    at_mobiles: Optional[List[str]] = Field(default=None, description="需要提醒的手机号列表")
    is_atall: bool = Field(default=False, description="是否@所有人")


class FeishuInput(BaseModel):
    """飞书消息输入模型"""
    webhook_url: Optional[str] = Field(default=None, description="飞书机器人 Webhook URL（未提供则使用 .env 配置）")
    content: str = Field(description="消息内容")
    open_ids: Optional[List[str]] = Field(default=None, description="需要提醒的用户 ID 列表")


class NotificationValidator:
    """通知验证器"""
    
    @staticmethod
    def validate_webhook_url(url: str, platform: str) -> tuple[bool, str]:
        """验证 Webhook URL"""
        if not url or not url.strip():
            return False, "Webhook URL 不能为空"
        
        if not url.startswith('https://'):
            return False, "Webhook URL 必须以 https:// 开头"
        
        # 验证平台特定 URL
        if platform == 'wecom':
            if 'weixin.qq.com' not in url and 'work.weixin.qq.com' not in url:
                return False, "不是有效的企业微信 Webhook URL"
        elif platform == 'dingtalk':
            if 'dingtalk.com' not in url and 'oapi.dingtalk.com' not in url:
                return False, "不是有效的钉钉 Webhook URL"
        elif platform == 'feishu':
            if 'feishu.cn' not in url:
                return False, "不是有效的飞书 Webhook URL"
        
        return True, ""


def send_wecom_message(
    webhook_url: Optional[str] = None,
    content: str = "",
    mentioned_list: Optional[List[str]] = None
) -> str:
    """
    发送企业微信消息。
    支持文本消息和@成员
    
    Args:
        webhook_url: 企业微信机器人 Webhook URL（未提供则使用 .env 配置）
        content: 消息内容
        mentioned_list: 需要提醒的成员 ID 列表
        
    Returns:
        发送结果
    """
    try:
        import requests
        
        # 如果未提供 webhook_url，从 Settings 读取
        if webhook_url is None:
            from core.config import get_settings
            settings = get_settings()
            webhook_url = settings.notification.wecom_webhook_url
        
        if not webhook_url:
            return "错误：未提供 Webhook URL，请传入参数或在 .env 中配置 WECOM_WEBHOOK_URL"
        
        # 验证 URL
        is_valid, error_msg = NotificationValidator.validate_webhook_url(webhook_url, 'wecom')
        if not is_valid:
            return f"错误：{error_msg}"
        
        # 构建消息
        message = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        # 添加@成员
        if mentioned_list:
            message["text"]["mentioned_list"] = mentioned_list
        
        # 发送请求
        logger.info(f"发送企业微信消息到：{webhook_url[:50]}...")
        response = requests.post(
            webhook_url,
            json=message,
            timeout=10
        )
        
        result = response.json()
        
        if result.get('errcode') == 0:
            logger.info("企业微信消息发送成功")
            return "✓ 企业微信消息发送成功"
        else:
            error_msg = result.get('errmsg', '未知错误')
            logger.error(f"企业微信消息发送失败：{error_msg}")
            return f"✗ 发送失败：{error_msg}"
        
    except ImportError:
        return "错误：需要安装 requests 库，请运行：pip install requests"
    except requests.exceptions.Timeout:
        return "错误：请求超时"
    except Exception as e:
        logger.error(f"发送企业微信消息失败：{e}")
        return f"错误：{str(e)}"


def send_dingtalk_message(
    webhook_url: Optional[str] = None,
    content: str = "",
    at_mobiles: Optional[List[str]] = None,
    is_atall: bool = False
) -> str:
    """
    发送钉钉消息。
    支持文本消息和@成员
    
    Args:
        webhook_url: 钉钉机器人 Webhook URL（未提供则使用 .env 配置）
        content: 消息内容
        at_mobiles: 需要提醒的手机号列表
        is_atall: 是否@所有人
        
    Returns:
        发送结果
    """
    try:
        import requests
        
        # 如果未提供 webhook_url，从 Settings 读取
        if webhook_url is None:
            from core.config import get_settings
            settings = get_settings()
            webhook_url = settings.notification.dingtalk_webhook_url
        
        if not webhook_url:
            return "错误：未提供 Webhook URL，请传入参数或在 .env 中配置 DINGTALK_WEBHOOK_URL"
        
        # 验证 URL
        is_valid, error_msg = NotificationValidator.validate_webhook_url(webhook_url, 'dingtalk')
        if not is_valid:
            return f"错误：{error_msg}"
        
        # 构建消息
        message = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": is_atall
            }
        }
        
        # 发送请求
        logger.info(f"发送钉钉消息到：{webhook_url[:50]}...")
        response = requests.post(
            webhook_url,
            json=message,
            timeout=10
        )
        
        result = response.json()
        
        if result.get('errcode') == 0:
            logger.info("钉钉消息发送成功")
            return "✓ 钉钉消息发送成功"
        else:
            error_msg = result.get('errmsg', '未知错误')
            logger.error(f"钉钉消息发送失败：{error_msg}")
            return f"✗ 发送失败：{error_msg}"
        
    except ImportError:
        return "错误：需要安装 requests 库，请运行：pip install requests"
    except requests.exceptions.Timeout:
        return "错误：请求超时"
    except Exception as e:
        logger.error(f"发送钉钉消息失败：{e}")
        return f"错误：{str(e)}"


def send_feishu_message(
    webhook_url: Optional[str] = None,
    content: str = "",
    open_ids: Optional[List[str]] = None
) -> str:
    """
    发送飞书消息。
    支持文本消息和@用户
    
    Args:
        webhook_url: 飞书机器人 Webhook URL（未提供则使用 .env 配置）
        content: 消息内容
        open_ids: 需要提醒的用户 ID 列表
        
    Returns:
        发送结果
    """
    try:
        import requests
        
        # 如果未提供 webhook_url，从 Settings 读取
        if webhook_url is None:
            from core.config import get_settings
            settings = get_settings()
            webhook_url = settings.notification.feishu_webhook_url
        
        if not webhook_url:
            return "错误：未提供 Webhook URL，请传入参数或在 .env 中配置 FEISHU_WEBHOOK_URL"
        
        # 验证 URL
        is_valid, error_msg = NotificationValidator.validate_webhook_url(webhook_url, 'feishu')
        if not is_valid:
            return f"错误：{error_msg}"
        
        # 构建消息（飞书使用富文本格式）
        message = {
            "msg_type": "text",
            "content": {
                "text": content
            }
        }
        
        # 发送请求
        logger.info(f"发送飞书消息到：{webhook_url[:50]}...")
        response = requests.post(
            webhook_url,
            json=message,
            timeout=10
        )
        
        result = response.json()
        
        if result.get('StatusCode') == 0 or result.get('code') == 0:
            logger.info("飞书消息发送成功")
            return "✓ 飞书消息发送成功"
        else:
            error_msg = result.get('msg', result.get('message', '未知错误'))
            logger.error(f"飞书消息发送失败：{error_msg}")
            return f"✗ 发送失败：{error_msg}"
        
    except ImportError:
        return "错误：需要安装 requests 库，请运行：pip install requests"
    except requests.exceptions.Timeout:
        return "错误：请求超时"
    except Exception as e:
        logger.error(f"发送飞书消息失败：{e}")
        return f"错误：{str(e)}"


def send_wecom_markdown(
    webhook_url: Optional[str] = None,
    title: str = "",
    markdown_content: str = ""
) -> str:
    """
    发送企业微信 Markdown 消息。
    支持富文本格式
    
    Args:
        webhook_url: 企业微信机器人 Webhook URL（未提供则使用 .env 配置）
        title: 消息标题
        markdown_content: Markdown 格式内容
        
    Returns:
        发送结果
    """
    try:
        import requests
        
        # 如果未提供 webhook_url，从 Settings 读取
        if webhook_url is None:
            from core.config import get_settings
            settings = get_settings()
            webhook_url = settings.notification.wecom_webhook_url
        
        if not webhook_url:
            return "错误：未提供 Webhook URL，请传入参数或在 .env 中配置 WECOM_WEBHOOK_URL"
        
        # 验证 URL
        is_valid, error_msg = NotificationValidator.validate_webhook_url(webhook_url, 'wecom')
        if not is_valid:
            return f"错误：{error_msg}"
        
        # 构建 Markdown 消息
        message = {
            "msgtype": "markdown",
            "markdown": {
                "content": f"## {title}\n\n{markdown_content}"
            }
        }
        
        # 发送请求
        logger.info(f"发送企业微信 Markdown 消息到：{webhook_url[:50]}...")
        response = requests.post(
            webhook_url,
            json=message,
            timeout=10
        )
        
        result = response.json()
        
        if result.get('errcode') == 0:
            logger.info("企业微信 Markdown 消息发送成功")
            return f"✓ 企业微信 Markdown 消息发送成功\n标题：{title}"
        else:
            error_msg = result.get('errmsg', '未知错误')
            logger.error(f"企业微信 Markdown 消息发送失败：{error_msg}")
            return f"✗ 发送失败：{error_msg}"
        
    except ImportError:
        return "错误：需要安装 requests 库，请运行：pip install requests"
    except Exception as e:
        logger.error(f"发送企业微信 Markdown 消息失败：{e}")
        return f"错误：{str(e)}"


def send_dingtalk_markdown(
    webhook_url: Optional[str] = None,
    title: str = "",
    markdown_content: str = ""
) -> str:
    """
    发送钉钉 Markdown 消息。
    支持富文本格式
    
    Args:
        webhook_url: 钉钉机器人 Webhook URL（未提供则使用 .env 配置）
        title: 消息标题
        markdown_content: Markdown 格式内容
        
    Returns:
        发送结果
    """
    try:
        import requests
        
        # 如果未提供 webhook_url，从 Settings 读取
        if webhook_url is None:
            from core.config import get_settings
            settings = get_settings()
            webhook_url = settings.notification.dingtalk_webhook_url
        
        if not webhook_url:
            return "错误：未提供 Webhook URL，请传入参数或在 .env 中配置 DINGTALK_WEBHOOK_URL"
        
        # 验证 URL
        is_valid, error_msg = NotificationValidator.validate_webhook_url(webhook_url, 'dingtalk')
        if not is_valid:
            return f"错误：{error_msg}"
        
        # 构建 Markdown 消息
        message = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": f"## {title}\n\n{markdown_content}"
            }
        }
        
        # 发送请求
        logger.info(f"发送钉钉 Markdown 消息到：{webhook_url[:50]}...")
        response = requests.post(
            webhook_url,
            json=message,
            timeout=10
        )
        
        result = response.json()
        
        if result.get('errcode') == 0:
            logger.info("钉钉 Markdown 消息发送成功")
            return f"✓ 钉钉 Markdown 消息发送成功\n标题：{title}"
        else:
            error_msg = result.get('errmsg', '未知错误')
            logger.error(f"钉钉 Markdown 消息发送失败：{error_msg}")
            return f"✗ 发送失败：{error_msg}"
        
    except ImportError:
        return "错误：需要安装 requests 库，请运行：pip install requests"
    except Exception as e:
        logger.error(f"发送钉钉 Markdown 消息失败：{e}")
        return f"错误：{str(e)}"


# 创建工具实例
wecom_tool = FunctionTool.from_defaults(
    fn=send_wecom_message,
    name="send_wecom_message",
    description="发送企业微信消息（支持@成员）。webhook_url 可选，未提供时使用 .env 中的 WECOM_WEBHOOK_URL",
    fn_schema=WeComInput
)

dingtalk_tool = FunctionTool.from_defaults(
    fn=send_dingtalk_message,
    name="send_dingtalk_message",
    description="发送钉钉消息（支持@成员）。webhook_url 可选，未提供时使用 .env 中的 DINGTALK_WEBHOOK_URL",
    fn_schema=DingTalkInput
)

feishu_tool = FunctionTool.from_defaults(
    fn=send_feishu_message,
    name="send_feishu_message",
    description="发送飞书消息。webhook_url 可选，未提供时使用 .env 中的 FEISHU_WEBHOOK_URL",
    fn_schema=FeishuInput
)

wecom_markdown_tool = FunctionTool.from_defaults(
    fn=send_wecom_markdown,
    name="send_wecom_markdown",
    description="发送企业微信 Markdown 消息。webhook_url 可选，未提供时使用 .env 中的 WECOM_WEBHOOK_URL",
    fn_schema=WeComInput
)

dingtalk_markdown_tool = FunctionTool.from_defaults(
    fn=send_dingtalk_markdown,
    name="send_dingtalk_markdown",
    description="发送钉钉 Markdown 消息。webhook_url 可选，未提供时使用 .env 中的 DINGTALK_WEBHOOK_URL",
    fn_schema=DingTalkInput
)

# 汇总所有通知工具
NOTIFICATION_TOOLS = [
    wecom_tool,
    dingtalk_tool,
    feishu_tool,
    wecom_markdown_tool,
    dingtalk_markdown_tool
]
