#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF自动书签工具
自动识别PDF中的目录并添加书签，只针对目录，不对段落添加书签
"""

import fitz  # PyMuPDF
import re
import os
import sys
from typing import List, Tuple, Dict, Optional
import argparse


class PDFBookmarkTool:
    def __init__(self, pdf_path: str):
        """
        初始化PDF书签工具
        
        Args:
            pdf_path: PDF文件路径
        """
        self.pdf_path = pdf_path
        self.doc = None
        self.toc_patterns = [
            # 匹配各种目录格式 - 支持最多8层深度
            r'^第[一二三四五六七八九十\d]+章\s+.*',  # 第X章
            r'^第[一二三四五六七八九十\d]+节\s+.*',  # 第X节  
            r'^第[一二三四五六七八九十\d]+部分\s+.*',  # 第X部分
            r'^\d+\.\s+.*',  # 1. 标题
            r'^\d+\.\d+\s+.*',  # 1.1 标题
            r'^\d+\.\d+\.\d+\s+.*',  # 1.1.1 标题
            r'^\d+\.\d+\.\d+\.\d+\s+.*',  # 1.1.1.1 标题
            r'^\d+\.\d+\.\d+\.\d+\.\d+\s+.*',  # 1.1.1.1.1 标题
            r'^\d+\.\d+\.\d+\.\d+\.\d+\.\d+\s+.*',  # 1.1.1.1.1.1 标题
            r'^\d+\.\d+\.\d+\.\d+\.\d+\.\d+\.\d+\s+.*',  # 1.1.1.1.1.1.1 标题
            r'^\d+\.\d+\.\d+\.\d+\.\d+\.\d+\.\d+\.\d+\s+.*',  # 1.1.1.1.1.1.1.1 标题 (8层)
            r'^\d+(\.\d+){1,7}\s+.*',  # 支持1-8层深度的数字层级
            r'^[一二三四五六七八九十]+[、\.]\s+.*',  # 一、标题
            r'^[IVXLCDM]+[、\.]\s+.*',  # I、标题 (罗马数字)
            r'^[A-Z]\.\s+.*',  # A. 标题
            r'^[a-z]\)\s+.*',  # a) 标题
            r'^\([一二三四五六七八九十\d]+\)\s+.*',  # (1) 标题
            r'^【.*】.*',  # 【标题】格式
            r'^\d+、\s*.*',  # 1、标题
            r'^（[一二三四五六七八九十\d]+）\s*.*',  # （1）标题 
        ]
    
    def open_pdf(self) -> bool:
        """
        打开PDF文件
        
        Returns:
            bool: 是否成功打开
        """
        try:
            self.doc = fitz.open(self.pdf_path)
            return True
        except Exception as e:
            print(f"错误：无法打开PDF文件 {self.pdf_path}: {e}")
            return False
    
    def close_pdf(self):
        """关闭PDF文件"""
        if self.doc:
            self.doc.close()
    
    def extract_text_with_font_info(self, page_num: int) -> List[Dict]:
        """
        提取页面文本及字体信息
        
        Args:
            page_num: 页码
            
        Returns:
            List[Dict]: 文本块信息列表
        """
        page = self.doc[page_num]
        text_dict = page.get_text("dict")
        
        text_blocks = []
        for block in text_dict["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    line_text = ""
                    font_size = 0
                    font_flags = 0
                    
                    for span in line["spans"]:
                        line_text += span["text"]
                        font_size = max(font_size, span["size"])
                        font_flags = span["flags"]
                    
                    if line_text.strip():
                        text_blocks.append({
                            "text": line_text.strip(),
                            "font_size": font_size,
                            "font_flags": font_flags,
                            "page": page_num,
                            "bbox": line["bbox"]
                        })
        
        return text_blocks
    
    def is_likely_toc_text(self, text: str) -> Tuple[bool, int]:
        """
        判断文本是否可能是目录条目
        
        Args:
            text: 文本内容
            
        Returns:
            Tuple[bool, int]: (是否为目录, 层级深度)
        """
        text = text.strip()
        
        # 跳过页码行
        if re.match(r'^\d+$', text) or re.match(r'^- \d+ -$', text):
            return False, 0
            
        # 跳过过短的文本
        if len(text) < 3:
            return False, 0
            
        # 跳过明显不是目录的文本
        skip_patterns = [
            r'^页\s*\d+',  # 页X
            r'^\d+\s*页',  # X页
            r'^目\s*录',   # 目录
            r'^contents?$',  # contents
            r'^index$',     # index
        ]
        
        for skip_pattern in skip_patterns:
            if re.match(skip_pattern, text, re.IGNORECASE):
                return False, 0
            
        # 检查各种目录格式并确定层级
        for pattern in self.toc_patterns:
            if re.match(pattern, text):
                # 根据具体格式确定层级
                # 首先检查数字编号格式，支持任意深度
                number_match = re.match(r'^(\d+(?:\.\d+)*)', text)
                if number_match:
                    number_part = number_match.group(1)
                    level = number_part.count('.') + 1
                    return True, level
                elif '章' in text or '第' in text and ('章' in text or '部分' in text):
                    return True, 1
                elif '节' in text:
                    return True, 2
                elif re.match(r'^[一二三四五六七八九十]+[、\.]', text):
                    return True, 1
                elif re.match(r'^[IVXLCDM]+[、\.]', text):
                    return True, 1
                elif re.match(r'^[A-Z]\.', text):
                    return True, 2
                elif re.match(r'^[a-z]\)', text):
                    return True, 3
                elif re.match(r'^\([一二三四五六七八九十\d]+\)', text) or re.match(r'^（[一二三四五六七八九十\d]+）', text):
                    return True, 2
                elif re.match(r'^【.*】', text):
                    return True, 1
                elif re.match(r'^\d+、', text):
                    return True, 1
                else:
                    return True, 1
        
        return False, 0
    
    def find_toc_entries(self) -> List[Dict]:
        """
        查找所有目录条目
        
        Returns:
            List[Dict]: 目录条目列表
        """
        toc_entries = []
        
        print("正在分析PDF页面...")
        for page_num in range(len(self.doc)):
            print(f"处理第 {page_num + 1} 页...")
            
            text_blocks = self.extract_text_with_font_info(page_num)
            
            for block in text_blocks:
                text = block["text"]
                is_toc, level = self.is_likely_toc_text(text)
                
                if is_toc:
                    # 检查是否包含页码引用
                    page_ref_match = re.search(r'\.{3,}(\d+)$|…+(\d+)$|\s+(\d+)$', text)
                    target_page = None
                    clean_text = text
                    
                    if page_ref_match:
                        target_page = int(page_ref_match.group(1) or page_ref_match.group(2) or page_ref_match.group(3))
                        clean_text = re.sub(r'\.{3,}\d+$|…+\d+$|\s+\d+$', '', text).strip()
                    
                    toc_entries.append({
                        "title": clean_text,
                        "level": level,
                        "source_page": page_num,
                        "target_page": target_page or page_num,
                        "font_size": block["font_size"],
                        "font_flags": block["font_flags"]
                    })
        
        # 根据字体大小和位置排序
        toc_entries.sort(key=lambda x: (x["source_page"], -x["font_size"]))
        
        return toc_entries
    
    def filter_duplicate_entries(self, toc_entries: List[Dict]) -> List[Dict]:
        """
        过滤重复的目录条目
        
        Args:
            toc_entries: 原始目录条目列表
            
        Returns:
            List[Dict]: 过滤后的目录条目列表
        """
        filtered_entries = []
        seen_titles = set()
        
        for entry in toc_entries:
            title_key = entry["title"].lower().strip()
            if title_key not in seen_titles and len(title_key) > 2:
                seen_titles.add(title_key)
                filtered_entries.append(entry)
        
        return filtered_entries
    
    def validate_toc_logic(self, toc_entries: List[Dict]) -> List[Dict]:
        """
        验证目录逻辑的合理性，过滤不合理的条目
        
        Args:
            toc_entries: 目录条目列表
            
        Returns:
            List[Dict]: 逻辑验证后的目录条目列表
        """
        if not toc_entries:
            return toc_entries
        
        # 第一步：构建全局数字序列索引
        number_sequences = []
        for entry in toc_entries:
            numbers = self.extract_number_sequence(entry["title"])
            number_sequences.append(numbers)
        
        # 第二步：验证顶层数字连续性
        toc_entries = self.validate_top_level_continuity(toc_entries, number_sequences)
        
        # 重新构建序列索引
        number_sequences = []
        for entry in toc_entries:
            numbers = self.extract_number_sequence(entry["title"])
            number_sequences.append(numbers)
        
        # 第三步：验证父子层级一致性
        toc_entries = self.validate_parent_child_consistency(toc_entries, number_sequences)
        
        # 重新构建序列索引
        number_sequences = []
        for entry in toc_entries:
            numbers = self.extract_number_sequence(entry["title"])
            number_sequences.append(numbers)
        
        # 第四步：强制排序验证
        toc_entries = self.validate_numeric_ordering(toc_entries, number_sequences)
        
        # 重新构建序列索引
        number_sequences = []
        for entry in toc_entries:
            numbers = self.extract_number_sequence(entry["title"])
            number_sequences.append(numbers)
        
        # 第五步：其他逻辑验证
        validated_entries = []
        
        for i, entry in enumerate(toc_entries):
            should_include = True
            current_numbers = number_sequences[i]
            
            if i > 0 and current_numbers:
                prev_entry = validated_entries[-1] if validated_entries else None
                
                if prev_entry:
                    prev_numbers = self.extract_number_sequence(prev_entry["title"])
                    
                    if prev_numbers and current_numbers:
                        # 检查基本的不合理跳跃
                        if self.is_unreasonable_jump(prev_numbers, current_numbers):
                            print(f"跳过不合理的条目: '{entry['title']}' (前一个: '{prev_entry['title']}')")
                            should_include = False
                        
                        # 检查前瞻性逻辑冲突
                        elif self.has_lookahead_conflict(prev_numbers, current_numbers, number_sequences[i+1:]):
                            print(f"跳过前瞻性冲突条目: '{entry['title']}' (前一个: '{prev_entry['title']}')")
                            should_include = False
            
            if should_include:
                validated_entries.append(entry)
        
        return validated_entries
    
    def validate_top_level_continuity(self, toc_entries: List[Dict], number_sequences: List[List[int]]) -> List[Dict]:
        """
        验证顶层数字的连续性，顶层数字必须连续（1、2、3...）
        
        Args:
            toc_entries: 目录条目列表
            number_sequences: 对应的数字序列列表
            
        Returns:
            List[Dict]: 验证后的目录条目列表
        """
        if not toc_entries or not number_sequences:
            return toc_entries
        
        # 收集所有顶层数字（第一个数字）
        top_level_numbers = set()
        top_level_entries = []
        
        for entry, numbers in zip(toc_entries, number_sequences):
            if numbers and len(numbers) >= 1:
                top_level_num = numbers[0]
                top_level_numbers.add(top_level_num)
                top_level_entries.append((entry, numbers, top_level_num))
        
        if not top_level_numbers:
            return toc_entries
        
        # 找出连续的顶层数字范围
        sorted_top_nums = sorted(top_level_numbers)
        valid_top_nums = set()
        
        # 从1开始检查连续性
        if 1 in sorted_top_nums:
            current = 1
            while current in sorted_top_nums:
                valid_top_nums.add(current)
                current += 1
        
        # 如果没有从1开始，检查是否有其他连续序列（至少3个连续数字）
        if not valid_top_nums:
            for start_num in sorted_top_nums:
                consecutive_count = 0
                current = start_num
                temp_valid = set()
                
                while current in sorted_top_nums:
                    temp_valid.add(current)
                    consecutive_count += 1
                    current += 1
                
                # 如果有至少3个连续数字，认为是有效的
                if consecutive_count >= 3:
                    valid_top_nums = temp_valid
                    break
        
        print(f"顶层数字连续性验证: 有效顶层数字 {sorted(valid_top_nums)}")
        
        # 过滤只保留有效顶层数字的条目
        validated_entries = []
        for entry, numbers in zip(toc_entries, number_sequences):
            should_include = True
            
            if numbers and len(numbers) >= 1:
                top_level_num = numbers[0]
                if top_level_num not in valid_top_nums:
                    print(f"跳过顶层数字不连续的条目: '{entry['title']}' (顶层数字: {top_level_num})")
                    should_include = False
            
            if should_include:
                validated_entries.append(entry)
        
        return validated_entries
    
    def validate_parent_child_consistency(self, toc_entries: List[Dict], number_sequences: List[List[int]]) -> List[Dict]:
        """
        验证父子层级一致性，子级必须包含父级的完整数字前缀
        
        Args:
            toc_entries: 目录条目列表
            number_sequences: 对应的数字序列列表
            
        Returns:
            List[Dict]: 验证后的目录条目列表
        """
        if not toc_entries or not number_sequences:
            return toc_entries
        
        validated_entries = []
        valid_sequences = []  # 记录已验证通过的序列
        
        for entry, current_numbers in zip(toc_entries, number_sequences):
            should_include = True
            
            if current_numbers and len(current_numbers) > 1:
                # 检查是否存在有效的父级
                parent_found = False
                
                # 寻找父级序列（比当前序列少一层的序列）
                parent_sequence = current_numbers[:-1]
                
                for valid_seq in valid_sequences:
                    if valid_seq == parent_sequence:
                        parent_found = True
                        break
                
                if not parent_found:
                    print(f"跳过缺少父级的条目: '{entry['title']}' (需要父级: {'.'.join(map(str, parent_sequence))})")
                    should_include = False
            
            if should_include:
                validated_entries.append(entry)
                if current_numbers:
                    valid_sequences.append(current_numbers)
        
        return validated_entries
    
    def extract_number_sequence(self, title: str) -> List[int]:
        """
        提取标题中的数字序列
        
        Args:
            title: 标题文本
            
        Returns:
            List[int]: 数字序列，如"2.4.1"返回[2,4,1]
        """
        match = re.match(r'^(\d+(?:\.\d+)*)', title.strip())
        if match:
            number_str = match.group(1)
            return [int(x) for x in number_str.split('.')]
        return []
    
    def is_unreasonable_jump(self, prev_numbers: List[int], current_numbers: List[int]) -> bool:
        """
        判断两个数字序列之间是否存在不合理的跳跃
        
        Args:
            prev_numbers: 前一个条目的数字序列
            current_numbers: 当前条目的数字序列
            
        Returns:
            bool: 是否为不合理的跳跃
        """
        if not prev_numbers or not current_numbers:
            return False
        
        # 情况1: 在较高层级之后突然跳回较低层级的开头
        # 例如: 2.4 之后出现 1. (应该是 2.5 或 2.4.1)
        if len(current_numbers) == 1 and len(prev_numbers) >= 2:
            if current_numbers[0] < prev_numbers[0]:
                return True
        
        # 情况2: 同一层级的数字倒退
        # 例如: 2.4 之后出现 2.2
        if len(current_numbers) == len(prev_numbers):
            for i in range(len(current_numbers) - 1):
                if current_numbers[i] != prev_numbers[i]:
                    break
            else:
                # 前面的数字都相同,检查最后一个数字
                if current_numbers[-1] < prev_numbers[-1]:
                    # 允许小幅度的倒退(可能是页面顺序问题)，但不允许大幅度倒退
                    if prev_numbers[-1] - current_numbers[-1] > 2:
                        return True
        
        # 情况3: 跨级别的不合理跳跃
        # 例如: 1.1 之后直接出现 3.1 (跳过了 1.2, 2.x)
        if len(current_numbers) >= 2 and len(prev_numbers) >= 2:
            if current_numbers[0] > prev_numbers[0] + 1:
                return True
        
        return False
    
    def validate_numeric_ordering(self, toc_entries: List[Dict], number_sequences: List[List[int]]) -> List[Dict]:
        """
        验证数字编号的排序合理性，过滤违反递增规律的条目
        
        Args:
            toc_entries: 目录条目列表
            number_sequences: 对应的数字序列列表
            
        Returns:
            List[Dict]: 排序验证后的目录条目列表
        """
        if not toc_entries or not number_sequences:
            return toc_entries
        
        validated_entries = []
        validated_sequences = []
        
        for i, (entry, current_numbers) in enumerate(zip(toc_entries, number_sequences)):
            should_include = True
            
            if current_numbers:  # 只验证有数字编号的条目
                # 检查与已验证条目的排序关系
                if self.violates_numeric_ordering(current_numbers, validated_sequences):
                    print(f"跳过排序不合理的条目: '{entry['title']}' (违反数字递增规律)")
                    should_include = False
            
            if should_include:
                validated_entries.append(entry)
                validated_sequences.append(current_numbers)
        
        return validated_entries
    
    def violates_numeric_ordering(self, current_numbers: List[int], 
                                 previous_sequences: List[List[int]]) -> bool:
        """
        检查当前数字序列是否违反了排序规律
        
        Args:
            current_numbers: 当前条目的数字序列
            previous_sequences: 之前所有验证通过的数字序列
            
        Returns:
            bool: 是否违反排序规律
        """
        if not current_numbers or not previous_sequences:
            return False
        
        # 对于深层级标题（5层及以上），采用更宽松的验证策略
        if len(current_numbers) >= 5:
            # 允许深层级标题有一定的重复，只检查连续重复超过2次的情况
            duplicate_count = 0
            for prev_seq in previous_sequences:
                if prev_seq == current_numbers:
                    duplicate_count += 1
            
            # 如果同一个深层级序列重复超过2次，才认为是违规
            if duplicate_count >= 2:
                return True
            return False  # 允许少量重复通过
        
        # 对于浅层级标题，使用原有的严格验证
        most_relevant_prev = self.find_most_relevant_sequence(current_numbers, previous_sequences)
        
        if most_relevant_prev:
            comparison_result = self.compare_number_sequences(most_relevant_prev, current_numbers)
            if comparison_result == "VIOLATION":
                return True
        
        return False
    
    def find_most_relevant_sequence(self, current_numbers: List[int], 
                                   previous_sequences: List[List[int]]) -> List[int]:
        """
        找到与当前序列最相关的前序序列进行比较
        
        Args:
            current_numbers: 当前数字序列
            previous_sequences: 之前的数字序列列表
            
        Returns:
            List[int]: 最相关的前序序列，如果没有找到返回None
        """
        if not current_numbers or not previous_sequences:
            return None
        
        best_match = None
        max_common_prefix = -1
        best_layer_diff = float('inf')
        
        # 寻找具有最长公共前缀的同层级或相关层级序列
        for prev_numbers in reversed(previous_sequences):  # 从最近的开始
            if not prev_numbers:
                continue
            
            # 计算公共前缀长度
            common_prefix_len = 0
            min_len = min(len(current_numbers), len(prev_numbers))
            
            for i in range(min_len):
                if current_numbers[i] == prev_numbers[i]:
                    common_prefix_len += 1
                else:
                    break
            
            layer_diff = abs(len(current_numbers) - len(prev_numbers))
            
            # 优先选择同层级且有公共前缀的序列
            if len(current_numbers) == len(prev_numbers) and common_prefix_len >= len(current_numbers) - 1:
                return prev_numbers
            
            # 对于深层级标题（5层及以上），更宽松的匹配条件
            if len(current_numbers) >= 5:
                # 如果公共前缀足够长（至少3级），则认为相关
                if common_prefix_len >= 3 and common_prefix_len > max_common_prefix:
                    max_common_prefix = common_prefix_len
                    best_match = prev_numbers
                    best_layer_diff = layer_diff
                elif common_prefix_len == max_common_prefix and layer_diff < best_layer_diff:
                    best_match = prev_numbers
                    best_layer_diff = layer_diff
            else:
                # 对于浅层级标题，保持原有逻辑
                if common_prefix_len > max_common_prefix:
                    max_common_prefix = common_prefix_len
                    best_match = prev_numbers
                    best_layer_diff = layer_diff
                elif common_prefix_len == max_common_prefix and layer_diff < best_layer_diff:
                    best_match = prev_numbers
                    best_layer_diff = layer_diff
        
        # 根据层级调整最小公共前缀要求
        min_prefix_required = 2
        if len(current_numbers) >= 5:
            min_prefix_required = 4  # 深层级需要更多公共前缀才进行比较
        elif len(current_numbers) >= 4:
            min_prefix_required = 3  # 4层级需要至少3级公共前缀
        
        if max_common_prefix >= min_prefix_required:
            return best_match
        
        return None
    
    def compare_number_sequences(self, prev_numbers: List[int], current_numbers: List[int]) -> str:
        """
        比较两个数字序列的排序合理性
        
        Args:
            prev_numbers: 前一个数字序列
            current_numbers: 当前数字序列
            
        Returns:
            str: "VALID" (合理), "VIOLATION" (违反), "UNRELATED" (无关)
        """
        if not prev_numbers or not current_numbers:
            return "UNRELATED"
        
        # 情况1: 完全相同层级的比较
        if len(prev_numbers) == len(current_numbers):
            # 检查前缀是否相同
            prefix_match_len = 0
            for i in range(len(prev_numbers) - 1):
                if prev_numbers[i] == current_numbers[i]:
                    prefix_match_len += 1
                else:
                    break
            
            # 如果前缀完全相同，比较最后一个数字
            if prefix_match_len == len(prev_numbers) - 1:
                if current_numbers[-1] <= prev_numbers[-1]:
                    return "VIOLATION"  # 数字倒退或相等，违反递增规律
                else:
                    # 对于深层级（5层及以上），允许更大的跳跃
                    if len(current_numbers) >= 5:
                        jump = current_numbers[-1] - prev_numbers[-1]
                        if jump > 50:  # 深层级允许更大跳跃
                            return "VIOLATION"
                    else:
                        jump = current_numbers[-1] - prev_numbers[-1]
                        if jump > 10:  # 浅层级保持原有限制
                            return "VIOLATION"
                    return "VALID"
            else:
                return "UNRELATED"  # 不同分支，无需比较
        
        # 情况2: 不同层级但有关联的比较
        min_len = min(len(prev_numbers), len(current_numbers))
        
        # 检查公共前缀
        common_prefix_len = 0
        for i in range(min_len):
            if prev_numbers[i] == current_numbers[i]:
                common_prefix_len += 1
            else:
                break
        
        # 如果有公共前缀
        if common_prefix_len > 0:
            # 在公共前缀之后的第一个数字进行比较
            if common_prefix_len < min_len:
                if current_numbers[common_prefix_len] <= prev_numbers[common_prefix_len]:
                    return "VIOLATION"
                else:
                    return "VALID"
            else:
                # 一个是另一个的前缀
                if len(current_numbers) < len(prev_numbers):
                    # 从深层级回到浅层级，通常是合理的层级回退
                    return "VALID"
                else:
                    # 从浅层级进入深层级，通常是合理的
                    return "VALID"
        else:
            # 完全不同的分支，检查第一个数字
            if current_numbers[0] <= prev_numbers[0]:
                return "VIOLATION"  # 分支倒退或相等
            else:
                return "VALID"  # 分支正常前进
        
        return "UNRELATED"
    
    def has_lookahead_conflict(self, prev_numbers: List[int], current_numbers: List[int], 
                              future_sequences: List[List[int]]) -> bool:
        """
        检查当前条目是否与后续条目存在前瞻性逻辑冲突
        
        Args:
            prev_numbers: 前一个条目的数字序列
            current_numbers: 当前条目的数字序列  
            future_sequences: 后续所有条目的数字序列列表
            
        Returns:
            bool: 是否存在前瞻性冲突
        """
        if not prev_numbers or not current_numbers or not future_sequences:
            return False
        
        # 查找未来是否有与前一个条目同族的条目
        for future_numbers in future_sequences:
            if not future_numbers:
                continue
            
            # 情况1: 如果前一个条目是深层级(如2.6.2.1.1)，当前是高层级(如3)
            # 但后续还有与前一个条目同族的条目(如2.6.2.2)，则当前条目不合理
            if len(prev_numbers) >= 3 and len(current_numbers) == 1:
                # 检查未来是否有与前一个条目同族的条目
                if self.is_same_family(prev_numbers, future_numbers):
                    return True
            
            # 情况2: 更一般的情况 - 检查是否跨越了应该连续的数字序列
            if len(prev_numbers) >= 2 and len(current_numbers) <= len(prev_numbers) - 1:
                # 如果当前层级比前一个浅很多，但未来有更匹配的序列
                if self.is_better_sequence_ahead(prev_numbers, current_numbers, future_numbers):
                    return True
        
        return False
    
    def is_same_family(self, numbers1: List[int], numbers2: List[int]) -> bool:
        """
        判断两个数字序列是否属于同一族群
        
        Args:
            numbers1: 第一个数字序列
            numbers2: 第二个数字序列
            
        Returns:
            bool: 是否属于同一族群
        """
        if not numbers1 or not numbers2:
            return False
        
        # 如果两个序列的前缀相同，则属于同一族群
        # 例如 [2,6,2,1,1] 和 [2,6,2,2] 都属于 [2,6,2] 族群
        min_len = min(len(numbers1), len(numbers2))
        common_prefix_len = 0
        
        for i in range(min_len):
            if numbers1[i] == numbers2[i]:
                common_prefix_len += 1
            else:
                break
        
        # 如果公共前缀长度>=2，则认为是同族群
        return common_prefix_len >= 2
    
    def is_better_sequence_ahead(self, prev_numbers: List[int], current_numbers: List[int], 
                                future_numbers: List[int]) -> bool:
        """
        判断未来是否有更合适的序列
        
        Args:
            prev_numbers: 前一个数字序列
            current_numbers: 当前数字序列
            future_numbers: 未来的数字序列
            
        Returns:
            bool: 未来是否有更合适的序列
        """
        if not all([prev_numbers, current_numbers, future_numbers]):
            return False
        
        # 如果前一个是深层级，当前是浅层级，但未来有中间层级
        # 例如：prev=[2,6,2,1,1], current=[3], future=[2,6,2,2]
        # 这种情况下，current=[3]是不合理的，因为应该先有[2,6,2,2]
        
        if len(prev_numbers) >= 3 and len(current_numbers) == 1:
            # 检查future是否是更合理的下一个条目
            if len(future_numbers) >= 2:
                # 如果future与prev有公共前缀，且层级更接近
                if self.is_same_family(prev_numbers, future_numbers):
                    return True
        
        return False
    
    def normalize_toc_levels(self, toc_entries: List[Dict]) -> List[Dict]:
        """
        基于数字序列规范化目录层级，确保层级关系正确
        
        Args:
            toc_entries: 原始目录条目列表
            
        Returns:
            List[Dict]: 规范化后的目录条目列表
        """
        if not toc_entries:
            return toc_entries
        
        normalized_entries = []
        
        for entry in toc_entries:
            # 提取数字序列来确定真实层级
            numbers = self.extract_number_sequence(entry["title"])
            
            if numbers:
                # 基于数字序列的长度确定层级
                correct_level = len(numbers)
            else:
                # 如果没有数字序列，保持原始层级或默认为1
                correct_level = entry.get("level", 1)
            
            # 确保层级至少为1
            correct_level = max(1, correct_level)
            
            # 创建新条目
            new_entry = entry.copy()
            new_entry["level"] = correct_level
            normalized_entries.append(new_entry)
        
        # 验证并调整层级跳跃 - 使用更智能的逻辑
        final_entries = []
        level_stack = []  # 记录各层级的最后出现位置
        
        for i, entry in enumerate(normalized_entries):
            current_level = entry["level"]
            
            # 更新层级栈
            # 移除比当前层级更深的层级
            level_stack = [level for level in level_stack if level < current_level]
            
            # 检查层级跳跃是否合理
            if level_stack:
                max_existing_level = max(level_stack)
                if current_level > max_existing_level + 1:
                    # 层级跳跃过大，但如果是基于数字序列的，可能是合理的
                    numbers = self.extract_number_sequence(entry["title"])
                    if numbers and len(numbers) == current_level:
                        # 数字序列支持这个层级，保持不变
                        pass
                    else:
                        # 调整为合理的层级
                        adjusted_level = max_existing_level + 1
                        print(f"调整层级跳跃: '{entry['title'][:30]}...' 从层级{current_level}调整到{adjusted_level}")
                        entry = entry.copy()
                        entry["level"] = adjusted_level
                        current_level = adjusted_level
            
            # 添加当前层级到栈中
            if current_level not in level_stack:
                level_stack.append(current_level)
            
            final_entries.append(entry)
        
        return final_entries

    def reorder_for_hierarchy(self, toc_entries: List[Dict]) -> List[Dict]:
        """
        重新排序条目以确保父子关系正确
        
        Args:
            toc_entries: 规范化后的目录条目列表
            
        Returns:
            List[Dict]: 重新排序后的目录条目列表
        """
        if not toc_entries:
            return toc_entries
        
        # 按数字序列进行分组和排序
        groups = {}
        
        for entry in toc_entries:
            numbers = self.extract_number_sequence(entry["title"])
            if numbers:
                # 使用数字序列的前缀作为分组键
                for i in range(1, len(numbers) + 1):
                    prefix = tuple(numbers[:i])
                    if prefix not in groups:
                        groups[prefix] = []
                    if len(numbers) == i:  # 只有当数字序列长度匹配时才添加
                        groups[prefix].append(entry)
            else:
                # 没有数字序列的条目，使用特殊键
                key = ("no_numbers", entry["title"])
                if key not in groups:
                    groups[key] = []
                groups[key].append(entry)
        
        # 递归构建层级结构
        def build_hierarchy(prefix_tuple, max_depth=10):
            result = []
            if max_depth <= 0:
                return result
            
            # 添加当前层级的条目
            if prefix_tuple in groups:
                result.extend(groups[prefix_tuple])
            
            # 添加子层级的条目
            for key in sorted(groups.keys()):
                if (isinstance(key, tuple) and 
                    len(key) == len(prefix_tuple) + 1 and 
                    key[:len(prefix_tuple)] == prefix_tuple):
                    result.extend(build_hierarchy(key, max_depth - 1))
            
            return result
        
        # 从顶层开始构建
        reordered_entries = []
        
        # 处理顶层条目（单个数字）
        top_level_keys = [key for key in groups.keys() 
                         if isinstance(key, tuple) and len(key) == 1]
        top_level_keys.sort()
        
        for key in top_level_keys:
            reordered_entries.extend(build_hierarchy(key))
        
        # 处理没有数字序列的条目
        for key in groups.keys():
            if not isinstance(key, tuple) or len(key) != 1:
                if isinstance(key, tuple) and key[0] == "no_numbers":
                    reordered_entries.extend(groups[key])
        
        print(f"重新排序: 原始{len(toc_entries)}个条目 -> 排序后{len(reordered_entries)}个条目")
        return reordered_entries

    def adjust_for_pymupdf(self, toc_entries: List[Dict]) -> List[Dict]:
        """
        调整TOC条目以符合PyMuPDF的严格层级要求
        
        Args:
            toc_entries: 已规范化的目录条目列表
            
        Returns:
            List[Dict]: 调整后的目录条目列表
        """
        if not toc_entries:
            return toc_entries
        
        adjusted_entries = []
        prev_level = 0
        
        for i, entry in enumerate(toc_entries):
            current_level = entry["level"]
            
            # PyMuPDF要求层级跳跃不能超过1
            if current_level > prev_level + 1:
                # 调整为合理的层级
                adjusted_level = prev_level + 1
                print(f"PyMuPDF兼容性调整: '{entry['title'][:30]}...' 层级从 {current_level} 调整到 {adjusted_level}")
                entry = entry.copy()
                entry["level"] = adjusted_level
                current_level = adjusted_level
            
            adjusted_entries.append(entry)
            prev_level = current_level
        
        return adjusted_entries

    def add_bookmarks(self, toc_entries: List[Dict]) -> bool:
        """
        添加书签到PDF
        
        Args:
            toc_entries: 目录条目列表
            
        Returns:
            bool: 是否成功
        """
        try:
            # 清除现有书签
            self.doc.set_toc([])
            
            if not toc_entries:
                print("警告：没有目录条目可添加")
                return False
            
            # 规范化层级结构
            normalized_entries = self.normalize_toc_levels(toc_entries)
            
            # 重新排序以确保父子关系正确
            print("开始重新排序以确保父子关系正确...")
            reordered_entries = self.reorder_for_hierarchy(normalized_entries)
            print(f"重新排序完成，条目数: {len(reordered_entries)}")
            
            # 进一步调整层级以符合PyMuPDF的严格要求
            print("开始PyMuPDF兼容性调整...")
            final_entries = self.adjust_for_pymupdf(reordered_entries)
            print(f"PyMuPDF兼容性调整完成，最终条目数: {len(final_entries)}")
            
            # 构建新的目录结构
            toc = []
            for i, entry in enumerate(final_entries):
                # 确保目标页面在有效范围内
                target_page = min(entry["target_page"], len(self.doc) - 1)
                target_page = max(0, target_page)
                
                toc_item = [
                    entry["level"],
                    entry["title"],
                    target_page + 1,  # PyMuPDF使用1基索引
                    {"kind": 1, "page": target_page}  # 添加页面引用
                ]
                
                toc.append(toc_item)
                
                # 添加调试信息
                if i < 5:  # 只显示前5个条目的调试信息
                    print(f"调试: 条目 {i+1} - 层级: {entry['level']}, 标题: {entry['title'][:20]}..., 页面: {target_page + 1}")
            
            print(f"准备添加 {len(toc)} 个书签条目")
            
            # 验证TOC结构
            if not self.validate_toc_structure(toc):
                print("错误：TOC结构验证失败")
                return False
            
            # 设置新的目录
            self.doc.set_toc(toc)
            return True
            
        except Exception as e:
            print(f"错误：添加书签失败: {e}")
            print(f"错误详情：在处理第 {len(toc) if 'toc' in locals() else 0} 个条目时出错")
            return False
    
    def validate_toc_structure(self, toc: List) -> bool:
        """
        验证TOC结构是否符合PyMuPDF的要求（使用更宽松的验证）
        
        Args:
            toc: TOC列表
            
        Returns:
            bool: 结构是否有效
        """
        if not toc:
            return True
        
        # 检查第一个条目是否从层级1开始
        if toc[0][0] != 1:
            print(f"错误：第一个条目的层级必须是1，当前是{toc[0][0]}")
            return False
        
        # 使用更宽松的层级验证
        level_stack = []  # 记录出现过的层级
        
        for i, item in enumerate(toc):
            level = item[0]
            title = item[1]
            
            # 层级必须是正整数
            if level < 1:
                print(f"错误：第 {i+1} 个条目层级必须大于0，当前是 {level}")
                return False
            
            # 更新层级栈
            level_stack = [l for l in level_stack if l < level]
            
            # 检查层级跳跃是否合理
            if level_stack:
                max_existing_level = max(level_stack)
                if level > max_existing_level + 1:
                    # 检查是否是基于数字序列的合理跳跃
                    numbers = self.extract_number_sequence(title)
                    if numbers and len(numbers) == level:
                        # 数字序列支持这个层级，允许跳跃
                        print(f"允许层级跳跃：第 {i+1} 个条目 '{title[:30]}...' (层级 {level}，数字序列支持)")
                    else:
                        print(f"警告：第 {i+1} 个条目层级跳跃较大 (从最大层级 {max_existing_level} 跳到 {level})，但将继续处理")
            
            # 添加当前层级到栈中
            if level not in level_stack:
                level_stack.append(level)
        
        return True
    
    def save_pdf(self, output_path: Optional[str] = None) -> bool:
        """
        保存PDF文件
        
        Args:
            output_path: 输出路径，如果为None则生成新文件名
            
        Returns:
            bool: 是否成功
        """
        try:
            if output_path:
                save_path = output_path
            else:
                # 生成新的文件名避免覆盖原文件时的问题
                base_name = self.pdf_path.rsplit('.', 1)[0]
                save_path = f"{base_name}_with_bookmarks.pdf"
            
            self.doc.save(save_path, garbage=4, deflate=True)
            print(f"PDF已保存到: {save_path}")
            return True
        except Exception as e:
            print(f"错误：保存PDF失败: {e}")
            return False
    
    def process_pdf(self, output_path: Optional[str] = None) -> bool:
        """
        处理PDF文件，添加书签
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        if not self.open_pdf():
            return False
        
        try:
            print(f"开始处理PDF文件: {self.pdf_path}")
            print(f"总页数: {len(self.doc)}")
            
            # 查找目录条目
            toc_entries = self.find_toc_entries()
            print(f"找到 {len(toc_entries)} 个潜在目录条目")
            
            if not toc_entries:
                print("警告：未找到任何目录条目")
                return False
            
            # 过滤重复条目
            toc_entries = self.filter_duplicate_entries(toc_entries)
            print(f"过滤重复后剩余 {len(toc_entries)} 个目录条目")
            
            # 验证目录逻辑合理性
            toc_entries = self.validate_toc_logic(toc_entries)
            print(f"逻辑验证后剩余 {len(toc_entries)} 个目录条目")
            
            # 显示找到的目录条目
            print("\n找到的目录条目:")
            for i, entry in enumerate(toc_entries[:10]):  # 只显示前10个
                indent = "  " * (entry["level"] - 1)
                print(f"{i+1:2d}. {indent}{entry['title']} (页面 {entry['target_page'] + 1})")
            
            if len(toc_entries) > 10:
                print(f"... 还有 {len(toc_entries) - 10} 个条目")
            
            # 添加书签
            if self.add_bookmarks(toc_entries):
                print("成功添加书签")
                
                # 保存文件
                if self.save_pdf(output_path):
                    save_path = output_path or self.pdf_path
                    print(f"PDF文件已保存到: {save_path}")
                    return True
                else:
                    return False
            else:
                return False
                
        except Exception as e:
            print(f"错误：处理PDF时发生异常: {e}")
            return False
        finally:
            self.close_pdf()


def main():
    parser = argparse.ArgumentParser(description="PDF自动书签工具")
    parser.add_argument("input_pdf", help="输入PDF文件路径")
    parser.add_argument("-o", "--output", help="输出PDF文件路径（可选，默认覆盖原文件）")
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input_pdf):
        print(f"错误：文件不存在: {args.input_pdf}")
        return 1
    
    # 创建工具实例并处理PDF
    tool = PDFBookmarkTool(args.input_pdf)
    
    if tool.process_pdf(args.output):
        print("✅ PDF书签添加完成！")
        return 0
    else:
        print("PDF书签添加失败！")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 