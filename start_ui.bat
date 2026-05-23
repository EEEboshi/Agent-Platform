@echo off
echo ========================================
echo   Agent Platform - 启动前端界面
echo ========================================
echo.

call venv\Scripts\activate.bat
echo 虚拟环境已激活
echo.

echo 启动 Gradio 界面...
python ui\app.py

pause
