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
└── README.md           # 本文档
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

### macOS构建

**方法一：使用专用脚本（推荐）**
```bash
# 在macOS系统上运行
./scripts/build-mac.sh
```

**方法二：手动构建**
```bash
# 确保在macOS系统上运行
npm install
npm run build-mac
```

**注意事项**：
- Mac应用构建建议在macOS系统上进行，以确保最佳兼容性
- 需要icon.icns文件（脚本会自动从icon.png生成）
- 首次运行构建的应用时，可能需要在系统偏好设置中允许运行

### Linux构建

```bash
# 在任何系统上都可以构建Linux版本
npm install
npm run build-linux
```

### 跨平台构建

**使用快速开始脚本（全平台支持）**：

Windows用户：
```cmd
# 双击运行
快速开始.bat
```

macOS/Linux用户：
```bash
# 添加执行权限（首次运行）
chmod +x 快速开始.sh

# 运行脚本
./快速开始.sh
```

**手动构建所有平台**：
```bash
npm run build
```

### 🚀 自动化构建（GitHub Actions）

如果您的项目托管在GitHub上，可以使用自动化构建：

**功能特性**：
- ✅ 自动构建Windows、macOS、Linux三个平台
- ✅ 自动生成Mac图标文件（从PNG转换）
- ✅ 在推送代码或创建标签时自动触发
- ✅ 支持手动触发构建
- ✅ 自动创建Release并上传安装包

**使用方法**：
1. 确保项目已推送到GitHub
2. 创建标签触发Release构建：
   ```bash
   git tag v2.0.0
   git push origin v2.0.0
   ```
3. 或者在GitHub界面手动触发：
   - 进入Actions页面
   - 选择"构建跨平台应用"工作流
   - 点击"Run workflow"

**构建产物**：
- Windows: 在Actions的Artifacts中下载
- macOS: 自动生成.dmg安装包
- Linux: 生成AppImage便携应用

## 🖼️ 图标文件说明

不同平台需要不同格式的图标文件：

| 平台    | 文件名             | 格式 | 自动生成         |
| ------- | ------------------ | ---- | ---------------- |
| Windows | `assets/icon.ico`  | ICO  | ❌ 需手动准备     |
| macOS   | `assets/icon.icns` | ICNS | ✅ 从icon.png生成 |
| Linux   | `assets/icon.png`  | PNG  | ✅ 已存在         |

**Mac图标自动生成**：
- 构建脚本会自动检查是否存在`icon.icns`文件
- 如果不存在，会尝试从`icon.png`生成（需要macOS系统的`sips`和`iconutil`工具）
- 生成的图标包含所有必需的尺寸（16x16到1024x1024）

**Windows图标准备**：
- 需要手动创建`assets/icon.ico`文件
- 可以使用在线工具将PNG转换为ICO格式
- 推荐尺寸：16x16, 32x32, 48x48, 256x256

## 📦 打包输出

构建完成后，可执行文件将在 `dist/` 目录中：

- **Windows**: `PDF自动书签工具 Setup 2.0.0.exe` (安装包)
- **macOS**: `PDF自动书签工具-2.0.0.dmg` (磁盘映像)
- **Linux**: `PDF自动书签工具-2.0.0.AppImage` (便携应用)

## 🚨 构建故障排除

### 常见问题

**1. Mac构建失败**
```
Error: Application entry file "dist/electron/main.js" does not exist
```
**解决方案**：确保在macOS系统上运行，或使用GitHub Actions等CI服务

**2. Windows图标缺失警告**
```
Warning: icon.ico not found
```
**解决方案**：
- 下载PNG to ICO转换工具或使用在线服务
- 将`assets/icon.png`转换为`assets/icon.ico`
- 或临时注释掉package.json中的Windows图标配置

**3. Python依赖问题**
```
Error: Python script failed to run
```
**解决方案**：
- 确保Python已正确安装
- 在`python-backend`目录运行`pip install -r requirements.txt`
- 检查PyMuPDF等关键依赖是否安装成功

**4. 权限问题（macOS/Linux）**
```
Permission denied: ./快速开始.sh
```
**解决方案**：
```bash
chmod +x 快速开始.sh
chmod +x scripts/build-mac.sh
```

### 获得帮助

如果遇到其他构建问题：
1. 检查Node.js和npm版本是否满足要求
2. 清理node_modules并重新安装：`rm -rf node_modules && npm install`
3. 查看Electron Builder文档：https://www.electron.build/
4. 在项目Issues中搜索类似问题

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