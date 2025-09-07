# 新增功能说明

## 功能概述

PDF书签工具现在支持三种处理模式：

1. **自动加书签** - 原有的自动识别PDF标题并生成书签功能
2. **书签文件辅助加书签** - 使用现有的书签文件来为PDF添加书签
3. **Markdown辅助加书签** - 从Markdown文件中解析标题结构，自动生成带数字前缀的书签

## 界面变化

### 新增Tab
- 在原有的"自动加书签"和"自动提取书签"之间新增了两个tab：
  - "书签文件辅助加书签"
  - "markdown辅助加书签"

### 自动加书签Tab优化
- 移除了"书签文件（可选）"选项，简化了界面

## 新功能详细说明

### 1. 书签文件辅助加书签

**用途**：使用现有的书签文件来为PDF添加书签

**输入要求**：
- PDF文件（必填）
- 输出文件路径（必填）
- 书签文件（必填）

**支持的书签文件格式**：
- JSON格式
- TXT格式
- CSV格式

**使用场景**：
- 当您已经有一个结构化的书签文件时
- 需要精确控制书签的标题和层级时
- 批量处理多个PDF文件时

### 2. Markdown辅助加书签

**用途**：从Markdown文件中解析标题结构，自动生成带数字前缀的书签

**输入要求**：
- PDF文件（必填）
- 输出文件路径（必填）
- Markdown文件（必填）

**Markdown解析规则**：
- `# 标题` → `1 标题` (级别1)
- `## 标题` → `1.1 标题` (级别2)
- `### 标题` → `1.1.1 标题` (级别3)
- 依此类推...

**预览功能**：
- 选择Markdown文件后，会自动显示解析的标题结构预览
- 预览区域会显示每个标题的完整标题、数字前缀和级别

**使用场景**：
- 当您有Markdown格式的文档大纲时
- 需要将文档结构转换为PDF书签时
- 学术论文、技术文档等结构化文档处理

## 技术实现

### 后端支持
- 新增了`--bookmark-file-assisted`和`--markdown-assisted`命令行参数
- 新增了`--parse-markdown`参数用于仅解析Markdown文件
- 支持JSON格式的Markdown解析结果输出

### 前端界面
- 新增了完整的UI界面支持
- 实现了文件选择、预览、处理等功能
- 支持实时日志显示和进度跟踪

### API集成
- 新增了`parse-markdown-file` API用于Markdown文件解析
- 修改了`process-pdf` API以支持新的处理模式
- 保持了向后兼容性

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

1. 打开应用程序
2. 选择相应的tab（书签文件辅助加书签 或 markdown辅助加书签）
3. 选择PDF文件
4. 选择书签文件或Markdown文件
5. 指定输出文件路径
6. 点击"开始处理"

## 注意事项

1. **文件格式**：确保书签文件格式正确，Markdown文件使用标准的标题语法
2. **文件路径**：所有文件路径都支持中文和特殊字符
3. **处理时间**：根据PDF文件大小和书签数量，处理时间可能有所不同
4. **错误处理**：如果处理失败，请查看日志输出获取详细错误信息

## 更新日志

- ✅ 新增书签文件辅助加书签功能
- ✅ 新增Markdown辅助加书签功能
- ✅ 新增Markdown解析预览功能
- ✅ 优化自动加书签界面
- ✅ 完善错误处理和日志显示
- ✅ 保持向后兼容性
