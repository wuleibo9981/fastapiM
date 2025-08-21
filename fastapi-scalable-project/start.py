#!/usr/bin/env python3
"""
FastAPI多节点扩展项目启动脚本
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        sys.exit(1)
    print(f"✅ Python版本: {sys.version}")


def check_dependencies():
    """检查依赖是否安装"""
    try:
        import fastapi
        import uvicorn
        import sqlalchemy
        print("✅ 核心依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        return False


def install_dependencies():
    """安装依赖"""
    print("📦 正在安装依赖...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        return False


def setup_environment():
    """设置环境变量"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 创建环境配置文件...")
        import shutil
        shutil.copy(env_example, env_file)
        print("✅ 已创建 .env 文件，请根据需要修改配置")
    
    # 设置基本环境变量
    os.environ.setdefault("ENVIRONMENT", "development")
    os.environ.setdefault("DATABASE_URL", "sqlite:///./dev.db")
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


def start_application(host="127.0.0.1", port=8000, reload=True):
    """启动应用"""
    print(f"🚀 正在启动FastAPI应用...")
    print(f"   访问地址: http://{host}:{port}")
    print(f"   API文档: http://{host}:{port}/docs")
    print(f"   健康检查: http://{host}:{port}/health")
    print()
    
    try:
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="FastAPI多节点扩展项目启动脚本")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument("--port", type=int, default=8000, help="监听端口")
    parser.add_argument("--no-reload", action="store_true", help="禁用自动重载")
    parser.add_argument("--install-deps", action="store_true", help="安装依赖")
    
    args = parser.parse_args()
    
    print("🌟 FastAPI多节点扩展项目")
    print("=" * 50)
    
    # 检查Python版本
    check_python_version()
    
    # 安装依赖（如果需要）
    if args.install_deps or not check_dependencies():
        if not install_dependencies():
            sys.exit(1)
    
    # 设置环境
    setup_environment()
    
    # 启动应用
    start_application(
        host=args.host,
        port=args.port,
        reload=not args.no_reload
    )


if __name__ == "__main__":
    main()
