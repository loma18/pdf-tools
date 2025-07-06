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
        self.root.title("PDF自动书签工具")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # 设置窗口图标（如果有的话）
        try:
            self.root.iconbitmap("icon.ico")  # 可选的图标文件
        except:
            pass
        
        # 创建主框架
        self.create_widgets()
        
        # 存储文件路径
        self.input_file = ""
        self.output_file = ""
        
    def create_widgets(self):
        """创建GUI组件"""
        # 主容器
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # 标题框架
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 标题
        title_label = ttk.Label(title_frame, text="📚 PDF自动书签工具", 
                               font=("Microsoft YaHei", 18, "bold"))
        title_label.pack()
        
        # 副标题
        subtitle_label = ttk.Label(title_frame, text="智能识别PDF目录结构，自动添加多层级书签", 
                                  font=("Microsoft YaHei", 10), foreground="gray")
        subtitle_label.pack(pady=(5, 0))
        
        # 文件选择框架
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        file_frame.columnconfigure(1, weight=1)
        
        # 输入文件选择
        ttk.Label(file_frame, text="📄 输入PDF文件:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(file_frame, textvariable=self.input_var, width=50)
        self.input_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(file_frame, text="浏览...", command=self.browse_input_file).grid(row=0, column=2, pady=5)
        
        # 输出文件选择
        ttk.Label(file_frame, text="💾 输出文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar()
        self.output_entry = ttk.Entry(file_frame, textvariable=self.output_var, width=50)
        self.output_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 5), pady=5)
        ttk.Button(file_frame, text="浏览...", command=self.browse_output_file).grid(row=1, column=2, pady=5)
        
        # 添加选项框架
        options_frame = ttk.LabelFrame(main_frame, text="处理选项", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        options_frame.columnconfigure(1, weight=1)
        
        # 字体大小过滤选项
        self.enable_font_filter_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="启用字体大小过滤（过滤非标题文本）", 
                        variable=self.enable_font_filter_var).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # 手动设置字体大小阈值
        ttk.Label(options_frame, text="字体大小阈值:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.font_threshold_var = tk.StringVar()
        threshold_entry = ttk.Entry(options_frame, textvariable=self.font_threshold_var, width=10)
        threshold_entry.grid(row=1, column=1, sticky=tk.W, padx=(10, 5), pady=5)
        ttk.Label(options_frame, text="（可选，留空则自动判断）").grid(row=1, column=2, sticky=tk.W, pady=5)
        
        # 控制按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        # 开始处理按钮
        self.process_button = ttk.Button(button_frame, text="🚀 开始处理", 
                                        command=self.start_processing, 
                                        style="Accent.TButton" if hasattr(ttk.Style(), 'theme_names') else None)
        self.process_button.pack(side=tk.LEFT, padx=10)
        
        # 清空按钮
        ttk.Button(button_frame, text="🗑️ 清空", command=self.clear_fields).pack(side=tk.LEFT, padx=5)
        
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
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.grid(row=0, column=1)
        
        # 日志输出区域
        log_frame = ttk.LabelFrame(main_frame, text="📋 处理日志", padding="5")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80, 
                                                 font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar()
        self.status_var.set("📌 就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W, 
                              font=("Microsoft YaHei", 9))
        status_bar.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
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
        self.log_text.delete(1.0, tk.END)
        self.status_var.set("📌 就绪")
        self.progress_label.config(text="")
    
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
        
        # 禁用处理按钮
        self.process_button.config(state="disabled")
        self.progress_bar.start()
        self.status_var.set("⚙️ 正在处理...")
        self.progress_label.config(text="处理中...")
        
        # 清空日志
        self.log_text.delete(1.0, tk.END)
        
        # 在新线程中处理文件
        thread = threading.Thread(target=self.process_file)
        thread.daemon = True
        thread.start()
    
    def process_file(self):
        """在后台线程中处理PDF文件"""
        try:
            input_file = self.input_var.get()
            output_file = self.output_var.get()
            
            self.log_message(f"开始处理文件: {input_file}")
            self.log_message(f"输出文件: {output_file}")
            self.log_message("=" * 50)
            
            # 创建PDF书签工具实例
            tool = PDFBookmarkTool(input_file)
            
            # 设置字体大小过滤选项
            tool.enable_font_size_filter = self.enable_font_filter_var.get()
            self.log_message(f"字体大小过滤: {'启用' if tool.enable_font_size_filter else '禁用'}")
            
            # 设置手动字体大小阈值（如果有）
            if self.font_threshold_var.get().strip():
                try:
                    threshold = float(self.font_threshold_var.get())
                    tool.font_size_threshold = threshold
                    self.log_message(f"手动设置字体大小阈值: {threshold}")
                except ValueError:
                    self.log_message("警告: 字体大小阈值格式不正确，将使用自动检测")
            
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
                    self.root.after(0, self.processing_complete, False, "无法打开PDF文件")
                    return
                
                # 查找目录条目
                toc_entries = tool.find_toc_entries()
                if not toc_entries:
                    self.root.after(0, self.processing_complete, False, "未找到目录条目")
                    return
                
                # 过滤重复条目
                toc_entries = tool.filter_duplicate_entries(toc_entries)
                
                # 验证目录逻辑
                toc_entries = tool.validate_toc_logic(toc_entries)
                
                # 添加书签
                success = tool.add_bookmarks(toc_entries)
                
                if success:
                    # 保存文件
                    save_success = tool.save_pdf(output_file)
                    if save_success:
                        self.root.after(0, self.processing_complete, True, f"处理完成！文件已保存到: {output_file}")
                    else:
                        self.root.after(0, self.processing_complete, False, "书签添加成功但保存文件失败")
                else:
                    self.root.after(0, self.processing_complete, False, "添加书签失败")
                    
            finally:
                # 恢复原始print函数
                builtins.print = original_print
                tool.close_pdf()
                
        except Exception as e:
            error_msg = f"处理过程中发生错误: {str(e)}"
            self.root.after(0, self.processing_complete, False, error_msg)
    
    def processing_complete(self, success, message):
        """处理完成回调"""
        # 停止进度条
        self.progress_bar.stop()
        self.progress_label.config(text="")
        
        # 重新启用处理按钮
        self.process_button.config(state="normal")
        
        # 更新状态
        if success:
            self.status_var.set("✅ 处理完成")
            self.log_message("=" * 50)
            self.log_message("✅ " + message)
            messagebox.showinfo("🎉 处理成功", message)
        else:
            self.status_var.set("❌ 处理失败")
            self.log_message("=" * 50)
            self.log_message("❌ " + message)
            messagebox.showerror("💥 处理失败", message)

def main():
    """主函数"""
    # 设置DPI感知（Windows）
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    # 创建主窗口
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