"""
数据库工具
支持 SQL 查询、数据导出、数据库连接管理
"""
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnectionInput(BaseModel):
    """数据库连接输入模型"""
    db_type: str = Field(description="数据库类型：sqlite, mysql, postgresql")
    db_path: Optional[str] = Field(default=None, description="数据库文件路径（SQLite 使用）")
    host: Optional[str] = Field(default=None, description="数据库主机地址（MySQL/PostgreSQL 使用）")
    port: Optional[int] = Field(default=None, description="数据库端口")
    database: Optional[str] = Field(default=None, description="数据库名称")
    user: Optional[str] = Field(default=None, description="用户名")
    password: Optional[str] = Field(default=None, description="密码")


class SQLQueryInput(BaseModel):
    """SQL 查询输入模型"""
    query: str = Field(description="SQL 查询语句")
    db_type: str = Field(description="数据库类型：sqlite, mysql, postgresql")
    db_path: Optional[str] = Field(default=None, description="数据库路径（SQLite）")
    host: Optional[str] = Field(default=None, description="数据库主机（MySQL/PostgreSQL）")
    port: Optional[int] = Field(default=None, description="数据库端口")
    database: Optional[str] = Field(default=None, description="数据库名称")
    user: Optional[str] = Field(default=None, description="用户名")
    password: Optional[str] = Field(default=None, description="密码")


class ExportDataInput(BaseModel):
    """数据导出输入模型"""
    query: str = Field(description="SQL 查询语句")
    output_file: str = Field(description="输出文件路径（.csv, .xlsx, .json）")
    db_type: str = Field(description="数据库类型")
    db_path: Optional[str] = Field(default=None, description="数据库路径（SQLite）")
    host: Optional[str] = Field(default=None, description="数据库主机")
    port: Optional[int] = Field(default=None, description="数据库端口")
    database: Optional[str] = Field(default=None, description="数据库名称")
    user: Optional[str] = Field(default=None, description="用户名")
    password: Optional[str] = Field(default=None, description="密码")


class DatabaseConnection:
    """数据库连接管理器"""
    
    @staticmethod
    def get_connection(
        db_type: str,
        db_path: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None
    ):
        """获取数据库连接"""
        try:
            if db_type == 'sqlite':
                import sqlite3
                if not db_path:
                    return None, "SQLite 数据库路径不能为空"
                conn = sqlite3.connect(db_path)
                return conn, None
                
            elif db_type == 'mysql':
                import pymysql
                if not all([host, database, user]):
                    return None, "MySQL 连接需要 host, database, user 参数"
                conn = pymysql.connect(
                    host=host,
                    port=port or 3306,
                    database=database,
                    user=user,
                    password=password or '',
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor
                )
                return conn, None
                
            elif db_type == 'postgresql':
                import psycopg2
                if not all([host, database, user]):
                    return None, "PostgreSQL 连接需要 host, database, user 参数"
                conn = psycopg2.connect(
                    host=host,
                    port=port or 5432,
                    database=database,
                    user=user,
                    password=password or ''
                )
                return conn, None
            else:
                return None, f"不支持的数据库类型：{db_type}"
                
        except ImportError as e:
            return None, f"缺少数据库驱动：{str(e)}"
        except Exception as e:
            return None, f"数据库连接失败：{str(e)}"


class SQLValidator:
    """SQL 验证器"""
    
    DANGEROUS_KEYWORDS = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'GRANT', 'REVOKE']
    
    @staticmethod
    def is_safe_query(query: str, allow_write: bool = False) -> tuple[bool, str]:
        """验证 SQL 查询是否安全"""
        if not query or not query.strip():
            return False, "SQL 查询不能为空"
        
        query_upper = query.upper().strip()
        
        # 检查危险操作
        if not allow_write:
            for keyword in SQLValidator.DANGEROUS_KEYWORDS:
                if keyword in query_upper:
                    return False, f"不允许的操作：{keyword}"
        
        # 只允许 SELECT 查询（默认模式）
        if not allow_write and not query_upper.startswith('SELECT'):
            return False, "默认只允许 SELECT 查询"
        
        # 检查长度
        if len(query) > 10000:
            return False, "SQL 查询过长"
        
        return True, ""


