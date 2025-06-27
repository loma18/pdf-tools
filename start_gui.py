#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF自动书签工具启动器
"""

import sys
import os
import subprocess
from pathlib import Path

def check_dependencies():
    """检查依赖包"""
    required_packages = ['PyMuPDF', 'pdfplumber', 'tkinter']
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'PyMuPDF':
                import fitz
            elif package == 'pdfplumber':
                import pdfplumber
            elif package == 'tkinter':
                import tkinter
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_missing_packages(packages):
    """安装缺失的包"""
    print("正在安装缺失的依赖包...")
    for package in packages:
        if package == 'PyMuPDF':
            package = 'pymupdf'
        print(f"安装 {package}...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
        except subprocess.CalledProcessError:
            print(f"❌ 安装 {package} 失败")
            return False
    return True

def main():
    """主函数"""
    print("📚 PDF自动书签工具启动器")
    print("=" * 40)
    
    # 检查依赖
    missing = check_dependencies()
    if missing:
        print(f"⚠️  检测到缺失的依赖包: {', '.join(missing)}")
        
        # 询问是否安装
        try:
            choice = input("是否自动安装缺失的依赖包? (y/n): ").lower().strip()
            if choice in ['y', 'yes', '是']:
                if install_missing_packages(missing):
                    print("✅ 依赖包安装完成")
                else:
                    print("❌ 依赖包安装失败，请手动安装")
                    return
            else:
                print("请手动安装依赖包后再运行程序")
                return
        except KeyboardInterrupt:
            print("\n程序已取消")
            return
    
    # 启动GUI
    print("🚀 启动GUI界面...")
    try:
        from pdf_bookmark_gui import main as gui_main
        gui_main()
    except Exception as e:
        print(f"❌ 启动GUI失败: {e}")
        print("请检查是否所有依赖都已正确安装")

if __name__ == "__main__":
    main() 