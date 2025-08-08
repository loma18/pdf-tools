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
echo 4. 🍎 构建Mac应用程序
echo 5. 🐧 构建Linux应用程序
echo 6. 📦 构建所有平台
echo 7. 📖 查看使用说明
echo 8. ❌ 退出
echo.
set /p choice=请输入选择 (1-8): 

if "%choice%"=="1" goto install
if "%choice%"=="2" goto dev
if "%choice%"=="3" goto build_win
if "%choice%"=="4" goto build_mac
if "%choice%"=="5" goto build_linux
if "%choice%"=="6" goto build_all
if "%choice%"=="7" goto docs
if "%choice%"=="8" goto exit
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

:build_win
echo.
echo 🏗️ 构建Windows可执行文件...
echo 这可能需要几分钟时间...
echo.
call scripts\build.bat
pause
goto menu

:build_mac
echo.
echo 🍎 构建Mac应用程序...
echo 注意：此功能需要在macOS系统上运行，或使用GitHub Actions等CI/CD服务
echo 这可能需要几分钟时间...
echo.

echo 🔧 检查构建环境...
node --version
if %errorlevel% neq 0 (
    echo ❌ 请先安装Node.js
    pause
    goto menu
)

echo.
echo 📦 安装依赖包...
call npm install
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    goto menu
)

echo.
echo 🔧 准备构建环境...
node build-setup.js
if %errorlevel% neq 0 (
    echo ❌ 构建环境准备失败
    pause
    goto menu
)

echo.
echo 🏗️ 开始构建Mac应用...
call npm run build-mac
if %errorlevel% neq 0 (
    echo ❌ Mac构建失败
    echo 💡 提示：Mac应用构建通常需要在macOS系统上进行
    pause
    goto menu
)

echo.
echo ✅ Mac应用构建完成！
echo 📁 输出目录: dist/
pause
goto menu

:build_linux
echo.
echo 🐧 构建Linux应用程序...
echo 这可能需要几分钟时间...
echo.

echo 🔧 检查构建环境...
node --version
if %errorlevel% neq 0 (
    echo ❌ 请先安装Node.js
    pause
    goto menu
)

echo.
echo 📦 安装依赖包...
call npm install
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    goto menu
)

echo.
echo 🔧 准备构建环境...
node build-setup.js
if %errorlevel% neq 0 (
    echo ❌ 构建环境准备失败
    pause
    goto menu
)

echo.
echo 🏗️ 开始构建Linux应用...
call npm run build-linux
if %errorlevel% neq 0 (
    echo ❌ Linux构建失败
    pause
    goto menu
)

echo.
echo ✅ Linux应用构建完成！
echo 📁 输出目录: dist/
pause
goto menu

:build_all
echo.
echo 📦 构建所有平台的应用程序...
echo 注意：这可能需要较长时间，Mac构建需要macOS环境
echo.

echo 🔧 检查构建环境...
node --version
if %errorlevel% neq 0 (
    echo ❌ 请先安装Node.js
    pause
    goto menu
)

echo.
echo 📦 安装依赖包...
call npm install
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    goto menu
)

echo.
echo 🔧 准备构建环境...
node build-setup.js
if %errorlevel% neq 0 (
    echo ❌ 构建环境准备失败
    pause
    goto menu
)

echo.
echo 🏗️ 开始构建所有平台...
call npm run build
if %errorlevel% neq 0 (
    echo ❌ 多平台构建失败
    echo 💡 提示：某些平台的构建可能需要特定的系统环境
    pause
    goto menu
)

echo.
echo ✅ 多平台构建完成！
echo 📁 输出目录: dist/
echo.
echo 按任意键打开输出目录...
pause > nul
explorer dist
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