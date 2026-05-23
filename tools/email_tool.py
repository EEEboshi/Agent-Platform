# tools/email_tool.py
"""
邮件发送工具
支持邮件格式验证、模板功能和错误处理
"""
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field, EmailStr
import logging
import time
import re
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailInput(BaseModel):
    """邮件输入验证模型"""
    to_email: str = Field(description="收件人邮箱地址")
    subject: str = Field(description="邮件主题")
    body: str = Field(description="邮件正文内容")
    cc_email: Optional[str] = Field(default=None, description="抄送邮箱地址（可选）")

class EmailValidator:
    """邮箱验证器"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """验证邮箱格式"""
        if not email:
            return False
        
        # 基础邮箱格式验证
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_email_list(emails: str) -> tuple[bool, str]:
        """
        验证邮箱列表（支持逗号或分号分隔）
        返回：(是否有效，错误信息)
        """
        if not emails:
            return True, ""
        
        # 分割多个邮箱
        separator = ';' if ';' in emails else ','
        email_list = [e.strip() for e in emails.split(separator) if e.strip()]
        
        for email in email_list:
            if not EmailValidator.is_valid_email(email):
                return False, f"无效的邮箱地址：{email}"
        
        return True, ""

# 邮件模板
EMAIL_TEMPLATES = {
    "notification": """
尊敬的 {recipient}：

{content}

此致
敬礼

{sender}
""",
    "report": """
主题报告：{subject}

{content}

---
发送时间：{timestamp}
""",
    "reminder": """
提醒：{subject}

{content}

请及时处理，谢谢！
"""
}

def send_automated_email(
    to_email: str, 
    subject: str, 
    body: str,
    cc_email: Optional[str] = None
) -> str:
    """
    发送自动化电子邮件。
    当用户明确要求发送邮件、通知某人或发送报告时，使用此工具。
    
    特性：
    - 邮箱格式验证
    - 支持抄送功能
    - 详细的错误信息
    - 模拟发送延迟
    """
    # 验证收件人邮箱
    is_valid, error_msg = EmailValidator.validate_email_list(to_email)
    if not is_valid:
        return f"邮箱格式错误：{error_msg}"
    
    # 验证抄送邮箱（如果有）
    if cc_email:
        is_valid, error_msg = EmailValidator.validate_email_list(cc_email)
        if not is_valid:
            return f"抄送邮箱格式错误：{error_msg}"
    
    # 验证邮件内容
    if not subject or not subject.strip():
        return "邮件主题不能为空"
    
    if not body or not body.strip():
        return "邮件正文不能为空"
    
    try:
        logger.info(f"准备发送邮件到：{to_email}")
        if cc_email:
            logger.info(f"抄送到：{cc_email}")
        logger.info(f"主题：{subject}")
        
        # 模拟网络延迟（实际使用时应调用真实邮件 API）
        time.sleep(1.5)
        
        # 模拟发送（生产环境应替换为真实邮件服务）
        print("\n" + "="*60)
        print("📧 邮件发送模拟")
        print("="*60)
        print(f"收件人：{to_email}")
        if cc_email:
            print(f"抄送：{cc_email}")
        print(f"主题：{subject}")
        print(f"正文：\n{body}")
        print("="*60 + "\n")
        
        # 返回成功信息
        result_msg = f"邮件已成功发送到 {to_email}"
        if cc_email:
            result_msg += f" (抄送：{cc_email})"
        result_msg += f"，主题：'{subject}'"
        
        logger.info("邮件发送成功")
        return result_msg
        
    except Exception as e:
        error_msg = f"邮件发送失败：{str(e)}"
        logger.error(error_msg)
        return error_msg

# 导出 LlamaIndex 工具实例
email_tool = FunctionTool.from_defaults(
    fn=send_automated_email,
    name="send_automated_email",
    description="发送自动化电子邮件。仅在用户明确要求发送邮件时使用。支持邮箱格式验证和抄送功能。",
    fn_schema=EmailInput
)
