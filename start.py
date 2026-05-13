"""
一键启动脚本
"""

import os
import sys
import subprocess
import webbrowser
import time

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    print("=" * 50)
    print("   财务造假识别系统 - 启动中...")
    print("=" * 50)

    # 检查依赖
    try:
        import fastapi  # noqa
        print("[✓] 依赖已安装")
    except ImportError:
        print("[!] 正在安装依赖...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r",
             os.path.join(BACKEND_DIR, "backend", "requirements.txt")]
        )
        print("[✓] 依赖安装完成")

    # 启动后端
    print("[*] 启动后端服务...")
    backend_path = os.path.join(BACKEND_DIR, "backend")
    env = os.environ.copy()
    env["PYTHONPATH"] = BACKEND_DIR + os.pathsep + env.get("PYTHONPATH", "")

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "0.0.0.0", "--port", "8000",
         "--reload"],
        cwd=BACKEND_DIR,
        env=env,
    )

    time.sleep(2)

    # 打开浏览器
    frontend_url = f"file://{os.path.join(BACKEND_DIR, 'frontend', 'index.html').replace(os.sep, '/')}"
    print(f"[*] 前端页面: {frontend_url}")
    print(f"[*] API 文档: http://localhost:8000/docs")
    print(f"[*] 后端地址: http://localhost:8000")
    print("[*] 正在打开浏览器...")
    webbrowser.open(frontend_url)

    print("=" * 50)
    print("   系统已启动! 按 Ctrl+C 停止")
    print("=" * 50)

    try:
        process.wait()
    except KeyboardInterrupt:
        print("\n[*] 正在关闭...")
        process.terminate()
        print("[✓] 已停止")


if __name__ == "__main__":
    main()
