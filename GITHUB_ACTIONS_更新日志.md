# GitHub Actions 更新日志

## 2024年修复 - Actions版本更新

### 🐛 问题描述
GitHub Actions构建失败，报错：
```
Error: This request has been automatically failed because it uses a deprecated version of `actions/upload-artifact: v3`
```

### ✅ 解决方案
更新所有已废弃的GitHub Actions到最新版本：

| Action | 旧版本 | 新版本 | 更新原因 |
|--------|--------|--------|----------|
| `actions/upload-artifact` | v3 | v4 | v3已废弃 |
| `actions/download-artifact` | v3 | v4 | v3已废弃 |
| `actions/setup-python` | v4 | v5 | 推荐使用最新版 |
| `softprops/action-gh-release` | v1 | v2 | 更好的稳定性 |

### 🔧 主要更改

**1. 上传构建产物** (upload-artifact@v4)
```yaml
- name: 📤 上传构建产物
  uses: actions/upload-artifact@v4  # 从v3升级
  if: success()
  with:
    name: ${{ matrix.artifact_name }}
    path: ${{ matrix.artifact_pattern }}
    retention-days: 30
```

**2. 下载构建产物** (download-artifact@v4)
```yaml
- name: 📥 下载所有构建产物
  uses: actions/download-artifact@v4  # 从v3升级
  with:
    path: artifacts/
    merge-multiple: true  # 新增选项，合并多个artifact
```

**3. 文件路径调整**
由于download-artifact@v4的行为变化，调整了Release步骤的文件路径：
```yaml
files: |
  artifacts/*  # 简化路径匹配
```

### 🚀 验证步骤

1. **手动触发测试**：
   - 进入GitHub仓库的Actions页面
   - 选择"构建跨平台应用"工作流
   - 点击"Run workflow"按钮
   - 选择分支（通常是main或master）
   - 点击"Run workflow"

2. **推送代码测试**：
   ```bash
   git add .
   git commit -m "修复GitHub Actions废弃版本问题"
   git push
   ```

3. **标签发布测试**：
   ```bash
   git tag v2.0.1
   git push origin v2.0.1
   ```

### 📋 检查清单

- [x] 更新upload-artifact到v4
- [x] 更新download-artifact到v4
- [x] 更新setup-python到v5
- [x] 更新action-gh-release到v2
- [x] 添加merge-multiple选项
- [x] 调整文件路径匹配
- [x] 保持所有现有功能

### 🎯 预期结果

修复后的GitHub Actions应该能够：
- ✅ 成功构建Windows、macOS、Linux三个平台
- ✅ 正确上传构建产物
- ✅ 在创建标签时自动发布Release
- ✅ 不再出现废弃版本警告

### 📚 参考链接

- [GitHub Actions artifacts v4 迁移指南](https://github.blog/changelog/2024-04-16-deprecation-notice-v3-of-the-artifact-actions/)
- [upload-artifact@v4 文档](https://github.com/actions/upload-artifact/tree/v4)
- [download-artifact@v4 文档](https://github.com/actions/download-artifact/tree/v4)

---

---

## 2024年修复 - 包管理器切换

### 🐛 问题描述
GitHub Actions构建失败，npm ci报错：
```
npm error The `npm ci` command can only install with an existing package-lock.json or
npm error npm-shrinkwrap.json with lockfileVersion >= 1
```

### 🔍 根本原因
项目使用Yarn作为包管理器（存在yarn.lock文件），但GitHub Actions中使用了npm命令。

### ✅ 解决方案
将GitHub Actions从npm切换到yarn：

| 修改项      | 原配置            | 新配置                           |
| ----------- | ----------------- | -------------------------------- |
| Node.js缓存 | `cache: 'npm'`    | `cache: 'yarn'`                  |
| 安装依赖    | `npm ci`          | `yarn install --frozen-lockfile` |
| 构建命令    | `npm run build-*` | `yarn build-*`                   |

### 🔧 详细更改

**1. Node.js设置**
```yaml
- name: 🟢 设置Node.js
  uses: actions/setup-node@v4
  with:
    node-version: '18'
    cache: 'yarn'  # 从npm改为yarn
```

**2. 依赖安装**
```yaml
- name: 📦 安装Node.js依赖
  run: yarn install --frozen-lockfile  # 替代npm ci
```

**3. 构建命令**
```yaml
# Windows构建
build_script: yarn build-win

# macOS构建  
build_script: yarn build-mac

# Linux构建
build_script: yarn build-linux
```

### 💡 yarn install --frozen-lockfile 说明
- 等效于npm ci的yarn命令
- 确保严格按照yarn.lock安装依赖
- 如果yarn.lock与package.json不匹配会失败
- 适合CI/CD环境使用

---

**更新时间**: 2024年
**状态**: ✅ 已修复
**测试状态**: 待验证 