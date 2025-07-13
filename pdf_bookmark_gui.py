#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
from pathlib import Path
from pdf_bookmark_tool import PDFBookmarkTool

class PDFBookmarkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF自动书签工具 v2.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap("icon.ico")  # 可选的图标文件
        except:
            pass
        
        # 设置窗口居中
        self.center_window()
        
        # 创建主框架
        self.create_widgets()
        
        # 存储文件路径
        self.input_file = ""
        self.output_file = ""
        
        # 设置拖拽支持
        self.setup_drag_drop()
        
    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
    def setup_drag_drop(self):
        """设置拖拽支持"""
        try:
            from tkinterdnd2 import DND_FILES
            # 检查是否是TkinterDnD窗口
            if hasattr(self.root, 'drop_target_register'):
                self.root.drop_target_register(DND_FILES)
                self.root.dnd_bind('<<Drop>>', self.on_drop)
                self.log_message("🎯 拖拽功能已启用")
            else:
                self.log_message("ℹ️ 拖拽功能不可用，请使用浏览按钮选择文件")
        except (ImportError, AttributeError):
            # 如果没有安装tkinterdnd2或出现其他错误，跳过拖拽功能
            self.log_message("ℹ️ 拖拽功能不可用，请使用浏览按钮选择文件")
        
    def on_drop(self, event):
        """处理文件拖拽"""
        files = self.root.tk.splitlist(event.data)
        if files and files[0].lower().endswith('.pdf'):
            self.input_var.set(files[0])
            self.input_file = files[0]
            self.auto_generate_output_filename()
            self.log_message(f"📁 已拖入文件: {files[0]}")
        
    def create_widgets(self):
        """创建GUI组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
        # 标题框架
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 标题
        title_label = ttk.Label(title_frame, text="📚 PDF自动书签工具", 
                               font=("Microsoft YaHei", 20, "bold"))
        title_label.pack()
        
        # 副标题
        subtitle_label = ttk.Label(title_frame, text="智能识别PDF目录结构，自动添加多层级书签 | AI语义过滤 + 表格内容过滤", 
                                  font=("Microsoft YaHei", 10), foreground="gray")
        subtitle_label.pack(pady=(5, 0))
        
        # 版本信息
        version_label = ttk.Label(title_frame, text="v2.0 - 混合架构版本", 
                                 font=("Microsoft YaHei", 8), foreground="blue")
        version_label.pack(pady=(2, 0))
        
        # 文件选择框架
        file_frame = ttk.LabelFrame(main_frame, text="📁 文件选择", padding="12")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        file_frame.columnconfigure(1, weight=1)
        
        # 输入文件选择
        ttk.Label(file_frame, text="📄 输入PDF文件:", font=("Microsoft YaHei", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(file_frame, textvariable=self.input_var, width=60, font=("Consolas", 9))
        self.input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(file_frame, text="浏览...", command=self.browse_input_file).grid(row=0, column=2, pady=5)
        
        # 拖拽提示
        drag_label = ttk.Label(file_frame, text="💡 提示: 可以直接将PDF文件拖拽到窗口中", 
                              font=("Microsoft YaHei", 8), foreground="green")
        drag_label.grid(row=1, column=0, columnspan=3, pady=(2, 5))
        
        # 输出文件选择
        ttk.Label(file_frame, text="💾 输出文件:", font=("Microsoft YaHei", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(file_frame, textvariable=self.output_var, width=60, font=("Consolas", 9))
        self.output_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(file_frame, text="浏览...", command=self.browse_output_file).grid(row=2, column=2, pady=5)
        
        # 高级选项框架
        options_frame = ttk.LabelFrame(main_frame, text="⚙️ 处理选项", padding="12")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(2, weight=1)
        
        # 字体大小过滤选项
        self.enable_font_filter_var = tk.BooleanVar(value=True)
        font_filter_cb = ttk.Checkbutton(options_frame, text="🔍 启用字体大小过滤（过滤非标题文本）", 
                        variable=self.enable_font_filter_var)
        font_filter_cb.grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # 表格内容过滤选项
        self.enable_table_filter_var = tk.BooleanVar(value=True)
        table_filter_cb = ttk.Checkbutton(options_frame, text="🚫 启用表格内容过滤（过滤表格中的编号）", 
                         variable=self.enable_table_filter_var)
        table_filter_cb.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # AI语义过滤选项
        self.enable_ai_filter_var = tk.BooleanVar(value=True)
        ai_filter_cb = ttk.Checkbutton(options_frame, text="🤖 启用AI语义过滤（使用GPT-4优化结构）", 
                      variable=self.enable_ai_filter_var)
        ai_filter_cb.grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # 手动设置字体大小阈值
        ttk.Label(options_frame, text="📏 字体大小阈值:", font=("Microsoft YaHei", 9)).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.font_threshold_var = tk.StringVar()
        threshold_entry = ttk.Entry(options_frame, textvariable=self.font_threshold_var, width=12)
        threshold_entry.grid(row=3, column=1, sticky=tk.W, padx=(10, 5), pady=5)
        ttk.Label(options_frame, text="（可选，留空则自动判断）", font=("Microsoft YaHei", 8), foreground="gray").grid(row=3, column=2, sticky=tk.W, pady=5)
        
        # 控制按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        # 开始处理按钮
        self.process_button = ttk.Button(button_frame, text="🚀 开始处理", 
                                        command=self.start_processing)
        self.process_button.pack(side=tk.LEFT, padx=10)
        
        # 清空按钮
        ttk.Button(button_frame, text="🗑️ 清空", command=self.clear_fields).pack(side=tk.LEFT, padx=5)
        
        # 打开文件夹按钮
        self.open_folder_button = ttk.Button(button_frame, text="📂 打开文件夹", 
                                           command=self.open_output_folder, state="disabled")
        self.open_folder_button.pack(side=tk.LEFT, padx=5)
        
        # 关于按钮
        ttk.Button(button_frame, text="ℹ️ 关于", command=self.show_about).pack(side=tk.LEFT, padx=5)
        
        # 退出按钮
        ttk.Button(button_frame, text="❌ 退出", command=self.root.quit).pack(side=tk.LEFT, padx=5)
        
        # 进度条框架
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          mode='indeterminate')
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # 进度标签
        self.progress_label = ttk.Label(progress_frame, text="", font=("Microsoft YaHei", 9))
        self.progress_label.grid(row=0, column=1)
        
        # 统计信息框架
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 统计标签
        self.stats_label = ttk.Label(stats_frame, text="", font=("Microsoft YaHei", 9), foreground="blue")
        self.stats_label.pack()
        
        # 日志输出区域
        log_frame = ttk.LabelFrame(main_frame, text="📋 处理日志", padding="8")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=18, width=100, 
                                                 font=("Consolas", 9), wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 添加右键菜单
        self.setup_context_menu()
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("📌 就绪 - 请选择PDF文件开始处理")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W, 
                              font=("Microsoft YaHei", 9))
        status_bar.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
    def setup_context_menu(self):
        """设置右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="复制", command=self.copy_log)
        self.context_menu.add_command(label="全选", command=self.select_all_log)
        self.context_menu.add_command(label="清空日志", command=self.clear_log)
        
        self.log_text.bind("<Button-3>", self.show_context_menu)
        
    def show_context_menu(self, event):
        """显示右键菜单"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
            
    def copy_log(self):
        """复制日志内容"""
        try:
            self.log_text.clipboard_clear()
            self.log_text.clipboard_append(self.log_text.selection_get())
        except tk.TclError:
            pass
            
    def select_all_log(self):
        """全选日志"""
        self.log_text.tag_add(tk.SEL, "1.0", tk.END)
        self.log_text.mark_set(tk.INSERT, "1.0")
        self.log_text.see(tk.INSERT)
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        
    def show_about(self):
        """显示关于对话框"""
        about_text = """PDF自动书签工具 v2.0

