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


def debug_with_direct_call():
    """方法2: 直接调用PDFBookmarkTool类"""
    print("\n🔧 方法2: 直接调用PDFBookmarkTool类")
    print("="*50)
    
    # input_file = "D:\\aiStudy\pdf-tools\\使用MasterGO的提效分析.pdf"
    input_file = "D:\\aiStudy\pdf-tools\\江苏移动数智云原生UI规范.pdf"
    output_file = "output666.pdf"
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"❌ 错误：文件 '{input_file}' 不存在")
        return
    
    try:
        # 创建工具实例
        tool = PDFBookmarkTool(input_file)
        
        # 设置工具选项
        # tool.enable_debug = True  # 启用调试模式
        tool.enable_enhanced_filter = True  # 是否启用增强过滤
        tool.enable_x_coordinate_filter = True  # 启用X坐标过滤
        tool.x_coordinate_tolerance = 5.0  # X坐标容差
        tool.require_numeric_start = True  # 是否要求数字开头
        tool.enable_font_size_filter = True
        tool.font_size_threshold = 9.0  # 字体大小阈值
        
        # 手动控制选项（可选）
        # tool.exclude_titles = []  # 排除的标题列表
        # tool.include_titles = []  # 包含的标题列表

        
        # 执行书签处理
        success = tool.new_auto_bookmark_process(output_file)
        
        if success:
            print(f"✅ 成功！输出文件: {output_file}")
        else:
            print("❌ 处理失败")
            
    except Exception as e:
        print(f"❌ 执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


def debug_with_custom_options():
    """方法3: 自定义调试选项"""
    print("\n🔧 方法3: 自定义调试选项")
    print("="*50)
    
    input_file = "../使用MasterGO的提效分析.pdf"
    output_file = "output666_custom.pdf"
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"❌ 错误：文件 '{input_file}' 不存在")
        return
    
    try:
        # 创建工具实例
        tool = PDFBookmarkTool(input_file)
        
        # 自定义调试设置
        tool.enable_debug = True
        tool.enable_enhanced_filter = True  # 启用增强过滤
        tool.enable_x_coordinate_filter = True
        tool.x_coordinate_tolerance = 3.0  # 更严格的X坐标容差
        tool.require_numeric_start = True  # 启用数字开头要求（测试新功能）
        tool.font_size_threshold = 12.0  # 设置字体大小阈值
        
        print(f"📁 输入文件: {input_file}")
        print(f"📁 输出文件: {output_file}")
        print(f"🔍 调试模式: {tool.enable_debug}")
        print(f"🔍 增强过滤: {tool.enable_enhanced_filter}")
        print(f"🔍 X坐标过滤: {tool.enable_x_coordinate_filter}")
        print(f"🔍 X坐标容差: {tool.x_coordinate_tolerance}")
        print(f"🔍 数字开头要求: {tool.require_numeric_start}")
        print(f"🔍 字体大小阈值: {tool.font_size_threshold}")
        print()
        
        # 执行书签处理
        success = tool.new_auto_bookmark_process(output_file)
        
        if success:
            print(f"✅ 成功！输出文件: {output_file}")
        else:
            print("❌ 处理失败")
            
    except Exception as e:
        print(f"❌ 执行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 PDF书签工具调试脚本")
    print("="*60)
    
    # 选择调试方法
    # method = input("选择调试方法 (1: main函数调用, 2: 直接调用, 3: 自定义选项, 0: 全部): ").strip()
    
    # if method == "1" or method == "0":
    debug_with_main_function()
    
    # if method == "2" or method == "0":
    # debug_with_direct_call()
    
    # if method == "3" or method == "0":
    #     debug_with_custom_options()
    
    # print("\n🎯 调试完成！")
