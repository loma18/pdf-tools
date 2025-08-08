@echo off
echo ========================================
echo PDF自动书签工具 - 构建脚本
echo ========================================

echo.
echo 🔧 检查Node.js环境...
node --version
if %errorlevel% neq 0 (
    echo ❌ 请先安装Node.js
    pause
    exit /b 1
)

echo.
echo 📦 安装依赖包...
call npm install
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

echo.
echo 🔧 准备构建环境...
node build-setup.js
if %errorlevel% neq 0 (
    echo ❌ 构建环境准备失败
    pause
    exit /b 1
)

echo.
echo 🏗️ 开始构建Windows应用...
call npm run build-win
if %errorlevel% neq 0 (
    echo ❌ 构建失败
    pause
    exit /b 1
)

echo.
echo ✅ 构建完成！
echo 📁 输出目录: dist/
echo.
echo 按任意键打开输出目录...
pause > nul
explorer dist 