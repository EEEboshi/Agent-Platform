"""
项目统一启动入口
支持启动 UI 界面、API 服务或同时启动两者
"""
import sys
import os
import argparse
import threading
import time
from pathlib import Path


def check_env():
    """检查 .env 文件是否存在"""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        print("⚠️  警告：未找到 .env 文件")
        print("   请复制 .env.example 为 .env 并配置 API Key")
        print("   命令：cp .env.example .env")
        return False
    return True


def check_dependencies():
    """检查必要的依赖是否已安装"""
    try:
        import llama_index
        import fastapi
        import gradio
        import pydantic
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖：{e}")
        print("   请运行：pip install -r requirements.txt")
        return False


def start_api():
    """启动 API 服务"""
    from api.main import app
    import uvicorn
    from core.config import get_settings
    
    settings = get_settings()
    
    print(f"\n🚀 启动 API 服务...")
    print(f"   地址：http://{settings.server.host}:{settings.server.port}")
    print(f"   API 文档：http://localhost:{settings.server.port}/api/docs")
    
    uvicorn.run(
        app,
        host=settings.server.host,
        port=settings.server.port,
        log_level=settings.log_level.lower()
    )


def start_ui():
    """启动 UI 界面"""
    from ui.app import demo
    from core.config import get_settings
    
    settings = get_settings()
    
    print(f"\n🎨 启动 UI 界面...")
    print(f"   地址：http://localhost:7860")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )


def start_both():
    """同时启动 UI 和 API"""
    print("\n🚀 同时启动 UI 和 API 服务...")
    
    # 在后台线程启动 API
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    
    # 等待 API 启动
    time.sleep(2)
    
    # 在主线程启动 UI
    start_ui()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="AI Agent Platform 启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run.py              # 同时启动 UI 和 API
  python run.py --ui         # 只启动 UI
  python run.py --api        # 只启动 API
  python run.py --check      # 检查环境配置
        """
    )
    
    parser.add_argument(
        "--ui",
        action="store_true",
        help="只启动 UI 界面 (http://localhost:7860)"
    )
    
    parser.add_argument(
        "--api",
        action="store_true",
        help="只启动 API 服务 (http://localhost:8000)"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="检查环境配置"
    )
    
    args = parser.parse_args()
    
    # 打印欢迎信息
    print("=" * 60)
    print("🤖 多功能自动化 AI 智能体平台")
    print("=" * 60)
    
    # 检查环境
    if args.check:
        print("\n📋 环境检查...")
        env_ok = check_env()
        deps_ok = check_dependencies()
        
        if env_ok and deps_ok:
            print("\n✅ 环境配置正常")
        else:
            print("\n❌ 环境配置有问题，请先解决上述问题")
        return
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 检查环境变量
    check_env()
    
    # 根据参数启动服务
    if args.ui and args.api:
        start_both()
    elif args.ui:
        start_ui()
    elif args.api:
        start_api()
    else:
        # 默认同时启动
        start_both()


if __name__ == "__main__":
    main()
