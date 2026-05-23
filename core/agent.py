# core/agent.py
"""
Agent 核心模块
负责创建和配置 AI Agent 实例，包括大模型、记忆和工具集成
"""
import os
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.memory import ChatMemoryBuffer
from tools import ALL_TOOLS
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

def validate_environment() -> bool:
    """验证必要的环境变量是否已设置"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("DASHSCOPE_API_KEY 环境变量未设置")
        return False
    
    api_base = os.getenv("DASHSCOPE_API_BASE")
    if not api_base:
        logger.warning("DASHSCOPE_API_BASE 未设置，将使用默认值")
    
    return True

def create_llm():
    """
    创建大语言模型实例
    使用 OpenAI 兼容模式调用阿里云通义千问
    """
    api_key = os.getenv("DASHSCOPE_API_KEY")
    api_base = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model_name = os.getenv("DASHSCOPE_MODEL", "qwen-max")
    temperature = float(os.getenv("AGENT_TEMPERATURE", "0.1"))
    
    logger.info(f"初始化 LLM: model={model_name}, temperature={temperature}")
    
    return OpenAI(
        model="gpt-4",  # 兼容标识，实际使用 additional_kwargs 中的模型
        temperature=temperature,
        api_key=api_key,
        api_base=api_base,
        additional_kwargs={
            "model": model_name
        },
        timeout=30.0,  # 添加超时设置
        max_retries=2  # 添加自动重试
    )

def create_memory(token_limit: int = None):
    """
    创建对话记忆实例
    限制 token 数量防止上下文溢出
    """
    if token_limit is None:
        token_limit = int(os.getenv("AGENT_MEMORY_TOKEN_LIMIT", "8000"))
    
    logger.info(f"创建记忆缓冲区，token 限制：{token_limit}")
    return ChatMemoryBuffer.from_defaults(token_limit=token_limit)

# 系统提示词配置
SYSTEM_PROMPT = """你是一个强大且多功能的自动化 AI 智能体助手。
你的主要职责是准确理解用户意图，并合理调用提供的工具来完成任务。

核心规则：
1. 【工具使用优先】如果用户的问题需要实时信息、新闻、计算或外部数据，必须调用相应工具，严禁自己编造。
2. 【参数准确性】调用工具时确保参数准确完整。如果工具返回错误，分析原因后调整参数重试。
3. 【操作确认】对于发送邮件等不可逆操作，执行前需向用户确认（除非用户明确说"直接发送"）。
4. 【错误处理】工具调用失败时，向用户清晰解释原因并提供替代方案。
5. 【专业回复】始终使用清晰、专业、友好的中文回答用户。

可用工具：
- web_search: 联网搜索实时信息、新闻、事实
- calculate_math: 数学表达式计算
- send_automated_email: 发送邮件

回答格式：
- 先给出直接答案或结论
- 如使用了工具，简要说明信息来源
- 必要时提供后续建议"""

def create_agent(session_id: str = "default") -> OpenAIAgent:
    """
    工厂函数：为每个 session 创建一个带有独立记忆的 Agent 实例。
    
    Args:
        session_id: 会话标识符，用于区分不同用户的记忆
        
    Returns:
        配置好的 OpenAIAgent 实例
    """
    # 验证环境变量
    if not validate_environment():
        raise ValueError("环境变量配置不完整，请检查 .env 文件")
    
    # 创建 LLM 实例
    llm = create_llm()
    
    # 创建记忆实例
    memory = create_memory()
    
    # 获取可用工具
    available_tools = ALL_TOOLS
    logger.info(f"加载 {len(available_tools)} 个工具")
    
    # 组装 Agent
    agent = OpenAIAgent.from_tools(
        tools=available_tools,
        llm=llm,
        memory=memory,
        verbose=True,
        system_prompt=SYSTEM_PROMPT,
        max_function_calls=int(os.getenv("AGENT_MAX_FUNCTION_CALLS", "10"))
    )
    
    logger.info(f"Agent 创建成功，session_id={session_id}")
    return agent

# 测试入口
if __name__ == "__main__":
    print("=" * 60)
    print("多功能 AI Agent 平台 - 测试模式")
    print("=" * 60)
    
    try:
        test_agent = create_agent()
        print("\n✓ Agent 初始化成功")
        print("\n开始对话测试 (输入 'quit' 或 'exit' 退出):\n")
        
        while True:
            user_input = input("\n👤 用户：")
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n再见！")
                break
            
            if not user_input.strip():
                continue
                
            try:
                response = test_agent.chat(user_input)
                print(f"\n🤖 Agent: {response}")
            except Exception as e:
                print(f"\n❌ 错误：{str(e)}")
                
    except Exception as e:
        print(f"\n❌ Agent 初始化失败：{str(e)}")
        print("\n请检查:")
        print("1. .env 文件是否存在")
        print("2. DASHSCOPE_API_KEY 是否正确配置")
        print("3. 网络连接是否正常")
