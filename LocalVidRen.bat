# LocalVidRen - 本地短视频智能重命名系统
# Windows 专属一键启动脚本

@echo off
chcp 65001 >nul
title LocalVidRen - 本地短视频智能重命名系统

echo ========================================
echo   LocalVidRen 启动中...
echo ========================================
echo.

REM 检查 Python 是否已安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.11+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python 环境已就绪
echo.

REM 检查依赖是否已安装
python -c "import PyQt6" >nul 2>&1
if errorlevel 1 (
    echo [提示] 正在安装依赖包，请稍候...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请检查网络连接
        pause
        exit /b 1
    )
    echo [OK] 依赖安装完成
) else (
    echo [OK] 依赖包已安装
)

echo.
echo ========================================
echo   启动 LocalVidRen...
echo ========================================
echo.

REM 启动应用程序
python "%~dp0src\main.py"

pause
