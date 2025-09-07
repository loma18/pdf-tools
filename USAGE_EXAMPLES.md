# PDF书签工具使用示例

## 新增功能

### 1. 书签文件辅助加书签模式

使用现有的书签文件来为PDF添加书签，PDF文件和书签文件都是必填项。

```bash
# 使用JSON格式的书签文件
python python-backend/pdf_bookmark_tool.py input.pdf --bookmark-file-assisted --bookmark-file bookmarks.json -o output.pdf

# 使用TXT格式的书签文件
python python-backend/pdf_bookmark_tool.py input.pdf --bookmark-file-assisted --bookmark-file bookmarks.txt -o output.pdf

# 使用CSV格式的书签文件
python python-backend/pdf_bookmark_tool.py input.pdf --bookmark-file-assisted --bookmark-file bookmarks.csv -o output.pdf
```

### 2. Markdown辅助加书签模式

从Markdown文件中解析标题结构，自动生成带数字前缀的书签，PDF文件和Markdown文件都是必填项。

```bash
# 使用Markdown文件生成书签
python python-backend/pdf_bookmark_tool.py input.pdf --markdown-assisted --markdown-file content.md -o output.pdf
```

#### Markdown解析示例

对于以下Markdown内容：
```markdown
# 标题1
## 标题test
## 标题test2
# 标题啊
## 标题66
```

会自动解析为：
- `1 标题1` (级别1)
- `1.1 标题test` (级别2)
- `1.2 标题test2` (级别2)
- `2 标题啊` (级别1)
- `2.1 标题66` (级别2)

### 3. 自动加书签模式（原有功能）

原有的自动书签功能保持不变，但已移除"书签文件（可选）"选项。

```bash
# 自动识别PDF中的标题并添加书签
python python-backend/pdf_bookmark_tool.py input.pdf -o output.pdf
```

## 书签文件格式

### JSON格式
```json
[
  {"title": "第一章", "level": 1, "page": 1},
  {"title": "1.1 概述", "level": 2, "page": 5},
  {"title": "1.2 背景", "level": 2, "page": 10}
]
```

### TXT格式
```
第一章
1.1 概述
1.2 背景
```

### CSV格式
```csv
title,level,page
第一章,1,1
1.1 概述,2,5
1.2 背景,2,10
```

## 其他功能

### 提取现有书签
```bash
# 提取PDF中的现有书签
python python-backend/pdf_bookmark_tool.py input.pdf --extract-only --format json -o bookmarks.json
```

### 调试模式
```bash
# 启用调试模式查看详细信息
python python-backend/pdf_bookmark_tool.py input.pdf --debug -o output.pdf
```
