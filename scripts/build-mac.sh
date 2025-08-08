#!/bin/bash

# Mac平台专用构建脚本
# 用于在macOS系统上构建Mac应用

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo ""
echo "========================================"
echo -e "${PURPLE}🍎 PDF自动书签工具 - Mac构建脚本${NC}"
echo "========================================"
echo ""

# 检查是否在macOS系统上运行
if [[ $(uname) != "Darwin" ]]; then
    echo -e "${YELLOW}⚠️  警告：您不在macOS系统上，Mac应用构建可能会失败${NC}"
    echo -e "${YELLOW}   建议在macOS系统上运行此脚本以获得最佳效果${NC}"
    echo ""
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "构建已取消"
        exit 1
    fi
fi

# 检查Node.js
echo -e "${BLUE}🔧 检查Node.js环境...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js未安装${NC}"
    echo "请先安装Node.js: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✅ Node.js已安装: $NODE_VERSION${NC}"

# 检查npm
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm未安装${NC}"
    exit 1
fi

# 检查必要的icon文件
echo ""
echo -e "${BLUE}🔍 检查Mac图标文件...${NC}"
if [[ ! -f "assets/icon.icns" ]]; then
    echo -e "${YELLOW}⚠️  Mac图标文件(icon.icns)不存在${NC}"
    echo "将尝试从icon.png生成icon.icns..."
    
    if command -v sips &> /dev/null && [[ -f "assets/icon.png" ]]; then
        echo "正在生成icon.icns..."
        
        # 创建临时图标集目录
        mkdir -p tmp.iconset
        
        # 生成不同尺寸的图标
        sips -z 16 16 assets/icon.png --out tmp.iconset/icon_16x16.png
        sips -z 32 32 assets/icon.png --out tmp.iconset/icon_16x16@2x.png
        sips -z 32 32 assets/icon.png --out tmp.iconset/icon_32x32.png
        sips -z 64 64 assets/icon.png --out tmp.iconset/icon_32x32@2x.png
        sips -z 128 128 assets/icon.png --out tmp.iconset/icon_128x128.png
        sips -z 256 256 assets/icon.png --out tmp.iconset/icon_128x128@2x.png
        sips -z 256 256 assets/icon.png --out tmp.iconset/icon_256x256.png
        sips -z 512 512 assets/icon.png --out tmp.iconset/icon_256x256@2x.png
        sips -z 512 512 assets/icon.png --out tmp.iconset/icon_512x512.png
        sips -z 1024 1024 assets/icon.png --out tmp.iconset/icon_512x512@2x.png
        
        # 生成icns文件
        iconutil -c icns tmp.iconset -o assets/icon.icns
        
        # 清理临时文件
        rm -rf tmp.iconset
        
        echo -e "${GREEN}✅ icon.icns生成成功${NC}"
    else
        echo -e "${YELLOW}⚠️  无法自动生成icon.icns，构建可能会使用默认图标${NC}"
    fi
else
    echo -e "${GREEN}✅ Mac图标文件存在${NC}"
fi

# 安装依赖
echo ""
echo -e "${BLUE}📦 安装Node.js依赖...${NC}"
npm install
if [[ $? -ne 0 ]]; then
    echo -e "${RED}❌ 依赖安装失败${NC}"
    exit 1
fi

# 运行构建准备脚本
echo ""
echo -e "${BLUE}🔧 准备构建环境...${NC}"
if [[ -f "build-setup.js" ]]; then
    node build-setup.js
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}❌ 构建环境准备失败${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  build-setup.js不存在，跳过构建准备${NC}"
fi

# 清理之前的构建产物
echo ""
echo -e "${BLUE}🧹 清理之前的构建产物...${NC}"
rm -rf dist/

# 开始构建
echo ""
echo -e "${PURPLE}🏗️  开始构建Mac应用...${NC}"
echo "这可能需要几分钟时间，请耐心等待..."
echo ""

npm run build-mac

if [[ $? -eq 0 ]]; then
    echo ""
    echo -e "${GREEN}🎉 Mac应用构建成功！${NC}"
    echo ""
    
    # 显示构建产物信息
    if [[ -d "dist" ]]; then
        echo -e "${BLUE}📁 构建产物：${NC}"
        ls -la dist/
        echo ""
        
        # 查找.dmg文件
        DMG_FILE=$(find dist -name "*.dmg" | head -1)
        if [[ -n "$DMG_FILE" ]]; then
            DMG_SIZE=$(du -h "$DMG_FILE" | cut -f1)
            echo -e "${GREEN}💿 安装包：${NC} $DMG_FILE (${DMG_SIZE})"
        fi
        
        # 查找.app文件
        APP_FILE=$(find dist -name "*.app" | head -1)
        if [[ -n "$APP_FILE" ]]; then
            echo -e "${GREEN}📱 应用程序：${NC} $APP_FILE"
        fi
        
        echo ""
        echo -e "${BLUE}🚀 使用说明：${NC}"
        echo "1. 双击 .dmg 文件进行安装"
        echo "2. 或者直接运行 .app 文件"
        echo "3. 首次运行可能需要在系统偏好设置中允许运行"
        
        # 询问是否打开输出目录
        echo ""
        read -p "是否打开输出目录？(Y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            open dist/
        fi
    else
        echo -e "${YELLOW}⚠️  构建产物目录不存在${NC}"
    fi
    
else
    echo ""
    echo -e "${RED}❌ Mac应用构建失败${NC}"
    echo ""
    echo -e "${YELLOW}💡 可能的解决方案：${NC}"
    echo "1. 确保在macOS系统上运行"
    echo "2. 检查Node.js版本是否兼容"
    echo "3. 确保所有依赖已正确安装"
    echo "4. 检查package.json中的Mac构建配置"
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}✨ 构建完成！${NC}" 