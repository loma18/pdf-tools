# 🐍 嵌入式Python使用指南

## 概述

PDF书签工具现在支持嵌入式Python环境！这意味着用户**无需单独安装Python**即可使用所有功能。

## ✨ 主要优势

### 🎯 用户体验
- **零配置**：下载即用，无需额外安装Python
- **一致性**：所有用户使用相同的Python环境
- **便携性**：应用完全自包含，可在任何机器上运行
- **兼容性**：自动处理不同操作系统的差异

### 🔧 技术优势
- **稳定性**：避免系统Python版本冲突
- **依赖管理**：自动安装所需的Python包
- **版本控制**：确保Python和包版本一致
- **部署简化**：减少部署复杂性

## 🏗️ 技术实现

### 使用的技术栈
- **portable-python**：基于 python-build-standalone
- **Python 3.11**：稳定且功能完整的版本
- **PyMuPDF**：PDF处理核心库
- **自动依赖安装**：首次使用时自动安装必要包

### 工作原理

1. **优先级策略**：
   ```
   嵌入式Python (第一优先) → 系统Python (备用)
   ```

2. **路径解析**：
   - 开发环境：`node_modules/@bjia56/portable-python-3.11/`
   - 打包环境：`app.asar.unpacked/portable-python/`

3. **依赖管理**：
   - 检查依赖是否已安装
   - 自动安装 PyMuPDF 和 python-dotenv
   - 仅对嵌入式Python执行（系统Python跳过）

## 📦 构建和部署

### 开发环境设置

```bash
# 1. 安装项目依赖
npm install

# 2. 设置嵌入式Python
npm run setup-python

# 3. 启动开发模式
npm run dev
```

### 生产构建

```bash
# 方法一：一键构建（推荐）
npm run build-with-python

# 方法二：分步构建
npm run setup-python
npm run build
```

### 构建配置详解

```json
{
  "extraResources": [
    {
      "from": "python-backend/",
      "to": "python-backend/"
    },
    {
      "from": "node_modules/@bjia56/portable-python-3.11/",
      "to": "portable-python/"
    }
  ]
}
```

## 🔍 诊断和调试

### 使用内置诊断工具

1. 打开应用
2. 点击底部"环境诊断"按钮
3. 查看详细的环境信息：
   - 嵌入式Python状态
   - 当前使用的Python类型
   - 文件路径和存在性检查
   - 状态总结和建议

### 诊断信息解读

#### 🔗 嵌入式Python
- **✅ 可用**：嵌入式Python已正确安装
- **⚠️ 不可用**：回退到系统Python
- **❌ 损坏**：需要重新安装应用

#### 🖥️ 当前Python环境
- **🔗 嵌入式**：使用内置Python（推荐）
- **🖥️ 系统**：使用系统安装的Python

## 🚀 功能对比

| 功能 | 传统模式 | 嵌入式模式 |
|------|----------|------------|
| 用户安装 | 需要安装Python | 无需安装 |
| 环境一致性 | 可能不一致 | 完全一致 |
| 依赖管理 | 手动安装 | 自动处理 |
| 版本冲突 | 可能发生 | 完全避免 |
| 便携性 | 有限 | 完全便携 |
| 启动速度 | 快 | 稍慢（首次） |
| 文件大小 | 小 | 较大（~50MB） |

## 📊 性能和资源

### 文件大小影响
- **增加大小**：约 50-80MB（取决于平台）
- **打包时间**：增加 30-60 秒
- **下载时间**：取决于网络速度

### 运行时性能
- **首次启动**：依赖安装需要 10-30 秒
- **后续启动**：与原版本相近
- **内存使用**：增加约 20-40MB
- **处理速度**：与系统Python相同

## 🛠️ 开发者选项

### 强制使用系统Python

在开发过程中，如果需要强制使用系统Python：

```javascript
// 在 main.js 中临时注释嵌入式Python检查
function getEmbeddedPythonPath() {
  return null; // 强制使用系统Python
}
```

### 自定义Python版本

要使用不同版本的Python：

```bash
# 卸载当前版本
npm uninstall @bjia56/portable-python-3.11

# 安装其他版本
npm install @bjia56/portable-python-3.12
```

然后更新 `main.js` 中的 require 路径。

## 🔧 故障排除

### 常见问题

#### Q: 嵌入式Python不工作怎么办？
A: 
1. 检查诊断信息
2. 重新运行 `npm run setup-python`
3. 重新构建应用
4. 如果仍有问题，应用会自动回退到系统Python

#### Q: 应用启动很慢
A: 
首次启动时需要安装Python依赖，这是正常的。后续启动会快很多。

#### Q: 如何验证嵌入式Python正在使用？
A: 
1. 打开诊断工具
2. 查看"当前Python环境"
3. 类型显示"🔗 嵌入式"即为正确

#### Q: 能否禁用嵌入式Python？
A: 
目前不支持运行时禁用，但会在嵌入式Python不可用时自动回退。

### 调试模式

启用详细日志：

```bash
# 设置环境变量
export DEBUG_PYTHON=true

# 启动应用
npm run dev
```

## 📋 版本兼容性

### 支持的平台
- **Windows**: x64, ia32
- **macOS**: x64, arm64 (Apple Silicon)
- **Linux**: x64, arm64

### Python版本
- **当前**: Python 3.11.x
- **计划**: 支持 Python 3.12+

### 依赖版本
- **PyMuPDF**: 最新稳定版
- **python-dotenv**: 最新稳定版

## 🎯 最佳实践

### 开发建议
1. 始终使用 `npm run build-with-python` 构建
2. 定期更新 portable-python 包
3. 在不同平台上测试构建结果
4. 使用诊断工具验证功能

### 部署建议
1. 在CI/CD中包含Python设置步骤
2. 测试自动依赖安装功能
3. 验证跨平台兼容性
4. 监控应用启动时间

## 📚 相关资源

- [portable-python 项目](https://github.com/bjia56/portable-python)
- [python-build-standalone](https://github.com/indygreg/python-build-standalone)
- [Electron Builder 文档](https://www.electron.build/)
- [PyMuPDF 文档](https://pymupdf.readthedocs.io/)

---

**最后更新**: 2024年12月  
**版本要求**: PDF书签工具 v3.2.0+ 