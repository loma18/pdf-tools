#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF书签工具使用示例
"""

from pdf_bookmark_tool import PDFBookmarkTool
import os

def example_usage():
    """演示如何使用PDF书签工具"""
    
    # 示例PDF文件路径（您需要提供实际的PDF文件）
    input_pdf = "sample_document.pdf"
    output_pdf = "sample_document_with_bookmarks.pdf"
    
    # 检查文件是否存在
    if not os.path.exists(input_pdf):
        print(f"请确保PDF文件 '{input_pdf}' 存在")
        print("您可以将任何包含目录的PDF文件重命名为 'sample_document.pdf' 进行测试")
        return
    
    print("=== PDF自动书签工具示例 ===\n")
    
    # 创建工具实例
    tool = PDFBookmarkTool(input_pdf)
    
    # 处理PDF文件
    print("开始处理PDF文件...")
    success = tool.process_pdf(output_pdf)
    
    if success:
        print(f"\n✅ 成功！已为PDF文件添加书签")
        print(f"原文件: {input_pdf}")
        print(f"新文件: {output_pdf}")
        print("\n您现在可以在PDF阅读器中看到自动生成的书签了！")
    else:
        print("\n❌ 处理失败，请检查PDF文件格式和内容")

def batch_process_example():
    """批量处理示例"""
    
    # 可以处理的PDF文件列表
    pdf_files = [
        "document1.pdf",
        "document2.pdf", 
        "document3.pdf"
    ]
    
    print("=== 批量处理示例 ===\n")
    
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            print(f"处理文件: {pdf_file}")
            tool = PDFBookmarkTool(pdf_file)
            
            # 生成输出文件名
            base_name = os.path.splitext(pdf_file)[0]
            output_file = f"{base_name}_带书签.pdf"
            
            if tool.process_pdf(output_file):
                print(f"✅ {pdf_file} 处理完成")
            else:
                print(f"❌ {pdf_file} 处理失败")
            print("-" * 50)
        else:
            print(f"⚠️  文件不存在: {pdf_file}")

if __name__ == "__main__":
    print("选择执行模式：")
    print("1. 单文件处理示例")
    print("2. 批量处理示例")
    
    choice = input("请输入选择 (1 或 2): ").strip()
    
    if choice == "1":
        example_usage()
    elif choice == "2":
        batch_process_example()
    else:
        print("无效选择，执行单文件处理示例")
        example_usage() 