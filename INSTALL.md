# 安装指南

## 快速开始

### 1. 克隆项目

```bash
git clone https://gitee.com/shiqwas/agent-platform.git
cd agent-platform
```

### 2. 创建虚拟环境

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的阿里云 DashScope API Key：

```env
DASHSCOPE_API_KEY=your_api_key_here
```

### 5. 启动服务

#### 方式一：启动 UI 界面（推荐）

```bash
python ui/app.py
```

访问：http://localhost:7860

#### 方式二：启动 API 服务

```bash
python api/main.py
```

API 文档：http://localhost:8000/api/docs

#### 方式三：同时启动 UI 和 API

Windows 用户可以直接运行：

```batch
start_server.bat
```

## 常见问题

### 1. 导入错误 `ModuleNotFoundError: No module named 'core'`

确保在项目根目录下运行，并且已正确设置虚拟环境：

```bash
cd e:\AIProgram\my_agent_platform
.\venv\Scripts\activate
python ui/app.py
```

### 2. Hugging Face Hub 导入错误

如果遇到 `ImportError: cannot import name 'HfFolder'` 错误，请确保 huggingface_hub 版本正确：

```bash
pip install "huggingface_hub>=0.23.2,<1.0"
```

### 3. 端口被占用

如果端口 7860 或 8000 被占用，可以修改启动参数：

```bash
# UI 端口
python ui/app.py --server-port 7861

# API 端口
# 修改 api/main.py 中的端口号
```

### 4. 搜索工具无法使用

如果在国内使用 DuckDuckGo 搜索不稳定，可以配置代理：

```env
SEARCH_PROXY=http://127.0.0.1:7890
```

## 环境变量说明

### 必需配置

- `DASHSCOPE_API_KEY`: 阿里云 DashScope API 密钥

### 可选配置

#### Agent 配置
- `DASHSCOPE_API_BASE`: API 基础地址（默认：https://dashscope.aliyuncs.com/compatible-mode/v1）
- `DASHSCOPE_MODEL`: 模型名称（默认：qwen-max）
- `AGENT_TEMPERATURE`: 温度参数（默认：0.1）
- `AGENT_MEMORY_TOKEN_LIMIT`: 记忆 token 限制（默认：8000）

#### 搜索工具配置
- `SEARCH_MAX_RESULTS`: 最大搜索结果数（默认：5）
- `SEARCH_TIMEOUT`: 搜索超时（秒）（默认：10）
- `SEARCH_MAX_RETRIES`: 最大重试次数（默认：3）
- `SEARCH_PROXY`: 代理地址（可选）

## 依赖说明

核心依赖：
- `llama-index-core==0.10.43`: LlamaIndex 核心库
- `gradio==4.36.1`: Web 界面
- `fastapi==0.111.0`: API 框架
- `huggingface_hub>=0.23.2,<1.0`: Hugging Face 客户端（注意版本限制）

完整依赖列表请查看 `requirements.txt`。

## 测试

运行测试脚本：

```bash
python core/agent.py
```

输入问题测试 Agent 功能。

## 获取帮助

如有问题，请查看日志输出或提交 Issue。
