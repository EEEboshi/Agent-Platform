# AI Agent Platform

智能体平台 - 一个基于 LlamaIndex 和 FastAPI 的多功能 AI Agent 平台

## 项目结构

```
my_agent_platform/
├── .env                  # 环境变量配置（需自行创建）
├── .gitignore            # Git 忽略文件配置
├── requirements.txt      # Python 依赖
├── run.py                # 统一启动入口
├── README.md             # 项目说明文档
├── INSTALL.md            # 安装指南
├── TOOLS_GUIDE.md        # 工具使用指南
├── tools/                # 自定义工具集（24+ 工具）
│   ├── __init__.py           # 工具导出
│   ├── search_tool.py        # 联网搜索工具
│   ├── math_tool.py          # 数学计算工具
│   ├── email_tool.py         # 邮件发送工具
│   ├── file_tool.py          # 文件处理工具（PDF/Excel/Word/TXT）
│   ├── database_tool.py      # 数据库工具（SQLite/MySQL/PostgreSQL）
│   ├── api_tool.py           # HTTP API 调用工具
│   ├── visualization_tool.py # 数据可视化工具
│   └── notification_tool.py  # 通知工具（企业微信/钉钉/飞书）
├── core/                 # 核心引擎
│   ├── __init__.py           # 模块导出
│   ├── agent.py              # Agent 组装与记忆管理
│   ├── config.py             # 配置管理（pydantic-settings）
│   ├── logging_config.py     # 日志配置
│   └── session_store.py      # 会话存储
├── api/                  # 后端服务
│   ├── __init__.py           # 模块导出
│   └── main.py               # FastAPI 路由
└── ui/                   # 前端界面
    └── app.py                # Gradio 界面
```

## 快速开始

### 1. 环境要求

- Python 3.12+
- Windows 系统

### 2. 安装依赖

```powershell
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件并填写你的 API Key：

```env
# 阿里云通义千问 API Key
DASHSCOPE_API_KEY=your_api_key_here
DASHSCOPE_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_MODEL=qwen-max

# 通知工具 Webhook URL（可选）
WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=xxx
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
```

### 4. 启动服务

#### 方式一：统一启动（推荐）

```powershell
# 同时启动 UI 和 API
python run.py

# 只启动 UI
python run.py --ui

# 只启动 API
python run.py --api

# 检查环境配置
python run.py --check
```

#### 方式二：分别启动

```powershell
# 启动前端界面
python ui/app.py
# 访问：http://localhost:7860

# 启动后端 API
python api/main.py
# 访问：http://localhost:8000
# API 文档：http://localhost:8000/api/docs
```

## API 使用示例

### 健康检查

```bash
GET http://localhost:8000/api/health
```

### 发送消息

```bash
POST http://localhost:8000/api/chat
{
  "session_id": "user_1",
  "message": "你好！"
}
```

### 重置会话

```bash
POST http://localhost:8000/api/reset_session
{
  "session_id": "user_1"
}
```

### 列出活跃会话

```bash
GET http://localhost:8000/api/sessions
```

## 功能特性

### 核心功能

- ✅ **智能体管理** - 基于 session_id 隔离的 Agent 实例，独立记忆
- ✅ **对话记忆** - ChatMemoryBuffer 管理上下文，支持 token 限制
- ✅ **流式输出** - 打字机效果，实时显示回复
- ✅ **REST API** - 完整的 RESTful API 接口，支持 Swagger 文档
- ✅ **Web 界面** - 友好的 Gradio Web 交互界面
- ✅ **配置管理** - pydantic-settings 统一管理环境变量

### 工具系统（24+ 工具）

| 类别 | 工具数 | 功能描述 |
|------|--------|----------|
| 🔍 **搜索工具** | 1 | 联网搜索实时信息、新闻、知识 |
| 🧮 **数学工具** | 1 | 数学表达式计算 |
| 📧 **邮件工具** | 1 | 自动化邮件发送 |
| 📄 **文件处理** | 7 | 读写 PDF、Excel、Word、文本文件 |
| 🗄️ **数据库** | 4 | SQL 查询、数据导出、表结构查看 |
| 🌐 **API 调用** | 5 | 通用 HTTP 请求（GET/POST/PUT/DELETE） |
| 📊 **数据可视化** | 3 | 生成折线图、柱状图、饼图 |
| 🔔 **通知工具** | 5 | 企业微信、钉钉、飞书消息推送 |

## 通知工具配置

### 企业微信

1. 群设置 → 群机器人 → 添加机器人
2. 复制 Webhook URL 到 `.env` 文件

### 钉钉

1. 群设置 → 智能群助手 → 添加机器人
2. 选择"自定义（通过 Webhook 接入）"
3. 复制 Webhook URL 到 `.env` 文件

### 飞书

1. 群设置 → 群机器人 → 添加机器人
2. 选择"自定义机器人"
3. 复制 Webhook URL 到 `.env` 文件

详细配置指南：[NOTIFICATION_SETUP.md](NOTIFICATION_SETUP.md)

## 技术栈

- **核心框架**: LlamaIndex 0.10.43
- **后端**: FastAPI 0.111.0 + Uvicorn
- **前端**: Gradio 4.36.1
- **AI 模型**: 阿里云通义千问（DashScope API，OpenAI 兼容模式）
- **配置管理**: pydantic + python-dotenv
- **搜索**: DuckDuckGo/Bing Search
- **数据处理**: pandas, numexpr
- **可视化**: matplotlib

## 注意事项

1. 首次运行需要配置有效的 API Key
2. 生产环境请使用 Redis 替代内存 Session 存储
3. 邮件功能需要配置 SMTP 服务器信息
4. 通知工具需要配置各平台的 Webhook URL
5. `.env` 文件包含敏感信息，不要提交到代码仓库


