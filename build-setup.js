const fs = require('fs');

// 构建前的准备工作
function setupBuild() {
    console.log('🔧 准备构建环境...');
    
    // 检查必要的文件
    const requiredFiles = [
        'src/main.js',
        'src/renderer/index.html',
        'src/renderer/styles.css',
        'src/renderer/renderer.js',
        'python-backend/pdf_bookmark_tool.py',
        'python-backend/requirements.txt'
    ];
    
    let allFilesExist = true;
    requiredFiles.forEach(file => {
        if (!fs.existsSync(file)) {
            console.error(`❌ 缺少必要文件: ${file}`);
            allFilesExist = false;
        } else {
            console.log(`✅ 找到文件: ${file}`);
        }
    });
    
    if (!allFilesExist) {
        console.error('❌ 构建失败：缺少必要文件');
        process.exit(1);
    }
    
    // 检查Python后端
    console.log('🐍 检查Python环境...');
    const { spawn } = require('child_process');
    
    const pythonCheck = spawn('python', ['--version'], { stdio: 'pipe' });
    pythonCheck.on('close', (code) => {
        if (code === 0) {
            console.log('✅ Python环境正常');
        } else {
            console.warn('⚠️ Python环境检查失败，请确保系统已安装Python');
        }
    });
    
    console.log('✅ 构建环境准备完成');
}

if (require.main === module) {
    setupBuild();
}

module.exports = { setupBuild }; 