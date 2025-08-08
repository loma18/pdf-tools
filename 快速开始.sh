#!/bin/bash

# 设置颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 获取操作系统类型
OS_TYPE=""
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="mac"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS_TYPE="windows"
else
    OS_TYPE="unknown"
fi

echo ""
echo "========================================"
echo "📚 PDF自动书签工具 - Electron桌面版"
echo "========================================"
echo ""
echo "这个脚本将帮助您快速开始使用桌面版应用"
echo "当前系统: $OS_TYPE"
echo ""

function show_menu() {
    echo "请选择操作："
    echo ""
    echo "1. 🔧 安装开发环境 (首次使用)"
    echo "2. 🚀 运行开发版本"
    echo "3. 🏗️ 构建当前平台应用"
    echo "4. 🍎 构建Mac应用程序"
    echo "5. 🐧 构建Linux应用程序"
    echo "6. 🪟 构建Windows应用程序"
    echo "7. 📦 构建所有平台"
    echo "8. 📖 查看使用说明"
    echo "9. ❌ 退出"
    echo ""
    read -p "请输入选择 (1-9): " choice
    
    case $choice in
        1) install_env ;;
        2) run_dev ;;
        3) build_current ;;
        4) build_mac ;;
        5) build_linux ;;
        6) build_windows ;;
        7) build_all ;;
        8) show_docs ;;
        9) exit_script ;;
        *) 
            echo -e "${RED}无效选择，请重新输入${NC}"
            show_menu
            ;;
    esac
}

function check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✅ $1 已安装${NC}"
        return 0
    else
        echo -e "${RED}❌ $1 未安装${NC}"
        return 1
    fi
}

function install_env() {
    echo ""
    echo -e "${BLUE}🔧 正在安装开发环境...${NC}"
    echo ""
    
    echo "检查Node.js..."
    if check_command "node"; then
        node --version
    else
        echo "请先安装Node.js: https://nodejs.org/"
        read -p "按Enter键继续..."
        show_menu
        return
    fi
    
    echo ""
    echo "检查Python..."
    if check_command "python3" || check_command "python"; then
        python3 --version 2>/dev/null || python --version
    else
        echo "请先安装Python: https://python.org/"
        read -p "按Enter键继续..."
        show_menu
        return
    fi
    
    echo ""
    echo -e "${BLUE}📦 安装Node.js依赖...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Node.js依赖安装失败${NC}"
        read -p "按Enter键继续..."
        show_menu
        return
    fi
    
    echo ""
    echo -e "${BLUE}🐍 安装Python依赖...${NC}"
    cd python-backend
    pip3 install -r requirements.txt 2>/dev/null || pip install -r requirements.txt
    cd ..
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Python依赖安装失败${NC}"
        read -p "按Enter键继续..."
        show_menu
        return
    fi
    
    echo ""
    echo -e "${GREEN}✅ 开发环境安装完成！${NC}"
    read -p "按Enter键继续..."
    show_menu
}

function run_dev() {
    echo ""
    echo -e "${BLUE}🚀 启动开发版本...${NC}"
    echo "注意：这将打开开发者模式，包含调试工具"
    echo ""
    npm run dev
    read -p "按Enter键继续..."
    show_menu
}

function build_current() {
    echo ""
    echo -e "${BLUE}🏗️ 构建当前平台应用...${NC}"
    
    case $OS_TYPE in
        "mac")
            build_mac_app
            ;;
        "linux")
            build_linux_app
            ;;
        "windows")
            build_windows_app
            ;;
        *)
            echo -e "${YELLOW}⚠️ 未识别的系统类型，将尝试构建所有平台${NC}"
            build_all_platforms
            ;;
    esac
}

function build_mac() {
    echo ""
    echo -e "${PURPLE}🍎 构建Mac应用程序...${NC}"
    if [[ "$OS_TYPE" != "mac" ]]; then
        echo -e "${YELLOW}注意：此功能建议在macOS系统上运行以获得最佳效果${NC}"
    fi
    build_mac_app
}

function build_mac_app() {
    echo "这可能需要几分钟时间..."
    echo ""
    
    if ! check_environment; then
        return
    fi
    
    echo ""
    echo -e "${BLUE}🏗️ 开始构建Mac应用...${NC}"
    npm run build-mac
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Mac构建失败${NC}"
        if [[ "$OS_TYPE" != "mac" ]]; then
            echo -e "${YELLOW}💡 提示：Mac应用构建在macOS系统上效果最佳${NC}"
        fi
        read -p "按Enter键继续..."
        show_menu
        return
    fi
    
    echo ""
    echo -e "${GREEN}✅ Mac应用构建完成！${NC}"
    echo -e "${CYAN}📁 输出目录: dist/${NC}"
    read -p "按Enter键继续..."
    show_menu
}

