@echo off
echo ========================================
echo   Agent Platform - 启动后端服务
echo ========================================
echo.

call venv\Scripts\activate.bat
echo 虚拟环境已激活
echo.

echo 启动 FastAPI 服务器...
python api\main.py

pause
