"""
Session 存储管理模块
支持内存存储和 Redis 存储双模式，可根据配置自动切换
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
import logging
import json
from datetime import datetime

from core.config import get_settings

logger = logging.getLogger(__name__)


class BaseSessionStore(ABC):
    """Session 存储抽象基类"""
    
    @abstractmethod
    def get(self, session_id: str) -> Optional[Any]:
        """获取 session"""
        pass
    
    @abstractmethod
    def set(self, session_id: str, value: Any) -> None:
        """设置 session"""
        pass
    
    @abstractmethod
    def delete(self, session_id: str) -> bool:
        """删除 session"""
        pass
    
    @abstractmethod
    def exists(self, session_id: str) -> bool:
        """检查 session 是否存在"""
        pass
    
    @abstractmethod
    def list_all(self) -> list[str]:
        """列出所有 session"""
        pass
    
    @abstractmethod
    def clear(self) -> int:
        """清空所有 session，返回清空数量"""
        pass


class MemorySessionStore(BaseSessionStore):
    """内存 Session 存储（默认实现）"""
    
    def __init__(self):
        self._store: dict[str, Any] = {}
        logger.info("使用内存 Session 存储")
    
    def get(self, session_id: str) -> Optional[Any]:
        return self._store.get(session_id)
    
    def set(self, session_id: str, value: Any) -> None:
        self._store[session_id] = value
    
    def delete(self, session_id: str) -> bool:
        if session_id in self._store:
            del self._store[session_id]
            logger.info(f"Session 已删除：{session_id}")
            return True
        return False
    
    def exists(self, session_id: str) -> bool:
        return session_id in self._store
    
    def list_all(self) -> list[str]:
        return list(self._store.keys())
    
    def clear(self) -> int:
        count = len(self._store)
        self._store.clear()
        logger.info(f"已清空 {count} 个 session")
        return count


class RedisSessionStore(BaseSessionStore):
    """Redis Session 存储（生产环境推荐）"""
    
    def __init__(self):
        try:
            import redis
            settings = get_settings()
            redis_config = settings.redis
            
            self._redis = redis.Redis(
                host=redis_config.host,
                port=redis_config.port,
                db=redis_config.db,
                password=redis_config.password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            
            self._key_prefix = redis_config.key_prefix
            self._ttl = redis_config.session_ttl
            
            # 测试连接
            self._redis.ping()
            logger.info(f"Redis Session 存储已连接：{redis_config.host}:{redis_config.port}")
            
        except ImportError:
            logger.error("未安装 redis 包，请运行：pip install redis")
            raise
        except Exception as e:
            logger.error(f"Redis 连接失败：{e}，将降级为内存存储")
            raise
    
    def _make_key(self, session_id: str) -> str:
        """生成 Redis key"""
        return f"{self._key_prefix}{session_id}"
    
    def get(self, session_id: str) -> Optional[Any]:
        try:
            key = self._make_key(session_id)
            data = self._redis.get(key)
            if data is None:
                return None
            
            # 反序列化（注意：Agent 实例无法序列化，此方法仅适用于存储简单数据）
            # 对于 Agent 实例，建议使用内存存储或自定义序列化
            return json.loads(data)
        except Exception as e:
            logger.error(f"获取 Session 失败：{e}")
            return None
    
    def set(self, session_id: str, value: Any) -> None:
        try:
            key = self._make_key(session_id)
            # 序列化
            data = json.dumps(value, default=str)
            self._redis.setex(key, self._ttl, data)
        except Exception as e:
            logger.error(f"设置 Session 失败：{e}")
            raise
    
    def delete(self, session_id: str) -> bool:
        try:
            key = self._make_key(session_id)
            result = self._redis.delete(key)
            if result > 0:
                logger.info(f"Session 已删除：{session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"删除 Session 失败：{e}")
            return False
    
    def exists(self, session_id: str) -> bool:
        try:
            key = self._make_key(session_id)
            return self._redis.exists(key) > 0
        except Exception as e:
            logger.error(f"检查 Session 失败：{e}")
            return False
    
    def list_all(self) -> list[str]:
        try:
            pattern = f"{self._key_prefix}*"
            keys = self._redis.keys(pattern)
            # 提取 session_id
            prefix_len = len(self._key_prefix)
            return [key[prefix_len:] for key in keys]
        except Exception as e:
            logger.error(f"列出 Session 失败：{e}")
            return []
    
    def clear(self) -> int:
        try:
            pattern = f"{self._key_prefix}*"
            keys = self._redis.keys(pattern)
            if keys:
                count = self._redis.delete(*keys)
                logger.info(f"已清空 {count} 个 session")
                return count
            return 0
        except Exception as e:
            logger.error(f"清空 Session 失败：{e}")
            return 0


class SessionStoreManager:
    """Session 存储管理器（工厂模式）"""
    
    _instance: Optional['SessionStoreManager'] = None
    _store: BaseSessionStore = None
    
    def __new__(cls) -> 'SessionStoreManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        settings = get_settings()
        
        # 根据配置选择存储后端
        if settings.redis.enabled:
            try:
                self._store = RedisSessionStore()
            except Exception as e:
                logger.warning(f"Redis 不可用，降级为内存存储：{e}")
                self._store = MemorySessionStore()
        else:
            self._store = MemorySessionStore()
        
        self._initialized = True
        logger.info(f"Session 存储管理器初始化完成，当前模式：{type(self._store).__name__}")
    
    def get(self, session_id: str) -> Optional[Any]:
        """获取 session"""
        return self._store.get(session_id)
    
    def set(self, session_id: str, value: Any) -> None:
        """设置 session"""
        self._store.set(session_id, value)
    
    def delete(self, session_id: str) -> bool:
        """删除 session"""
        return self._store.delete(session_id)
    
    def exists(self, session_id: str) -> bool:
        """检查 session 是否存在"""
        return self._store.exists(session_id)
    
    def list_all(self) -> list[str]:
        """列出所有 session"""
        return self._store.list_all()
    
    def clear(self) -> int:
        """清空所有 session"""
        return self._store.clear()
    
    @property
    def store_type(self) -> str:
        """获取当前存储类型"""
        return type(self._store).__name__
    
    @property
    def count(self) -> int:
        """获取 session 数量"""
        return len(self.list_all())


# 全局单例
session_store = SessionStoreManager()
