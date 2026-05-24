# tools/__init__.py

# 原有工具
from .search_tool import search_tool
from .math_tool import math_tool
from .email_tool import email_tool

# 文件处理工具
from .file_tool import (
    read_text_tool,
    write_text_tool,
    read_excel_tool,
    write_excel_tool,
    read_word_tool,
    write_word_tool,
    read_pdf_tool,
    FILE_TOOLS
)

# 数据库工具
from .database_tool import (
    query_tool,
    export_tool,
    list_tables_tool,
    get_schema_tool,
    DATABASE_TOOLS
)

# API 调用工具
from .api_tool import (
    http_request_tool,
    get_tool,
    post_tool,
    put_tool,
    delete_tool,
    API_TOOLS
)

# 数据可视化工具
from .visualization_tool import (
    chart_tool,
    multi_series_chart_tool,
    comparison_chart_tool,
    VISUALIZATION_TOOLS
)

# 通知工具
from .notification_tool import (
    wecom_tool,
    dingtalk_tool,
    feishu_tool,
    wecom_markdown_tool,
    dingtalk_markdown_tool,
    NOTIFICATION_TOOLS
)

# 汇总所有工具
ALL_TOOLS = [
    # 原有工具
    search_tool,
    math_tool,
    email_tool,
    # 文件处理工具
    *FILE_TOOLS,
    # 数据库工具
    *DATABASE_TOOLS,
    # API 调用工具
    *API_TOOLS,
    # 数据可视化工具
    *VISUALIZATION_TOOLS,
    # 通知工具
    *NOTIFICATION_TOOLS,
]

# 工具分类字典
TOOLS_BY_CATEGORY = {
    'basic': [search_tool, math_tool, email_tool],
    'file': FILE_TOOLS,
    'database': DATABASE_TOOLS,
    'api': API_TOOLS,
    'visualization': VISUALIZATION_TOOLS,
    'notification': NOTIFICATION_TOOLS,
}

def get_tools_by_category(category: str):
    """
    根据类别获取工具
    
    Args:
        category: 工具类别（basic/file/database/api/visualization/notification）
        
    Returns:
        对应类别的工具列表
    """
    return TOOLS_BY_CATEGORY.get(category, [])

def get_tool_names() -> list[str]:
    """获取所有工具名称列表"""
    return [tool.name for tool in ALL_TOOLS]

def print_tool_info():
    """打印工具信息"""
    print("=" * 60)
    print("多功能 AI Agent 平台 - 工具列表")
    print("=" * 60)
    
    for category, tools in TOOLS_BY_CATEGORY.items():
        print(f"\n【{category.upper()}】类别工具：")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description}")
    
    print(f"\n总计：{len(ALL_TOOLS)} 个工具")
    print("=" * 60)
