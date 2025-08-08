# PDF自动书签工具 - Electron桌面版

## 🚀 项目概述

这是PDF自动书签工具的Electron桌面版本，提供现代化的图形界面和跨平台支持。用户无需安装Python环境，即可直接使用打包好的可执行文件。

## ✨ 特性

- 🖥️ **现代化界面** - 基于Web技术的美观用户界面
- 📦 **开箱即用** - 无需安装Python，内置所有依赖
- 🔄 **拖拽支持** - 支持拖拽PDF文件到应用窗口
- 📊 **实时进度** - 显示处理进度和详细日志
- 🌐 **跨平台** - 支持Windows、macOS和Linux
- ⚡ **高性能** - 基于Electron和Node.js

## 📁 项目结构

```
pdf-tools/
├── src/                          # Electron源代码
│   ├── main.js                   # 主进程
│   └── renderer/                 # 渲染进程
│       ├── index.html           # 主界面
│       ├── styles.css           # 样式文件
│       └── renderer.js          # 前端逻辑
├── python-backend/               # Python后端
│   ├── pdf_bookmark_tool.py     # 核心处理引擎
│   └── requirements.txt         # Python依赖
├── assets/                       # 资源文件
│   └── icon.png                 # 应用图标
├── scripts/                      # 构建脚本
│   └── build.bat                # Windows构建脚本
├── package.json                 # Node.js配置
├── build-setup.js               # 构建准备脚本
└── ELECTRON_README.md           # 本文档
```

## 🛠️ 开发环境设置

### 前提条件

1. **Node.js** (v16或更高版本)
2. **Python** (v3.7或更高版本)
3. **Git** (可选，用于版本控制)

### 安装步骤

1. **克隆或下载项目**
   ```bash
   git clone <repository-url>
   cd pdf-tools
   ```

2. **安装Node.js依赖**
   ```bash
   npm install
   ```

3. **安装Python依赖**
   ```bash
   cd python-backend
   pip install -r requirements.txt
   cd ..
   ```

4. **运行开发版本**
   ```bash
   npm run dev
   ```

## 🏗️ 构建可执行文件

### Windows构建

**方法一：使用批处理脚本（推荐）**
```bash
# 双击运行或在命令行执行
scripts\build.bat
```

**方法二：手动构建**
```bash
# 安装依赖
npm install

# 构建Windows版本
npm run build-win
```

### 其他平台构建

```bash
# macOS
npm run build-mac

# Linux
npm run build-linux

# 所有平台
npm run build
```

## 📦 打包输出

构建完成后，可执行文件将在 `dist/` 目录中：

- **Windows**: `PDF自动书签工具 Setup 2.0.0.exe` (安装包)
- **macOS**: `PDF自动书签工具-2.0.0.dmg` (磁盘映像)
- **Linux**: `PDF自动书签工具-2.0.0.AppImage` (便携应用)

## 🎯 使用方法

### 开发模式
```bash
npm run dev
```

### 生产模式
```bash
npm start
```

### 构建发布版
```bash
npm run build
```

## 🔧 配置选项

### Electron Builder配置

在 `package.json` 中的 `build` 字段可以配置：

- **应用信息** - 名称、版本、描述
- **图标设置** - 不同平台的图标文件
- **打包选项** - 输出格式、架构支持
- **安装程序** - NSIS配置、快捷方式等

### 主要配置项

```json
{
  "build": {
    "appId": "com.pdftools.bookmark",
    "productName": "PDF自动书签工具",
    "win": {
      "target": "nsis",
      "icon": "assets/icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true,
      "createDesktopShortcut": true
    }
  }
}
```

## 🐛 故障排除

### 常见问题

1. **构建失败 - 缺少Python**
   ```
   解决方案：确保系统已安装Python 3.7+并添加到PATH
   ```

2. **依赖安装失败**
   ```bash
   # 清除缓存重新安装
   npm cache clean --force
   rm -rf node_modules
   npm install
   ```

3. **Python后端无法运行**
   ```bash
   # 检查Python依赖
   cd python-backend
   pip install -r requirements.txt
   python pdf_bookmark_tool.py --help
   ```

4. **图标不显示**
   ```
   解决方案：确保assets/目录下有正确格式的图标文件
   - Windows: icon.ico
   - macOS: icon.icns  
   - Linux: icon.png
   ```

### 调试模式

启用开发者工具进行调试：
```bash
npm run dev
```

## 📋 开发指南

### 添加新功能

1. **前端功能** - 修改 `src/renderer/` 下的文件
2. **后端功能** - 修改 `python-backend/` 下的Python脚本
3. **主进程功能** - 修改 `src/main.js`

### IPC通信

前端与主进程通过IPC通信：

```javascript
// 渲染进程 -> 主进程
const result = await ipcRenderer.invoke('process-pdf', options);

// 主进程 -> 渲染进程
mainWindow.webContents.send('process-output', data);
```

### 样式自定义

修改 `src/renderer/styles.css` 来自定义界面样式。

## 🚀 部署发布

### 发布检查清单

- [ ] 更新版本号 (`package.json`)
- [ ] 测试所有功能
- [ ] 检查图标文件
- [ ] 构建所有目标平台
- [ ] 测试安装包
- [ ] 准备发布说明

### 自动化发布

可以配置GitHub Actions或其他CI/CD工具自动构建和发布：

```yaml
# .github/workflows/build.yml
name: Build and Release
on:
  push:
    tags:
      - 'v*'
jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '16'
      - run: npm install
      - run: npm run build
```

## 📄 许可证

本项目采用MIT许可证。详见LICENSE文件。

## 🤝 贡献

欢迎提交问题报告和功能请求！如果您想贡献代码：

1. Fork本项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📞 支持

如有问题或需要帮助，请：

1. 查看本文档的故障排除部分
2. 搜索已有的Issues
3. 创建新的Issue描述问题

---

**开发团队**: PDF Tools Team  
**最后更新**: 2024年1月 