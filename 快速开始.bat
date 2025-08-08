@echo off
chcp 65001 > nul
title PDF自动书签工具 - 桌面版快速开始

echo.
echo ========================================
echo 📚 PDF自动书签工具 - Electron桌面版
echo ========================================
echo.
echo 这个脚本将帮助您快速开始使用桌面版应用
echo.

:menu
echo 请选择操作：
echo.
echo 1. 🔧 安装开发环境 (首次使用)
echo 2. 🚀 运行开发版本
echo 3. 🏗️ 构建Windows可执行文件
echo 4. 📖 查看使用说明
echo 5. ❌ 退出
echo.
set /p choice=请输入选择 (1-5): 

if "%choice%"=="1" goto install
if "%choice%"=="2" goto dev
if "%choice%"=="3" goto build
if "%choice%"=="4" goto docs
if "%choice%"=="5" goto exit
echo 无效选择，请重新输入
goto menu

:install
echo.
echo 🔧 正在安装开发环境...
echo.
echo 检查Node.js...
node --version
if %errorlevel% neq 0 (
    echo ❌ 请先安装Node.js: https://nodejs.org/
    pause
    goto menu
)

echo.
echo 检查Python...
python --version
if %errorlevel% neq 0 (
    echo ❌ 请先安装Python: https://python.org/
    pause
    goto menu
)

echo.
echo 📦 安装Node.js依赖...
call npm install
if %errorlevel% neq 0 (
    echo ❌ Node.js依赖安装失败
    pause
    goto menu
)

echo.
echo 🐍 安装Python依赖...
cd python-backend
pip install -r requirements.txt
cd ..
if %errorlevel% neq 0 (
    echo ❌ Python依赖安装失败
    pause
    goto menu
)

echo.
echo ✅ 开发环境安装完成！
pause
goto menu

:dev
echo.
echo 🚀 启动开发版本...
echo 注意：这将打开开发者模式，包含调试工具
echo.
call npm run dev
pause
goto menu

:build
echo.
echo 🏗️ 构建Windows可执行文件...
echo 这可能需要几分钟时间...
echo.
call scripts\build.bat
pause
goto menu

:docs
echo.
echo 📖 打开使用说明...
start 用户使用指南.md
start ELECTRON_README.md
goto menu

:exit
echo.
echo 👋 感谢使用PDF自动书签工具！
echo.
pause
exit 