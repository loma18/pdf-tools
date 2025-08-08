#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import subprocess

def test_electron_args():
    """测试Electron传递给Python的参数"""
    print("=== 测试Electron参数传递 ===")
    
    # 创建一个简单的参数接收脚本
    test_script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import argparse

def main():
    print("=== 参数接收测试 ===")
    print(f"所有参数: {sys.argv}")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file")
    parser.add_argument("--include-titles", type=str, help="包含的标题列表(JSON格式)")
    parser.add_argument("--exclude-titles", type=str, help="排除的标题列表(JSON格式)")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    
    try:
        args = parser.parse_args()
        print(f"解析成功:")
        print(f"  输入文件: {args.input_file}")
        print(f"  包含标题参数: {args.include_titles}")
        print(f"  排除标题参数: {args.exclude_titles}")
        print(f"  调试模式: {args.debug}")
        
        if args.include_titles:
            try:
                include_titles = json.loads(args.include_titles)
                print(f"  解析后的包含标题: {include_titles}")
            except json.JSONDecodeError as e:
                print(f"  JSON解析失败: {e}")
                
        if args.exclude_titles:
            try:
                exclude_titles = json.loads(args.exclude_titles)
                print(f"  解析后的排除标题: {exclude_titles}")
            except json.JSONDecodeError as e:
                print(f"  JSON解析失败: {e}")
                
    except Exception as e:
        print(f"参数解析失败: {e}")

if __name__ == "__main__":
    main()
'''
    
    # 写入测试脚本
    with open("test_args_receiver.py", "w", encoding="utf-8") as f:
        f.write(test_script_content)
    
    # 测试不同的参数传递方式
    test_cases = [
        {
            "name": "简单JSON字符串",
            "args": [
                "python", "test_args_receiver.py", "test.pdf",
                "--include-titles", '["综合结论"]',
                "--debug"
            ]
        },
        {
            "name": "带引号的JSON字符串",
            "args": [
                "python", "test_args_receiver.py", "test.pdf",
                "--include-titles", '"[\"综合结论\"]"',
                "--debug"
            ]
        },
        {
            "name": "转义的JSON字符串",
            "args": [
                "python", "test_args_receiver.py", "test.pdf",
                "--include-titles", '[\"综合结论\"]',
                "--debug"
            ]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- 测试 {i}: {test_case['name']} ---")
        print("命令:", " ".join(test_case['args']))
        
        try:
            result = subprocess.run(
                test_case['args'],
                capture_output=True,
                text=True,
                shell=True
            )
            
            print(f"返回码: {result.returncode}")
            if result.stdout:
                print("输出:")
                print(result.stdout)
            if result.stderr:
                print("错误:")
                print(result.stderr)
                
        except Exception as e:
            print(f"执行失败: {e}")
    
    # 清理测试文件
    try:
        os.remove("test_args_receiver.py")
    except:
        pass

if __name__ == "__main__":
    test_electron_args() 