def execute_query(
    query: str,
    db_type: str,
    db_path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None
) -> str:
    """
    执行 SQL 查询。
    支持 SQLite, MySQL, PostgreSQL
    
    Args:
        query: SQL 查询语句
        db_type: 数据库类型（sqlite/mysql/postgresql）
        db_path: SQLite 数据库路径
        host: 数据库主机地址
        port: 数据库端口
        database: 数据库名称
        user: 用户名
        password: 密码
        
    Returns:
        查询结果（CSV 格式）
    """
    # 验证 SQL
    is_safe, error_msg = SQLValidator.is_safe_query(query)
    if not is_safe:
        return f"错误：{error_msg}"
    
    # 获取连接
    conn, error = DatabaseConnection.get_connection(
        db_type, db_path, host, port, database, user, password
    )
    if error:
        return f"错误：{error}"
    
    try:
        import pandas as pd
        
        cursor = conn.cursor()
        cursor.execute(query)
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # 获取数据
        rows = cursor.fetchall()
        
        # 转换为 DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        # 转换为 CSV 格式
        csv_result = df.to_csv(index=False)
        
        logger.info(f"查询成功，返回 {len(rows)} 行数据")
        
        cursor.close()
        conn.close()
        
        return csv_result
        
    except ImportError:
        return "错误：需要安装 pandas，请运行：pip install pandas"
    except Exception as e:
        logger.error(f"查询执行失败：{e}")
        return f"查询失败：{str(e)}"
    finally:
        if conn:
            conn.close()


def export_to_file(
    query: str,
    output_file: str,
    db_type: str,
    db_path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None
) -> str:
    """
    导出查询结果到文件。
    支持 CSV, Excel, JSON 格式
    
    Args:
        query: SQL 查询语句
        output_file: 输出文件路径
        db_type: 数据库类型
        db_path: SQLite 数据库路径
        host: 数据库主机地址
        port: 数据库端口
        database: 数据库名称
        user: 用户名
        password: 密码
        
    Returns:
        导出结果
    """
    # 验证 SQL
    is_safe, error_msg = SQLValidator.is_safe_query(query)
    if not is_safe:
        return f"错误：{error_msg}"
    
    # 检查输出文件扩展名
    output_path = Path(output_file)
    file_ext = output_path.suffix.lower()
    
    if file_ext not in ['.csv', '.xlsx', '.json']:
        return f"错误：不支持的导出格式：{file_ext}，支持 .csv, .xlsx, .json"
    
    # 获取连接
    conn, error = DatabaseConnection.get_connection(
        db_type, db_path, host, port, database, user, password
    )
    if error:
        return f"错误：{error}"
    
    try:
        import pandas as pd
        import json
        
        cursor = conn.cursor()
        cursor.execute(query)
        
        # 获取列名
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # 获取数据
        rows = cursor.fetchall()
        
        # 转换为 DataFrame
        df = pd.DataFrame(rows, columns=columns)
        
        # 根据扩展名导出
        if file_ext == '.csv':
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
        elif file_ext == '.xlsx':
            df.to_excel(output_file, index=False)
        elif file_ext == '.json':
            df.to_json(output_file, orient='records', force_ascii=False, indent=2)
        
        logger.info(f"成功导出 {len(rows)} 行数据到：{output_file}")
        return f"成功导出 {len(rows)} 行数据到：{output_file}"
        
    except ImportError:
        return "错误：需要安装 pandas 和 openpyxl，请运行：pip install pandas openpyxl"
    except Exception as e:
        logger.error(f"导出失败：{e}")
        return f"导出失败：{str(e)}"
    finally:
        if conn:
            conn.close()


