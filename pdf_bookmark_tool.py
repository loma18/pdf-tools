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
import requests


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
        # 添加字体大小分析相关属性
        self.font_size_threshold = 0  # 将在分析阶段动态设置
        self.title_font_sizes = []  # 用于收集标题字体大小
        self.enable_font_size_filter = True  # 是否启用字体大小过滤
        
        # 大模型API配置
        self.api_key = "666ailab_F4YlwHmeTJbeaPdVs6L0OUyJ80HrDlRQoH4o41UODYjk5/em00RclX1HAq3kQovn64O5hyMvh91FM5ZMrISlFjMCJx1a5hiNYkNYswO+qaG6kpXml5FppXM="
        self.api_url = "https://lab.iwhalecloud.com/gpt-proxy/v1/chat/completions"
    
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
                block_lines = []  # 收集当前块的所有行
                
                for line in block["lines"]:
                    line_text = ""
                    font_size = 0
                    font_flags = 0
                    
                    for span in line["spans"]:
                        line_text += span["text"]
                        font_size = max(font_size, span["size"])
                        font_flags = span["flags"]
                    
                    if line_text.strip():
                        block_lines.append({
                            "text": line_text.strip(),
                            "font_size": font_size,
                            "font_flags": font_flags,
                            "page": page_num,
                            "bbox": line["bbox"]
                        })
                
                # 为每行添加上下文信息
                for i, line_info in enumerate(block_lines):
                    line_info["context"] = {
                        "is_first_in_block": i == 0,
                        "is_last_in_block": i == len(block_lines) - 1,
                        "is_single_line_block": len(block_lines) == 1,
                        "prev_line_text": block_lines[i-1]["text"] if i > 0 else None,
                        "next_line_text": block_lines[i+1]["text"] if i < len(block_lines) - 1 else None,
                        "block_line_count": len(block_lines)
                    }
                    text_blocks.append(line_info)
        
        return text_blocks
    
    def is_likely_toc_text(self, text: str, context: Dict = None) -> Tuple[bool, int]:
        """
        判断文本是否可能是目录条目
        
        Args:
            text: 文本内容
            context: 上下文信息
            
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
        
        # 检查文本独立性（必须是独立的一行，不能前后有其他文字）
        if context and not self.is_text_independent(text, context):
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
        
        # 添加对无序号但可能是标题的短文本的支持
        # 如"后续想法"这类没有序号但是作为标题的文本
        if len(text) <= 15 and not re.search(r'[,.;:，。；：？！]', text):
            # 短文本且不包含标点符号，可能是标题
            # 此处返回level=1，后续会根据字体大小和逻辑关系再判断
            return True, 1
        
        return False, 0
    
    def is_text_independent(self, text: str, context: Dict) -> bool:
        """
        检查文本是否是独立的一行（不是表格或列表的一部分）
        
        Args:
            text: 要检查的文本
            context: 上下文信息
            
        Returns:
            bool: 是否是独立的文本
        """
        if not context:
            return True
        
        # 检查前后文本内容
        prev_text = context.get("prev_line_text", "")
        next_text = context.get("next_line_text", "")
        
        # 如果是单行块，很可能是独立的
        if context.get("is_single_line_block", False):
            return True
        
        # 检查是否在表格中
        if self.is_likely_in_table(text, prev_text, next_text):
            print(f"跳过表格中的文本: '{text}'")
            return False
        
        # 检查是否在列表中且前后有紧密相关的内容
        if self.is_likely_in_list(text, prev_text, next_text):
            print(f"跳过列表中的文本: '{text}'")
            return False
        
        # 检查是否是段落的一部分
        if self.is_likely_in_paragraph(text, prev_text, next_text):
            print(f"跳过段落中的文本: '{text}'")
            return False
        
        return True
    
    def is_likely_in_table(self, text: str, prev_text: str, next_text: str) -> bool:
        """
        检查文本是否在表格中
        
        Args:
            text: 当前文本
            prev_text: 前一行文本
            next_text: 后一行文本
            
        Returns:
            bool: 是否在表格中
        """
        # 检查常见的表格模式
        table_indicators = [
            # 如果前后文本都包含多个制表符或空格分隔的内容
            lambda t: len(t.split()) > 3 and any(len(word) < 4 for word in t.split()),
            # 如果文本前后有类似表格标题的内容
            lambda t: any(keyword in t for keyword in ['思考角度', '有利或不利因素', '优势', '劣势', '优点', '缺点']),
            # 如果前后文本有相似的结构
            lambda t: bool(re.search(r'\d+\.', t)) and len(t.split()) > 5,
        ]
        
        # 检查当前文本及前后文本是否符合表格模式
        texts_to_check = [t for t in [prev_text, next_text] if t]
        
        for indicator in table_indicators:
            if any(indicator(t) for t in texts_to_check):
                # 如果当前文本是编号开头且相对较长，可能是表格中的条目
                if re.match(r'^\d+\.', text) and len(text) > 10:
                    return True
        
        return False
    
    def is_likely_in_list(self, text: str, prev_text: str, next_text: str) -> bool:
        """
        检查文本是否在列表中
        
        Args:
            text: 当前文本
            prev_text: 前一行文本
            next_text: 后一行文本
            
        Returns:
            bool: 是否在列表中
        """
        # 如果前后文本都是类似的编号格式，可能是列表
        if prev_text and next_text:
            # 检查是否都是数字编号
            current_match = re.match(r'^(\d+)\.', text)
            prev_match = re.match(r'^(\d+)\.', prev_text)
            next_match = re.match(r'^(\d+)\.', next_text)
            
            if current_match and prev_match and next_match:
                current_num = int(current_match.group(1))
                prev_num = int(prev_match.group(1))
                next_num = int(next_match.group(1))
                
                # 如果是连续的编号，且不是常见的章节编号模式
                if (current_num == prev_num + 1 and next_num == current_num + 1):
                    # 检查是否是表格或列表的一部分而不是标题
                    if len(text) > 20 and not re.search(r'[第章节]', text):
                        return True
        
        return False
    
    def is_likely_in_paragraph(self, text: str, prev_text: str, next_text: str) -> bool:
        """
        检查文本是否是段落的一部分
        
        Args:
            text: 当前文本
            prev_text: 前一行文本
            next_text: 后一行文本
            
        Returns:
            bool: 是否是段落的一部分
        """
        # 如果前后文本都比较长且没有明显的标题特征，可能是段落的一部分
        if prev_text and next_text:
            if (len(prev_text) > 15 and len(next_text) > 15 and
                not re.match(r'^\d+\.', prev_text) and not re.match(r'^\d+\.', next_text)):
                # 当前文本如果也比较长且不是明显的标题格式，可能是段落
                if len(text) > 20 and not re.search(r'^[第\d]', text):
                    return True
        
        return False
    
    def analyze_font_distribution(self, font_sizes: List[float]) -> Dict:
        """
        分析字体大小分布，识别可能的标题字体大小
        
        Args:
            font_sizes: 字体大小列表
            
        Returns:
            Dict: 字体分析结果
        """
        if not font_sizes:
            return {"threshold": 0, "clusters": {}}
        
        # 对字体大小进行分组
        font_groups = {}
        for size in font_sizes:
            # 将相近的字体大小分到同一组（精确到小数点后1位）
            key = round(size, 1)
            if key not in font_groups:
                font_groups[key] = []
            font_groups[key].append(size)
        
        # 计算每个字体大小组的频率
        font_frequencies = {size: len(fonts) for size, fonts in font_groups.items()}
        
        # 按字体大小排序
        sorted_sizes = sorted(font_frequencies.keys(), reverse=True)
        
        # 识别可能的标题字体大小（通常较大且较少使用）
        title_sizes = []
        content_sizes = []
        
        # 如果有至少3种不同的字体大小
        if len(sorted_sizes) >= 3:
            # 假设最大的1-2种字体大小是标题
            title_sizes = sorted_sizes[:2]
            content_sizes = sorted_sizes[2:]
            
            # 检查频率 - 标题字体通常出现次数较少
            for size in sorted_sizes[:3]:  # 检查前三大字体
                if font_frequencies[size] < len(font_sizes) * 0.1:  # 如果出现频率低于10%
                    if size not in title_sizes:
                        title_sizes.append(size)
        else:
            # 字体种类较少，假设最大的是标题字体
            title_sizes = [sorted_sizes[0]] if sorted_sizes else []
            content_sizes = sorted_sizes[1:] if len(sorted_sizes) > 1 else []
        
        # 计算阈值 - 取标题字体中最小值的90%
        threshold = min(title_sizes) * 0.9 if title_sizes else 0
        
        # 构建分析结果
        result = {
            "threshold": threshold,
            "clusters": {
                "title_sizes": title_sizes,
                "content_sizes": content_sizes
            },
            "frequencies": font_frequencies,
            "all_sizes": sorted_sizes
        }
        
        return result
        
    def find_toc_entries(self) -> List[Dict]:
        """
        查找所有目录条目
        
        Returns:
            List[Dict]: 目录条目列表
        """
        toc_entries = []
        all_font_sizes = []  # 收集所有文本的字体大小
        potential_title_font_sizes = []  # 收集潜在标题的字体大小
        
        print("正在分析PDF页面...")
        for page_num in range(len(self.doc)):
            print(f"处理第 {page_num + 1} 页...")
            
            text_blocks = self.extract_text_with_font_info(page_num)
            
            # 收集当前页面的所有字体大小
            page_font_sizes = [block["font_size"] for block in text_blocks]
            all_font_sizes.extend(page_font_sizes)
            
            for block in text_blocks:
                text = block["text"]
                context = block.get("context", {})
                is_toc, level = self.is_likely_toc_text(text, context)
                
                if is_toc:
                    # 收集潜在标题的字体大小
                    potential_title_font_sizes.append(block["font_size"])
                    
                    # 检查是否包含页码引用
                    page_ref_match = re.search(r'\.{3,}(\d+)$|…+(\d+)$|\s+(\d+)$', text)
                    target_page = None
                    clean_text = text
                    
                    if page_ref_match:
                        target_page = int(page_ref_match.group(1) or page_ref_match.group(2) or page_ref_match.group(3))
                        clean_text = re.sub(r'\.{3,}\d+$|…+\d+$|\s+\d+$', '', text).strip()
                    
                    # 判断是否为数字序列格式的标题（如1.2.3格式）
                    number_sequence = self.extract_number_sequence(clean_text)
                    is_numbered_sequence = bool(number_sequence and len(number_sequence) > 1)
                    
                    toc_entries.append({
                        "title": clean_text,
                        "level": level,
                        "source_page": page_num,
                        "target_page": target_page or page_num,
                        "font_size": block["font_size"],
                        "font_flags": block["font_flags"],
                        "has_number": bool(re.match(r'^(\d+(?:\.\d+)*)|^第[一二三四五六七八九十\d]+[章节部分]|^[一二三四五六七八九十]+[、\.]|^[IVXLCDM]+[、\.]|^\d+、', clean_text)),
                        "is_numbered_sequence": is_numbered_sequence
                    })
        
        # 分析字体大小分布
        if self.enable_font_size_filter and potential_title_font_sizes:
            # 保存所有潜在标题的字体大小
            self.title_font_sizes = potential_title_font_sizes
            
            # 检查是否已经手动设置了字体大小阈值
            if self.font_size_threshold <= 0:
                # 如果没有手动设置，则进行自动分析
                font_analysis = self.analyze_font_distribution(potential_title_font_sizes)
                self.font_size_threshold = font_analysis["threshold"]
                print(f"字体大小分析: 识别到的标题字体大小 = {font_analysis['clusters']['title_sizes']}")
                print(f"自动计算字体大小阈值设置为: {self.font_size_threshold:.2f}")
            else:
                print(f"使用手动设置的字体大小阈值: {self.font_size_threshold:.2f}")
            
            # 根据字体大小过滤条目
            filtered_by_font = []
            
            # 首先找出所有有序号的标题及其字体大小
            numbered_title_font_sizes = set()
            for entry in toc_entries:
                if entry["has_number"] and entry["font_size"] >= self.font_size_threshold:
                    numbered_title_font_sizes.add(round(entry["font_size"], 1))
            
            print(f"有序号标题的字体大小: {sorted(numbered_title_font_sizes, reverse=True)}")
            
            # 降低多级数字序列标题的字体大小阈值（如3.4.1）
            sequence_threshold = self.font_size_threshold * 0.9
            print(f"多级数字序列标题的字体大小阈值: {sequence_threshold:.2f}")
            
            # 过滤条目，主要保留有序号的标题，对无序号标题采用更严格的条件
            for entry in toc_entries:
                should_keep = False
                
                # 情况1: 有序号的标题，字体大小大于阈值
                if entry["has_number"] and entry["font_size"] >= self.font_size_threshold:
                    should_keep = True
                
                # 情况2: 多级数字序列标题（如3.4.1），使用较低的阈值
                elif entry["is_numbered_sequence"] and entry["font_size"] >= sequence_threshold:
                    should_keep = True
                    print(f"保留多级数字序列标题: '{entry['title'][:30]}...' (字体大小: {entry['font_size']:.2f}，低于标准阈值但符合序列标题阈值)")
                
                # 情况3: 无序号标题，宽松保留（由大模型进行精确过滤）
                elif not entry["has_number"] and entry["font_size"] >= self.font_size_threshold:
                    # 对于无序号标题，采用宽松策略保留，让大模型进行精确的语义过滤
                    should_keep = True
                    print(f"保留无序号标题(交由大模型过滤): '{entry['title'][:30]}...' (字体大小: {entry['font_size']:.2f})")
                
                if should_keep:
                    filtered_by_font.append(entry)
                else:
                    print(f"基于字体大小过滤掉: '{entry['title'][:30]}...' (字体大小: {entry['font_size']:.2f})")
            
            print(f"字体大小过滤: 原始 {len(toc_entries)} 条目 -> 过滤后 {len(filtered_by_font)} 条目")
            toc_entries = filtered_by_font
        
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
        print(f"第二步后剩余条目数: {len(toc_entries)}")
        
        # 重新构建序列索引
        number_sequences = []
        for entry in toc_entries:
            numbers = self.extract_number_sequence(entry["title"])
            number_sequences.append(numbers)
        
        # 第三步：验证父子层级一致性
        toc_entries = self.validate_parent_child_consistency(toc_entries, number_sequences)
        print(f"第三步后剩余条目数: {len(toc_entries)}")
        
        # 重新构建序列索引
        number_sequences = []
        for entry in toc_entries:
            numbers = self.extract_number_sequence(entry["title"])
            number_sequences.append(numbers)
        
        # 第四步：强制排序验证
        toc_entries = self.validate_numeric_ordering(toc_entries, number_sequences)
        print(f"第四步后剩余条目数: {len(toc_entries)}")
        
        # 重新构建序列索引
        number_sequences = []
        for entry in toc_entries:
            numbers = self.extract_number_sequence(entry["title"])
            number_sequences.append(numbers)
        
        # 第五步：验证无编号标题的层级规则
        toc_entries = self.validate_unnumbered_title_hierarchy(toc_entries, number_sequences)
        print(f"第五步后剩余条目数: {len(toc_entries)}")
        
        # 重新构建序列索引
        number_sequences = []
        for entry in toc_entries:
            numbers = self.extract_number_sequence(entry["title"])
            number_sequences.append(numbers)
        
        # 第六步：字体大小与层级一致性验证
        toc_entries = self.validate_font_size_hierarchy_consistency(toc_entries, number_sequences)
        print(f"第六步后剩余条目数: {len(toc_entries)}")
        
        # 重新构建序列索引
        number_sequences = []
        for entry in toc_entries:
            numbers = self.extract_number_sequence(entry["title"])
            number_sequences.append(numbers)
        
        # 第七步：其他逻辑验证
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
    
    def validate_unnumbered_title_hierarchy(self, toc_entries: List[Dict], number_sequences: List[List[int]]) -> List[Dict]:
        """
        验证无编号标题的层级规则
        1. 无编号标题只能出现在第一层级或者父级是无编号标题的子级
        2. 第一层级的字体大小要保持全部相同大小
        
        Args:
            toc_entries: 目录条目列表
            number_sequences: 对应的数字序列列表
            
        Returns:
            List[Dict]: 验证后的目录条目列表
        """
        if not toc_entries:
            return toc_entries
        
        validated_entries = []
        
        # 第一步：收集第一层级条目的字体大小，验证一致性
        first_level_font_sizes = []
        for i, entry in enumerate(toc_entries):
            current_numbers = number_sequences[i]
            
            # 判断是否为第一层级
            is_first_level = False
            if current_numbers and len(current_numbers) == 1:  # 有编号的第一层级
                is_first_level = True
            elif not current_numbers:  # 无编号，可能是第一层级
                # 检查前面是否有编号条目，如果没有或者前面的都是第一层级，则认为是第一层级
                is_first_level = True
                for j in range(i):
                    prev_numbers = number_sequences[j]
                    if prev_numbers and len(prev_numbers) > 1:  # 前面有深层级编号
                        is_first_level = False
                        break
            
            if is_first_level:
                first_level_font_sizes.append(entry["font_size"])
        
        # 验证第一层级字体大小一致性
        if first_level_font_sizes:
            # 计算字体大小的标准差，判断是否基本一致
            import statistics
            if len(set(round(size, 1) for size in first_level_font_sizes)) > 2:  # 允许最多2种字体大小
                # 找出最常见的字体大小作为标准
                font_size_counts = {}
                for size in first_level_font_sizes:
                    rounded_size = round(size, 1)
                    font_size_counts[rounded_size] = font_size_counts.get(rounded_size, 0) + 1
                
                standard_font_size = max(font_size_counts.keys(), key=lambda x: font_size_counts[x])
                print(f"第一层级标准字体大小: {standard_font_size:.1f}")
            else:
                standard_font_size = round(statistics.mean(first_level_font_sizes), 1)
                print(f"第一层级字体大小: {standard_font_size:.1f}")
        else:
            standard_font_size = None
        
        # 第二步：验证每个条目的层级规则
        for i, entry in enumerate(toc_entries):
            should_include = True
            current_numbers = number_sequences[i]
            
            # 如果是无编号标题
            if not current_numbers:
                # 检查是否违反层级规则
                violation_reason = self.check_unnumbered_title_violation(i, toc_entries, number_sequences)
                
                if violation_reason:
                    print(f"跳过违反无编号标题层级规则的条目: '{entry['title']}' ({violation_reason})")
                    should_include = False
                
                # 如果是第一层级，检查字体大小一致性
                elif standard_font_size and self.is_first_level_unnumbered(i, toc_entries, number_sequences):
                    if abs(entry["font_size"] - standard_font_size) > 0.5:  # 允许0.5的误差
                        print(f"跳过第一层级字体大小不一致的条目: '{entry['title']}' "
                              f"(字体大小: {entry['font_size']:.1f} ≠ 标准: {standard_font_size:.1f})")
                        should_include = False
            
            if should_include:
                validated_entries.append(entry)
        
        return validated_entries
    
    def check_unnumbered_title_violation(self, index: int, toc_entries: List[Dict], number_sequences: List[List[int]]) -> str:
        """
        检查无编号标题是否违反层级规则
        
        Args:
            index: 当前条目索引
            toc_entries: 目录条目列表
            number_sequences: 数字序列列表
            
        Returns:
            str: 违反原因，如果没有违反返回空字符串
        """
        current_entry = toc_entries[index]
        
        # 查找前一个条目作为潜在的父级
        prev_entry = None
        prev_numbers = None
        
        for i in range(index - 1, -1, -1):
            if i >= 0:
                prev_entry = toc_entries[i]
                prev_numbers = number_sequences[i]
                break
        
        if not prev_entry:
            # 如果是第一个条目，肯定是第一层级，合法
            return ""
        
        # 检查前一个条目的层级
        if prev_numbers and len(prev_numbers) > 1:
            # 前一个条目是深层级的有编号标题，无编号标题不能作为其子级
            return f"不能作为深层级有编号标题 '{prev_entry['title']}' 的子级"
        
        if prev_numbers and len(prev_numbers) == 1:
            # 前一个条目是第一层级有编号标题
            # 检查后续是否有同级的有编号标题
            for j in range(index + 1, len(toc_entries)):
                next_numbers = number_sequences[j]
                if next_numbers and len(next_numbers) == 1:
                    # 发现后续有第一层级有编号标题，说明当前无编号标题夹在有编号标题中间
                    return f"出现在第一层级有编号标题之间，违反层级规则"
                elif next_numbers and len(next_numbers) > 1:
                    # 如果后续是深层级标题，则当前无编号标题可能是合法的
                    break
        
        # 如果前一个条目也是无编号标题，则当前条目可以作为其子级
        if not prev_numbers:
            return ""
        
        return ""
    
    def is_first_level_unnumbered(self, index: int, toc_entries: List[Dict], number_sequences: List[List[int]]) -> bool:
        """
        判断无编号标题是否为第一层级
        
        Args:
            index: 当前条目索引
            toc_entries: 目录条目列表
            number_sequences: 数字序列列表
            
        Returns:
            bool: 是否为第一层级
        """
        # 检查前面是否有深层级编号条目
        for i in range(index):
            prev_numbers = number_sequences[i]
            if prev_numbers and len(prev_numbers) > 1:
                return False
        
        # 检查后面是否有第一层级编号条目
        for i in range(index + 1, len(toc_entries)):
            next_numbers = number_sequences[i]
            if next_numbers and len(next_numbers) == 1:
                # 如果后面有第一层级编号条目，且中间没有深层级条目，则当前是第一层级
                has_deep_level_between = False
                for j in range(index + 1, i):
                    between_numbers = number_sequences[j]
                    if between_numbers and len(between_numbers) > 1:
                        has_deep_level_between = True
                        break
                
                if not has_deep_level_between:
                    return True
        
        # 如果前面只有第一层级或无编号条目，则认为是第一层级
        return True

    def validate_font_size_hierarchy_consistency(self, toc_entries: List[Dict], number_sequences: List[List[int]]) -> List[Dict]:
        """
        验证字体大小与层级一致性（已禁用，交由大模型语义过滤处理）
        """
        # 由于已经集成大模型语义过滤，这个验证逻辑容易误判，直接返回原始条目
        print("跳过字体大小一致性验证（交由大模型语义过滤处理）")
        return toc_entries
    
    def is_valid_child_sequence(self, parent_numbers: List[int], child_numbers: List[int]) -> bool:
        """
        检查是否是合理的父子层级关系
        
        Args:
            parent_numbers: 父级数字序列
            child_numbers: 子级数字序列
            
        Returns:
            bool: 是否为合理的父子关系
        """
        if not parent_numbers or not child_numbers:
            return False
        
        # 子级应该比父级多一层
        if len(child_numbers) != len(parent_numbers) + 1:
            return False
        
        # 子级的前缀应该与父级完全相同
        if child_numbers[:-1] != parent_numbers:
            return False
        
        # 子级的最后一个数字应该合理（通常从1开始）
        if child_numbers[-1] < 1:
            return False
        
        return True
    
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
            child_keys = []
            for key in groups.keys():
                if (isinstance(key, tuple) and 
                    len(key) == len(prefix_tuple) + 1 and 
                    key[:len(prefix_tuple)] == prefix_tuple):
                    child_keys.append(key)
            
            # 自定义排序函数，确保相同类型的键进行比较
            def safe_sort_key(key):
                if isinstance(key, tuple):
                    if key[0] == "no_numbers":
                        return (2, key[1])  # 无序号条目排在最后
                    else:
                        return (1, key)  # 有序号条目排在前面
                return (0, str(key))  # 其他类型转为字符串
            
            # 安全排序子键
            child_keys.sort(key=safe_sort_key)
            
            for key in child_keys:
                result.extend(build_hierarchy(key, max_depth - 1))
            
            return result
        
        # 从顶层开始构建
        reordered_entries = []
        
        # 处理顶层条目（单个数字）
        top_level_keys = [key for key in groups.keys() 
                         if isinstance(key, tuple) and len(key) == 1 and key[0] != "no_numbers"]
        
        # 自定义排序函数，确保只比较相同类型
        def safe_top_level_sort(key):
            if isinstance(key, tuple) and len(key) == 1 and isinstance(key[0], int):
                return key[0]
            return 999999  # 非数字键排在最后
        
        # 安全排序顶层键
        top_level_keys.sort(key=safe_top_level_sort)
        
        for key in top_level_keys:
            reordered_entries.extend(build_hierarchy(key))
        
        # 处理没有数字序列的条目
        no_number_entries = []
        for key in groups.keys():
            if isinstance(key, tuple) and key[0] == "no_numbers":
                no_number_entries.extend(groups[key])
        
        # 将无序号条目添加到结果末尾
        reordered_entries.extend(no_number_entries)
        
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

    def filter_table_and_prefix_entries(self, toc_entries: List[Dict]) -> List[Dict]:
        """
        过滤掉表格内容和有其他字符前缀的文本
        
        Args:
            toc_entries: 原始目录条目列表
            
        Returns:
            List[Dict]: 过滤后的目录条目列表
        """
        if not toc_entries:
            return toc_entries
        
        print(f"开始过滤表格内容和特殊前缀文本，原始条目数: {len(toc_entries)}")
        
        filtered_entries = []
        
        for i, entry in enumerate(toc_entries):
            title = entry["title"]
            should_filter = False
            filter_reason = ""
            
            # 1. 检查是否有非标准前缀字符
            # 允许的前缀模式：数字编号、中文编号、罗马数字
            valid_prefix_patterns = [
                r'^\d+\..*',  # 1. 2. 3.
                r'^\d+\.\d+.*',  # 1.1 1.2
                r'^\d+\.\d+\.\d+.*',  # 1.1.1 1.1.2
                r'^第[一二三四五六七八九十\d]+[章节部分].*',  # 第一章、第二节
                r'^[一二三四五六七八九十]+[、\.].*',  # 一、二、
                r'^[IVXLCDM]+[、\.].*',  # I. II.
                r'^\d+、.*',  # 1、2、
                r'^[^0-9一二三四五六七八九十IVXLCDM第].*'  # 无编号的标题（字母开头等）
            ]
            
            # 检查是否有其他字符前缀（如表格中的内容）
            if re.match(r'^[^\w\u4e00-\u9fff]', title):  # 以非字母数字汉字开头
                should_filter = True
                filter_reason = "包含非标准前缀字符"
            
            # 2. 检查是否为表格内容的特征
            # table_indicators = [
            #     # 检查是否包含表格特征词汇
            #     lambda t: any(keyword in t for keyword in ['思考角度', '有利或不利因素', '优势', '劣势', '优点', '缺点', '分析维度']),
            #     # 检查是否为表格中的条目（通常较长且包含描述性内容）
            #     lambda t: re.match(r'^\d+\.', t) and len(t) > 30 and ('使用' in t or '操作' in t or '功能' in t or '设计' in t),
            #     # 检查是否包含表格中常见的描述性文本
            #     lambda t: len(t) > 40 and any(phrase in t for phrase in ['从', '到', '进行', '实现', '提供', '支持']),
            #     # 检查是否为表格中的具体条目（包含工具名称、技术术语等）
            #     lambda t: re.match(r'^\d+\.', t) and any(tool in t for tool in ['cursor', 'Figma', 'MasterGo', 'MasterGO']),
            #     # 检查是否为表格中的功能描述
            #     lambda t: re.match(r'^\d+\.', t) and any(desc in t for desc in ['难以', '无法', '不能', '困难', '问题', '缺陷']),
            #     # 检查是否包含明显的表格内容特征（技术描述、对比内容等）
            #     lambda t: re.match(r'^\d+\.', t) and any(feature in t for feature in ['平台', '内容', '迁移', '对接', '提效', '开发人员']),
            # ]
            
            # if any(indicator(title) for indicator in table_indicators):
            #     should_filter = True
            #     filter_reason = "疑似表格内容"
            
            # 3. 检查上下文是否为表格环境
            # 通过检查相邻条目是否有相似的结构来判断
            if i > 0 and i < len(toc_entries) - 1:
                prev_title = toc_entries[i-1]["title"]
                next_title = toc_entries[i+1]["title"]
                
                # 如果前后条目都是编号开头且内容较长，可能是表格
                prev_is_numbered_long = re.match(r'^\d+\.', prev_title) and len(prev_title) > 20
                curr_is_numbered_long = re.match(r'^\d+\.', title) and len(title) > 20
                next_is_numbered_long = re.match(r'^\d+\.', next_title) and len(next_title) > 20
                
                if prev_is_numbered_long and curr_is_numbered_long and next_is_numbered_long:
                    # 进一步检查是否包含表格特征内容
                    table_content_patterns = [
                        r'(从|到|进行|实现|提供|支持|操作|功能|设计|使用|切换|对接)',
                        r'(平台|工具|系统|模式|方式|方法)',
                        r'(优势|劣势|优点|缺点|有利|不利)'
                    ]
                    
                    if any(re.search(pattern, title) for pattern in table_content_patterns):
                        should_filter = True
                        filter_reason = "疑似表格内容（基于上下文判断）"
            
            # 4. 检查是否为明显的非标题内容
            non_title_patterns = [
                # r'^.*[，。；：？！].*[，。；：？！].*',  # 包含多个标点符号的长句
                r'^.{50,}',  # 超长文本（可能是段落内容）
                r'^.*\d+年\d+月.*',  # 日期格式
                r'^.*\d+%.*',  # 百分比
            ]
            
            if any(re.search(pattern, title) for pattern in non_title_patterns):
                should_filter = True
                filter_reason = "疑似非标题内容"
            
            if should_filter:
                print(f"过滤掉: '{title[:50]}...' - {filter_reason}")
            else:
                filtered_entries.append(entry)
        
        print(f"表格和前缀过滤完成，过滤后条目数: {len(filtered_entries)}")
        return filtered_entries

    def llm_semantic_filter(self, toc_entries: List[Dict]) -> List[Dict]:
        """
        使用大模型进行语义过滤，优化书签结构（分批调用模式，每批100条）
        Args:
            toc_entries: 原始目录条目列表
        Returns:
            List[Dict]: 过滤后的目录条目列表
        """
        if len(toc_entries) == 0:
            return toc_entries
        print(f"开始使用大模型进行语义过滤（分批调用模式），原始条目数: {len(toc_entries)}")
        return self._batched_llm_filter(toc_entries)

    def _batched_llm_filter(self, toc_entries: List[Dict], batch_size: int = 100) -> List[Dict]:
        """
        分批调用大模型API，每批batch_size条，最后合并结果
        """
        all_filtered = []
        total = len(toc_entries)
        batch_count = (total + batch_size - 1) // batch_size
        print(f"将目录条目分为 {batch_count} 批，每批{batch_size}条")
        for i in range(batch_count):
            batch = toc_entries[i*batch_size:(i+1)*batch_size]
            print(f"\n🚀 调用大模型处理第{i+1}/{batch_count}批（条目{i*batch_size+1}-{min((i+1)*batch_size, total)}）...")
            filtered = self._single_request_llm_filter(batch)
            print(f"✅ 第{i+1}批处理完成，保留{len(filtered)}条")
            all_filtered.extend(filtered)
        # 合并后去重（标题+页码）
        def get_title_page_key(entry):
            return (entry["title"].strip(), entry.get("target_page", entry.get("source_page", 0)))
        seen = set()
        deduped = []
        for entry in all_filtered:
            key = get_title_page_key(entry)
            if key not in seen:
                seen.add(key)
                deduped.append(entry)
        print(f"\n📦 分批合并后去重，最终保留{len(deduped)}条")
        return deduped

    def _single_request_llm_filter(self, toc_entries: List[Dict]) -> List[Dict]:
        """单次请求的LLM过滤（用于小数据量）"""
        try:
            # 构建提示词
            prompt = self._build_semantic_filter_prompt()
            
            # 格式化候选数据
            candidates_text = self._format_toc_entries_for_llm(toc_entries)
            print(f"数据长度: {len(candidates_text)} 字符")
            
            # 调用大模型API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "claude-4-sonnet",
                "messages": [
                    {
                        "role": "user",
                        "content": f"{prompt}\n\n目录条目数据:\n{candidates_text}"
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 32768
            }
            
            response = requests.post(self.api_url, headers=headers, json=data, timeout=60)
            print(f"收到响应，状态码: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    
                    if "choices" in result and result["choices"]:
                        content = result["choices"][0]["message"]["content"]
                        print(f"响应内容长度: {len(content)}")
                        
                        filtered_entries = self._parse_llm_semantic_response(content, toc_entries)
                        print(f"语义过滤完成，过滤后条目数: {len(filtered_entries)}")
                        
                        # 保存调试信息
                        self._save_semantic_filter_debug(toc_entries, filtered_entries, content)
                        
                        return filtered_entries
                    else:
                        print(f"响应格式错误: {result}")
                        return self._simple_rule_filter(toc_entries)
                except Exception as json_error:
                    print(f"解析响应JSON失败: {json_error}")
                    return self._simple_rule_filter(toc_entries)
            else:
                print(f"API调用失败，状态码: {response.status_code}")
                return self._simple_rule_filter(toc_entries)
                
        except Exception as e:
            print(f"单次处理失败: {e}")
            return self._simple_rule_filter(toc_entries)
    
    def _simple_rule_filter(self, toc_entries: List[Dict]) -> List[Dict]:
        """简单的规则过滤，作为LLM过滤失败时的备用方案"""
        filtered = []
        for entry in toc_entries:
            title = entry.get('title', '').strip()
            # 简单的过滤规则：排除明显的非标题内容
            if (len(title) < 3 or 
                '页码' in title or 
                '页脚' in title or 
                '页眉' in title or
                title.isdigit() or
                len(title) > 200):
                continue
            filtered.append(entry)
        
        print(f"规则过滤完成: {len(toc_entries)} -> {len(filtered)}")
        return filtered
    
    def _build_semantic_filter_prompt(self) -> str:
        """构建语义过滤的提示词"""
        return """你是一个专业的PDF文档结构分析专家。请分析以下目录条目，进行语义过滤和结构优化。

