"""
配置管理模块
使用 pydantic-settings 统一管理所有配置项，支持环境变量和 .env 文件
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class LLMSettings(BaseSettings):
    """大语言模型配置"""
    api_key: str = Field(..., description="API 密钥", alias="DASHSCOPE_API_KEY")
    api_base: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="API 基础 URL",
        alias="DASHSCOPE_API_BASE"
    )
    model: str = Field(default="qwen-max", description="模型名称", alias="DASHSCOPE_MODEL")
    temperature: float = Field(default=0.1, ge=0.0, le=2.0, description="温度参数", alias="AGENT_TEMPERATURE")
    timeout: int = Field(default=30, ge=1, description="请求超时时间（秒）", alias="LLM_TIMEOUT")
    max_retries: int = Field(default=2, ge=0, description="最大重试次数", alias="LLM_MAX_RETRIES")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True


class MemorySettings(BaseSettings):
    """记忆管理配置"""
    token_limit: int = Field(default=8000, ge=1000, description="记忆 token 限制", alias="AGENT_MEMORY_TOKEN_LIMIT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True


class AgentSettings(BaseSettings):
    """Agent 行为配置"""
    max_function_calls: int = Field(default=10, ge=1, le=50, description="单次对话最大工具调用次数", alias="AGENT_MAX_FUNCTION_CALLS")
    verbose: bool = Field(default=True, description="是否输出详细日志", alias="AGENT_VERBOSE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True


class SearchSettings(BaseSettings):
    """搜索工具配置"""
    max_results: int = Field(default=5, ge=1, le=20, description="最大搜索结果数量", alias="SEARCH_MAX_RESULTS")
    timeout: int = Field(default=10, ge=1, description="搜索请求超时（秒）", alias="SEARCH_TIMEOUT")
    max_retries: int = Field(default=3, ge=0, description="搜索最大重试次数", alias="SEARCH_MAX_RETRIES")
    retry_delay: float = Field(default=1.0, ge=0, description="重试延迟（秒）", alias="SEARCH_RETRY_DELAY")
    proxy: Optional[str] = Field(default=None, description="代理服务器地址", alias="SEARCH_PROXY")
    search_engine: str = Field(default="bing", description="搜索引擎（bing/baidu）", alias="SEARCH_ENGINE")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True


class RedisSettings(BaseSettings):
    """Redis 配置"""
    enabled: bool = Field(default=False, description="是否启用 Redis", alias="REDIS_ENABLED")
    host: str = Field(default="localhost", description="Redis 主机地址", alias="REDIS_HOST")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis 端口", alias="REDIS_PORT")
    db: int = Field(default=0, ge=0, le=15, description="Redis 数据库编号", alias="REDIS_DB")
    password: Optional[str] = Field(default=None, description="Redis 密码", alias="REDIS_PASSWORD")
    key_prefix: str = Field(default="agent_session:", description="Session 键前缀", alias="REDIS_KEY_PREFIX")
    session_ttl: int = Field(default=3600, ge=60, description="Session 过期时间（秒）", alias="REDIS_SESSION_TTL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True


class ServerSettings(BaseSettings):
    """服务器配置"""
    host: str = Field(default="127.0.0.1", description="服务器监听地址", alias="SERVER_HOST")
    port: int = Field(default=8000, ge=1, le=65535, description="服务器端口", alias="SERVER_PORT")
    cors_origins: list[str] = Field(
        default=["http://localhost:7860", "http://127.0.0.1:7860", "http://localhost:3000", "http://127.0.0.1:3000"],
        description="允许的 CORS 源",
        alias="CORS_ORIGINS"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True


class NotificationSettings(BaseSettings):
    """通知工具配置"""
    wecom_webhook_url: Optional[str] = Field(default=None, description="企业微信 Webhook URL", alias="WECOM_WEBHOOK_URL")
    dingtalk_webhook_url: Optional[str] = Field(default=None, description="钉钉 Webhook URL", alias="DINGTALK_WEBHOOK_URL")
    feishu_webhook_url: Optional[str] = Field(default=None, description="飞书 Webhook URL", alias="FEISHU_WEBHOOK_URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True


class Settings(BaseSettings):
    """全局配置（聚合所有子配置）"""
    llm: LLMSettings = LLMSettings()
    memory: MemorySettings = MemorySettings()
    agent: AgentSettings = AgentSettings()
    search: SearchSettings = SearchSettings()
    redis: RedisSettings = RedisSettings()
    server: ServerSettings = ServerSettings()
    notification: NotificationSettings = NotificationSettings()
    
    app_name: str = Field(default="AI Agent Platform", description="应用名称", alias="APP_NAME")
    debug: bool = Field(default=False, description="调试模式", alias="DEBUG")
    log_level: str = Field(default="INFO", description="日志级别", alias="LOG_LEVEL")
    log_format: str = Field(default="text", description="日志格式（text/json）", alias="LOG_FORMAT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        populate_by_name = True


@lru_cache()
def get_settings() -> Settings:
    """
    获取全局配置实例（带缓存）
    使用 lru_cache 确保配置只加载一次，提升性能
    """
    return Settings()


def reload_settings() -> Settings:
    """
    重新加载配置（清除缓存）
    用于热更新配置场景
    """
    get_settings.cache_clear()
    return get_settings()