function build_linux() {
    echo ""
    echo -e "${CYAN}🐧 构建Linux应用程序...${NC}"
    build_linux_app
}

function build_linux_app() {
    echo "这可能需要几分钟时间..."
    echo ""
    
    if ! check_environment; then
        return
    fi
    
    echo ""
    echo -e "${BLUE}🏗️ 开始构建Linux应用...${NC}"
    npm run build-linux
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Linux构建失败${NC}"
        read -p "按Enter键继续..."
        show_menu
        return
    fi
    
    echo ""
    echo -e "${GREEN}✅ Linux应用构建完成！${NC}"
    echo -e "${CYAN}📁 输出目录: dist/${NC}"
    read -p "按Enter键继续..."
    show_menu
}

function build_windows() {
    echo ""
    echo -e "${BLUE}🪟 构建Windows应用程序...${NC}"
    if [[ "$OS_TYPE" != "windows" ]]; then
        echo -e "${YELLOW}注意：在非Windows系统上构建Windows应用${NC}"
    fi
    build_windows_app
}

function build_windows_app() {
    echo "这可能需要几分钟时间..."
    echo ""
    
    if ! check_environment; then
        return
    fi
    
    echo ""
    echo -e "${BLUE}🏗️ 开始构建Windows应用...${NC}"
    npm run build-win
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Windows构建失败${NC}"
        read -p "按Enter键继续..."
        show_menu
        return
    fi
    
    echo ""
    echo -e "${GREEN}✅ Windows应用构建完成！${NC}"
    echo -e "${CYAN}📁 输出目录: dist/${NC}"
    read -p "按Enter键继续..."
    show_menu
}

function build_all() {
    echo ""
    echo -e "${PURPLE}📦 构建所有平台的应用程序...${NC}"
    build_all_platforms
}

function build_all_platforms() {
    echo "注意：这可能需要较长时间"
    echo ""
    
    if ! check_environment; then
        return
    fi
    
    echo ""
    echo -e "${BLUE}🏗️ 开始构建所有平台...${NC}"
    npm run build
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 多平台构建失败${NC}"
        echo -e "${YELLOW}💡 提示：某些平台的构建可能需要特定的系统环境${NC}"
        read -p "按Enter键继续..."
        show_menu
        return
    fi
    
    echo ""
    echo -e "${GREEN}✅ 多平台构建完成！${NC}"
    echo -e "${CYAN}📁 输出目录: dist/${NC}"
    
    # 打开输出目录
    if command -v open &> /dev/null; then
        open dist  # macOS
    elif command -v xdg-open &> /dev/null; then
        xdg-open dist  # Linux
    elif command -v explorer &> /dev/null; then
        explorer dist  # Windows
    fi
    
    read -p "按Enter键继续..."
    show_menu
}

function check_environment() {
    echo -e "${BLUE}🔧 检查构建环境...${NC}"
    if ! check_command "node"; then
        echo "请先安装Node.js"
        read -p "按Enter键继续..."
        show_menu
        return 1
    fi
    
    echo ""
    echo -e "${BLUE}📦 安装依赖包...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 依赖安装失败${NC}"
        read -p "按Enter键继续..."
        show_menu
        return 1
    fi
    
    echo ""
    echo -e "${BLUE}🔧 准备构建环境...${NC}"
    node build-setup.js
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 构建环境准备失败${NC}"
        read -p "按Enter键继续..."
        show_menu
        return 1
    fi
    
    return 0
}

function show_docs() {
    echo ""
    echo -e "${BLUE}📖 打开使用说明...${NC}"
    
    # 尝试打开文档文件
    if command -v open &> /dev/null; then
        # macOS
        open "用户使用指南.md" 2>/dev/null || echo "请手动打开 用户使用指南.md"
        open "ELECTRON_README.md" 2>/dev/null || echo "请手动打开 ELECTRON_README.md"
    elif command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open "用户使用指南.md" 2>/dev/null || echo "请手动打开 用户使用指南.md"
        xdg-open "ELECTRON_README.md" 2>/dev/null || echo "请手动打开 ELECTRON_README.md"
    else
        echo "请手动打开以下文件："
        echo "- 用户使用指南.md"
        echo "- ELECTRON_README.md"
    fi
    
    show_menu
}

function exit_script() {
    echo ""
    echo -e "${GREEN}👋 感谢使用PDF自动书签工具！${NC}"
    echo ""
    exit 0
}

# 主程序入口
show_menu 