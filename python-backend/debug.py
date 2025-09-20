#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本 - 程序化调用pdf_bookmark_tool.py
等同于命令行: python pdf_bookmark_tool.py "../使用MasterGO的提效分析.pdf" -o output666.pdf
"""

import sys
import os
from pdf_bookmark_tool import main, PDFBookmarkTool


def debug_with_main_function():
    """方法1: 通过修改sys.argv调用main函数"""
    print("🔧 方法1: 通过main函数调用")
    print("="*50)
    
    # 备份原始的sys.argv
    original_argv = sys.argv.copy()
    
    try:
        # 模拟命令行参数
        sys.argv =  [
          'D:\\aiStudy\\pdf-tools\\python-backend\\pdf_bookmark_tool.py',
          'D:\\aiStudy\\pdf-tools\\江苏移动数智云原生UI规范.pdf',
          '-o',
          'D:\\aiStudy\\pdf-tools\\output668.pdf',
          '--enable-enhanced-filter',
          '--font-threshold',
          '9',
          '--x-tolerance',
          '2',
          '--require-numeric-start'
        ]
        
        # 调用main函数
        main()
        
    except SystemExit as e:
        print(f"程序正常结束，退出代码: {e.code}")
    except Exception as e:
        print(f"执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv


def debug_markdown_assisted():
    """调试Markdown辅助加书签功能"""
    print("🔧 调试Markdown辅助加书签功能")
    print("="*50)
    
    # 备份原始的sys.argv
    original_argv = sys.argv.copy()
    
    try:
        # 模拟命令行参数 - Markdown辅助加书签
        sys.argv = [
            'D:\\aiStudy\\pdf-tools\\python-backend\\pdf_bookmark_tool.py',
            r'C:\\Users\\90962\\Desktop\\test\\移动云原生主题UIUE规范.pdf',
            '--markdown-assisted',
            '--markdown-file',
            r'C:\\Users\\90962\Desktop\\test\\移动云原生主题UIUE规范.md',
            '-o',
            r'C:\\Users\\90962\\Desktop\\test\\移动云原生主题UIUE规范_with_bookmarks.pdf',
        ]
        
        # 调用main函数
        main()
        
    except SystemExit as e:
        print(f"程序正常结束，退出代码: {e.code}")
    except Exception as e:
        print(f"执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 恢复原始的sys.argv
        sys.argv = original_argv




if __name__ == "__main__":
    debug_markdown_assisted()
    
    # # 选择调试方法
    # print("选择调试方法:")
    # print("1. Markdown辅助加书签完整流程")
    # print("2. 原有的自动加书签方法")
    
    # method = input("请选择 (1/2): ").strip()
    
    # if method == "1":
    #     debug_markdown_assisted()
    # elif method == "2":
    #     debug_with_main_function()
    # else:
    #     print("无效选择，默认执行Markdown辅助加书签完整流程")
    #     debug_markdown_assisted()
    
    # print("\n🎯 调试完成！")
