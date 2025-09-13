#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Python脚本是否能正常工作
"""

import subprocess
import sys
import os

def test_python_script():
    # 获取Python脚本路径
    script_path = os.path.join("python-backend", "pdf_bookmark_tool.py")
    
    if not os.path.exists(script_path):
        print(f"❌ Python脚本不存在: {script_path}")
        return False
    
    # 测试帮助信息
    try:
        result = subprocess.run([sys.executable, script_path, "--help"], 
                              capture_output=True, text=True, timeout=10)
        print("✅ Python脚本可以正常启动")
        print("帮助信息:")
        print(result.stdout)
        return True
    except subprocess.TimeoutExpired:
        print("❌ Python脚本启动超时")
        return False
    except Exception as e:
        print(f"❌ Python脚本启动失败: {e}")
        return False

if __name__ == "__main__":
    test_python_script()
