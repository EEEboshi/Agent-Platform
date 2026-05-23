# Agent Platform

智能体平台 - 一个基于 LlamaIndex 和 FastAPI 的 AI Agent 平台

## 项目结构

```
my_agent_platform/
├── .env                  # API Keys 配置
├── requirements.txt      # Python 依赖
├── tools/                # 自定义工具集
│   ├── search_tool.py   # 联网搜索工具
│   ├── math_tool.py     # 数学计算工具
│   └── email_tool.py    # 邮件发送工具
├── core/                 # 核心引擎
│   └── agent.py         # Agent 组装与记忆管理
├── api/                  # 后端服务
│   └── main.py          # FastAPI 路由
└── ui/                   # 前端界面
    └── app.py           # Gradio 界面
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

### 3. 配置 API Key

编辑 `.env` 文件，填入你的 API Key：

```env
OPENAI_API_KEY=sk-your-api-key-here
```

### 4. 启动服务

#### 方式一：启动后端 API 服务

```powershell
.\start_server.bat
```

或手动启动：

```powershell
.\venv\Scripts\Activate.ps1
python api\main.py
```

服务将在 http://localhost:8000 启动

#### 方式二：启动前端界面

```powershell
.\start_ui.bat
```

或手动启动：

```powershell
.\venv\Scripts\Activate.ps1
python ui\app.py
```

界面将在 http://localhost:7860 启动

## API 使用示例

### 创建智能体

```bash
POST http://localhost:8000/agents
{
  "name": "MyAssistant",
  "model": "gpt-4"
}
```

### 发送消息

```bash
POST http://localhost:8000/chat
{
  "agent_id": "agent_1",
  "message": "你好！"
}
```

### 使用工具

```bash
POST http://localhost:8000/agents/{agent_id}/tools/use
{
  "tool_name": "search",
  "method": "search",
  "params": {"query": "Python 3.12 新特性"}
}
```

## 功能特性

- ✅ **智能体管理** - 创建、配置和管理多个 AI 智能体
- ✅ **对话记忆** - 自动保存和管理对话历史
- ✅ **工具系统** - 支持搜索、数学计算、邮件发送等工具
- ✅ **REST API** - 完整的 RESTful API 接口
- ✅ **Web 界面** - 友好的 Gradio Web 交互界面
- ✅ **Python 3.12 兼容** - 完全兼容最新 Python 版本

## 注意事项

1. 首次运行需要配置有效的 API Key
2. 生产环境请使用 Redis 替代内存 Session 存储
3. 邮件功能需要配置 SMTP 服务器信息

## 技术栈

- **核心框架**: LlamaIndex 0.10.43
- **后端**: FastAPI 0.111.0
- **前端**: Gradio 4.36.1
- **AI 模型**: OpenAI GPT-4
- **搜索**: DuckDuckGo Search

## 许可证

MIT License
