# PDF自动书签工具 - 详细使用说明

## 📖 目录
- [快速开始](#快速开始)
- [功能详解](#功能详解)
- [配置选项](#配置选项)
- [常见问题](#常见问题)
- [高级用法](#高级用法)
- [故障排除](#故障排除)

## 🚀 快速开始

### 1. 环境准备
确保您的系统满足以下要求：
- Python 3.7 或更高版本
- Windows/macOS/Linux 操作系统

### 2. 安装依赖
```bash
# 自动安装（推荐）
python start_gui.py

# 手动安装
pip install -r requirements.txt
```

### 3. 启动程序
```bash
# GUI界面（推荐新手）
python start_gui.py
# 或双击 run_gui.bat (Windows)

# 命令行界面（适合批量处理）
python pdf_bookmark_tool.py input.pdf -o output.pdf
```

## 🔧 功能详解

### 智能目录识别
工具能够自动识别以下格式的目录：

#### 数字编号格式
```
1. 第一章
1.1 第一节
1.1.1 子节
1.1.1.1 子子节（支持8层深度）
```

#### 中文格式
```
第一章 标题
第一节 标题
一、标题
二、标题
（1）标题
（2）标题
```

#### 字母和罗马数字
```
I. 标题
II. 标题
A. 标题
B. 标题
a) 标题
b) 标题
```

### AI语义过滤系统
- **智能识别**：区分真实标题与普通文本
- **表格过滤**：自动排除表格中的编号内容
- **语义理解**：基于GPT-4的深度语义分析
- **结构优化**：自动调整书签层级结构

### 严格逻辑验证
- **连续性检查**：确保章节编号连续
- **层级验证**：验证父子关系的逻辑性
- **排序检查**：确保同级标题按序排列

## ⚙️ 配置选项

### GUI界面选项

#### 基础设置
- **输入文件**：选择要处理的PDF文件
- **输出文件**：指定处理后的文件保存位置

#### 高级选项
- **字体大小过滤**：根据字体大小筛选标题
- **表格内容过滤**：排除表格中的编号文本
- **AI语义过滤**：使用人工智能优化结构
- **字体大小阈值**：手动设置字体筛选标准

### 命令行参数
```bash
python pdf_bookmark_tool.py [选项] 输入文件

选项：
  -o, --output PATH        输出文件路径
  --font-threshold FLOAT   字体大小阈值
  -h, --help              显示帮助信息
```

## 💡 使用技巧

### 1. 选择合适的字体阈值
- **自动模式**：让程序自动分析（推荐）
- **手动设置**：根据文档特点调整
  - 学术论文：通常 12-14
  - 技术手册：通常 10-12
  - 报告文档：通常 11-13

### 2. 优化处理效果
- **预处理**：确保PDF文本可选择（非扫描版）
- **清理**：移除不必要的页眉页脚
- **检查**：验证目录结构的逻辑性

### 3. 批量处理
```bash
# 处理多个文件
for file in *.pdf; do
    python pdf_bookmark_tool.py "$file"
done
```

## ❓ 常见问题

### Q1: 为什么没有识别到目录？
**可能原因：**
- PDF是扫描版，需要OCR处理
- 目录格式不标准
- 字体大小阈值设置不当

**解决方案：**
- 使用OCR软件转换扫描版PDF
- 调整字体大小阈值
- 检查目录是否符合支持格式

### Q2: 书签层级不正确怎么办？
**可能原因：**
- 原文档目录结构不规范
- AI过滤过于严格

**解决方案：**
- 禁用AI语义过滤试试
- 手动调整字体阈值
- 检查原文档的目录编号

### Q3: 处理速度很慢怎么办？
**可能原因：**
- 文档页数过多
- 网络连接影响AI处理

**解决方案：**
- 禁用AI语义过滤加快速度
- 检查网络连接
- 分段处理大型文档

### Q4: 无法保存文件怎么办？
**可能原因：**
- 输出目录不存在
- 文件被其他程序占用
- 权限不足

**解决方案：**
- 检查输出路径是否正确
- 关闭占用文件的程序
- 以管理员权限运行

## 🔬 高级用法

### 1. 自定义过滤规则
修改 `pdf_bookmark_tool.py` 中的过滤逻辑：
```python
# 自定义表格检测规则
def custom_table_filter(self, title):
    # 添加您的自定义逻辑
    return False  # 返回True表示过滤掉
```

### 2. 批量处理脚本
```python
import os
from pdf_bookmark_tool import PDFBookmarkTool

def batch_process(input_dir, output_dir):
    for filename in os.listdir(input_dir):
        if filename.endswith('.pdf'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"{filename[:-4]}_bookmarked.pdf")
            
            tool = PDFBookmarkTool(input_path)
            if tool.process_pdf(output_path):
                print(f"✅ 处理完成: {filename}")
            else:
                print(f"❌ 处理失败: {filename}")
```

### 3. API集成
```python
from pdf_bookmark_tool import PDFBookmarkTool

# 创建工具实例
tool = PDFBookmarkTool("input.pdf")

# 自定义配置
tool.enable_font_size_filter = True
tool.font_size_threshold = 12.0

# 处理文档
if tool.process_pdf("output.pdf"):
    print("处理成功")
```

## 🛠️ 故障排除

### 安装问题
```bash
# 清理缓存重新安装
pip cache purge
pip install -r requirements.txt --force-reinstall

# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/
```

### 运行时错误
```bash
# 检查Python版本
python --version

# 检查依赖版本
pip list | grep -E "(PyMuPDF|pdfplumber|requests)"

# 重新安装核心依赖
pip install --upgrade PyMuPDF pdfplumber
```

### 内存问题
对于大型PDF文件：
- 增加系统虚拟内存
- 分页处理大文档
- 关闭其他占用内存的程序

## 📞 技术支持

如果您遇到问题：
1. 查看日志输出的详细错误信息
2. 检查是否符合系统要求
3. 尝试使用不同的配置选项
4. 提供错误信息和文档样本以获得帮助

## 📈 性能优化建议

### 提升处理速度
- 对于大批量处理，禁用AI语义过滤
- 使用SSD存储提高文件读写速度
- 确保充足的系统内存

### 提升准确性
- 启用所有过滤选项
- 根据文档类型调整字体阈值
- 预处理文档以规范格式

---

**祝您使用愉快！如有问题，欢迎反馈。** 📚✨ 