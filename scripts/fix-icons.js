const fs = require('fs');
const path = require('path');

/**
 * 图标修复脚本
 * 自动处理Mac构建时的图标问题
 */

console.log('🖼️ 开始图标修复检查...');

// 检查图标文件
const iconPngPath = path.join(__dirname, '..', 'assets', 'icon.png');
const iconIcnsPath = path.join(__dirname, "..", "assets", "icon.icns");
const packageJsonPath = path.join(__dirname, '..', 'package.json');

// 检查PNG图标
let pngValid = false;
if (fs.existsSync(iconPngPath)) {
  const stats = fs.statSync(iconPngPath);
  console.log(`📊 PNG图标大小: ${stats.size} 字节`);
  
  if (stats.size > 1000) {
    pngValid = true;
    console.log('✅ PNG图标有效');
  } else {
    console.log('⚠️ PNG图标文件太小，可能无效');
  }
} else {
  console.log('❌ PNG图标文件不存在');
}

// 检查ICNS图标
let icnsExists = fs.existsSync(iconIcnsPath);
console.log(icnsExists ? '✅ ICNS图标存在' : '❌ ICNS图标不存在');

// 读取package.json
let packageJson;
try {
  packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
} catch (error) {
  console.error('❌ 无法读取package.json:', error.message);
  process.exit(1);
}

// 修复策略
let needsUpdate = false;

if (!pngValid && !icnsExists) {
  console.log('🔧 创建默认图标配置...');
  
  // 移除Mac图标配置，使用默认图标
  if (packageJson.build && packageJson.build.mac && packageJson.build.mac.icon) {
    console.log('📝 移除硬编码的Mac图标路径');
    delete packageJson.build.mac.icon;
    needsUpdate = true;
  }
  
  // 如果PNG也无效，移除Linux图标配置
  if (!pngValid && packageJson.build && packageJson.build.linux && packageJson.build.linux.icon) {
    console.log('📝 移除硬编码的Linux图标路径');
    delete packageJson.build.linux.icon;
    needsUpdate = true;
  }
} else if (icnsExists && packageJson.build && packageJson.build.mac) {
  // 确保Mac配置指向正确的图标
  if (packageJson.build.mac.icon !== 'assets/icon.icns') {
    console.log('📝 更新Mac图标路径');
    packageJson.build.mac.icon = 'assets/icon.icns';
    needsUpdate = true;
  }
}

// 保存更新的package.json
if (needsUpdate) {
  try {
    fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2) + '\n');
    console.log('✅ package.json已更新');
  } catch (error) {
    console.error('❌ 保存package.json失败:', error.message);
    process.exit(1);
  }
} else {
  console.log('ℹ️ package.json无需更新');
}

// 生成图标修复建议
console.log('\n📋 图标状态总结:');

if (!pngValid) {
  console.log('⚠️ 建议操作:');
  console.log('  1. 提供一个有效的PNG图标文件 (assets/icon.png)');
  console.log('  2. 建议尺寸: 至少512x512像素');
  console.log('  3. 格式: PNG，文件大小应大于1KB');
  console.log('');
  console.log('💡 临时解决方案:');
  console.log('  - 构建将使用Electron默认图标');
  console.log('  - 应用功能不受影响');
}

if (!icnsExists && pngValid) {
  console.log('ℹ️ Mac图标将在构建时自动生成');
}

console.log('\n🎯 修复完成！构建现在应该可以正常进行。'); 