#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF自动书签工具启动器 v2.0
支持自动依赖检查、安装和GUI启动
"""

import sys
import subprocess
import os

def check_dependencies():
    """检查依赖包"""
    required_packages = {
        'PyMuPDF': 'fitz',
        'pdfplumber': 'pdfplumber', 
        'tkinter': 'tkinter',
        'requests': 'requests'
    }
    
    optional_packages = {
        'tkinterdnd2': 'tkinterdnd2'  # 拖拽支持（可选）
    }
    
    missing_required = []
    missing_optional = []
    
    # 检查必需包
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} - 已安装")
        except ImportError:
            missing_required.append(package_name)
            print(f"❌ {package_name} - 未安装")
    
    # 检查可选包
    for package_name, import_name in optional_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name} - 已安装 (可选功能)")
        except ImportError:
            missing_optional.append(package_name)
            print(f"⚠️  {package_name} - 未安装 (可选，支持拖拽功能)")
    
    return missing_required, missing_optional

def install_missing_packages(packages):
    """安装缺失的包"""
    print(f"\n正在安装缺失的依赖包: {', '.join(packages)}...")
    
    success_count = 0
    for package in packages:
        # 特殊处理包名映射
        install_name = package
        if package == 'PyMuPDF':
            install_name = 'pymupdf'
        
        print(f"\n📦 安装 {package}...")
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'install', install_name
            ], capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0:
                print(f"✅ {package} 安装成功")
                success_count += 1
            else:
                print(f"❌ {package} 安装失败: {result.stderr}")
        except subprocess.TimeoutExpired:
            print(f"❌ {package} 安装超时")
        except Exception as e:
            print(f"❌ {package} 安装异常: {e}")
    
    return success_count == len(packages)

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python版本过低: {version.major}.{version.minor}")
        print("   需要Python 3.7或更高版本")
        return False
    else:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True

def main():
    """主函数"""
    print("=" * 60)
    print("📚 PDF自动书签工具启动器 v2.0")
    print("=" * 60)
    
    # 检查Python版本
    if not check_python_version():
        input("\n按回车键退出...")
        return
    
    print("\n🔍 检查依赖包...")
    print("-" * 40)
    
    # 检查依赖
    missing_required, missing_optional = check_dependencies()
    
    # 处理必需依赖
    if missing_required:
        print(f"\n⚠️  检测到缺失的必需依赖包: {', '.join(missing_required)}")
        
        # 询问是否安装
        try:
            choice = input("\n是否自动安装缺失的必需依赖包? (y/n): ").lower().strip()
            if choice in ['y', 'yes', '是', '']:
                if install_missing_packages(missing_required):
                    print("\n✅ 必需依赖包安装完成")
                else:
                    print("\n❌ 部分必需依赖包安装失败")
                    print("请尝试手动安装：pip install -r requirements.txt")
                    input("\n按回车键退出...")
                    return
            else:
                print("\n请手动安装必需依赖包后再运行程序：")
                print("pip install -r requirements.txt")
                input("\n按回车键退出...")
                return
        except KeyboardInterrupt:
            print("\n\n程序已取消")
            return
    
    # 处理可选依赖
    if missing_optional:
        print(f"\n💡 可选依赖包未安装: {', '.join(missing_optional)}")
        print("   这些包提供额外功能（如拖拽支持），不影响核心功能")
        
        try:
            choice = input("\n是否安装可选依赖包? (y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                install_missing_packages(missing_optional)
        except KeyboardInterrupt:
            print("\n跳过可选依赖包安装")
    
    # 启动GUI
    print("\n" + "=" * 60)
    print("🚀 启动GUI界面...")
    print("=" * 60)
    
    try:
        # 检查GUI文件是否存在
        gui_file = "pdf_bookmark_gui.py"
        if not os.path.exists(gui_file):
            print(f"❌ 找不到GUI文件: {gui_file}")
            print("请确保所有项目文件都在同一目录下")
            input("\n按回车键退出...")
            return
        
        from pdf_bookmark_gui import main as gui_main
        gui_main()
        
    except ImportError as e:
        print(f"❌ 导入GUI模块失败: {e}")
        print("请检查是否所有依赖都已正确安装")
        input("\n按回车键退出...")
    except Exception as e:
        print(f"❌ 启动GUI失败: {e}")
        print("请检查错误信息并重试")
        input("\n按回车键退出...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程序已取消")
    except Exception as e:
        print(f"\n❌ 启动器异常: {e}")
        input("\n按回车键退出...") 