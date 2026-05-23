# tools/__init__.py
from .search_tool import search_tool
from .math_tool import math_tool
from .email_tool import email_tool

# 汇总所有工具
ALL_TOOLS = [search_tool, math_tool, email_tool]
