# 🚀 自动发布功能指南

## 📋 功能概述

本项目已配置自动发布功能，当您推送带有版本标签的代码时，GitHub Actions会自动构建并发布到GitHub Releases。

## 🔧 配置步骤

### 1. 设置GitHub Personal Access Token

1. **创建Token**：
   - 访问 [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
   - 点击 "Generate new token (classic)"
   - 设置名称：`PDF Tools Auto Release`
   - 选择权限：
     - ✅ `repo` (完整仓库访问)
     - ✅ `workflow` (工作流权限)
   - 生成并复制Token

2. **添加到仓库Secrets**：
   - 进入您的仓库 → Settings → Secrets and variables → Actions
   - 点击 "New repository secret"
   - 名称：`BUILDACTION`
   - 值：粘贴刚才复制的Token
   - 点击 "Add secret"

### 2. 发布新版本

#### 方法一：使用Git命令
```bash
# 1. 更新版本号（在package.json中）
# 2. 提交更改
git add .
git commit -m "准备发布v2.1.0"

# 3. 创建并推送标签
git tag v2.1.0
git push origin v2.1.0

# 4. 推送代码
git push origin main
```

#### 方法二：使用GitHub界面
1. 在GitHub仓库页面点击 "Releases"
2. 点击 "Create a new release"
3. 选择 "Choose a tag" → "Create new tag"
4. 输入版本号（如：v2.1.0）
5. 填写Release标题和描述
6. 点击 "Publish release"

## 🔄 自动发布流程

### 触发条件
- 推送标签格式：`v*` (如 v1.0.0, v2.1.0)
- 推送分支：`main` 或 `master`

### 构建平台
- ✅ **Windows**: 生成 `.exe` 安装程序
- ✅ **macOS**: 生成 `.dmg` 安装包
- ✅ **Linux**: 生成 `.AppImage` 应用

### 发布内容
- 📦 所有平台的安装包
- 📝 自动生成的Release Notes
- 🔗 下载链接

## 📊 监控发布状态

1. **查看Actions**：
   - 进入仓库 → Actions 标签
   - 查看最新的工作流运行状态

2. **查看Releases**：
   - 进入仓库 → Releases
   - 查看已发布的版本和下载统计

## 🛠️ 故障排除

### 常见问题

**1. Token权限不足**
```
Error: GitHub Personal Access Token is not set
```
- 检查 `BUILDACTION` secret是否正确设置
- 确认Token有足够的权限（repo, workflow）

**2. 构建失败**
- 检查Actions日志中的具体错误信息
- 确认所有依赖都已正确安装

**3. 发布失败**
- 检查网络连接
- 确认GitHub API限制未超限

### 调试命令

```bash
# 本地测试构建
yarn build-win    # Windows
yarn build-mac    # macOS (仅在macOS上)
yarn build-linux  # Linux

# 检查构建产物
ls -la dist/
```

## 📝 版本管理建议

### 版本号格式
- 使用语义化版本：`主版本.次版本.修订版本`
- 示例：`v1.0.0`, `v2.1.3`

### 发布频率
- 🚀 **正式版**: 功能完整时发布
- 🧪 **测试版**: 可添加 `-beta` 后缀
- 🔧 **热修复**: 紧急修复时快速发布

### Release Notes模板
```markdown
## 🎉 新功能
- 功能1描述
- 功能2描述

## 🔧 修复
- 修复1描述
- 修复2描述

## 📦 技术改进
- 改进1描述
- 改进2描述
```

## 🔐 安全注意事项

- ⚠️ 不要将Token提交到代码中
- 🔄 定期更新Token（建议90天）
- 🚫 如果Token泄露，立即撤销并重新生成
- 📋 只给Token必要的权限

## 📞 支持

如果遇到问题，请：
1. 检查GitHub Actions日志
2. 查看本指南的故障排除部分
3. 在Issues中报告问题 