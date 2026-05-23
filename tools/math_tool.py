# tools/math_tool.py
"""
数学计算工具
支持安全的表达式求值、输入验证和详细的错误提示
"""
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field
import numexpr
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MathInput(BaseModel):
    """数学计算输入验证模型"""
    expression: str = Field(description="要计算的数学表达式，例如：'2 + 2', '(100 * 5) / 2', 'sin(3.14)'")

class MathExpressionValidator:
    """数学表达式验证器"""
    
    # 允许的字符和函数
    ALLOWED_CHARS = set('0123456789.+-*/()^ ')
    ALLOWED_FUNCTIONS = {
        'sin', 'cos', 'tan', 'asin', 'acos', 'atan',
        'sqrt', 'log', 'log10', 'exp', 'abs',
        'pi', 'e'
    }
    
    @staticmethod
    def is_safe_expression(expression: str) -> tuple[bool, str]:
        """
        验证表达式是否安全
        返回：(是否安全，错误信息)
        """
        if not expression or not expression.strip():
            return False, "表达式不能为空"
        
        expression = expression.strip()
        
        # 检查长度限制
        if len(expression) > 200:
            return False, "表达式过长（最大长度 200 字符）"
        
        # 检查字符合法性
        for char in expression:
            if char not in MathExpressionValidator.ALLOWED_CHARS and not char.isalpha():
                return False, f"包含非法字符：'{char}'"
        
        # 检查是否包含危险函数调用
        lower_expr = expression.lower()
        if any(dangerous in lower_expr for dangerous in ['import', 'exec', 'eval', 'open', 'file', 'os', 'sys']):
            return False, "表达式包含不允许的函数或关键字"
        
        # 检查括号匹配
        if expression.count('(') != expression.count(')'):
            return False, "括号不匹配"
        
        # 检查连续运算符
        if re.search(r'[+\-*/]{2,}', expression.replace('**', '')):
            return False, "包含连续的运算符"
        
        # 检查除以零
        if re.search(r'/\s*0+(?![\d.])', expression):
            return False, "包含除以零的操作"
        
        return True, ""
    
    @staticmethod
    def normalize_expression(expression: str) -> str:
        """
        标准化表达式格式
        - 支持 ^ 作为幂运算符
        - 移除多余空格
        """
        expression = expression.strip()
        # 将 ^ 替换为 **（幂运算）
        expression = expression.replace('^', '**')
        return expression

def calculate_math(expression: str) -> str:
    """
    计算复杂的数学表达式。
    当用户需要进行加减乘除、幂运算、三角函数等数学计算时，必须使用此工具。
    
    支持的操作：
    - 基本运算：+ - * / ** (幂)
    - 三角函数：sin, cos, tan, asin, acos, atan
    - 其他函数：sqrt, log, log10, exp, abs
    - 常量：pi, e
    
    特性：
    - 表达式安全验证
    - 详细的错误提示
    - 友好的结果展示
    """
    # 验证表达式安全性
    is_safe, error_msg = MathExpressionValidator.is_safe_expression(expression)
    if not is_safe:
        logger.warning(f"表达式验证失败：{expression} - {error_msg}")
        return f"无效的数学表达式：{error_msg}"
    
    # 标准化表达式
    normalized_expr = MathExpressionValidator.normalize_expression(expression)
    logger.info(f"计算表达式：{normalized_expr}")
    
    try:
        # 使用 numexpr 安全计算
        result = numexpr.evaluate(normalized_expr).item()
        
        # 格式化结果
        if isinstance(result, float):
            # 处理浮点数精度问题
            if abs(result - round(result)) < 1e-10:
                result = round(result)
            else:
                result = round(result, 10)
        
        success_msg = f"计算结果：{expression} = {result}"
        logger.info(f"计算成功：{result}")
        return success_msg
        
    except ZeroDivisionError:
        error_msg = "错误：除以零操作"
        logger.error(error_msg)
        return error_msg
        
    except ValueError as e:
        error_msg = f"数学错误：表达式超出函数定义域或包含无效操作 ({str(e)})"
        logger.error(error_msg)
        return error_msg
        
    except Exception as e:
        error_msg = f"计算失败：{str(e)}"
        logger.error(f"计算错误：{error_msg}")
        return error_msg

# 导出 LlamaIndex 工具实例
math_tool = FunctionTool.from_defaults(
    fn=calculate_math,
    name="calculate_math",
    description="计算数学表达式。支持加减乘除、幂运算、三角函数等。当需要进行精确计算时使用，严禁大模型自己心算。",
    fn_schema=MathInput
)
