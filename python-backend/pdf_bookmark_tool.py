#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF自动书签工具
自动识别PDF中的目录并添加书签，只针对目录，不对段落添加书签
"""

# 确保在Windows上正确输出UTF-8编码的中文
import sys
import os

import fitz  # PyMuPDF
import re
import json
from typing import List, Tuple, Dict, Optional
import argparse
# 新增dotenv导入
from dotenv import load_dotenv

# 设置环境变量确保UTF-8输出
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 在Windows上设置标准输出编码
if sys.platform == 'win32':
    try:
        import codecs
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        # 如果编码设置失败，继续执行
        pass


def safe_json_parse(json_str, param_name):
    """安全解析JSON字符串，提供详细的错误信息"""
    if not json_str:
        print(f"调试：{param_name} 参数为空")
        return []
    
    print(f"调试：{param_name} 原始值: {repr(json_str)}")
    print(f"调试：{param_name} 长度: {len(json_str)}")
    
    # 检查常见问题
    if json_str.strip() == "[":
        print(f"调试：{param_name} 只有开始括号，可能被截断")
        return []
    
    if json_str.strip() == "[]":
        print(f"调试：{param_name} 是空数组")
        return []
    
    try:
        result = json.loads(json_str)
        if not isinstance(result, list):
            print(f"警告：{param_name} 不是数组格式，转换为数组")
            return [str(result)]
        print(f"调试：{param_name} 解析成功: {result}")
        return result
    except json.JSONDecodeError as e:
        print(f"警告：{param_name} JSON格式错误: {e}")
        print(f"调试：错误位置: 第{e.lineno}行，第{e.colno}列")
        
        # 检查是否是缺少引号的数组格式 [item1, item2, ...]
        if json_str.startswith('[') and json_str.endswith(']'):
            try:
                # 移除方括号并按逗号分割
                content = json_str[1:-1].strip()
                if content:
                    # 分割项目并清理
                    items = [item.strip() for item in content.split(',')]
                    # 为每个项目添加引号（如果需要）
                    fixed_items = []
                    for item in items:
                        item = item.strip()
                        if item and not (item.startswith('"') and item.endswith('"')):
                            # 添加引号
                            fixed_items.append(f'"{item}"')
                        else:
                            fixed_items.append(item)
                    
                    fixed_json = '[' + ', '.join(fixed_items) + ']'
                    print(f"调试：尝试修复缺少引号的数组: {repr(fixed_json)}")
                    result = json.loads(fixed_json)
                    print(f"调试：修复成功: {result}")
                    return result
                else:
                    print(f"调试：空数组内容")
                    return []
            except Exception as fix_error:
                print(f"调试：修复数组格式失败: {fix_error}")
                
        print(f"调试：无法解析 {param_name}，使用空列表")
        return []


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
            r'^\d+\.\d+\.\d+\.\d+\.\d+\.\d+\.\d+\s+.*',  # 1.1.1.1.1.1.1 标题 (8层)
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
        
        # 新增配置选项
        self.enable_debug = False  # 是否启用调试模式
        self.enable_x_coordinate_filter = True  # 是否启用X坐标过滤
        self.title_x_coordinate = None  # 文档标题的X坐标参考值
        self.x_coordinate_tolerance = 5.0  # X坐标容差（像素）
        
        # 手动控制选项
        self.exclude_titles = []  # 手动排除的标题列表
        self.include_titles = []  # 手动包含的标题列表
        
        # 标题格式过滤选项
        self.require_numeric_start = False  # 是否要求标题必须以数字开头
        
        # 大模型API配置
        load_dotenv()
        self.api_key = os.environ.get("API_KEY", "")
        self.api_url = "https://lab.iwhalecloud.com/gpt-proxy/v1/chat/completions"
        
        # 文档标题相关
        self.document_title_text = None  # 文档标题文本，避免被添加为书签
    
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
                    line_fonts = []  # 收集行内字体信息
                    line_bbox = line.get("bbox", [0, 0, 0, 0])  # 行的边界框
                    
                    for span in line["spans"]:
                        span_text = span["text"]
                        line_text += span_text
                        
                        # 收集详细的字体信息
                        font_info = {
                            "text": span_text,
                            "font": span.get("font", ""),
                            "size": span.get("size", 0),
                            "flags": span.get("flags", 0),  # 字体标志（粗体、斜体等）
                            "color": span.get("color", 0),  # 文字颜色
                            "bbox": span.get("bbox", [0, 0, 0, 0]),  # 文字边界框
                            "origin": span.get("origin", [0, 0]),  # 文字起始位置
                        }
                        line_fonts.append(font_info)
                    
                    if line_text.strip():
                        line_info = {
                            "text": line_text.strip(),
                            "fonts": line_fonts,
                            "bbox": line_bbox,
                            "page": page_num + 1
                        }
                        block_lines.append(line_info)
                
                # 将块内的所有行合并成一个文本块
                if block_lines:
                    combined_text = " ".join([line["text"] for line in block_lines])
                    
                    # 计算主要字体信息（取最频繁出现的）
                    all_fonts = []
                    all_sizes = []
                    all_flags = []
                    all_colors = []
                    
                    for line in block_lines:
                        for font_info in line["fonts"]:
                            if font_info["text"].strip():  # 只考虑非空文本
                                all_fonts.append(font_info["font"])
                                all_sizes.append(font_info["size"])
                                all_flags.append(font_info["flags"])
                                all_colors.append(font_info["color"])
                    
                    if all_sizes:
                        # 获取主要字体属性
                        main_font = max(set(all_fonts), key=all_fonts.count) if all_fonts else ""
                        main_size = max(set(all_sizes), key=all_sizes.count) if all_sizes else 0
                        main_flags = max(set(all_flags), key=all_flags.count) if all_flags else 0
                        main_color = max(set(all_colors), key=all_colors.count) if all_colors else 0
                        
                        # 计算位置信息
                        block_bbox = block.get("bbox", [0, 0, 0, 0])
                        
                        text_block = {
                            "text": combined_text,
                            "font": main_font,
                            "size": main_size,
                            "flags": main_flags,
                            "color": main_color,
                            "bbox": block_bbox,
                            "page": page_num + 1,
                            "lines": block_lines,  # 保留详细的行信息
                            # 添加更多分析信息
                            "position": {
                                "x": block_bbox[0],
                                "y": block_bbox[1],
                                "width": block_bbox[2] - block_bbox[0],
                                "height": block_bbox[3] - block_bbox[1],
                                "center_x": (block_bbox[0] + block_bbox[2]) / 2,
                                "center_y": (block_bbox[1] + block_bbox[3]) / 2,
                            },
                            "font_analysis": {
                                "all_fonts": list(set(all_fonts)),
                                "all_sizes": list(set(all_sizes)),
                                "all_flags": list(set(all_flags)),
                                "all_colors": list(set(all_colors)),
                                "size_range": [min(all_sizes), max(all_sizes)] if all_sizes else [0, 0],
                                "is_bold": bool(main_flags & 2**4),  # 检查粗体标志
                                "is_italic": bool(main_flags & 2**1),  # 检查斜体标志
                                "is_superscript": bool(main_flags & 2**0),  # 检查上标
                                "is_subscript": bool(main_flags & 2**1),  # 检查下标
                            }
                        }
                        text_blocks.append(text_block)
        
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
        # 暂时禁用过于严格的独立性检查
        # if context and not self.is_text_independent(text, context):
        #     return False, 0
        
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
        
        # 检查是否在列表中且前后有紧密相关的内容
        if self.is_likely_in_list(text, prev_text, next_text):
            print(f"跳过列表中的文本: '{text}'")
            return False
        
        # 检查是否是段落的一部分
        if self.is_likely_in_paragraph(text, prev_text, next_text):
            print(f"跳过段落中的文本: '{text}'")
            return False
        
        return True
    
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
        """分析字体大小分布"""
        if not font_sizes:
            return {}
        
        from collections import Counter
        
        # 统计字体大小分布
        size_counter = Counter([round(size, 1) for size in font_sizes])
        
        # 找到主要字体大小
        most_common = size_counter.most_common()
        
        stats = {
            'min_size': min(font_sizes),
            'max_size': max(font_sizes), 
            'avg_size': sum(font_sizes) / len(font_sizes),
            'size_distribution': dict(most_common),
            'primary_sizes': [size for size, count in most_common if count >= 2]
        }
        
        return stats

    def analyze_title_font_patterns(self, toc_entries: List[Dict]) -> Dict[int, Dict]:
        """
        分析每个层级标题的字体大小模式
        
        Args:
            toc_entries: 候选标题列表
            
        Returns:
            Dict[int, Dict]: 每个层级的字体大小统计信息
        """
        if not toc_entries:
            return {}
        
        # 按层级分组收集字体大小
        level_fonts = {}
        for entry in toc_entries:
            level = entry.get('level', 1)
            font_size = entry.get('font_size', 12.0)
            
            if level not in level_fonts:
                level_fonts[level] = []
            level_fonts[level].append(font_size)
        
        # 分析每个层级的字体大小模式
        level_patterns = {}
        for level, sizes in level_fonts.items():
            if not sizes:
                continue
                
            from collections import Counter
            
            # 统计字体大小分布
            size_counter = Counter([round(size, 1) for size in sizes])
            most_common_sizes = size_counter.most_common()
            
            # 计算统计信息
            avg_size = sum(sizes) / len(sizes)
            min_size = min(sizes)
            max_size = max(sizes)
            
            # 找到主要字体大小（出现次数最多的）
            primary_size = most_common_sizes[0][0] if most_common_sizes else avg_size
            
            # 计算字体大小的标准差
            variance = sum((s - avg_size) ** 2 for s in sizes) / len(sizes)
            std_dev = variance ** 0.5
            
            level_patterns[level] = {
                'count': len(sizes),
                'sizes': sizes,
                'avg_size': avg_size,
                'min_size': min_size,
                'max_size': max_size,
                'primary_size': primary_size,
                'std_dev': std_dev,
                'size_distribution': dict(most_common_sizes),
                'tolerance': 0.5  # 严格的0.5pt容差
            }
            
            print(f"层级 {level}: 主要字体 {primary_size:.1f}pt, 平均 {avg_size:.1f}pt, "
                  f"标准差 {std_dev:.1f}pt, 样本数 {len(sizes)}")
        
        return level_patterns

    def validate_font_size_consistency(self, toc_entries: List[Dict], is_manual_include=False) -> List[Dict]:
        """
        验证标题字体大小的一致性，过滤掉字体大小不符合层级规律的标题
        增加层级间递减验证：1级 > 2级 > 3级...
        
        Args:
            toc_entries: 原始标题列表
            is_manual_include: 是否为手动包含的标题（手动包含的标题使用更宽松的验证）
        
        Returns:
            List[Dict]: 过滤后的标题列表
        """
        if not toc_entries:
            return []
        
        verification_mode = "宽松" if is_manual_include else "严格"
        print(f"开始字体大小一致性验证（{verification_mode}模式），原始条目数: {len(toc_entries)}")
        
        # 分析每个层级的字体大小模式
        level_patterns = self.analyze_title_font_patterns(toc_entries)
        
        if not level_patterns:
            print("无法分析字体大小模式，跳过一致性验证")
            return toc_entries
        
        # 验证层级间字体大小递减规律
        sorted_levels = sorted(level_patterns.keys())
        level_order_valid = True
        
        if len(sorted_levels) > 1:
            print("验证层级间字体大小递减规律...")
            for i in range(len(sorted_levels) - 1):
                current_level = sorted_levels[i]
                next_level = sorted_levels[i + 1]
                
                current_font = level_patterns[current_level]['primary_size']
                next_font = level_patterns[next_level]['primary_size']
                
                # 检查递减规律：高层级字体应该 >= 低层级字体
                if current_font < next_font - 0.5:  # 允许0.5pt的误差
                    print(f"  ⚠️ 层级字体大小递减异常: L{current_level}({current_font:.1f}pt) < L{next_level}({next_font:.1f}pt)")
                    level_order_valid = False
                else:
                    print(f"  ✅ 层级字体大小正常: L{current_level}({current_font:.1f}pt) >= L{next_level}({next_font:.1f}pt)")
        
        # 验证每个标题的字体大小是否符合其层级的模式
        valid_entries = []
        filtered_count = 0
        
        for entry in toc_entries:
            level = entry.get('level', 1)
            font_size = entry.get('font_size', 12.0)
            title = entry.get('title', '')
            
            should_keep = True
            filter_reason = ""
            
            # 检查1：该层级的字体大小是否符合模式
            if level in level_patterns:
                pattern = level_patterns[level]
                primary_size = pattern['primary_size']
                tolerance = pattern['tolerance']  # 0.5pt严格容差
                
                # 手动包含的标题使用更宽松的容差
                if is_manual_include:
                    tolerance = max(tolerance, 1.0)  # 手动包含至少1pt容差
                
                size_diff = abs(font_size - primary_size)
                
                if size_diff > tolerance:
                    should_keep = False
                    filter_reason = f"字体大小偏离层级标准 (实际:{font_size:.1f}pt, 标准:{primary_size:.1f}pt, 差异:{size_diff:.1f}pt > 容差:{tolerance:.1f}pt)"
            
            # 检查2：层级间递减逻辑（仅在非手动模式下进行严格检查）
            if should_keep and not is_manual_include and level > 1:
                for higher_level in range(1, level):
                    if higher_level in level_patterns:
                        higher_font = level_patterns[higher_level]['primary_size']
                        current_font = font_size
                        
                        # 当前层级字体不应该明显大于上级层级字体
                        if current_font > higher_font + 1.0:  # 允许1pt的容差
                            should_keep = False
                            filter_reason = f"字体大小违反递减逻辑 (L{level}:{current_font:.1f}pt > L{higher_level}:{higher_font:.1f}pt)"
                            break
            
            # 检查3：如果层级顺序异常，进行额外验证
            if should_keep and not level_order_valid and not is_manual_include:
                # 基于字体大小预测应该属于哪个层级
                predicted_level = self._predict_level_by_font_size(font_size, level_patterns)
                if abs(predicted_level - level) > 1:
                    should_keep = False
                    filter_reason = f"字体大小与层级不匹配 (字体{font_size:.1f}pt更像L{predicted_level}而非L{level})"
            
            if should_keep:
                valid_entries.append(entry)
                if level in level_patterns:
                    pattern = level_patterns[level]
                    size_diff = abs(font_size - pattern['primary_size'])
                    if size_diff > 0.3:  # 如果差异较大但在容差内，输出警告
                        print(f"  ⚠️  保留边缘标题: '{title[:40]}...' (层级 {level}, 字体 {font_size:.1f}pt, "
                              f"标准 {pattern['primary_size']:.1f}pt, 差异 {size_diff:.1f}pt)")
            else:
                filtered_count += 1
                print(f"  ❌ 过滤字体不符标题: '{title[:40]}...' - {filter_reason}")
        
        print(f"字体大小一致性验证完成: 保留 {len(valid_entries)} 个，过滤 {filtered_count} 个")
        return valid_entries
    
    def _predict_level_by_font_size(self, font_size: float, level_patterns: Dict[int, Dict]) -> int:
        """
        根据字体大小预测应该属于哪个层级
        
        Args:
            font_size: 字体大小
            level_patterns: 各层级字体信息
            
        Returns:
            int: 预测的层级
        """
        if not level_patterns:
            return 1
        
        # 找到字体大小最接近的层级
        min_diff = float('inf')
        predicted_level = 1
        
        for level, pattern in level_patterns.items():
            primary_size = pattern['primary_size']
            diff = abs(font_size - primary_size)
            
            if diff < min_diff:
                min_diff = diff
                predicted_level = level
        
        return predicted_level
    
    def find_toc_entries(self) -> List[Dict]:
        """
        查找PDF中的目录条目（仅自动识别，不包括手动包含的标题）
        
        Returns:
            List[Dict]: 目录条目列表，每个条目包含标题、页面、字体等信息
        """
        toc_entries = []
        
        # 设置文档标题的X坐标作为参考
        if self.enable_x_coordinate_filter:
            first_page_blocks = self.extract_text_with_font_info(0)
            self.title_x_coordinate = self.detect_document_title_x_coordinate(first_page_blocks)
            print(f"检测到文档标题X坐标参考值: {self.title_x_coordinate}")
        
        # 进行正常的标题提取逻辑
        print("开始自动识别标题...")
        
        # 遍历所有页面查找目录条目
        for page_num in range(len(self.doc)):
            text_blocks = self.extract_text_with_font_info(page_num)
            
            for block in text_blocks:
                text = block.get('text', '').strip()
                
                if not text:
                    continue
                    
                # 检查是否为目录文本
                is_toc, level = self.is_likely_toc_text(text, block)
                
                if is_toc:
                    # 排除文档标题
                    if self.document_title_text and text.strip() == self.document_title_text:
                        print(f"跳过文档标题: '{text[:30]}...'")
                        continue
                    
                    # 获取坐标信息
                    text_x = block.get('position', {}).get('x', 0)
                    text_y = block.get('position', {}).get('y', 0)
                    if text_x == 0 or text_y == 0:
                        bbox = block.get('bbox', [0, 0, 0, 0])
                        if len(bbox) >= 4:
                            text_x = bbox[0] if text_x == 0 else text_x
                            text_y = bbox[1] if text_y == 0 else text_y
                    
                    # X坐标对齐检查
                    if self.enable_x_coordinate_filter and self.title_x_coordinate is not None:
                        x_diff = abs(text_x - self.title_x_coordinate)
                        
                        if x_diff > self.x_coordinate_tolerance:
                            # X坐标不对齐，跳过这个潜在标题
                            print(f"跳过标题 '{text[:20]}...' - X坐标不对齐: {text_x:.1f} vs {self.title_x_coordinate:.1f}, 差异={x_diff:.1f}")
                            continue
                        else:
                            print(f"自动识别标题 '{text[:20]}...' - X坐标对齐: {text_x:.1f}, 差异={x_diff:.1f}")
                    
                    entry = {
                        'title': text,
                        'page': page_num + 1,  # 转换为1基索引
                        'source_page': page_num + 1,
                        'target_page': page_num + 1,
                        'font_size': block.get('size', 12),
                        'font_name': block.get('font', ''),
                        'x_coordinate': text_x,
                        'y_coordinate': text_y,
                        'bbox': block.get('bbox', [0, 0, 0, 0]),
                        'level': level,
                        'matched_pattern': '自动识别'
                    }
                    
                    toc_entries.append(entry)
        
        print(f"自动识别完成，找到 {len(toc_entries)} 个标题")
        
        # 收集标题字体大小用于后续分析
        self.title_font_sizes = [entry['font_size'] for entry in toc_entries if entry['font_size'] > 0]
        
        return toc_entries
    
    def add_include_titles(self) -> List[Dict]:
        """
        主动搜索并添加用户指定的包含标题
            
        Returns:
            List[Dict]: 包含新添加标题的目录条目列表
        """
        toc_entries = []
        print(f"主动搜索包含标题: {self.include_titles}")
        
        # 获取所有文本块
        all_text_blocks = []
        for page_num in range(len(self.doc)):
            page_text_blocks = self.extract_text_with_font_info(page_num)
            all_text_blocks.extend(page_text_blocks)
        
        added_count = 0
        
        # 为每个包含标题搜索匹配的文本块
        for include_title in self.include_titles:
            include_title = include_title.strip()
            print(f"搜索包含标题: '{include_title}'")
            
            # 查找匹配的文本块
            for block in all_text_blocks:
                text = block.get('text', '').strip()
                
                # 1. 使用宽松匹配逻辑：只要包含指定文字即可
                if include_title in text:
                    print(f"  找到匹配文本: '{text}'")
                    
                    # 2. 验证匹配到的文本是否适合作为标题
                    is_title_candidate = self.is_valid_title_candidate(text, block)
                    
                    if is_title_candidate:
                        # 3. 通过验证，创建目录条目
                        # 获取正确的坐标信息
                        text_x = block.get('position', {}).get('x', 0)
                        text_y = block.get('position', {}).get('y', 0)
                        if text_x == 0 or text_y == 0:
                            bbox = block.get('bbox', [0, 0, 0, 0])
                            if len(bbox) >= 4:
                                text_x = bbox[0] if text_x == 0 else text_x
                                text_y = bbox[1] if text_y == 0 else text_y
                        
                        entry = {
                            'title': text,
                            'page': block.get('page', 1) + 1,  # 转换为1基索引
                            'source_page': block.get('page', 1) + 1,
                            'target_page': block.get('page', 1) + 1,
                            'font_size': block.get('size', 12),
                            'font_name': block.get('font', ''),
                            'x_coordinate': text_x,
                            'y_coordinate': text_y,
                            'bbox': block.get('bbox', [0, 0, 0, 0]),
                            'level': self.determine_level_from_text(text),
                            'matched_pattern': f'手动包含: {include_title}'
                        }
                        
                        toc_entries.append(entry)
                        added_count += 1
                        print(f"  ✅ 添加包含标题: '{text}' (页面: {entry['page']}, 字体: {entry['font_size']:.1f})")
                        break  # 每个包含标题只添加第一个匹配的
                    else:
                        print(f"  ❌ 文本不适合作为标题，跳过: '{text}'")
        
        if added_count > 0:
            print(f"主动搜索完成，添加了 {added_count} 个标题")
        else:
            print("未找到合适的包含标题")
        
        return toc_entries
    
    def is_valid_title_candidate(self, text: str, block: Dict) -> bool:
        """
        验证文本是否适合作为标题
        专注于结构化判断：位置、大小、格式特征、逻辑一致性
        
        Args:
            text: 文本内容
            block: 文本块信息
            
        Returns:
            bool: 是否适合作为标题
        """
        text = text.strip()
        
        # 1. 基本长度检查（标题不会太短或太长）
        if len(text) < 2 or len(text) > 100:
            return False
        
        # 排除文档标题（避免将文档标题添加为书签）
        if self.document_title_text and text.strip() == self.document_title_text:
            print(f"  ❌ 跳过文档标题: '{text[:30]}...'")
            return False
        
        # 2. X坐标对齐检查（最重要的结构化条件）
        if self.enable_x_coordinate_filter and self.title_x_coordinate is not None:
            # 从正确的位置获取x坐标
            text_x = block.get('position', {}).get('x', 0)
            if text_x == 0:
                # 如果position中没有x，尝试从bbox中获取
                bbox = block.get('bbox', [0, 0, 0, 0])
                text_x = bbox[0] if len(bbox) >= 1 else 0
            
            x_diff = abs(text_x - self.title_x_coordinate)
            
            if x_diff > self.x_coordinate_tolerance:
                print(f"  ❌ X坐标不对齐: 文本X={text_x:.1f}, 标题X={self.title_x_coordinate:.1f}, 差异={x_diff:.1f}")
                return False
            else:
                print(f"  ✅ X坐标对齐: 文本X={text_x:.1f}, 标题X={self.title_x_coordinate:.1f}, 差异={x_diff:.1f}")
        
        # 3. 字体大小检查（标题通常字体较大）
        font_size = block.get('size', 0)
        if font_size > 0:
            # 字体太小很可能不是标题
            if font_size < 9:
                print(f"  ❌ 字体过小: {font_size}pt")
                return False
            else:
                print(f"  ✅ 字体大小合适: {font_size}pt")
        
        # 4. 检查是否有编号格式特征
        has_numbering = self.has_title_numbering(text)
        if has_numbering:
            # 有编号格式，但需要进一步检查是否为描述性列举项
            # 检查是否为正文列举项（如"2. 降低沟通成本：提供清晰..."）
            number_match = re.match(r'^(\d+)[.、]\s*', text)
            if number_match:
                number_text = number_match.group(0)
                remaining_text = text[len(number_text):].strip()
                
                # 排除描述性列举项的条件：
                # 1. 剩余文本过长（>15字符）
                # 2. 包含冒号和具体描述
                # 3. 以动词开头的具体描述
                if (len(remaining_text) > 15 and 
                    ('：' in remaining_text or ('，' in remaining_text and len(remaining_text) > 25)) and
                    any(keyword in remaining_text[:8] for keyword in ['提供', '确保', '降低', '提高', '减少', '增加', '实现', '支持', '帮助', '促进'])):
                    
                    print(f"  ❌ 排除描述性列举项: '{text[:40]}...'")
                    return False
            
            print(f"  ✅ 有编号格式且非描述性列举")
            return True  # 有明确编号且非描述性列举的直接通过
        
        # 5. 对于无编号的文本，进行更宽松的检查
        # 避免明显的非标题模式
        if self.is_obviously_not_title(text):
            return False
        
        # 6. 简单的结构化检查：是否像标题
        if self.looks_like_title(text, block):
            print(f"  ✅ 符合标题特征")
            return True
        
        print(f"  ❌ 不符合标题特征")
        return False
    
    def has_title_numbering(self, text: str) -> bool:
        """
        检查文本是否有标题编号格式
        
        Args:
            text: 文本内容
            
        Returns:
            bool: 是否有编号格式
        """
        # 各种编号格式
        numbering_patterns = [
            r'^\d+[.、]\s*',  # 1. 或 1、
            r'^\d+\.\d+[.、]?\s*',  # 1.1 或 1.1.
            r'^\d+\.\d+\.\d+[.、]?\s*',  # 1.1.1
            r'^\d+\.\d+\.\d+\.\d+[.、]?\s*',  # 1.1.1.1
            r'^第[一二三四五六七八九十\d]+[章节部分段]\s*',  # 第X章
            r'^[一二三四五六七八九十]+[、.]\s*',  # 一、
            r'^[IVXLCDM]+[、.]\s*',  # I、
            r'^[A-Z][.]\s*',  # A.
            r'^\([一二三四五六七八九十\d]+\)\s*',  # (1)
            r'^（[一二三四五六七八九十\d]+）\s*',  # （1）
            r'^【[^】]*】\s*',  # 【标题】
            r'^\d+、\s*',  # 1、
        ]
        
        return any(re.match(pattern, text) for pattern in numbering_patterns)
    
    def is_obviously_not_title(self, text: str) -> bool:
        """
        检查是否明显不是标题（基于结构特征，不是具体内容）
        
        Args:
            text: 文本内容
            
        Returns:
            bool: 是否明显不是标题
        """
        # 纯数字（页码）
        if re.match(r'^\d+$', text):
            return True
        
        # 标点符号太多（可能是段落）
        punctuation_count = len(re.findall(r'[,，。！!？?；;：:()（）]', text))
        if punctuation_count > 4:  # 标点超过3个很可能是段落
            return True
        
        # 全是标点符号或分隔符
        if re.match(r'^[.。…\-_=\s]+$', text):
            return True
        
        # URL格式
        if 'http' in text.lower() or '@' in text:
            return True
        
        return False
    
    def looks_like_title(self, text: str, block: Dict) -> bool:
        """
        检查文本是否看起来像标题（基于结构特征）
        
        Args:
            text: 文本内容
            block: 文本块信息
            
        Returns:
            bool: 是否看起来像标题
        """
        # 1. 长度适中的文本更可能是标题
        if 3 <= len(text) <= 50:
            title_score = 1
        elif 51 <= len(text) <= 80:
            title_score = 0.5
        else:
            title_score = 0
        
        # 2. 字体相对较大加分
        font_size = block.get('size', 12)
        if font_size >= 14:
            title_score += 1
        elif font_size >= 12:
            title_score += 0.5
        
        # 3. 标点符号少加分
        punctuation_count = len(re.findall(r'[,，。.！!？?；;：:]', text))
        if punctuation_count == 0:
            title_score += 1
        elif punctuation_count <= 1:
            title_score += 0.5
        
        # 4. 包含常见标题词汇加分（不是排除，而是加分）
        title_words = ['方法', '分析', '结论', '总结', '概述', '介绍', '背景', '目标', '实现', '设计', '开发', '测试', '评估', '改进', '优化']
        if any(word in text for word in title_words):
            title_score += 0.5
        
        # 评分大于等于1.5认为可能是标题
        is_title = title_score >= 1.5
        
        print(f"  标题评分: {title_score:.1f} ({'通过' if is_title else '不通过'})")
        return is_title
    
    def apply_exclude_filter(self, toc_entries: List[Dict]) -> List[Dict]:
        """
        应用排除过滤（只处理exclude_titles）
        
        Args:
            toc_entries: 原始目录条目列表
            
        Returns:
            List[Dict]: 过滤后的目录条目列表
        """
        if not self.exclude_titles:
            return toc_entries
            
        print(f"应用排除过滤，原始条目数: {len(toc_entries)}")
        
        filtered_entries = []
        excluded_count = 0
        
        for entry in toc_entries:
            title = entry["title"].strip()
            should_exclude = False
            
            # 检查是否在排除列表中
            for exclude_title in self.exclude_titles:
                if exclude_title.strip() in title or title in exclude_title.strip():
                    should_exclude = True
                    excluded_count += 1
                    print(f"排除标题: '{title}' (匹配规则: '{exclude_title}')")
                    break
            
            if not should_exclude:
                filtered_entries.append(entry)
        
        print(f"排除过滤完成: 排除 {excluded_count} 个，最终保留 {len(filtered_entries)} 个条目")
        
        return filtered_entries
    
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
        重新设计：使用更宽松的验证逻辑，避免过度过滤
        
        Args:
            toc_entries: 目录条目列表
            
        Returns:
            List[Dict]: 逻辑验证后的目录条目列表
        """
        if not toc_entries:
            return toc_entries
            
        print(f"开始目录逻辑验证，原始条目数: {len(toc_entries)}")
        
        # 第一步：基本去重 - 移除完全相同的条目
        unique_entries = []
        seen_titles = set()
        
        for entry in toc_entries:
            title = entry.get('title', '').strip()
            page = entry.get('source_page', entry.get('page', 0))
            
            # 创建唯一标识：标题+页码
            unique_key = f"{title}|{page}"
            
            if unique_key not in seen_titles:
                seen_titles.add(unique_key)
                unique_entries.append(entry)
            else:
                print(f"  移除重复条目: '{title[:40]}...' (页面 {page})")
        
        print(f"第一步去重后剩余: {len(unique_entries)} 个条目")
        
        # 第二步：按页码和Y坐标排序，确保顺序正确
        try:
            sorted_entries = sorted(unique_entries, key=lambda x: (
                x.get('source_page', x.get('page', 0)),
                x.get('y_coordinate', 0)
            ))
            print("第二步排序完成")
        except Exception as e:
            print(f"排序失败，保持原顺序: {e}")
            sorted_entries = unique_entries
        
        # 第三步：简单的逻辑一致性检查
        validated_entries = []
        prev_level = 0
        level_stack = []  # 记录层级栈
        
        for i, entry in enumerate(sorted_entries):
            title = entry.get('title', '')
            level = entry.get('level', 1)
            font_size = entry.get('font_size', 12.0)
            page = entry.get('source_page', entry.get('page', 0))
            
            should_keep = True
            filter_reason = ""
            
            # 检查1：基本标题有效性
            if len(title.strip()) < 2:
                should_keep = False
                filter_reason = "标题过短"
            elif len(title.strip()) > 200:
                should_keep = False
                filter_reason = "标题过长"
            
            # 检查2：层级跳跃是否过大（宽松检查）
            if should_keep and level > prev_level + 2:
                # 允许跳跃1层，超过2层才认为不合理
                should_keep = False
                filter_reason = f"层级跳跃过大 (从L{prev_level}跳到L{level})"
            
            # 检查3：字体大小基本合理性（非常宽松）
            if should_keep and font_size > 0:
                if font_size < 6:  # 字体太小，可能是脚注
                    should_keep = False
                    filter_reason = f"字体过小 ({font_size}pt)"
                elif font_size > 72:  # 字体太大，可能是异常
                    should_keep = False
                    filter_reason = f"字体异常大 ({font_size}pt)"
            
            # 检查4：是否为明显的非标题内容（宽松检查）
            if should_keep:
                non_title_patterns = [
                    r'^第\s*\d+\s*页',  # 页码
                    r'^共\s*\d+\s*页',  # 总页数
                    r'^页码：\d+',  # 页码标记
                    r'^\s*\d+\s*$',  # 纯数字
                    r'^\.{3,}',  # 多个点
                    r'^-{3,}',  # 多个横线
                    r'^_{3,}',  # 多个下划线
                ]
                
                for pattern in non_title_patterns:
                    if re.search(pattern, title, re.IGNORECASE):
                        should_keep = False
                        filter_reason = f"明显非标题内容: {pattern}"
                        break
            
            if should_keep:
                validated_entries.append(entry)
                
                # 更新层级记录
                if level <= prev_level:
                    # 层级回退，更新栈
                    level_stack = [l for l in level_stack if l < level]
                
                level_stack.append(level)
                prev_level = level
                
            else:
                print(f"  过滤条目: '{title[:40]}...' - {filter_reason}")
        
        print(f"第三步逻辑验证后剩余: {len(validated_entries)} 个条目")
        
        # 第四步：确保至少保留一些标题（安全措施）
        if len(validated_entries) == 0 and len(toc_entries) > 0:
            print("⚠️ 警告：所有条目都被过滤，保留字体最大的几个条目")
            
            # 按字体大小排序，保留前几个
            font_sorted = sorted(toc_entries, key=lambda x: x.get('font_size', 0), reverse=True)
            validated_entries = font_sorted[:min(5, len(font_sorted))]
            
            for entry in validated_entries:
                print(f"  保留条目: '{entry['title'][:40]}...' (字体: {entry.get('font_size', 0)}pt)")
        
        # 第五步：最终排序
        try:
            final_entries = sorted(validated_entries, key=lambda x: (
                x.get('source_page', x.get('page', 0)),
                x.get('y_coordinate', 0)
            ))
        except Exception:
            final_entries = validated_entries
        
        print(f"目录逻辑验证完成: {len(toc_entries)} -> {len(final_entries)} 个条目")
        
        # 显示保留的条目
        if final_entries:
            print("保留的标题条目:")
            for i, entry in enumerate(final_entries[:10]):  # 只显示前10个
                title = entry['title'][:50]
                level = entry.get('level', 1)
                page = entry.get('source_page', entry.get('page', 0))
                font = entry.get('font_size', 0)
                print(f"  {i+1:2d}. L{level} '{title}' (页面{page}, 字体{font:.1f}pt)")
            
            if len(final_entries) > 10:
                print(f"  ... 还有 {len(final_entries) - 10} 个条目")
        
        return final_entries
    
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
            print(f"current_numbers: {current_numbers}")
            
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

    def validate_font_size_by_level(self, toc_entries: List[Dict]) -> List[Dict]:
        """
        根据层级验证字体大小一致性，剔除不符合层级字体大小规律的条目
        层级字体大小应该递减：1级 > 2级 > 3级...
        
        Args:
            toc_entries: 原始条目列表
            
        Returns:
            List[Dict]: 过滤后的条目列表
        """
        if not toc_entries:
            return []
        
        print("开始字体大小层级一致性验证...")
        
        # 首先重新确定每个条目的正确层级（基于数字序列）
        corrected_entries = []
        for entry in toc_entries:
            title = entry.get('title', '')
            # 从标题中提取数字序列来确定层级
            numbers = self.extract_number_sequence(title)
            if numbers:
                # 有数字序列，层级就是数字序列的长度
                correct_level = len(numbers)
            else:
                # 无数字序列，使用原有层级或默认为1
                correct_level = entry.get('level', 1)
            
            # 更新条目的层级
            entry_copy = entry.copy()
            entry_copy['level'] = correct_level
            corrected_entries.append(entry_copy)
        
        # 按层级分组统计字体大小
        level_font_stats = {}
        for entry in corrected_entries:
            level = entry.get('level', 1)
            font_size = entry.get('font_size', 12.0)
            title = entry.get('title', '')
            
            if level not in level_font_stats:
                level_font_stats[level] = []
            level_font_stats[level].append({
                'size': font_size,
                'title': title,
                'entry': entry
            })
        
        print(f"发现 {len(level_font_stats)} 个层级")
        
        # 计算每个层级的主要字体大小
        level_primary_fonts = {}
        for level, font_data in level_font_stats.items():
            if not font_data:
                continue
                
            sizes = [item['size'] for item in font_data]
            
            from collections import Counter
            size_counter = Counter([round(size, 1) for size in sizes])
            most_common_size = size_counter.most_common(1)[0][0]
            
            # 计算统计信息
            avg_size = sum(sizes) / len(sizes)
            min_size = min(sizes)
            max_size = max(sizes)
            variance = sum((s - avg_size) ** 2 for s in sizes) / len(sizes)
            std_dev = variance ** 0.5
            
            level_primary_fonts[level] = {
                'primary_size': most_common_size,
                'avg_size': avg_size,
                'min_size': min_size,
                'max_size': max_size,
                'std_dev': std_dev,
                'tolerance': 0.5,  # 严格的0.5pt容差
                'sample_count': len(sizes),
                'size_distribution': dict(size_counter)
            }
            
            print(f"层级 {level}: 主要字体 {most_common_size:.1f}pt, 平均 {avg_size:.1f}pt, 范围 {min_size:.1f}-{max_size:.1f}pt, 样本数 {len(sizes)}")
        
        # 验证层级间字体大小递减规律
        sorted_levels = sorted(level_primary_fonts.keys())
        level_order_valid = True
        
        print("验证层级间字体大小递减规律...")
        for i in range(len(sorted_levels) - 1):
            current_level = sorted_levels[i]
            next_level = sorted_levels[i + 1]
            
            current_font = level_primary_fonts[current_level]['primary_size']
            next_font = level_primary_fonts[next_level]['primary_size']
            
            if current_font <= next_font:
                print(f"  ⚠️ 层级字体大小顺序异常: L{current_level}({current_font:.1f}pt) <= L{next_level}({next_font:.1f}pt)")
                level_order_valid = False
            else:
                print(f"  ✅ 层级字体大小正常: L{current_level}({current_font:.1f}pt) > L{next_level}({next_font:.1f}pt)")
        
        if not level_order_valid:
            print("  ⚠️ 检测到层级字体大小顺序异常，将使用更严格的过滤")
        
        # 验证每个条目的字体大小
        valid_entries = []
        filtered_count = 0
        
        for entry in corrected_entries:
            level = entry.get('level', 1)
            font_size = entry.get('font_size', 12.0)
            title = entry.get('title', '')
            
            should_keep = True
            filter_reason = ""
            
            # 检查该层级的字体大小是否符合模式
            if level in level_primary_fonts:
                pattern = level_primary_fonts[level]
                primary_size = pattern['primary_size']
                tolerance = pattern['tolerance']
                
                size_diff = abs(font_size - primary_size)
                if size_diff > tolerance:
                    should_keep = False
                    filter_reason = f"字体大小偏离层级标准 (实际:{font_size:.1f}pt, 标准:{primary_size:.1f}pt, 差异:{size_diff:.1f}pt)"
            
            # 检查层级字体大小递减逻辑：当前层级字体应该 <= 上级层级字体
            if should_keep and level > 1:
                for higher_level in range(1, level):
                    if higher_level in level_primary_fonts:
                        higher_font = level_primary_fonts[higher_level]['primary_size']
                        current_font = font_size
                        
                        # 下级层级字体应该小于等于上级层级字体
                        if current_font > higher_font + 0.5:  # 允许0.5pt的容差
                            should_keep = False
                            filter_reason = f"字体大小违反递减逻辑 (L{level}:{current_font:.1f}pt > L{higher_level}:{higher_font:.1f}pt)"
                            break
            
            # 额外检查：如果层级顺序异常，进行更严格的字体大小验证
            if should_keep and not level_order_valid:
                # 基于字体大小重新判断层级
                predicted_level = self._predict_level_by_font_size(font_size, level_primary_fonts)
                if predicted_level != level and abs(predicted_level - level) > 1:
                    should_keep = False
                    filter_reason = f"字体大小与层级不匹配 (字体{font_size:.1f}pt更像L{predicted_level}而非L{level})"
            
            if should_keep:
                valid_entries.append(entry)
            else:
                filtered_count += 1
                print(f"  ❌ 过滤: '{title[:40]}...' - {filter_reason}")
        
        print(f"字体大小层级验证完成: 保留 {len(valid_entries)} 个，过滤 {filtered_count} 个")
        return valid_entries

    def validate_y_coordinate_ordering(self, toc_entries: List[Dict]) -> List[Dict]:
        """
        验证Y坐标递增顺序，确保书签按文档顺序排列
        
        Args:
            toc_entries: 原始条目列表
            
        Returns:
            List[Dict]: 过滤后的条目列表
        """
        if len(toc_entries) <= 1:
            return toc_entries
        
        print("开始Y坐标递增验证...")
        
        # 按页码和Y坐标排序
        sorted_entries = sorted(toc_entries, key=lambda x: (
            x.get('source_page', x.get('page', 0)), 
            x.get('y_coordinate', 0)
        ))
        
        valid_entries = []
        filtered_count = 0
        prev_page = -1
        prev_y = -1
        
        for i, entry in enumerate(sorted_entries):
            page = entry.get('source_page', entry.get('page', 0))
            y_coord = entry.get('y_coordinate', 0)
            title = entry.get('title', '')
            
            should_keep = True
            filter_reason = ""
            
            # 检查Y坐标递增规律
            if page == prev_page:
                # 同一页内，Y坐标必须递增（向下）
                if y_coord <= prev_y:
                    should_keep = False
                    filter_reason = f"Y坐标逆序 (当前Y:{y_coord:.1f} <= 前一个Y:{prev_y:.1f})"
            elif page < prev_page:
                # 页码应该递增
                should_keep = False
                filter_reason = f"页码逆序 (当前页:{page} < 前一页:{prev_page})"
            
            # 检查Y坐标的合理性（不应该为0或异常值）
            if should_keep and (y_coord <= 0 or y_coord > 10000):
                should_keep = False
                filter_reason = f"Y坐标异常 (Y:{y_coord:.1f})"
            
            if should_keep:
                valid_entries.append(entry)
                prev_page = page
                prev_y = y_coord
            else:
                filtered_count += 1
                print(f"  ❌ 过滤: '{title[:40]}...' - {filter_reason} (页面:{page}, Y:{y_coord:.1f})")
        
        print(f"Y坐标递增验证完成: 保留 {len(valid_entries)} 个，过滤 {filtered_count} 个")
        return valid_entries
    
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
            
            # 规范化层级结构
            print("步骤3: 规范化层级结构...")
            normalized_entries = self.normalize_toc_levels(pre_filtered_entries)
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
                # 获取目标页面（已经是1基索引）
                target_page_1based = entry.get("target_page", entry.get("page", 1))
                
                # 确保目标页面在有效范围内（转换为0基索引进行验证）
                target_page_0based = target_page_1based - 1
                target_page_0based = min(target_page_0based, len(self.doc) - 1)
                target_page_0based = max(0, target_page_0based)
                
                # 转换回1基索引
                target_page_1based = target_page_0based + 1
                
                toc_item = [
                    entry["level"],
                    entry["title"],
                    target_page_1based,  # PyMuPDF使用1基索引
                    {"kind": 1, "page": target_page_0based}  # 页面引用使用0基索引
                ]
                
                toc.append(toc_item)
                
                # 添加详细的调试信息
                source_page = entry.get('source_page', entry.get('page', 1))
                print(f"书签 {i+1}: '{entry['title']}' -> 源页面: {source_page}, 目标页面: {target_page_1based}")
            
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
                # 'after_semantic_filter': after_semantic_filter,
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
            return True
        except Exception as e:
            print(f"错误：保存PDF失败: {e}")
            return False
    
    def print_debug_info(self, text_blocks: List[Dict], output_file: str = "pdf_debug_info.txt"):
        """
        打印和保存详细的调试信息到文件
        
        Args:
            text_blocks: 文本块列表
            output_file: 调试信息输出文件名
        """
        debug_lines = []
        debug_lines.append("=" * 80)
        debug_lines.append("PDF 标题特征分析调试信息")
        debug_lines.append("=" * 80)
        debug_lines.append(f"PDF文件: {self.pdf_path}")
        debug_lines.append(f"总文本块数: {len(text_blocks)}")
        debug_lines.append("")
        
        # 按页码分组
        pages_data = {}
        for block in text_blocks:
            page = block.get("page", 1)
            if page not in pages_data:
                pages_data[page] = []
            pages_data[page].append(block)
        
        for page_num in sorted(pages_data.keys()):
            page_blocks = pages_data[page_num]
            debug_lines.append(f"\n{'='*60}")
            debug_lines.append(f"第 {page_num} 页 ({len(page_blocks)} 个文本块)")
            debug_lines.append('='*60)
            
            for i, block in enumerate(page_blocks):
                debug_lines.append(f"\n--- 文本块 #{i+1} ---")
                debug_lines.append(f"📝 文本内容: {repr(block['text'][:100])}{'...' if len(block['text']) > 100 else ''}")
                debug_lines.append(f"📏 文本长度: {len(block['text'])} 字符")
                
                # 字体信息
                debug_lines.append(f"\n🔤 字体信息:")
                debug_lines.append(f"  主要字体: {block.get('font', 'Unknown')}")
                debug_lines.append(f"  主要字号: {block.get('size', 0):.1f}")
                debug_lines.append(f"  字体标志: {block.get('flags', 0)} (二进制: {bin(block.get('flags', 0))})")
                debug_lines.append(f"  文字颜色: {block.get('color', 0)}")
                
                # 字体分析
                font_analysis = block.get('font_analysis', {})
                debug_lines.append(f"  是否粗体: {font_analysis.get('is_bold', False)}")
                debug_lines.append(f"  是否斜体: {font_analysis.get('is_italic', False)}")
                debug_lines.append(f"  字号范围: {font_analysis.get('size_range', [0, 0])}")
                debug_lines.append(f"  所有字体: {font_analysis.get('all_fonts', [])}")
                debug_lines.append(f"  所有字号: {font_analysis.get('all_sizes', [])}")
                
                # 位置信息
                position = block.get('position', {})
                debug_lines.append(f"\n📍 位置信息:")
                debug_lines.append(f"  X坐标: {position.get('x', 0):.1f}")
                debug_lines.append(f"  Y坐标: {position.get('y', 0):.1f}")
                debug_lines.append(f"  宽度: {position.get('width', 0):.1f}")
                debug_lines.append(f"  高度: {position.get('height', 0):.1f}")
                debug_lines.append(f"  中心点: ({position.get('center_x', 0):.1f}, {position.get('center_y', 0):.1f})")
                
                # X坐标过滤分析
                if self.title_x_coordinate is not None:
                    x_diff = abs(position.get('x', 0) - self.title_x_coordinate)
                    debug_lines.append(f"  与标题X坐标差异: {x_diff:.1f}px (容差: {self.x_coordinate_tolerance:.1f}px)")
                    debug_lines.append(f"  X坐标过滤结果: {'通过' if x_diff <= self.x_coordinate_tolerance else '被过滤'}")
                
                # 边界框
                bbox = block.get('bbox', [0, 0, 0, 0])
                debug_lines.append(f"  边界框: [{bbox[0]:.1f}, {bbox[1]:.1f}, {bbox[2]:.1f}, {bbox[3]:.1f}]")
                
                # 目录模式匹配
                debug_lines.append(f"\n🔍 目录模式匹配:")
                text = block['text']
                matched_patterns = []
                for j, pattern in enumerate(self.toc_patterns):
                    if re.match(pattern, text.strip()):
                        matched_patterns.append(f"模式{j+1}: {pattern}")
                
                if matched_patterns:
                    debug_lines.append(f"  匹配的模式: {len(matched_patterns)} 个")
                    for pattern in matched_patterns:
                        debug_lines.append(f"    - {pattern}")
                else:
                    debug_lines.append("  匹配的模式: 无")
                
                # 详细行信息
                lines = block.get('lines', [])
                if len(lines) > 1:
                    debug_lines.append(f"\n📄 行详情 ({len(lines)} 行):")
                    for line_idx, line in enumerate(lines):
                        debug_lines.append(f"  行{line_idx+1}: {repr(line['text'][:50])}{'...' if len(line['text']) > 50 else ''}")
                        line_fonts = line.get('fonts', [])
                        if line_fonts:
                            debug_lines.append(f"    字体详情: {len(line_fonts)} 个字体段")
                            for font_idx, font_info in enumerate(line_fonts[:3]):  # 只显示前3个
                                debug_lines.append(f"      段{font_idx+1}: '{font_info['text'][:20]}...' "
                                f"字号={font_info['size']:.1f} "
                                f"字体={font_info['font']} "
                                f"标志={font_info['flags']}")
                
                debug_lines.append("-" * 50)
        
        # 统计信息
        debug_lines.append(f"\n\n{'='*60}")
        debug_lines.append("📊 统计信息")
        debug_lines.append('='*60)
        
        all_sizes = []
        all_fonts = []
        all_flags = []
        toc_candidates = []
        
        for block in text_blocks:
            all_sizes.append(block.get('size', 0))
            all_fonts.append(block.get('font', ''))
            all_flags.append(block.get('flags', 0))
            
            # 检查是否可能是目录项
            text = block['text']
            for pattern in self.toc_patterns:
                if re.match(pattern, text.strip()):
                    toc_candidates.append(block)
                    break
        
        if all_sizes:
            debug_lines.append(f"字号统计:")
            debug_lines.append(f"  最小字号: {min(all_sizes):.1f}")
            debug_lines.append(f"  最大字号: {max(all_sizes):.1f}")
            debug_lines.append(f"  平均字号: {sum(all_sizes)/len(all_sizes):.1f}")
            
            # 字号分布
            size_counts = {}
            for size in all_sizes:
                size_key = round(size, 1)
                size_counts[size_key] = size_counts.get(size_key, 0) + 1
            
            debug_lines.append(f"  字号分布 (出现次数 >= 2):")
            for size, count in sorted(size_counts.items(), key=lambda x: x[1], reverse=True):
                if count >= 2:
                    debug_lines.append(f"    {size:.1f}pt: {count} 次")
        
        if all_fonts:
            font_counts = {}
            for font in all_fonts:
                if font:
                    font_counts[font] = font_counts.get(font, 0) + 1
            
            debug_lines.append(f"\n常用字体 (出现次数 >= 2):")
            for font, count in sorted(font_counts.items(), key=lambda x: x[1], reverse=True):
                if count >= 2:
                    debug_lines.append(f"  {font}: {count} 次")
        
        debug_lines.append(f"\n潜在目录项: {len(toc_candidates)} 个")
        if toc_candidates:
            debug_lines.append("前10个潜在目录项:")
            for i, candidate in enumerate(toc_candidates[:10]):
                x_coord = candidate.get('position', {}).get('x', 0)
                debug_lines.append(f"  {i+1}. [{candidate.get('size', 0):.1f}pt] X={x_coord:.1f} {candidate['text'][:60]}...")
        
        # X坐标分析
        if self.title_x_coordinate is not None:
            debug_lines.append(f"\nX坐标分析:")
            debug_lines.append(f"  文档标题X坐标: {self.title_x_coordinate:.1f}")
            debug_lines.append(f"  X坐标容差: {self.x_coordinate_tolerance:.1f}")
            
            # 统计X坐标分布
            x_coords = []
            for candidate in toc_candidates:
                x_coord = candidate.get('position', {}).get('x', 0)
                if x_coord > 0:
                    x_coords.append(x_coord)
            
            if x_coords:
                debug_lines.append(f"  潜在目录项X坐标范围: {min(x_coords):.1f} - {max(x_coords):.1f}")
                
                # X坐标分布统计
                x_counter = {}
                for x in x_coords:
                    x_key = round(x, 1)
                    x_counter[x_key] = x_counter.get(x_key, 0) + 1
                
                debug_lines.append(f"  X坐标分布 (出现次数 >= 2):")
                for x_coord, count in sorted(x_counter.items(), key=lambda x: x[1], reverse=True):
                    if count >= 2:
                        diff = abs(x_coord - self.title_x_coordinate)
                        status = "✓" if diff <= self.x_coordinate_tolerance else "✗"
                        debug_lines.append(f"    {x_coord:.1f}: {count} 次 {status}")
        
        # 保存到文件
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(debug_lines))
            print(f"📄 调试信息已保存到: {output_file}")
        except Exception as e:
            print(f"保存调试信息失败: {e}")
        
        # 同时在控制台输出摘要
        print("\n" + "="*50)
        print("📊 PDF 标题特征分析摘要")
        print("="*50)
        print(f"总文本块数: {len(text_blocks)}")
        print(f"潜在目录项: {len(toc_candidates)} 个")
        if all_sizes:
            print(f"字号范围: {min(all_sizes):.1f} - {max(all_sizes):.1f}pt")
            print(f"平均字号: {sum(all_sizes)/len(all_sizes):.1f}pt")
        print(f"详细调试信息请查看: {output_file}")
        print("="*50)

    def determine_level_from_text(self, text: str) -> int:
        """
        根据文本内容判断层级深度
        
        Args:
            text: 标题文本
            
        Returns:
            int: 层级深度 (1-8)
        """
        text = text.strip()
        
        # 模式1: 数字序列格式 (1.2.3.4...)，但需要排除正文列举项
        number_match = re.match(r'^(\d+(?:\.\d+)*)', text)
        if number_match:
            numbers = number_match.group(1).split('.')
            number_text = number_match.group(1)
            
            # 检查是否为正文列举项（排除标准）：
            # 1. 单个数字后紧跟句号和长文本（如"2. 降低沟通成本：提供清晰..."）
            # 2. 文本长度过长（超过30字符通常不是标题）
            # 3. 包含冒号和长句（标题通常简洁）
            
            if len(numbers) == 1:  # 单层数字（如 "1.", "2."）
                remaining_text = text[len(number_text)+1:].strip()  # 去掉数字部分的剩余文本
                
                # 排除条件：
                # - 剩余文本过长（>20字符）且包含具体描述内容
                # - 包含冒号和详细说明
                # - 包含"提供"、"确保"、"降低"等动词开头的描述性语言
                if (len(remaining_text) > 20 and 
                    ('：' in remaining_text or '，' in remaining_text) and
                    any(keyword in remaining_text[:10] for keyword in ['提供', '确保', '降低', '提高', '减少', '增加', '实现', '支持', '帮助'])):
                    
                    print(f"排除正文列举项: '{text[:40]}...' (判断为描述性列举，非标题)")
                    return 1  # 虽然格式像标题，但给一个默认层级，让字体大小验证来过滤它
            
            return min(len(numbers), 8)  # 最多8层
        
        # 模式2: 第X章 (第一层)
        if re.match(r'^第[一二三四五六七八九十\d]+章', text):
            return 1
        
        # 模式3: 第X节 (第二层)
        if re.match(r'^第[一二三四五六七八九十\d]+节', text):
            return 2
        
        # 模式4: 第X部分 (第一层)
        if re.match(r'^第[一二三四五六七八九十\d]+部分', text):
            return 1
        
        # 模式5: 中文数字 (一、二、三...)
        if re.match(r'^[一二三四五六七八九十]+[、\.]', text):
            return 1
        
        # 模式6: 罗马数字 (I、II、III...)
        if re.match(r'^[IVXLCDM]+[、\.]', text):
            return 1
        
        # 模式7: 大写字母 (A、B、C...)
        if re.match(r'^[A-Z]\.\s+', text):
            return 2
        
        # 模式8: 小写字母加括号 (a)、b)...)
        if re.match(r'^[a-z]\)\s+', text):
            return 3
        
        # 模式9: 括号数字 ((1)、(2)...)
        if re.match(r'^\([一二三四五六七八九十\d]+\)', text):
            return 2
        
        # 模式10: 数字加顿号 (1、2、3...)
        if re.match(r'^\d+、', text):
            return 1
        
        # 模式11: 【标题】格式
        if re.match(r'^【.*】', text):
            return 1
        
        # 默认为第一层
        return 1

    def detect_document_title_x_coordinate(self, text_blocks: List[Dict]) -> float:
        """
        检测文档标题的X坐标作为参考
        
        Args:
            text_blocks: 所有文本块
            
        Returns:
            float: 文档标题的X坐标
        """
        # 策略1: 找到字号最大的文本块作为文档标题
        title_candidates = []
        
        for block in text_blocks:
            size = block.get('size', 0)
            if size > 0:
                title_candidates.append({
                    'text': block['text'],
                    'size': size,
                    'x': block.get('position', {}).get('x', 0),
                    'page': block.get('page', 1)
                })
        
        if not title_candidates:
            print("⚠️ 无法找到文档标题，使用默认X坐标")
            self.document_title_text = None
            return 0
        
        # 按字号排序，取最大的几个
        title_candidates.sort(key=lambda x: x['size'], reverse=True)
        
        # 取前3个最大字号的文本块
        top_candidates = title_candidates[:3]
        
        # 优先选择第一页的标题
        first_page_titles = [c for c in top_candidates if c['page'] == 1]
        if first_page_titles:
            selected_title = first_page_titles[0]
        else:
            selected_title = top_candidates[0]
        
        title_x = selected_title['x']
        title_text = selected_title['text']
        
        # 记录文档标题文本，避免将其添加为书签
        self.document_title_text = title_text.strip()
        
        print(f"📍 检测到文档标题X坐标: {title_x:.1f} (文档标题: '{title_text[:30]}...')")
        print(f"📍 文档标题将被排除，不会添加为书签")
        
        # 策略2: 验证并调整X坐标
        # 收集所有可能的标题X坐标
        potential_title_x_coords = []
        for block in text_blocks:
            text = block['text'].strip()
            # 检查是否符合标题模式
            for pattern in self.toc_patterns:
                if re.match(pattern, text):
                    x_coord = block.get('position', {}).get('x', 0)
                    if x_coord > 0:
                        potential_title_x_coords.append(x_coord)
                    break
        
        if potential_title_x_coords:
            # 找到最常见的X坐标
            from collections import Counter
            x_counter = Counter([round(x, 1) for x in potential_title_x_coords])
            most_common_x = x_counter.most_common(1)[0][0]
            
            # 如果最常见的X坐标与检测到的标题X坐标相近，使用最常见的
            if abs(most_common_x - title_x) <= self.x_coordinate_tolerance * 2:
                title_x = most_common_x
                print(f"📍 根据标题模式调整X坐标为: {title_x:.1f}")
        
        return title_x

    def extract_existing_bookmarks(self):
        """
        提取PDF中已有的书签
        
        Returns:
            List[Dict]: 书签列表
        """
        try:
            # 确保PDF文档已打开
            if self.doc is None:
                if not self.open_pdf():
                    print("无法打开PDF文件")
                    return []
            
            toc = self.doc.get_toc()
            if not toc:
                print("PDF中没有找到书签")
                return []
            
            bookmarks = []
            for item in toc:
                if len(item) >= 3:
                    level = item[0]
                    title = item[1]
                    page = item[2]
                    
                    bookmark = {
                        'level': level,
                        'title': title,
                        'page': page
                    }
                    
                    # 如果有额外的位置信息
                    if len(item) > 3 and isinstance(item[3], dict):
                        if 'page' in item[3]:
                            bookmark['target_page'] = item[3]['page']
                    
                    bookmarks.append(bookmark)
            
            print(f"成功提取 {len(bookmarks)} 个书签")
            return bookmarks
            
        except Exception as e:
            print(f"提取书签时发生错误: {str(e)}")
            return []
    
    def export_bookmarks(self, bookmarks, output_path, format_type='json', include_page_info=True, include_level_info=True):
        """
        导出书签到文件
        
        Args:
            bookmarks: 书签列表
            output_path: 输出文件路径
            format_type: 导出格式 ('json', 'txt', 'csv')
            include_page_info: 是否包含页面信息
            include_level_info: 是否包含层级信息
        """
        try:
            if format_type == 'json':
                self._export_to_json(bookmarks, output_path, include_page_info, include_level_info)
            elif format_type == 'txt':
                self._export_to_txt(bookmarks, output_path, include_page_info, include_level_info)
            elif format_type == 'csv':
                self._export_to_csv(bookmarks, output_path, include_page_info, include_level_info)
            else:
                raise ValueError(f"不支持的导出格式: {format_type}")
            
            print(f"书签文件已保存到: {output_path}")
            return True
            
        except Exception as e:
            print(f"导出书签时发生错误: {str(e)}")
            return False
    
    def _export_to_json(self, bookmarks, output_path, include_page_info, include_level_info):
        """导出为JSON格式"""
        import json
        
        export_data = []
        for bookmark in bookmarks:
            item = {'title': bookmark['title']}
            
            if include_level_info:
                item['level'] = bookmark['level']
            
            if include_page_info:
                item['page'] = bookmark['page']
                if 'target_page' in bookmark:
                    item['target_page'] = bookmark['target_page']
            
            export_data.append(item)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    def _export_to_txt(self, bookmarks, output_path, include_page_info, include_level_info):
        """导出为文本格式"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("PDF书签列表\n")
            f.write("=" * 50 + "\n\n")
            
            for bookmark in bookmarks:
                level = bookmark['level']
                title = bookmark['title']
                page = bookmark['page']
                
                # 根据层级添加缩进
                indent = "  " * (level - 1)
                
                line = f"{indent}{title}"
                
                info_parts = []
                if include_level_info:
                    info_parts.append(f"层级 {level}")
                if include_page_info:
                    info_parts.append(f"页面 {page}")
                
                if info_parts:
                    line += f" ({', '.join(info_parts)})"
                
                f.write(line + "\n")
    
    def _export_to_csv(self, bookmarks, output_path, include_page_info, include_level_info):
        """导出为CSV格式"""
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['title']
            if include_level_info:
                fieldnames.append('level')
            if include_page_info:
                fieldnames.append('page')
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for bookmark in bookmarks:
                row = {'title': bookmark['title']}
                
                if include_level_info:
                    row['level'] = bookmark['level']
                if include_page_info:
                    row['page'] = bookmark['page']
                
                writer.writerow(row)

    def new_auto_bookmark_process(self, output_path: Optional[str] = None) -> bool:
        """
        新的自动书签处理流程，按照以下步骤：
        1. 通过x坐标过滤出所有符合逻辑的数据，得到dataList1
        2. 通过 --font-threshold对dataList1过滤得到dataList2
        3. 对dataList2根据坐标y进行排序得到dataList3
        4. 根据字体大小对dataList3构建出有层级的treeList
        5. 最后将treeList加为书签
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            bool: 是否成功
        """
        if not self.open_pdf():
            return False
        
        try:
            print(f"开始新的自动书签处理流程: {self.pdf_path}")
            print(f"总页数: {len(self.doc)}")
            
            # 步骤1: 通过x坐标过滤数据
            print("步骤1: 通过x坐标过滤数据...")
            dataList1 = self._filter_by_x_coordinate()
            print(f"x坐标过滤后得到 {len(dataList1)} 个文本块")
            
            if not dataList1:
                print("警告：x坐标过滤后没有找到任何数据")
                return False
            
            # 步骤2: 通过font-threshold过滤
            print("步骤2: 通过font-threshold过滤...")
            dataList2 = self._filter_by_font_threshold(dataList1)
            print(f"字体阈值过滤后得到 {len(dataList2)} 个文本块")
            
            if not dataList2:
                print("警告：字体阈值过滤后没有找到任何数据")
                return False
            
            # 步骤3: 根据y坐标排序
            print("步骤3: 根据y坐标排序...")
            dataList3 = self._sort_by_y_coordinate(dataList2)
            print(f"y坐标排序完成，共 {len(dataList3)} 个文本块")
            
            # 步骤4: 根据字体大小构建层级树结构
            print("步骤4: 根据字体大小构建层级树结构...")
            treeList = self._build_hierarchy_tree(dataList3)
            print(f"构建层级树完成，共 {len(treeList)} 个节点")
            
            if not treeList:
                print("警告：构建层级树后没有找到任何节点")
                return False
            
            # 步骤5: 将treeList加为书签
            print("步骤5: 添加书签...")
            success, bookmark_stats = self._add_tree_bookmarks(treeList)
            
            if success:
                if bookmark_stats:
                    print(f"最终添加了 {bookmark_stats.get('final', 0)} 个书签， 共 {bookmark_stats.get('levels', 0)} 个层级")
                
                # 保存文件
                if self.save_pdf(output_path):
                    return True
                else:
                    return False
            else:
                print("添加书签失败")
                return False
                
        except Exception as e:
            print(f"错误：处理PDF时发生异常: {e}")
            return False
        finally:
            self.close_pdf()
    
    def _filter_by_x_coordinate(self) -> List[Dict]:
        """
        步骤1: 通过x坐标过滤出所有符合逻辑的数据
        
        Returns:
            List[Dict]: 过滤后的文本块列表 (dataList1)
        """
        print("  提取所有页面的文本块...")
        all_text_blocks = []
        
        # 提取所有页面的文本
        for page_num in range(len(self.doc)):
            page_text_blocks = self.extract_text_with_font_info(page_num)
            all_text_blocks.extend(page_text_blocks)
        
        print(f"  总共提取了 {len(all_text_blocks)} 个文本块")
        
        # 检测文档标题的X坐标（如果启用了x坐标过滤）
        if self.enable_x_coordinate_filter:
            self.title_x_coordinate = self.detect_document_title_x_coordinate(all_text_blocks)
            print(f"  检测到的标题X坐标: {self.title_x_coordinate}")
        
        # 根据x坐标过滤
        filtered_blocks = []
        
        for block in all_text_blocks:
            text = block.get('text', '').strip()
            if not text:
                continue
            
            # 获取x坐标
            x_coordinate = block.get('position', {}).get('x', 0)
            if x_coordinate == 0:
                bbox = block.get('bbox', [0, 0, 0, 0])
                if len(bbox) >= 4:
                    x_coordinate = bbox[0]
            
            # 基本的文本过滤
            if not self._is_potential_title_text(text):
                continue
            
            # 检查是否为文档标题，如果是则跳过
            if self.document_title_text:
                # 双向检查：文档标题包含当前文本，或当前文本包含文档标题
                text_clean = text.strip()
                title_clean = self.document_title_text.strip()
                if (text_clean in title_clean) or (title_clean in text_clean) or (text_clean == title_clean):
                    print(f"    跳过文档标题: '{text[:30]}...'")
                    continue
            
            # 数字开头过滤检查
            if self._should_filter_by_numeric_start(text):
                print(f"    跳过非数字开头的文本: '{text[:30]}...'")
                continue
            
            # X坐标过滤
            if self.enable_x_coordinate_filter and self.title_x_coordinate is not None:
                x_diff = abs(x_coordinate - self.title_x_coordinate)
                if x_diff > self.x_coordinate_tolerance:
                    print(f"    跳过X坐标不对齐的文本: '{text[:30]}...' (x={x_coordinate:.1f}, 差异={x_diff:.1f})")
                    continue
                else:
                    print(f"    保留X坐标对齐的文本: '{text[:30]}...' (x={x_coordinate:.1f}, 差异={x_diff:.1f})")
            
            # 添加额外的分析信息
            block_info = block.copy()
            block_info.update({
                'x_coordinate': x_coordinate,
                'y_coordinate': block.get('position', {}).get('y', block.get('bbox', [0, 0, 0, 0])[1]),
                'font_size': block.get('size', 12),
                'font_name': block.get('font', ''),
                'page_num': block.get('page', 1),
                'is_potential_title': True
            })
            
            filtered_blocks.append(block_info)
        
        print(f"  X坐标过滤完成，保留 {len(filtered_blocks)} 个文本块")
        return filtered_blocks
    
    def _filter_by_font_threshold(self, data_list: List[Dict]) -> List[Dict]:
        """
        步骤2: 通过 --font-threshold对dataList1过滤得到dataList2
        
        Args:
            data_list: dataList1
            
        Returns:
            List[Dict]: 过滤后的文本块列表 (dataList2)
        """
        if not self.enable_font_size_filter:
            print("  字体大小过滤未启用，跳过此步骤")
            return data_list
        
        print(f"  应用字体大小阈值过滤: {self.font_size_threshold}")
        
        filtered_blocks = []
        
        for block in data_list:
            font_size = block.get('font_size', 0)
            
            if font_size >= self.font_size_threshold:
                filtered_blocks.append(block)
                print(f"    保留字体大小 {font_size:.1f} 的文本: '{block.get('text', '')[:30]}...'")
            else:
                print(f"    过滤掉字体大小 {font_size:.1f} 的文本: '{block.get('text', '')[:30]}...'")
        
        print(f"  字体阈值过滤完成，保留 {len(filtered_blocks)} 个文本块")
        return filtered_blocks
    
    def _sort_by_y_coordinate(self, data_list: List[Dict]) -> List[Dict]:
        """
        步骤3: 对dataList2根据坐标y进行排序得到dataList3
        
        Args:
            data_list: dataList2
            
        Returns:
            List[Dict]: 排序后的文本块列表 (dataList3)
        """
        print("  根据Y坐标和页码进行排序...")
        
        # 先按页码排序，再按Y坐标排序（Y坐标较小的在前）
        sorted_list = sorted(data_list, key=lambda x: (x.get('page_num', 1), x.get('y_coordinate', 0)))
        
        print("  排序完成")
        print("  前5个文本块的位置信息:")
        for i, block in enumerate(sorted_list[:5]):
            page = block.get('page_num', 1)
            y = block.get('y_coordinate', 0)
            text = block.get('text', '')[:30]
            print(f"    {i+1}. 页码:{page}, Y:{y:.1f}, 文本:'{text}...'")
        
        return sorted_list
    
    def _validate_numeric_hierarchy_relationship(self, current_title: str, potential_parent_title: str) -> bool:
        """
        当require_numeric_start为true时，根据数字序列验证层级关系
        
        Args:
            current_title: 当前标题
            potential_parent_title: 潜在父级标题
            
        Returns:
            bool: 是否为有效的父子关系
        """
        if not self.require_numeric_start:
            return True  # 如果未启用数字开头要求，则不进行数字序列验证
        
        current_numbers = self.extract_number_sequence(current_title)
        parent_numbers = self.extract_number_sequence(potential_parent_title)
        
        # 如果任一标题没有数字序列，使用默认字体大小层级判断
        if not current_numbers or not parent_numbers:
            return False
        
        # 检查是否为有效的父子关系
        # 规则1: 子级的数字序列应该比父级多一层
        if len(current_numbers) != len(parent_numbers) + 1:
            return False
            
        # 规则2: 子级的前n-1层数字应该与父级完全匹配
        if current_numbers[:-1] != parent_numbers:
            return False
            
        return True
    
    def _build_hierarchy_tree(self, data_list: List[Dict]) -> List[Dict]:
        """
        步骤4: 根据字体大小对dataList3构建出有层级的treeList
        从上到下一个个数据进行比对，得到每个数据的父子关系，最后得到树结构数据
        
        Args:
            data_list: dataList3
            
        Returns:
            List[Dict]: 层级树结构列表 (treeList)
        """
        if not data_list:
            return []
        
        print("  分析字体大小分布...")
        
        # 分析字体大小分布
        font_sizes = [block.get('font_size', 0) for block in data_list]
        unique_sizes = sorted(list(set(font_sizes)), reverse=True)  # 从大到小排序
        
        print(f"  发现 {len(unique_sizes)} 种字体大小: {unique_sizes}")
        
        # 为每种字体大小分配连续的层级（从1开始）
        size_to_level = {}
        for i, size in enumerate(unique_sizes):
            size_to_level[size] = i + 1
        
        print("  字体大小到层级的映射:")
        for size, level in size_to_level.items():
            print(f"    字体大小 {size:.1f} -> 层级 {level}")
        
        # 构建树结构
        tree_list = []
        
        for i, block in enumerate(data_list):
            font_size = block.get('font_size', 0)
            level = size_to_level.get(font_size, 1)
            
            # 创建节点
            node = {
                'title': block.get('text', ''),
                'page': block.get('page_num', 1),
                'source_page': block.get('page_num', 1),
                'target_page': block.get('page_num', 1),
                'font_size': font_size,
                'font_name': block.get('font_name', ''),
                'x_coordinate': block.get('x_coordinate', 0),
                'y_coordinate': block.get('y_coordinate', 0),
                'bbox': block.get('bbox', [0, 0, 0, 0]),
                'level': level,
                'matched_pattern': '新流程自动识别',
                'children': [],
                'parent_index': -1
            }
            
            # 查找合适的父节点
            if level == 1:
                # 顶级节点
                node['parent_index'] = -1
                tree_list.append(node)
            else:
                # 查找最近的较小层级作为父节点
                # parent_found = False
                for j in range(len(tree_list) - 1, -1, -1):
                    if tree_list[j]['level'] < level and self.require_numeric_start and not self._validate_numeric_hierarchy_relationship(node['title'], tree_list[j]['title']):
                        break
                    if tree_list[j]['level'] < level or (self.require_numeric_start and self._validate_numeric_hierarchy_relationship(node['title'], tree_list[j]['title'])):
                        # 找到父节点
                        node['parent_index'] = j
                        if tree_list[j]['level'] == level and (self.require_numeric_start and self._validate_numeric_hierarchy_relationship(node['title'], tree_list[j]['title'])):
                            node['level'] = level + 1
                        # parent_found = True
                        tree_list.append(node)
                        print(f"    节点 '{node['title'][:20]}...' (层级{level}) 的父节点是 '{tree_list[j]['title'][:20]}...' (层级{tree_list[j]['level']})")
                        break
                
                # if not parent_found:
                #     # 没有找到合适的父节点，设为顶级节点
                #     node['parent_index'] = -1
                #     node['level'] = 1
                #     print(f"    节点 '{node['title'][:20]}...' 没有找到父节点，设为顶级节点")
            
            # tree_list.append(node)
        
        # 验证并修复层级连续性 - 这个步骤是必需的！
        tree_list = self._normalize_hierarchy_levels(tree_list)
        
        print(f"  构建层级树完成，共 {len(tree_list)} 个节点")
        
        # 打印树结构预览
        print("  层级树结构预览:")
        for i, node in enumerate(tree_list[:10]):  # 只显示前10个
            level_indent = "  " * (node['level'] - 1)
            title = node['title'][:40]
            page = node['page']
            font_size = node['font_size']
            print(f"    {i+1:2d}. {level_indent}[{node['level']}] {title} (页面{page}, 字体{font_size:.1f})")
        
        if len(tree_list) > 10:
            print(f"    ... 还有 {len(tree_list) - 10} 个节点")
        
        return tree_list
    
    def _normalize_hierarchy_levels(self, tree_list: List[Dict]) -> List[Dict]:
        """
        规范化层级，确保层级连续且符合PyMuPDF要求
        PyMuPDF要求：
        1. 第一个条目必须是层级1
        2. 每个条目的层级不能比前面所有条目的最大层级大于1
        3. 不能有层级跳跃
        
        Args:
            tree_list: 原始树列表
            
        Returns:
            List[Dict]: 规范化后的树列表
        """
        if not tree_list:
            return tree_list
        
        print("  开始严格的层级规范化...")
        
        # 确保第一个条目是层级1
        if tree_list[0]['level'] != 1:
            print(f"    强制设置第一个节点 '{tree_list[0]['title'][:20]}...' 为层级1")
            tree_list[0]['level'] = 1
        
        # 逐个处理每个节点，确保层级严格连续
        max_level_so_far = 1
        
        for i in range(1, len(tree_list)):
            current_level = tree_list[i]['level']
            
            # 计算允许的最大层级（当前最大层级+1）
            max_allowed = max_level_so_far + 1
            
            if current_level > max_allowed:
                # 层级跳跃过大，强制调整为允许的最大层级
                new_level = max_allowed
                print(f"    节点{i+1} '{tree_list[i]['title'][:20]}...' 层级从 {current_level} 强制调整为 {new_level}")
                tree_list[i]['level'] = new_level
                max_level_so_far = new_level
            elif current_level < 1:
                # 层级小于1，强制设为1
                print(f"    节点{i+1} '{tree_list[i]['title'][:20]}...' 层级从 {current_level} 强制调整为 1")
                tree_list[i]['level'] = 1
                # max_level_so_far 保持不变
            else:
                # 层级正常，更新最大层级
                max_level_so_far = max(max_level_so_far, current_level)
        
        # 最终验证：再次检查确保没有任何违规
        print("  进行最终验证...")
        current_max = 0
        for i, node in enumerate(tree_list):
            level = node['level']
            
            if i == 0:
                # 第一个必须是层级1
                if level != 1:
                    print(f"    最终修正：第一个节点必须是层级1，当前是{level}")
                    node['level'] = 1
                current_max = 1
            else:
                # 后续节点不能超过当前最大层级+1
                if level > current_max + 1:
                    new_level = current_max + 1
                    print(f"    最终修正：节点{i+1} '{node['title'][:20]}...' 从层级{level}调整为{new_level}")
                    node['level'] = new_level
                    current_max = new_level
                elif level < 1:
                    print(f"    最终修正：节点{i+1} '{node['title'][:20]}...' 从层级{level}调整为1")
                    node['level'] = 1
                else:
                    current_max = max(current_max, level)
        
        # 打印最终的层级分布
        level_counts = {}
        for node in tree_list:
            level = node['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        print(f"  层级规范化完成，层级分布: {dict(sorted(level_counts.items()))}")
        
        return tree_list
    
    def _add_tree_bookmarks(self, tree_list: List[Dict]) -> Tuple[bool, Dict]:
        """
        步骤5: 将treeList加为书签
        
        Args:
            tree_list: 层级树结构列表
            
        Returns:
            Tuple[bool, Dict]: (是否成功, 统计信息)
        """
        if not tree_list:
            return False, {}
        
        print(f"  开始添加 {len(tree_list)} 个书签...")
        
        # 构建PyMuPDF兼容的TOC结构
        toc_list = []
        
        for node in tree_list:
            toc_entry = [
                node['level'],
                node['title'],
                node['target_page']
            ]
            toc_list.append(toc_entry)
        
        # 最终的层级修复 - 确保完全符合PyMuPDF要求
        print("  进行最终的TOC层级修复...")
        toc_list = self._final_toc_level_fix(toc_list)
        
        try:
            # 验证TOC结构
            if not self.validate_toc_structure(toc_list):
                print("  错误：TOC结构验证失败")
                return False, {}
            
            # 设置TOC
            self.doc.set_toc(toc_list)
            
            # 统计信息
            stats = {
                'total': len(tree_list),
                'final': len(toc_list),
                'levels': len(set(entry[0] for entry in toc_list))
            }
            return True, stats
            
        except Exception as e:
            print(f"  错误：添加书签时发生异常: {e}")
            return False, {}
    
    def _final_toc_level_fix(self, toc_list: List) -> List:
        """
        对TOC列表进行最终的层级修复，确保完全符合PyMuPDF要求
        PyMuPDF层级规则：
        1. 第一个条目必须是层级1
        2. 任何条目的层级不能比当前"活跃层级路径"的最大值大于1
        3. 层级可以回退，但不能跳跃
        
        Args:
            toc_list: 原始TOC列表，格式为 [[level, title, page], ...]
            
        Returns:
            List: 修复后的TOC列表
        """
        if not toc_list:
            return toc_list
        
        print(f"    修复前TOC层级: {[item[0] for item in toc_list[:10]]}...")
        
        # 确保第一个条目是层级1
        if toc_list[0][0] != 1:
            print(f"    强制第一个条目层级为1，原来是{toc_list[0][0]}")
            toc_list[0][0] = 1
        
        # 维护层级路径栈，用于跟踪当前活跃的层级路径
        level_path = [1]  # 第一个条目是层级1
        
        for i in range(1, len(toc_list)):
            current_level = toc_list[i][0]
            
            # 根据当前层级更新层级路径
            if current_level <= max(level_path):
                # 层级回退或平级，需要截断层级路径
                level_path = [l for l in level_path if l < current_level]
                level_path.append(current_level)
                max_allowed_next = current_level + 1
            else:
                # 层级向前，检查是否跳跃过大
                max_allowed = max(level_path) + 1
                if current_level > max_allowed:
                    # 层级跳跃过大，强制调整
                    new_level = max_allowed
                    print(f"    TOC条目{i+1} '{toc_list[i][1][:20]}...' 层级从 {current_level} 调整为 {new_level}")
                    toc_list[i][0] = new_level
                    current_level = new_level
                
                # 更新层级路径
                level_path.append(current_level)
        
        print(f"    修复后TOC层级: {[item[0] for item in toc_list[:10]]}...")
        
        # 最终验证：确保没有任何跳跃
        print("    进行最终验证...")
        verified_toc = []
        current_max_level = 0
        
        for i, item in enumerate(toc_list):
            level, title, page = item
            
            if i == 0:
                # 第一个必须是层级1
                if level != 1:
                    print(f"    最终修正：第一个条目强制设为层级1，原来是{level}")
                    level = 1
                current_max_level = 1
            else:
                # 后续条目检查跳跃
                if level > current_max_level + 1:
                    new_level = current_max_level + 1
                    print(f"    最终修正：条目{i+1} '{title[:20]}...' 从层级{level}调整为{new_level}")
                    level = new_level
                
                # 更新当前最大层级（考虑回退）
                if level > current_max_level:
                    current_max_level = level
                # 如果是回退，current_max_level保持不变
            
            verified_toc.append([level, title, page])
        
        # 打印层级分布
        level_counts = {}
        for item in verified_toc:
            level = item[0]
            level_counts[level] = level_counts.get(level, 0) + 1
        
        print(f"    最终TOC层级分布: {dict(sorted(level_counts.items()))}")
        
        return verified_toc
    
    def _is_potential_title_text(self, text: str) -> bool:
        """
        判断文本是否可能是标题
        
        Args:
            text: 文本内容
            
        Returns:
            bool: 是否可能是标题
        """
        # 基本长度检查
        if len(text.strip()) < 2:
            return False
        
        # 过滤明显不是标题的文本
        if self.is_obviously_not_title(text):
            return False
        
        # 检查是否看起来像标题
        if self.looks_like_title(text, {}):
            return True
        
        # 检查是否有标题编号
        if self.has_title_numbering(text):
            return True
        
        return True  # 默认认为可能是标题，让后续步骤进一步过滤

    def _has_numeric_start(self, text: str) -> bool:
        """
        检查文本是否以数字开头
        
        Args:
            text: 文本内容
            
        Returns:
            bool: 是否以数字开头
        """
        text = text.strip()
        if not text:
            return False
            
        # 检查各种数字开头的模式
        numeric_patterns = [
            r'^\d+\.',          # 1. 2. 3.
            r'^\d+\.\d+',       # 1.1 1.2 1.3
            r'^\d+\s',          # 1 2 3 (后面跟空格)
            r'^\d+、',          # 1、2、3、
            r'^\(\d+\)',        # (1) (2) (3)
            r'^第\d+[章节部分]',  # 第1章 第2节 第3部分
        ]
        
        for pattern in numeric_patterns:
            if re.match(pattern, text):
                return True
        
        return False

    def _should_filter_by_numeric_start(self, text: str) -> bool:
        """
        判断是否应该因为数字开头过滤掉某个文本
        
        Args:
            text: 文本内容
            
        Returns:
            bool: 是否应该过滤掉
        """
        # 如果没有启用数字开头过滤，则不过滤
        if not self.require_numeric_start:
            return False
        
        # 如果文本在包含标题列表中，则不过滤（包含标题不受数字开头过滤影响）
        if self.include_titles:
            for include_title in self.include_titles:
                if include_title.strip() in text or text in include_title.strip():
                    return False
        
        # 如果启用了数字开头过滤，且文本不以数字开头，则过滤掉
        return not self._has_numeric_start(text)

    def parse_bookmark_file(self, bookmark_file_path: str) -> List[Dict]:
        """
        解析书签文件，支持JSON、TXT、CSV格式
        
        Args:
            bookmark_file_path: 书签文件路径
        
        Returns:
            解析后的书签列表，格式: [{'title': str, 'level': int, 'page': int}, ...]
        """
        if not os.path.exists(bookmark_file_path):
            print(f"书签文件不存在: {bookmark_file_path}")
            return []
        
        file_ext = os.path.splitext(bookmark_file_path)[1].lower()
        
        try:
            if file_ext == '.json':
                return self._parse_json_bookmark_file(bookmark_file_path)
            elif file_ext == '.txt':
                return self._parse_txt_bookmark_file(bookmark_file_path)
            elif file_ext == '.csv':
                return self._parse_csv_bookmark_file(bookmark_file_path)
            else:
                print(f"不支持的书签文件格式: {file_ext}")
                return []
        except Exception as e:
            print(f"解析书签文件时发生错误: {str(e)}")
            return []

    def _parse_json_bookmark_file(self, file_path: str) -> List[Dict]:
        """解析JSON格式的书签文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        bookmarks = []
        for item in data:
            if 'title' in item:
                bookmark = {
                    'title': item['title'],
                    'level': item.get('level', 1),
                    'page': item.get('page', 1)
                }
                bookmarks.append(bookmark)
        
        return bookmarks

    def _parse_txt_bookmark_file(self, file_path: str) -> List[Dict]:
        """解析TXT格式的书签文件"""
        bookmarks = []
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('=') or line == 'PDF书签列表':
                continue
            
            # 计算缩进层级
            original_line = line
            level = 1
            while line.startswith('  '):
                level += 1
                line = line[2:]
            
            # 提取标题和信息
            title = line
            page = 1
            
            # 尝试从括号中提取页面信息
            if '(' in title and ')' in title:
                import re
                match = re.search(r'\(.*?页面\s*(\d+).*?\)', title)
                if match:
                    page = int(match.group(1))
                    title = re.sub(r'\s*\(.*?\)', '', title).strip()
            
            if title:
                bookmark = {
                    'title': title,
                    'level': level,
                    'page': page
                }
                bookmarks.append(bookmark)
        
        return bookmarks

    def _parse_csv_bookmark_file(self, file_path: str) -> List[Dict]:
        """解析CSV格式的书签文件"""
        import csv
        bookmarks = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'title' in row and row['title']:
                    bookmark = {
                        'title': row['title'],
                        'level': int(row.get('level', 1)) if row.get('level') else 1,
                        'page': int(row.get('page', 1)) if row.get('page') else 1
                    }
                    bookmarks.append(bookmark)
        
        return bookmarks

    def match_bookmarks_with_pdf_text(self, bookmark_titles: List[str], fuzzy_match: bool = True) -> List[Dict]:
        """
        根据书签标题列表在PDF中进行匹配
        
        Args:
            bookmark_titles: 需要匹配的书签标题列表
            fuzzy_match: 是否启用模糊匹配
        
        Returns:
            匹配到的书签条目列表
        """
        print(f"开始匹配 {len(bookmark_titles)} 个书签标题...")
        
        # 获取所有页面的文本信息
        all_text_blocks = []
        for page_num in range(len(self.doc)):
            page_text_blocks = self.extract_text_with_font_info(page_num)
            for block in page_text_blocks:
                block['page'] = page_num + 1
            all_text_blocks.extend(page_text_blocks)
        
        matched_bookmarks = []
        
        for title in bookmark_titles:
            matched_block = self._find_matching_text_block(title, all_text_blocks, fuzzy_match)
            if matched_block:
                matched_bookmarks.append(matched_block)
                print(f"✅ 匹配成功: '{title}' -> 页面 {matched_block['page']}")
            else:
                print(f"❌ 未找到匹配: '{title}'")
        
        print(f"匹配完成，成功匹配 {len(matched_bookmarks)}/{len(bookmark_titles)} 个书签")
        return matched_bookmarks

    def _find_matching_text_block(self, target_title: str, text_blocks: List[Dict], fuzzy_match: bool = True) -> Optional[Dict]:
        """
        在文本块中查找匹配的标题
        
        Args:
            target_title: 目标标题
            text_blocks: 文本块列表
            fuzzy_match: 是否启用模糊匹配
        
        Returns:
            匹配到的文本块，包含书签信息
        """
        target_clean = self._clean_title_for_matching(target_title)
        
        # 优先进行精确匹配
        for block in text_blocks:
            block_text = block.get('text', '').strip()
            block_clean = self._clean_title_for_matching(block_text)
            
            if block_clean == target_clean:
                return {
                    'title': target_title,  # 使用原始标题
                    'page': block['page'],
                    'level': 1,  # 默认层级，后续会根据书签文件调整
                    'font_size': block.get('size', 12),
                    'x': block.get('x', 0),
                    'y': block.get('y', 0)
                }
        
        # 如果启用模糊匹配
        if fuzzy_match:
            best_match = None
            best_similarity = 0.8  # 相似度阈值
            
            for block in text_blocks:
                block_text = block.get('text', '').strip()
                similarity = self._calculate_text_similarity(target_clean, self._clean_title_for_matching(block_text))
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = block
            
            if best_match:
                return {
                    'title': target_title,  # 使用原始标题
                    'page': best_match['page'],
                    'level': 1,  # 默认层级
                    'font_size': best_match.get('size', 12),
                    'x': best_match.get('x', 0),
                    'y': best_match.get('y', 0)
                }
        
        return None

    def _clean_title_for_matching(self, title: str) -> str:
        """清理标题用于匹配"""
        import re
        # 移除额外的空白字符
        title = re.sub(r'\s+', ' ', title.strip())
        # 移除常见的标点符号
        title = re.sub(r'[。，、；：！？""''（）【】\[\](){}]', '', title)
        return title.lower()

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        # 简单的相似度计算，基于公共子串
        if not text1 or not text2:
            return 0.0
        
        # 计算最长公共子序列长度
        def lcs_length(s1, s2):
            m, n = len(s1), len(s2)
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if s1[i-1] == s2[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            
            return dp[m][n]
        
        lcs_len = lcs_length(text1, text2)
        max_len = max(len(text1), len(text2))
        
        return lcs_len / max_len if max_len > 0 else 0.0

    def process_with_bookmark_file(self, bookmark_file_path: str, output_path: Optional[str] = None) -> bool:
        """
        使用书签文件进行精确匹配处理
        
        Args:
            bookmark_file_path: 书签文件路径
            output_path: 输出文件路径
        
        Returns:
            处理是否成功
        """
        print(f"使用书签文件进行处理: {bookmark_file_path}")
        
        # 确保PDF文档已打开
        if not self.open_pdf():
            print("❌ 无法打开PDF文件")
            return False
        
        # 解析书签文件
        bookmark_data = self.parse_bookmark_file(bookmark_file_path)
        if not bookmark_data:
            print("书签文件为空或解析失败")
            return False
        
        print(f"从书签文件中读取到 {len(bookmark_data)} 个书签条目")
        
        # 提取标题列表进行匹配
        bookmark_titles = [item['title'] for item in bookmark_data]
        matched_bookmarks = self.match_bookmarks_with_pdf_text(bookmark_titles)
        
        if not matched_bookmarks:
            print("未找到任何匹配的书签")
            return False
        
        # 将书签文件中的层级信息应用到匹配结果
        title_to_level = {item['title']: item['level'] for item in bookmark_data}
        for bookmark in matched_bookmarks:
            if bookmark['title'] in title_to_level:
                bookmark['level'] = title_to_level[bookmark['title']]
        
        # 按页面和Y坐标排序
        matched_bookmarks.sort(key=lambda x: (x['page'], -x.get('y', 0)))
        
        # 添加书签到PDF
        success, result = self.add_bookmarks(matched_bookmarks)
        if success:
            # 保存PDF
            if self.save_pdf(output_path):
                print(f"✅ 基于书签文件的处理完成，共添加 {len(matched_bookmarks)} 个书签")
                return True
            else:
                print("❌ 保存PDF文件失败")
                return False
        else:
            print(f"❌ 添加书签失败: {result.get('error', '未知错误')}")
            return False


def main():
    parser = argparse.ArgumentParser(description="PDF书签工具")
    parser.add_argument("input_file", help="输入PDF文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径")
    
    # 处理模式选择
    parser.add_argument("--extract-only", action="store_true", help="仅提取现有书签，不创建新书签")
    
    # 书签提取相关参数
    parser.add_argument("--format", choices=['json', 'txt', 'csv'], default='json', help="导出格式 (默认: json)")
    parser.add_argument("--no-page-info", action="store_true", help="不包含页面信息")
    parser.add_argument("--no-level-info", action="store_true", help="不包含层级信息")
    
    # 书签创建相关参数
    parser.add_argument("--disable-font-filter", action="store_true", help="禁用字体大小过滤")
    parser.add_argument("--font-threshold", type=float, help="字体大小阈值")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--disable-x-filter", action="store_true", help="禁用X坐标过滤")
    parser.add_argument("--x-tolerance", type=float, default=5.0, help="X坐标容差(像素)")
    parser.add_argument("--require-numeric-start", action="store_true", help="书签必须以数字开头")
    parser.add_argument("--exclude-titles", type=str, help="排除的标题列表(JSON格式)")
    parser.add_argument("--include-titles", type=str, help="包含的标题列表(JSON格式)")
    parser.add_argument("--bookmark-file", type=str, help="书签文件路径(JSON/TXT/CSV格式)")
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input_file):
        print(f"错误：文件 '{args.input_file}' 不存在")
        sys.exit(1)
    
    try:
        tool = PDFBookmarkTool(args.input_file)
        
        # 设置工具选项
        tool.enable_debug = args.debug
        tool.enable_x_coordinate_filter = not args.disable_x_filter
        tool.x_coordinate_tolerance = args.x_tolerance
        
        # 设置字体过滤选项
        if args.disable_font_filter:
            tool.enable_font_size_filter = False
        if args.font_threshold:
            tool.font_size_threshold = args.font_threshold
        
        # 设置手动控制选项
        if args.exclude_titles:
            tool.exclude_titles = safe_json_parse(args.exclude_titles, "exclude_titles")
                
        if args.include_titles:
            tool.include_titles = safe_json_parse(args.include_titles, "include_titles")
        
        # 设置标题格式过滤选项
        tool.require_numeric_start = args.require_numeric_start
        
        if args.extract_only:
            # 书签提取模式
            print(f"开始提取PDF文件书签: {args.input_file}")
            
            bookmarks = tool.extract_existing_bookmarks()
            if not bookmarks:
                print("没有找到书签，退出")
                sys.exit(1)
            
            print(f"共提取 {len(bookmarks)} 个书签")
            
            # 确定输出文件路径
            if args.output:
                output_path = args.output
            else:
                base_name = os.path.splitext(args.input_file)[0]
                if args.format == 'json':
                    output_path = f"{base_name}_bookmarks.json"
                elif args.format == 'csv':
                    output_path = f"{base_name}_bookmarks.csv"
                else:
                    output_path = f"{base_name}_bookmarks.txt"
            
            # 导出书签
            include_page_info = not args.no_page_info
            include_level_info = not args.no_level_info
            
            success = tool.export_bookmarks(
                bookmarks, 
                output_path, 
                args.format, 
                include_page_info, 
                include_level_info
            )
            
            if success:
                print("✅ 书签提取完成!")
            else:
                print("❌ 书签提取失败!")
                sys.exit(1)
        
        else:
            # 书签创建模式
            print(f"开始处理PDF文件: {args.input_file}")
            
            # 确定输出文件路径
            if args.output:
                output_path = args.output
            else:
                base_name = os.path.splitext(args.input_file)[0]
                output_path = f"{base_name}_with_bookmarks.pdf"
            
            # 根据是否提供书签文件选择处理方式
            if args.bookmark_file:
                # 使用书签文件进行精确匹配
                print(f"使用书签文件进行精确匹配: {args.bookmark_file}")
                success = tool.process_with_bookmark_file(args.bookmark_file, output_path)
            else:
                # 使用自动书签处理流程
                print("使用自动书签处理流程...")
                success = tool.new_auto_bookmark_process(output_path)
            
            if success:
                print(f"✅ PDF书签添加完成！")
                print(f"PDF已保存到: {output_path}")
            else:
                print("❌ 处理失败!")
                sys.exit(1)
    
    except Exception as e:
        print(f"错误：处理PDF时发生异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # 清理资源
        if 'tool' in locals() and hasattr(tool, 'doc') and tool.doc is not None:
            try:
                tool.doc.close()
            except:
                pass  # 忽略关闭时的错误


if __name__ == "__main__":
    sys.exit(main()) 