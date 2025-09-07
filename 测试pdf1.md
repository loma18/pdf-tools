# 

# 新增功能说明

## 功能概述

1.  PDF书签工具现在支持三种处理模式：
    
2.  **自动加书签** - 原有的自动识别PDF标题并生成书签功能
    
3.  **书签文件辅助加书签** - 使用现有的书签文件来为PDF添加书签
    
4.  **Markdown辅助加书签** - 从Markdown文件中解析标题结构，自动生成带数字前缀的书签
    

## 界面变化

### 新增Tab

5.  在原有的"自动加书签"和"自动提取书签"之间新增了两个tab：
    
    1.  "书签文件辅助加书签"
        
    2.  "markdown辅助加书签"
        

### 自动加书签Tab优化

6.  移除了"书签文件（可选）"选项，简化了界面
    

## 新功能详细说明

### 1. 书签文件辅助加书签

7.  **用途**：使用现有的书签文件来为PDF添加书签
    
8.  **输入要求**：
    
9.  PDF文件（必填）
    
10.  输出文件路径（必填）
    
11.  书签文件（必填）
    
12.  **支持的书签文件格式**：
    
13.  JSON格式
    
14.  TXT格式
    
15.  CSV格式
    
16.  **使用场景**：
    
17.  当您已经有一个结构化的书签文件时
    
18.  需要精确控制书签的标题和层级时
    
19.  批量处理多个PDF文件时


### 2. Markdown辅助加书签

20.  **用途**：从Markdown文件中解析标题结构，自动生成带数字前缀的书签
    
21.  **输入要求**：
    
22.  PDF文件（必填）
    
23.  输出文件路径（必填）
    
24.  Markdown文件（必填）
    
25.  **Markdown解析规则**：
    
26.  `# 标题` → `1 标题` (级别1)
    
27.  `## 标题` → `1.1 标题` (级别2)
    
28.  `### 标题` → `1.1.1 标题` (级别3)
    
29.  依此类推...
    
30.  **预览功能**：
    
31.  选择Markdown文件后，会自动显示解析的标题结构预览
    
32.  预览区域会显示每个标题的完整标题、数字前缀和级别
    
33.  **使用场景**：
    
34.  当您有Markdown格式的文档大纲时
    
35.  需要将文档结构转换为PDF书签时
    
36.  学术论文、技术文档等结构化文档处理


## 技术实现

### 后端支持

37.  新增了`--bookmark-file-assisted`和`--markdown-assisted`命令行参数
    
38.  新增了`--parse-markdown`参数用于仅解析Markdown文件
    
39.  支持JSON格式的Markdown解析结果输出


### 前端界面

40.  新增了完整的UI界面支持
    
41.  实现了文件选择、预览、处理等功能
    
42.  支持实时日志显示和进度跟踪


### API集成

43.  新增了`parse-markdown-file` API用于Markdown文件解析
    
44.  修改了`process-pdf` API以支持新的处理模式
    
45.  保持了向后兼容性


## 使用示例

### 命令行使用

```bash
# 书签文件辅助加书签
python python-backend/pdf_bookmark_tool.py input.pdf --bookmark-file-assisted --bookmark-file bookmarks.json -o output.pdf

# markdown辅助加书签
python python-backend/pdf_bookmark_tool.py input.pdf --markdown-assisted --markdown-file content.md -o output.pdf

# 仅解析Markdown文件
python python-backend/pdf_bookmark_tool.py --parse-markdown content.md

```

### 图形界面使用

46.  打开应用程序
    
47.  选择相应的tab（书签文件辅助加书签 或 markdown辅助加书签）
    
48.  选择PDF文件
    
49.  选择书签文件或Markdown文件
    
50.  指定输出文件路径
    
51.  点击"开始处理"


## 注意事项

52.  **文件格式**：确保书签文件格式正确，Markdown文件使用标准的标题语法
    
53.  **文件路径**：所有文件路径都支持中文和特殊字符
    
54.  **处理时间**：根据PDF文件大小和书签数量，处理时间可能有所不同
    
55.  **错误处理**：如果处理失败，请查看日志输出获取详细错误信息


## 更新日志

56.  ✅ 新增书签文件辅助加书签功能
    
57.  ✅ 新增Markdown辅助加书签功能
    
58.  ✅ 新增Markdown解析预览功能
    
59.  ✅ 优化自动加书签界面
    
60.  ✅ 完善错误处理和日志显示
    
61.  ✅ 保持向后兼容性