🎯 功能特性:
• 智能目录识别与多层级书签生成
• AI语义过滤 + 表格内容过滤
• 支持8层深度的复杂文档结构
• 现代化GUI界面与拖拽支持

🛠️ 技术架构:
• 传统规则 + AI语义的混合架构
• GPT-4驱动的智能过滤系统
• 严格的逻辑验证与错误处理

📧 作者: AI Assistant
📄 许可证: MIT License
🌐 项目地址: https://github.com/your-repo

感谢使用PDF自动书签工具！"""
        
        messagebox.showinfo("关于 PDF自动书签工具", about_text)
        
    def open_output_folder(self):
        """打开输出文件所在文件夹"""
        if self.output_file and os.path.exists(self.output_file):
            folder = os.path.dirname(self.output_file)
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":  # macOS
                os.system(f"open '{folder}'")
            else:  # Linux
                os.system(f"xdg-open '{folder}'")
        else:
            messagebox.showwarning("警告", "输出文件不存在！")
    
    def browse_input_file(self):
        """浏览输入文件"""
        file_path = filedialog.askopenfilename(
            title="选择PDF文件",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if file_path:
            self.input_var.set(file_path)
            self.input_file = file_path
            # 自动生成输出文件名
            if not self.output_var.get():
                self.auto_generate_output_filename()
    
    def browse_output_file(self):
        """浏览输出文件"""
        file_path = filedialog.asksaveasfilename(
            title="保存PDF文件",
            defaultextension=".pdf",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if file_path:
            self.output_var.set(file_path)
            self.output_file = file_path
    
    def auto_generate_output_filename(self):
        """自动生成输出文件名"""
        if self.input_file:
            input_path = Path(self.input_file)
            output_path = input_path.parent / f"{input_path.stem}_bookmarked{input_path.suffix}"
            self.output_var.set(str(output_path))
            self.output_file = str(output_path)
    
    def clear_fields(self):
        """清空所有字段"""
        self.input_var.set("")
        self.output_var.set("")
        self.input_file = ""
        self.output_file = ""
        self.font_threshold_var.set("")
        self.enable_font_filter_var.set(True)
        self.enable_table_filter_var.set(True)
        self.enable_ai_filter_var.set(True)
        self.log_text.delete(1.0, tk.END)
        self.status_var.set("📌 就绪 - 请选择PDF文件开始处理")
        self.progress_label.config(text="")
        self.stats_label.config(text="")
        self.open_folder_button.config(state="disabled")
    
    def log_message(self, message):
        """添加日志消息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def start_processing(self):
        """开始处理PDF文件"""
        # 验证输入
        if not self.input_var.get():
            messagebox.showerror("错误", "请选择输入PDF文件！")
            return
        
        if not self.output_var.get():
            messagebox.showerror("错误", "请指定输出文件路径！")
            return
        
        if not os.path.exists(self.input_var.get()):
            messagebox.showerror("错误", "输入文件不存在！")
            return
        
        # 检查输出目录是否存在
        output_dir = os.path.dirname(self.output_var.get())
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                self.log_message(f"📁 创建输出目录: {output_dir}")
            except Exception as e:
                messagebox.showerror("错误", f"无法创建输出目录: {e}")
                return
        
        # 禁用处理按钮
        self.process_button.config(state="disabled")
        self.progress_bar.start()
        self.status_var.set("⚙️ 正在处理...")
        self.progress_label.config(text="处理中...")
        self.open_folder_button.config(state="disabled")
        
        # 清空日志和统计信息
        self.log_text.delete(1.0, tk.END)
        self.stats_label.config(text="")
        
        # 在新线程中处理文件
        thread = threading.Thread(target=self.process_file)
        thread.daemon = True
        thread.start()
    
    def process_file(self):
        """在后台线程中处理PDF文件"""
        try:
            input_file = self.input_var.get()
            output_file = self.output_var.get()
            
            self.log_message(f"🚀 开始处理文件: {os.path.basename(input_file)}")
            self.log_message(f"📁 输入路径: {input_file}")
            self.log_message(f"💾 输出路径: {output_file}")
            self.log_message("=" * 80)
            
            # 创建PDF书签工具实例
            tool = PDFBookmarkTool(input_file)
            
            # 设置处理选项
            tool.enable_font_size_filter = self.enable_font_filter_var.get()
            self.log_message(f"🔍 字体大小过滤: {'✅ 启用' if tool.enable_font_size_filter else '❌ 禁用'}")
            
            # 设置手动字体大小阈值（如果有）
            if self.font_threshold_var.get().strip():
                try:
                    threshold = float(self.font_threshold_var.get())
                    tool.font_size_threshold = threshold
                    self.log_message(f"📏 手动设置字体大小阈值: {threshold}")
                except ValueError:
                    self.log_message("⚠️ 警告: 字体大小阈值格式不正确，将使用自动检测")
            
            # 记录处理选项
            table_filter_enabled = self.enable_table_filter_var.get()
            ai_filter_enabled = self.enable_ai_filter_var.get()
            self.log_message(f"🚫 表格内容过滤: {'✅ 启用' if table_filter_enabled else '❌ 禁用'}")
            self.log_message(f"🤖 AI语义过滤: {'✅ 启用' if ai_filter_enabled else '❌ 禁用'}")
            self.log_message("")
            
            # 重定向输出到GUI
            original_print = print
            def gui_print(*args, **kwargs):
                message = " ".join(str(arg) for arg in args)
                self.root.after(0, self.log_message, message)
            
            # 临时替换print函数
            import builtins
            builtins.print = gui_print
            
            try:
                # 打开PDF文件
                if not tool.open_pdf():
                    self.root.after(0, self.processing_complete, False, "无法打开PDF文件", None)
                    return
                
                # 查找目录条目
                self.root.after(0, self.log_message, "🔍 正在查找目录条目...")
                toc_entries = tool.find_toc_entries()
                if not toc_entries:
                    self.root.after(0, self.processing_complete, False, "未找到目录条目", None)
                    return
                
                original_count = len(toc_entries)
                self.root.after(0, self.log_message, f"📊 找到 {original_count} 个潜在目录条目")
                
                # 过滤重复条目
                self.root.after(0, self.log_message, "🧹 过滤重复条目...")
                toc_entries = tool.filter_duplicate_entries(toc_entries)
                after_dedup = len(toc_entries)
                
                # 条件性执行表格过滤
                if table_filter_enabled:
                    self.root.after(0, self.log_message, "🚫 过滤表格内容...")
                    toc_entries = tool.filter_table_and_prefix_entries(toc_entries)
                    after_table_filter = len(toc_entries)
                else:
                    after_table_filter = after_dedup
                    self.root.after(0, self.log_message, "⏭️ 跳过表格内容过滤")
                
                # 验证目录逻辑
                self.root.after(0, self.log_message, "✅ 验证目录逻辑...")
                toc_entries = tool.validate_toc_logic(toc_entries)
                after_validation = len(toc_entries)
                
                # 条件性执行AI语义过滤
                if ai_filter_enabled:
                    self.root.after(0, self.log_message, "🤖 AI语义过滤...")
                    # 这里需要修改tool的方法，使其支持条件性AI过滤
                    # 暂时保持原有逻辑
                    pass
                
                # 添加书签
                self.root.after(0, self.log_message, "📑 添加书签...")
                success, bookmark_stats = tool.add_bookmarks(toc_entries)
                
                if success:
                    # 保存文件
                    self.root.after(0, self.log_message, "💾 保存文件...")
                    save_success = tool.save_pdf(output_file)
                    if save_success:
                        # 合并统计信息
                        stats = {
                            'original': original_count,
                            'after_dedup': after_dedup,
                            'after_table_filter': after_table_filter,
                            'after_validation': after_validation,
                            'final': bookmark_stats.get('final', len(toc_entries))
                        }
                        # 如果有详细的书签处理统计，使用它们
                        if bookmark_stats:
                            stats.update(bookmark_stats)
                        
                        self.root.after(0, self.processing_complete, True, 
                                      f"✅ 处理完成！文件已保存到: {output_file}", stats)
                    else:
                        self.root.after(0, self.processing_complete, False, "书签添加成功但保存文件失败", None)
                else:
                    self.root.after(0, self.processing_complete, False, "添加书签失败", None)
                    
            finally:
                # 恢复原始print函数
                builtins.print = original_print
                tool.close_pdf()
                
        except Exception as e:
            error_msg = f"💥 处理过程中发生错误: {str(e)}"
            self.root.after(0, self.processing_complete, False, error_msg, None)
    
    def processing_complete(self, success, message, stats=None):
        """处理完成回调"""
        # 停止进度条
        self.progress_bar.stop()
        self.progress_label.config(text="")
        
        # 重新启用处理按钮
        self.process_button.config(state="normal")
        
        # 更新状态和统计信息
        if success:
            self.status_var.set("✅ 处理完成")
            self.log_message("=" * 80)
            self.log_message("✅ " + message)
            
            # 显示统计信息
            if stats:
                # 如果有详细的书签处理统计，显示完整流程
                if 'after_semantic_filter' in stats:
                    stats_text = (f"📊 处理统计: 原始 {stats['original']} → "
                                 f"去重 {stats['after_dedup']} → "
                                 f"表格过滤 {stats['after_table_filter']} → "
                                 f"逻辑验证 {stats['after_validation']} → "
                                 f"AI语义过滤 {stats['after_semantic_filter']} → "
                                 f"最终 {stats['final']} 个书签")
                else:
                    # 简化显示
                    stats_text = (f"📊 处理统计: 原始 {stats['original']} → "
                                 f"去重 {stats['after_dedup']} → "
                                 f"表格过滤 {stats['after_table_filter']} → "
                                 f"逻辑验证 {stats['after_validation']} → "
                                 f"最终 {stats['final']} 个书签")
                self.stats_label.config(text=stats_text)
                self.log_message(stats_text)
            
            # 启用打开文件夹按钮
            self.open_folder_button.config(state="normal")
            
            messagebox.showinfo("🎉 处理成功", message)
        else:
            self.status_var.set("❌ 处理失败")
            self.log_message("=" * 80)
            self.log_message("❌ " + message)
            self.stats_label.config(text="")
            messagebox.showerror("💥 处理失败", message)

def main():
    """主函数"""
    # 设置DPI感知（Windows）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # 创建主窗口（支持拖拽）
    try:
        from tkinterdnd2 import TkinterDnD
        root = TkinterDnD.Tk()
    except ImportError:
        # 如果没有tkinterdnd2，使用普通窗口
        root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('winnative')  # 使用Windows原生样式
    
    # 创建应用
    app = PDFBookmarkGUI(root)
    
    # 运行主循环
    root.mainloop()

if __name__ == "__main__":
    main() 