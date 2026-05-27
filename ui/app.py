# ui/app.py
"""
用户界面模块
基于 Gradio 构建的 Web 聊天界面，支持流式输出和会话管理
"""
import sys
from pathlib import Path
import os

# 添加项目根目录到 Python 路径
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))
os.chdir(str(root_dir))

import gradio as gr
from core.agent import create_agent
from core.logging_config import setup_logging, get_logger
import uuid
from datetime import datetime

# 初始化日志系统
setup_logging()
logger = get_logger(__name__)

# 存储 Gradio 会话状态的字典
user_agents = {}

def get_agent(session_id):
    """获取现有 Agent 或创建新 Agent"""
    if session_id not in user_agents:
        logger.info(f"为新会话创建 Agent: {session_id}")
        try:
            user_agents[session_id] = create_agent(session_id)
        except Exception as e:
            logger.error(f"创建 Agent 失败：{e}", exc_info=True)
            raise
    return user_agents[session_id]

def chat_stream(message, history, session_id):
    """
    处理流式对话
    使用打字机效果逐步显示回复
    """
    if not session_id:
        session_id = str(uuid.uuid4())
        logger.info(f"创建新会话 ID: {session_id}")
    
    try:
        agent = get_agent(session_id)
        
        # 使用 stream_chat 实现打字机效果
        stream_response = agent.stream_chat(message)
        
        partial_message = ""
        for token in stream_response.response_gen:
            partial_message += token
            yield partial_message, session_id
            
    except Exception as e:
        error_msg = f"❌ 错误：{str(e)}"
        logger.error(f"聊天处理失败：{e}", exc_info=True)
        yield error_msg, session_id

def reset_chat(session_id):
    """重置对话"""
    if session_id and session_id in user_agents:
        del user_agents[session_id]
        logger.info(f"会话已重置：{session_id}")
    return [], None

def get_welcome_message():
    """获取欢迎消息"""
    return """
## 🎯 欢迎使用 AI 智能体助手

我是一个多功能 AI 助手，基于通义千问大模型构建，支持多种实用工具。

### ✨ 核心功能

| 功能 | 说明 | 示例 |
|------|------|------|
| 🔍 **联网搜索** | 查询实时信息、新闻、知识 | "今天北京天气怎么样？" |
| 🧮 **数学计算** | 执行复杂的数学运算 | "计算 (125 * 8) / 4 + sin(3.14)" |
| 📧 **邮件发送** | 自动化邮件通知 | "帮我写一封会议通知邮件" |

### 💡 使用提示

1. **直接提问** - 输入你的问题，我会自动判断是否需要使用工具
2. **工具自动调用** - 需要实时信息或计算时，我会自动使用相应工具
3. **清空对话** - 点击"清空对话"按钮可以清除记忆，开始新话题
4. **流式输出** - 回答会逐字显示，无需等待完整生成

### 🚀 快速开始

试试以下问题：
- "2024年奥运会在哪里举办？"
- "计算 2的10次方乘以3.14"
- "帮我写一封请假邮件"

---
*基于 LlamaIndex + Function Call 技术构建*
"""

# 构建 Gradio 界面
with gr.Blocks(
    theme=gr.themes.Soft(),
    title="AI 智能体助手",
    css="""
    .gradio-container {
        max-width: 1000px !important;
        margin: auto !important;
    }
    #chatbot {
        height: 600px;
        overflow: auto;
    }
    .main-title {
        text-align: center;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 20px;
    }
    """
) as demo:
    
    # 标题和说明
    gr.Markdown(
        """
        <div class="main-title">
        <h1>🤖 AI 智能体助手</h1>
        </div>
        <div class="subtitle">
        支持联网搜索 · 数学计算 · 自动化通知 | 基于通义千问大模型
        </div>
        """
    )
    
    # 状态管理
    session_id_state = gr.State(value=None)
    
    # 聊天显示区域
    chatbot_display = gr.Chatbot(
        elem_id="chatbot",
        height=600,
        show_copy_button=True,
        placeholder="💬 对话将显示在这里\n\n请输入消息开始对话..."
    )
    
    # 输入区域
    msg_input = gr.Textbox(
        placeholder="输入你的问题... (Shift+Enter 换行，Enter 发送)",
        label="消息",
        lines=2,
        container=True
    )
    
    # 按钮区域
    with gr.Row():
        send_btn = gr.Button("📤 发送", variant="primary", scale=2)
        clear_btn = gr.Button("� 清空对话", variant="secondary", scale=1)
    
    # 状态信息
    status_text = gr.Markdown("")
    
    # 欢迎消息
    gr.Markdown(get_welcome_message())
    
    def respond(message, history, session_id):
        """处理用户消息并返回响应"""
        if not message or not message.strip():
            return "", history, session_id
        
        try:
            for partial_message, new_session_id in chat_stream(message, history, session_id):
                yield "", history + [(message, partial_message)], new_session_id
        except Exception as e:
            error_history = history + [(message, f"❌ 处理失败：{str(e)}")]
            yield "", error_history, session_id
    
    # 绑定事件
    send_btn.click(
        fn=respond,
        inputs=[msg_input, chatbot_display, session_id_state],
        outputs=[msg_input, chatbot_display, session_id_state]
    )
    
    msg_input.submit(
        fn=respond,
        inputs=[msg_input, chatbot_display, session_id_state],
        outputs=[msg_input, chatbot_display, session_id_state]
    )
    
    clear_btn.click(
        fn=reset_chat,
        inputs=[session_id_state],
        outputs=[chatbot_display, session_id_state]
    )
    
    # 页面加载时的提示
    gr.HTML("""
    <script>
    window.addEventListener('load', function() {
        console.log('AI Agent 平台已加载');
    });
    </script>
    """)

if __name__ == "__main__":
    try:
        logger.info("启动 Gradio 界面...")
        demo.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            show_error=True
        )
    except Exception as e:
        logger.error(f"启动失败：{e}", exc_info=True)
        print(f"\n❌ 启动失败：{str(e)}")
        print("\n请检查:")
        print("1. 端口 7860 是否被占用")
        print("2. .env 文件是否正确配置")
        print("3. 所有依赖是否已安装")