分析目标：
1. **过滤无效条目**：去除明显不是标题的内容（如页眉、页脚、正文片段、表格数据等）
2. **保持结构完整**：确保层级关系合理，编号连续
3. **语义一致性**：标题应该简洁明了，有明确的主题性
4. **去除重复**：相同或相似的标题只保留一个
5. **补全缺失层级**：如果发现2.4.7但缺少2.4，自动补全

条目数据格式：
- title: 标题文本
- level: 层级深度(1-8)
- 页码: 目标页码
- 字体: 字体大小

层级判断规则（支持8层结构）：
- 第X章、第X部分 → 1级
- X、X.Y、第X节 → 2级  
- X.Y.Z → 3级
- X.Y.Z.W → 4级
- X.Y.Z.W.V → 5级
- X.Y.Z.W.V.U → 6级
- X.Y.Z.W.V.U.T → 7级
- X.Y.Z.W.V.U.T.S → 8级

请返回过滤和优化后的目录条目，保持JSON格式，**必须保留原始页码信息，支持最多8级标题**：
```json
[
  {
    "title": "标题文本",
    "level": 层级数字,
    "page_num": 页码数字
  }
]
```

只返回JSON数据，不要任何其他解释。"""
    
    def _format_toc_entries_for_llm(self, toc_entries: List[Dict]) -> str:
        """格式化目录条目数据供大模型分析"""
        formatted_lines = []
        for i, entry in enumerate(toc_entries):
            # 清理标题文本，移除可能导致问题的字符
            title = str(entry.get('title', '')).replace('"', '\\"').replace('\n', ' ').replace('\r', ' ').strip()
            # 限制标题长度
            if len(title) > 100:
                title = title[:100] + "..."
            
            line = f"[{i}] 标题: {title}"
            line += f" | 层级: {entry.get('level', 1)}"
            line += f" | 页码: {entry.get('target_page', entry.get('source_page', 0)) + 1}"  # 显示1基索引的页码
            line += f" | 字体: {entry.get('font_size', 12.0)}"
            formatted_lines.append(line)
        
        return "\n".join(formatted_lines)
    
    def _format_segment_for_llm(self, segment_entries: List[Dict], segment_num: int) -> str:
        """格式化单个段落的目录条目数据供大模型分析"""
        formatted_lines = [f"=== 段落 {segment_num} ==="]
        
        for i, entry in enumerate(segment_entries):
            # 清理标题文本，移除可能导致问题的字符
            title = str(entry.get('title', '')).replace('"', '\\"').replace('\n', ' ').replace('\r', ' ').strip()
            # 限制标题长度
            if len(title) > 100:
                title = title[:100] + "..."
            
            line = f"[{i}] 标题: {title}"
            line += f" | 层级: {entry.get('level', 1)}"
            line += f" | 页码: {entry.get('target_page', entry.get('source_page', 0)) + 1}"  # 显示1基索引的页码
            line += f" | 字体: {entry.get('font_size', 12.0)}"
            formatted_lines.append(line)
        
        return "\n".join(formatted_lines)
    
    def _parse_llm_semantic_response(self, content: str, original_entries: List[Dict]) -> List[Dict]:
        """解析大模型的语义过滤响应"""
        try:
            import json
            import re
            
            print("开始解析LLM响应...")
            
            # 尝试提取JSON数据
            json_match = re.search(r'```json\s*(\[.*?\])\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                print("从markdown代码块中提取到JSON")
            else:
                # 查找第一个[到最后一个]
                start_idx = content.find('[')
                end_idx = content.rfind(']')
                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    json_str = content[start_idx:end_idx+1]
                    print(f"从响应中提取JSON: 起始位置{start_idx}, 结束位置{end_idx}")
                else:
                    print("无法从响应中提取JSON数据")
                    print(f"查找'['的位置: {start_idx}, 查找']'的位置: {end_idx}")
                    return original_entries
            
            print(f"提取的JSON字符串长度: {len(json_str)}")
            print(f"JSON字符串前200字符: {json_str[:200]}...")
            
            # 解析JSON
            try:
                filtered_data = json.loads(json_str)
                print("JSON解析成功")
            except json.JSONDecodeError as json_error:
                print(f"JSON解析失败: {json_error}")
                print(f"尝试解析的JSON: {json_str[:500]}...")
                return original_entries
            
            if not isinstance(filtered_data, list):
                print("响应数据不是列表格式")
                return original_entries
            
            # 创建原始条目的标题到条目的映射
            original_dict = {entry["title"]: entry for entry in original_entries}
            
            # 转换为标准格式，保留原始页面信息
            filtered_entries = []
            kept_titles = set()  # 记录保留的标题
            
            for item in filtered_data:
                if isinstance(item, dict):
                    title = item.get("title", "")
                    kept_titles.add(title)
                    
                    # 从原始条目中查找匹配的条目来获取正确的页面信息
                    original_entry = original_dict.get(title)
                    if original_entry:
                        # 保留原始条目的所有信息，只更新level如果大模型提供了不同的值
                        entry = original_entry.copy()
                        if "level" in item:
                            entry["level"] = item["level"]
                        # 如果大模型提供了页码信息，优先使用它
                        if "page_num" in item:
                            page_num = item["page_num"] - 1  # 转换为0基索引
                            entry["target_page"] = page_num
                            # 如果页码发生了变化，也更新source_page
                            if page_num != original_entry.get("target_page", original_entry.get("source_page", 0)):
                                entry["source_page"] = page_num
                    else:
                        # 如果找不到匹配的原始条目，使用大模型提供的信息
                        page_num = item.get("page_num", 1) - 1  # 转换为0基索引
                        entry = {
                            "title": title,
                            "level": item.get("level", 1),
                            "source_page": page_num,
                            "target_page": page_num,
                            "font_size": item.get("font_size", 12.0),
                            "font_flags": 0,
                            "has_number": False,
                            "is_numbered_sequence": False
                        }
                    
                    filtered_entries.append(entry)
            
            # 统计被过滤掉的条目（用标题+页码联合精确匹配）
            def get_title_page_key(entry):
                return (entry["title"].strip(), entry.get("target_page", entry.get("source_page", 0)))
            
            llm_title_page_set = set(get_title_page_key(e) for e in filtered_entries)
            filtered_out_entries = []
            for original_entry in original_entries:
                if get_title_page_key(original_entry) not in llm_title_page_set:
                    filtered_out_entries.append(original_entry)
            
            # 打印过滤统计
            print(f"\n📊 LLM语义过滤统计:")
            print(f"✅ 保留条目: {len(filtered_entries)}")
            print(f"❌ 过滤原始条目: {len(filtered_out_entries)}")
            
            if filtered_out_entries:
                print(f"\n🗑️ 被大模型过滤掉的原始条目:")
                for i, entry in enumerate(filtered_out_entries, 1):
                    page_info = entry.get('target_page', entry.get('source_page', 0)) + 1
                    font_info = entry.get('font_size', 0)
                    print(f"  {i:2d}. [{page_info:3d}页] '{entry['title'][:60]}{'...' if len(entry['title']) > 60 else ''}' (字体:{font_info:.1f})")
                print()
            
            return filtered_entries
            
        except Exception as e:
            print(f"解析大模型响应失败: {e}")
            return original_entries
    
    def _save_semantic_filter_debug(self, original_entries: List[Dict], filtered_entries: List[Dict], llm_response: str):
        """保存语义过滤的调试信息"""
        try:
            import json
            
            # 计算被过滤掉的条目
            filtered_titles = {entry["title"] for entry in filtered_entries}
            filtered_out_entries = [entry for entry in original_entries if entry["title"] not in filtered_titles]
            
            debug_data = {
                "original_count": len(original_entries),
                "filtered_count": len(filtered_entries),
                "filtered_out_count": len(filtered_out_entries),
                "original_entries": original_entries,
                "filtered_entries": filtered_entries,
                "filtered_out_entries": filtered_out_entries,
                "llm_response": llm_response
            }
            
            with open("semantic_filter_debug.json", "w", encoding="utf-8") as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=2)
            print("已保存语义过滤调试信息到 semantic_filter_debug.json")
        except Exception as e:
            print(f"保存调试信息失败: {e}")

    def add_bookmarks(self, toc_entries: List[Dict]) -> Tuple[bool, Dict]:
        """
        添加书签到PDF
        
        Args:
            toc_entries: 目录条目列表
            
        Returns:
            Tuple[bool, Dict]: (是否成功, 统计信息)
        """
        try:
            # 清除现有书签
            self.doc.set_toc([])
            
            if not toc_entries:
                print("警告：没有目录条目可添加")
                return False, {}
            
            # 收集统计信息
            original_count = len(toc_entries)
            print(f"开始处理 {original_count} 个原始目录条目")
            
            # 预过滤：去除表格内容和特殊前缀文本
            print("步骤1: 过滤表格内容和特殊前缀文本...")
            pre_filtered_entries = self.filter_table_and_prefix_entries(toc_entries)
            after_pre_filter = len(pre_filtered_entries)
            print(f"预过滤完成，剩余 {after_pre_filter} 个条目")
            
            # 使用大模型进行语义过滤和结构优化
            print("步骤2: 大模型语义过滤...")
            semantic_filtered_entries = self.llm_semantic_filter(pre_filtered_entries)
            after_semantic_filter = len(semantic_filtered_entries)
            print(f"语义过滤完成，剩余 {after_semantic_filter} 个条目")
            
            # 规范化层级结构
            print("步骤3: 规范化层级结构...")
            normalized_entries = self.normalize_toc_levels(semantic_filtered_entries)
            after_normalize = len(normalized_entries)
            
            # 重新排序以确保父子关系正确
            print("步骤4: 重新排序以确保父子关系正确...")
            reordered_entries = self.reorder_for_hierarchy(normalized_entries)
            after_reorder = len(reordered_entries)
            print(f"重新排序完成，条目数: {after_reorder}")
            
            # 进一步调整层级以符合PyMuPDF的严格要求
            print("步骤5: PyMuPDF兼容性调整...")
            final_entries = self.adjust_for_pymupdf(reordered_entries)
            final_count = len(final_entries)
            print(f"PyMuPDF兼容性调整完成，最终条目数: {final_count}")
            
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
                
                # 添加详细的调试信息
                print(f"书签 {i+1}: '{entry['title']}' -> 源页面: {entry['source_page']+1}, 目标页面: {target_page+1}")
            
            print(f"准备添加 {len(toc)} 个书签条目")
            
            # 验证TOC结构
            if not self.validate_toc_structure(toc):
                print("错误：TOC结构验证失败")
                return False, {}
            
            # 设置新的目录
            self.doc.set_toc(toc)
            
            # 构建统计信息
            stats = {
                'original': original_count,
                'after_pre_filter': after_pre_filter,
                'after_semantic_filter': after_semantic_filter,
                'after_normalize': after_normalize,
                'after_reorder': after_reorder,
                'final': final_count
            }
            
            return True, stats
            
        except Exception as e:
            print(f"错误：添加书签失败: {e}")
            print(f"错误详情：在处理第 {len(toc) if 'toc' in locals() else 0} 个条目时出错")
            return False, {}
    
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
            print(f"启用字体大小过滤: {self.enable_font_size_filter}")
            
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
                print(f"{i+1:2d}. {indent}{entry['title']} (页面 {entry['target_page'] + 1}, 字体大小 {entry['font_size']:.2f})")
            
            if len(toc_entries) > 10:
                print(f"... 还有 {len(toc_entries) - 10} 个条目")
                
            # 显示字体大小分析结果
            if self.enable_font_size_filter and self.title_font_sizes:
                print("\n字体大小分析结果:")
                
                # 创建字体大小直方图
                font_sizes = {}
                for size in self.title_font_sizes:
                    key = round(size, 1)
                    if key not in font_sizes:
                        font_sizes[key] = 0
                    font_sizes[key] += 1
                
                # 显示字体大小分布
                print("字体大小分布:")
                for size in sorted(font_sizes.keys(), reverse=True):
                    count = font_sizes[size]
                    bar = "#" * min(count, 50)  # 限制条形图宽度
                    print(f"{size:5.1f}: {bar} ({count})")
                
                print(f"\n标题字体大小范围: {min(self.title_font_sizes):.2f} - {max(self.title_font_sizes):.2f}")
                print(f"字体大小阈值: {self.font_size_threshold:.2f}")
                print(f"字体大小低于阈值的条目已被过滤")
            
            # 添加书签
            success, bookmark_stats = self.add_bookmarks(toc_entries)
            if success:
                print("成功添加书签")
                if bookmark_stats:
                    print(f"最终添加了 {bookmark_stats.get('final', 0)} 个书签")
                
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
    parser.add_argument("--disable-font-filter", action="store_true", help="禁用字体大小过滤功能")
    parser.add_argument("--font-threshold", type=float, help="手动设置字体大小阈值（可选）")
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.input_pdf):
        print(f"错误：文件不存在: {args.input_pdf}")
        return 1
    
    # 创建工具实例并处理PDF
    tool = PDFBookmarkTool(args.input_pdf)
    
    # 设置字体过滤选项
    if args.disable_font_filter:
        tool.enable_font_size_filter = False
        print("字体大小过滤功能已禁用")
    
    # 设置手动字体大小阈值
    if args.font_threshold is not None:
        tool.font_size_threshold = args.font_threshold
        print(f"手动设置字体大小阈值为: {args.font_threshold}")
    
    if tool.process_pdf(args.output):
        print("✅ PDF书签添加完成！")
        return 0
    else:
        print("PDF书签添加失败！")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 