def list_tables(
    db_type: str,
    db_path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None
) -> str:
    """
    列出数据库中的所有表。
    
    Args:
        db_type: 数据库类型
        db_path: SQLite 数据库路径
        host: 数据库主机地址
        port: 数据库端口
        database: 数据库名称
        user: 用户名
        password: 密码
        
    Returns:
        表名列表
    """
    # 获取连接
    conn, error = DatabaseConnection.get_connection(
        db_type, db_path, host, port, database, user, password
    )
    if error:
        return f"错误：{error}"
    
    try:
        cursor = conn.cursor()
        
        # 根据不同数据库类型获取表名
        if db_type == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        elif db_type == 'mysql':
            cursor.execute("SHOW TABLES")
        elif db_type == 'postgresql':
            cursor.execute("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' 
                ORDER BY tablename
            """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        logger.info(f"找到 {len(tables)} 个表")
        return "\n".join(tables)
        
    except Exception as e:
        logger.error(f"获取表列表失败：{e}")
        return f"获取失败：{str(e)}"
    finally:
        if conn:
            conn.close()


def get_table_schema(
    table_name: str,
    db_type: str,
    db_path: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None
) -> str:
    """
    获取表结构信息。
    
    Args:
        table_name: 表名
        db_type: 数据库类型
        db_path: SQLite 数据库路径
        host: 数据库主机地址
        port: 数据库端口
        database: 数据库名称
        user: 用户名
        password: 密码
        
    Returns:
        表结构信息
    """
    # 获取连接
    conn, error = DatabaseConnection.get_connection(
        db_type, db_path, host, port, database, user, password
    )
    if error:
        return f"错误：{error}"
    
    try:
        cursor = conn.cursor()
        
        # 根据不同数据库类型获取表结构
        if db_type == 'sqlite':
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            schema_info = "列名 | 类型 | 是否 NULL | 默认值\n"
            schema_info += "-" * 50 + "\n"
            for col in columns:
                schema_info += f"{col[1]} | {col[2]} | {'NOT NULL' if col[3] else 'NULL'} | {col[4] or ''}\n"
                
        elif db_type == 'mysql':
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            schema_info = "列名 | 类型 | 是否 NULL | 键 | 默认值\n"
            schema_info += "-" * 60 + "\n"
            for col in columns:
                schema_info += f"{col[0]} | {col[1]} | {col[2]} | {col[3] or ''} | {col[4] or ''}\n"
                
        elif db_type == 'postgresql':
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cursor.fetchall()
            schema_info = "列名 | 类型 | 是否 NULL | 默认值\n"
            schema_info += "-" * 50 + "\n"
            for col in columns:
                schema_info += f"{col[0]} | {col[1]} | {col[2]} | {col[3] or ''}\n"
        
        cursor.close()
        conn.close()
        
        logger.info(f"获取表 {table_name} 的结构信息")
        return schema_info
        
    except Exception as e:
        logger.error(f"获取表结构失败：{e}")
        return f"获取失败：{str(e)}"
    finally:
        if conn:
            conn.close()


# 创建工具实例
query_tool = FunctionTool.from_defaults(
    fn=execute_query,
    name="execute_query",
    description="执行 SQL 查询（SELECT），支持 SQLite/MySQL/PostgreSQL",
    fn_schema=SQLQueryInput
)

export_tool = FunctionTool.from_defaults(
    fn=export_to_file,
    name="export_data",
    description="导出查询结果到文件（CSV/Excel/JSON）",
    fn_schema=ExportDataInput
)

list_tables_tool = FunctionTool.from_defaults(
    fn=list_tables,
    name="list_tables",
    description="列出数据库中的所有表",
    fn_schema=DatabaseConnectionInput
)

get_schema_tool = FunctionTool.from_defaults(
    fn=get_table_schema,
    name="get_table_schema",
    description="获取表结构信息",
    fn_schema=DatabaseConnectionInput
)

# 汇总所有数据库工具
DATABASE_TOOLS = [
    query_tool,
    export_tool,
    list_tables_tool,
    get_schema_tool
]
