"""
日志系统模块
支持文本格式和 JSON 格式的结构化日志，便于监控和排查
"""
import logging
import sys
import json
from datetime import datetime
from typing import Optional

from core.config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON 格式日志处理器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # 添加异常信息
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }
        
        # 添加额外字段
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        
        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """文本格式日志处理器（增强版）"""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        logger_name = record.name
        message = record.getMessage()
        
        log_line = f"{timestamp} | {level:8s} | {logger_name:30s} | {message}"
        
        # 添加异常信息
        if record.exc_info and record.exc_info[0] is not None:
            exception_type = record.exc_info[0].__name__
            exception_msg = str(record.exc_info[1])
            log_line += f"\n  └─ Exception: {exception_type}: {exception_msg}"
        
        return log_line


def setup_logging() -> None:
    """
    配置全局日志系统
    根据配置选择文本格式或 JSON 格式
    """
    settings = get_settings()
    
    # 获取日志级别
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # 选择格式化器
    if settings.log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 禁用第三方库的冗余日志
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    
    logging.info(f"日志系统初始化完成，级别：{settings.log_level}，格式：{settings.log_format}")


def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志器
    建议每个模块使用：logger = get_logger(__name__)
    """
    return logging.getLogger(name)


class LogContext:
    """日志上下文管理器（用于添加额外字段）"""
    
    def __init__(self, logger: logging.Logger, **kwargs):
        self.logger = logger
        self.extra_data = kwargs
    
    def info(self, message: str, **kwargs):
        data = {**self.extra_data, **kwargs}
        extra = logging.LogRecord("", 0, "", 0, "", (), None)
        extra.extra_data = data
        self.logger.info(message, extra={"extra_data": data})
    
    def warning(self, message: str, **kwargs):
        data = {**self.extra_data, **kwargs}
        self.logger.warning(message, extra={"extra_data": data})
    
    def error(self, message: str, **kwargs):
        data = {**self.extra_data, **kwargs}
        self.logger.error(message, extra={"extra_data": data})
    
    def debug(self, message: str, **kwargs):
        data = {**self.extra_data, **kwargs}
        self.logger.debug(message, extra={"extra_data": data})
