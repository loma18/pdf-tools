const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");

let mainWindow;
let pythonProcess = null;

// 递归查找目录中的Python可执行文件
function findPythonBinaryInDir(rootDir) {
  try {
    const stack = [rootDir];
    while (stack.length) {
      const current = stack.pop();
      const items = fs.readdirSync(current, { withFileTypes: true });
      for (const it of items) {
        const p = path.join(current, it.name);
        if (it.isDirectory()) {
          stack.push(p);
        } else {
          const base = path.basename(p);
          if (process.platform === 'win32') {
            if (base.toLowerCase() === 'python.exe') return p;
          } else if (process.platform === 'darwin' || process.platform === 'linux') {
            if (base === 'python3' || base === 'python') return p;
          }
        }
      }
    }
  } catch (e) {}
  return null;
}

// 获取嵌入式Python路径
function getEmbeddedPythonPath() {
  try {
    // 在开发环境中，直接使用require
    if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
      const portablePython = require("@bjia56/portable-python-3.11");
      return portablePython;
    }
    
    // 在打包环境中，从extraResources加载
    const portablePythonDir = path.join(process.resourcesPath, "portable-python");
    
    // 优先使用递归搜索，适配不同目录命名
    const found = findPythonBinaryInDir(portablePythonDir);
    if (found && fs.existsSync(found)) return found;
    
    // 兼容旧逻辑：根据平台确定可执行文件路径
    let pythonExe;
    if (process.platform === 'win32') {
      const candidates = fs.readdirSync(portablePythonDir).filter(dir => 
        dir.includes('python') && dir.includes('windows')
      );
      if (candidates.length > 0) {
        pythonExe = path.join(portablePythonDir, candidates[0], 'bin', 'python.exe');
      }
    } else if (process.platform === 'darwin') {
      const candidates = fs.readdirSync(portablePythonDir).filter(dir => 
        dir.includes('python') && (dir.includes('macos') || dir.includes('darwin') || dir.includes('osx'))
      );
      if (candidates.length > 0) {
        pythonExe = path.join(portablePythonDir, candidates[0], 'bin', 'python3');
      }
    } else {
      const candidates = fs.readdirSync(portablePythonDir).filter(dir => 
        dir.includes('python') && dir.includes('linux')
      );
      if (candidates.length > 0) {
        pythonExe = path.join(portablePythonDir, candidates[0], 'bin', 'python3');
      }
    }
    
    if (pythonExe && fs.existsSync(pythonExe)) {
      return pythonExe;
    }
    
    return null;
  } catch (error) {
    console.log("Embedded Python not available:", error.message);
    return null;
  }
}

// 获取Python后端路径的函数
function getPythonBackendPath() {
  // 在开发环境中
  if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
    return path.join(__dirname, "../python-backend");
  }
  
  // 在打包后的应用中，Python文件位于extraResources中
  return path.join(process.resourcesPath, "python-backend");
}

// 获取Python脚本路径
function getPythonScriptPath() {
  return path.join(getPythonBackendPath(), "pdf_bookmark_tool.py");
}

// 检查Python是否可用（优先使用嵌入式Python）
function checkPythonAvailability() {
  return new Promise((resolve) => {
    // 首先尝试嵌入式Python
    const embeddedPython = getEmbeddedPythonPath();
    if (embeddedPython && fs.existsSync(embeddedPython)) {
      console.log("Using embedded Python:", embeddedPython);
      
      // 验证嵌入式Python是否可以正常工作
      const checkProcess = spawn(embeddedPython, ['--version'], { 
        stdio: 'pipe',
        shell: false 
      });
      
      checkProcess.on('close', (code) => {
        if (code === 0) {
          resolve({ command: embeddedPython, type: 'embedded' });
        } else {
          console.log("Embedded Python validation failed, trying system Python");
          checkSystemPython(resolve);
        }
      });
      
      checkProcess.on('error', (error) => {
        console.log("Embedded Python error:", error.message);
        checkSystemPython(resolve);
      });
    } else {
      console.log("Embedded Python not found, trying system Python");
      checkSystemPython(resolve);
    }
  });
}

// 检查系统Python
function checkSystemPython(resolve) {
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  const checkProcess = spawn(pythonCmd, ['--version'], { 
    stdio: 'pipe',
    shell: true 
  });
  
  checkProcess.on('close', (code) => {
    if (code === 0) {
      resolve({ command: pythonCmd, type: 'system' });
    } else {
      // 尝试另一个命令
      const altCmd = pythonCmd === 'python' ? 'python3' : 'python';
      const altProcess = spawn(altCmd, ['--version'], { 
        stdio: 'pipe',
        shell: true 
      });
      
      altProcess.on('close', (altCode) => {
        resolve(altCode === 0 ? { command: altCmd, type: 'system' } : null);
      });
      
      altProcess.on('error', () => {
        resolve(null);
      });
    }
  });
  
  checkProcess.on('error', () => {
    // 尝试另一个命令
    const altCmd = pythonCmd === 'python' ? 'python3' : 'python';
    const altProcess = spawn(altCmd, ['--version'], { 
      stdio: 'pipe',
      shell: true 
    });
    
    altProcess.on('close', (altCode) => {
      resolve(altCode === 0 ? { command: altCmd, type: 'system' } : null);
    });
    
    altProcess.on('error', () => {
      resolve(null);
    });
  });
}

// 安装Python依赖
function installPythonDependencies(pythonInfo) {
  return new Promise((resolve) => {
    if (!pythonInfo || pythonInfo.type !== 'embedded') {
      // 系统Python不需要安装依赖
      resolve(true);
      return;
    }

    console.log("Checking Python dependencies for embedded Python...");
    
    // 检查是否已安装所有必需的依赖
    const checkProcess = spawn(
      pythonInfo.command,
      [
        "-c",
        'import fitz, dotenv, requests; print("All dependencies available")',
      ],
      {
        stdio: "pipe",
        shell: false,
      }
    );

    let checkOutput = "";
    let checkError = "";

    checkProcess.stdout.on("data", (data) => {
      checkOutput += data.toString();
    });

    checkProcess.stderr.on("data", (data) => {
      checkError += data.toString();
    });

    checkProcess.on("close", (code) => {
      if (code === 0) {
        console.log("✅ All Python dependencies already available");
        resolve(true);
      } else {
        console.log(
          "⚠️ Some dependencies missing in embedded Python (but build should have bundled them). Error:"
        );
        console.log("Check error:", checkError);
        // 即使检测失败，也继续运行，避免首启联网安装
        resolve(true);
      }
    });

    checkProcess.on('error', (err) => {
      console.error("❌ Check process error:", err.message);
      console.log("💡 Continuing anyway - dependencies may be available through other means");
      resolve(true);
    });
  });
}

// 使用多个源安装依赖
function installWithMultipleSources(pythonInfo) {
  const sources = [
    'https://pypi.org/simple/',  // 官方源
    null,  // 默认源
    'https://pypi.douban.com/simple/',  // 豆瓣源
  ];
  
  return new Promise((resolve) => {
    let sourceIndex = 0;
    
    function tryNextSource() {
      if (sourceIndex >= sources.length) {
        console.error("❌ All PyPI sources failed");
        resolve(false);
        return;
      }
      
      const source = sources[sourceIndex];
      const args = ['-m', 'pip', 'install', 'PyMuPDF', 'python-dotenv'];  // 安装两个包
      
      if (source) {
        args.push('-i', source);
        console.log(`💡 Trying PyPI source: ${source}`);
      } else {
        console.log("💡 Trying default PyPI source");
      }
      
      const installProcess = spawn(pythonInfo.command, args, {
        stdio: 'pipe',
        shell: false
      });

      let installOutput = '';
      let installError = '';

      installProcess.stdout.on('data', (data) => {
        installOutput += data.toString();
      });

      installProcess.stderr.on('data', (data) => {
        installError += data.toString();
      });

      installProcess.on('close', (installCode) => {
        if (installCode === 0) {
          console.log("✅ All dependencies installed successfully");
          resolve(true);
        } else {
          console.log(`❌ Installation failed with source ${source || 'default'}`);
          console.log("Error:", installError);
          sourceIndex++;
          setTimeout(tryNextSource, 1000); // 等待1秒后尝试下一个源
        }
      });

      installProcess.on('error', (err) => {
        console.error(`❌ Install process error with source ${source || 'default'}:`, err.message);
        sourceIndex++;
        setTimeout(tryNextSource, 1000); // 等待1秒后尝试下一个源
      });
    }
    
    tryNextSource();
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 900,
    frame: false,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, "preload.js"),
    },
    icon: path.join(__dirname, "../assets/icon.png"),
    show: false,
  });

  mainWindow.loadFile(path.join(__dirname, "renderer/index.html"));

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
  });

  mainWindow.on("closed", () => {
    if (pythonProcess) {
      pythonProcess.kill();
      pythonProcess = null;
    }
  });
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
  if (process.platform !== "darwin") {
    app.quit();
  }
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// 确保在应用退出时杀死Python进程
app.on("before-quit", () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
});

// IPC处理器
ipcMain.handle("select-input-file", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "选择PDF文件",
    filters: [{ name: "PDF文件", extensions: ["pdf"] }],
    properties: ["openFile"],
  });

  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

ipcMain.handle("select-output-file", async () => {
  const result = await dialog.showSaveDialog(mainWindow, {
    title: "保存PDF文件",
    filters: [{ name: "PDF文件", extensions: ["pdf"] }],
    defaultPath: "output_with_bookmarks.pdf",
  });

  if (!result.canceled) {
    return result.filePath;
  }
  return null;
});

ipcMain.handle("select-bookmark-file", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "选择书签文件",
    filters: [
      { name: "书签文件", extensions: ["json", "txt", "csv"] },
      { name: "JSON文件", extensions: ["json"] },
      { name: "文本文件", extensions: ["txt"] },
      { name: "CSV文件", extensions: ["csv"] },
      { name: "所有文件", extensions: ["*"] },
    ],
    properties: ["openFile"],
  });

  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

ipcMain.handle("select-markdown-file", async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: "选择Markdown文件",
    filters: [
      { name: "Markdown文件", extensions: ["md", "markdown"] },
      { name: "所有文件", extensions: ["*"] },
    ],
    properties: ["openFile"],
  });

  if (!result.canceled && result.filePaths.length > 0) {
    return result.filePaths[0];
  }
  return null;
});

ipcMain.handle(
  "select-extract-output-file",
  async (event, extension = ".json") => {
    let filterName, filterExt;
    switch (extension) {
      case ".json":
        filterName = "JSON文件";
        filterExt = "json";
        break;
      case ".csv":
        filterName = "CSV文件";
        filterExt = "csv";
        break;
      case ".txt":
        filterName = "文本文件";
        filterExt = "txt";
        break;
      default:
        filterName = "JSON文件";
        filterExt = "json";
    }

    const result = await dialog.showSaveDialog(mainWindow, {
      title: "保存书签文件",
      filters: [{ name: filterName, extensions: [filterExt] }],
      defaultPath: `bookmarks${extension}`,
    });

    if (!result.canceled) {
      return result.filePath;
    }
    return null;
  }
);

ipcMain.handle("process-pdf", async (event, options) => {
  return new Promise(async (resolve) => {
    if (pythonProcess) {
      pythonProcess.kill();
    }

    // 检查Python脚本是否存在
    const pythonScript = getPythonScriptPath();
    if (!fs.existsSync(pythonScript)) {
      resolve({
        success: false,
        error: `Python脚本不存在: ${pythonScript}`,
        output: "",
      });
      return;
    }

    // 检查Python是否可用
    const pythonInfo = await checkPythonAvailability();
    if (!pythonInfo) {
      resolve({
        success: false,
        error: "系统中未找到Python环境，且嵌入式Python不可用。请安装Python 3.7+并添加到系统PATH中。",
        output: "",
      });
      return;
    }

    // 安装Python依赖（仅对嵌入式Python）
    const depsInstalled = await installPythonDependencies(pythonInfo);
    if (!depsInstalled) {
      resolve({
        success: false,
        error: "Python依赖安装失败。请检查网络连接或使用系统Python环境。",
        output: "",
      });
      return;
    }

    // 验证必需参数
    if (!options.inputPath) {
      resolve({
        success: false,
        error: "缺少输入文件路径参数",
        output: "",
      });
      return;
    }

    const args = [pythonScript, options.inputPath];

    // 根据处理模式设置不同的参数
    if (options.mode === "bookmark-file-assisted") {
      args.push("--bookmark-file-assisted");
      if (!options.bookmarkFile) {
        resolve({
          success: false,
          error: "书签文件辅助加书签模式需要提供书签文件路径",
          output: "",
        });
        return;
      }
      args.push("--bookmark-file", options.bookmarkFile);
    } else if (options.mode === "markdown-assisted") {
      args.push("--markdown-assisted");
      if (!options.markdownFile) {
        resolve({
          success: false,
          error: "markdown辅助加书签模式需要提供markdown文件路径",
          output: "",
        });
        return;
      }
      args.push("--markdown-file", options.markdownFile);
    } else {
      // 原有的自动加书签模式
      if (options.disableFontFilter) {
        args.push("--disable-font-filter");
      }
      if (options.fontThreshold) {
        args.push("--font-threshold", options.fontThreshold.toString());
      }
      if (options.excludeTitles && options.excludeTitles.length > 0) {
        args.push("--exclude-titles", JSON.stringify(options.excludeTitles));
      }
      if (options.includeTitles && options.includeTitles.length > 0) {
        args.push("--include-titles", JSON.stringify(options.includeTitles));
      }
      if (options.requireNumericStart) {
        args.push("--require-numeric-start");
      }
    }

    if (options.outputPath) {
      args.push("-o", options.outputPath);
    }
    if (options.enableDebug) {
      args.push("--debug");
    }

    console.log("Spawning Python process:", pythonInfo.command);
    console.log("Python type:", pythonInfo.type);
    console.log("Script path:", pythonScript);
    console.log("Working directory:", getPythonBackendPath());
    console.log("Args:", args);
    
    pythonProcess = spawn(pythonInfo.command, args, {
      cwd: getPythonBackendPath(),
      shell: pythonInfo.type === 'system', // 嵌入式Python不需要shell
      encoding: "utf8",
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONPATH: getPythonBackendPath(),
      },
    });

    let output = "";
    let error = "";

    pythonProcess.stdout.on("data", (data) => {
      const text = data.toString("utf8");
      output += text;

      // 实时发送日志到渲染进程
      if (mainWindow && !mainWindow.isDestroyed()) {
        // 按行分割并发送每一行
        const lines = text.split("\n").filter((line) => line.trim());
        lines.forEach((line) => {
          // 根据处理模式发送不同的日志事件
          let logEvent = "process-log";
          if (options.mode === "markdown-assisted") {
            logEvent = "ma-log";
          } else if (options.mode === "bookmark-file-assisted") {
            logEvent = "bfa-log";
          }
          
          mainWindow.webContents.send(logEvent, {
            message: line.trim(),
            timestamp: new Date().toISOString(),
          });
        });
      }
    });

    pythonProcess.stderr.on("data", (data) => {
      const text = data.toString("utf8");
      error += text;

      // 实时发送错误日志到渲染进程
      if (mainWindow && !mainWindow.isDestroyed()) {
        const lines = text.split("\n").filter((line) => line.trim());
        lines.forEach((line) => {
          // 根据处理模式发送不同的日志事件
          let logEvent = "process-log";
          if (options.mode === "markdown-assisted") {
            logEvent = "ma-log";
          } else if (options.mode === "bookmark-file-assisted") {
            logEvent = "bfa-log";
          }
          
          mainWindow.webContents.send(logEvent, {
            message: line.trim(),
            timestamp: new Date().toISOString(),
            type: "error",
          });
        });
      }
    });

    pythonProcess.on("close", (code) => {
      pythonProcess = null;

      if (code === 0) {
        // 从输出中提取实际的输出文件路径
        const outputPathMatch = output.match(/PDF已保存到: (.+)/);
        const outputPath = outputPathMatch
          ? outputPathMatch[1].trim()
          : options.outputPath;

        resolve({
          success: true,
          outputPath: outputPath,
          output: output,
        });
      } else {
        resolve({
          success: false,
          error: error || "处理失败",
          output: output,
        });
      }
    });

    pythonProcess.on("error", (err) => {
      pythonProcess = null;
      
      let errorMessage = err.message;
      if (err.code === 'ENOENT') {
        errorMessage = `无法启动Python进程: ${pythonInfo.command}。${pythonInfo.type === 'embedded' ? '嵌入式Python损坏' : '请确保Python已正确安装并添加到系统PATH中'}。`;
      }
      
      resolve({
        success: false,
        error: errorMessage,
        output: output,
      });
    });
  });
});

ipcMain.handle("extract-bookmarks", async (event, options) => {
  return new Promise(async (resolve) => {
    if (pythonProcess) {
      pythonProcess.kill();
    }

    // 检查Python脚本是否存在
    const pythonScript = getPythonScriptPath();
    if (!fs.existsSync(pythonScript)) {
      resolve({
        success: false,
        error: `Python脚本不存在: ${pythonScript}`,
        output: "",
      });
      return;
    }

    // 检查Python是否可用
    const pythonInfo = await checkPythonAvailability();
    if (!pythonInfo) {
      resolve({
        success: false,
        error: "系统中未找到Python环境，且嵌入式Python不可用。请安装Python 3.7+并添加到系统PATH中。",
        output: "",
      });
      return;
    }

    // 安装Python依赖（仅对嵌入式Python）
    const depsInstalled = await installPythonDependencies(pythonInfo);
    if (!depsInstalled) {
      resolve({
        success: false,
        error: "Python依赖安装失败。请检查网络连接或使用系统Python环境。",
        output: "",
      });
      return;
    }

    const args = [pythonScript, options.inputPath, "--extract-only"];

    if (options.outputPath) {
      args.push("-o", options.outputPath);
    }

    args.push("--format", options.format);

    if (!options.includePageInfo) {
      args.push("--no-page-info");
    }
    if (!options.includeLevelInfo) {
      args.push("--no-level-info");
    }

    pythonProcess = spawn(pythonInfo.command, args, {
      cwd: getPythonBackendPath(),
      shell: pythonInfo.type === 'system', // 嵌入式Python不需要shell
      encoding: "utf8",
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONPATH: getPythonBackendPath(),
      },
    });

    let output = "";
    let error = "";

    pythonProcess.stdout.on("data", (data) => {
      const text = data.toString("utf8");
      output += text;

      // 实时发送日志到渲染进程
      if (mainWindow && !mainWindow.isDestroyed()) {
        // 按行分割并发送每一行
        const lines = text.split("\n").filter((line) => line.trim());
        lines.forEach((line) => {
          mainWindow.webContents.send("extract-log", {
            message: line.trim(),
            timestamp: new Date().toISOString(),
          });
        });
      }
    });

    pythonProcess.stderr.on("data", (data) => {
      const text = data.toString("utf8");
      error += text;

      // 实时发送错误日志到渲染进程
      if (mainWindow && !mainWindow.isDestroyed()) {
        const lines = text.split("\n").filter((line) => line.trim());
        lines.forEach((line) => {
          mainWindow.webContents.send("extract-log", {
            message: line.trim(),
            timestamp: new Date().toISOString(),
            type: "error",
          });
        });
      }
    });

    pythonProcess.on("close", (code) => {
      pythonProcess = null;

      if (code === 0) {
        // 解析输出以获取书签信息
        try {
          const bookmarkCountMatch = output.match(/共提取 (\d+) 个书签/);
          const bookmarkCount = bookmarkCountMatch
            ? parseInt(bookmarkCountMatch[1])
            : 0;

          const outputPathMatch = output.match(/书签文件已保存到: (.+)/);
          const outputPath = outputPathMatch
            ? outputPathMatch[1].trim()
            : options.outputPath;

          // 尝试读取生成的书签文件以提供预览
          let bookmarks = [];
          if (
            outputPath &&
            fs.existsSync(outputPath) &&
            options.format === "json"
          ) {
            try {
              const bookmarkData = fs.readFileSync(outputPath, "utf8");
              bookmarks = JSON.parse(bookmarkData);
            } catch (parseError) {
              console.error("Failed to parse bookmark file:", parseError);
            }
          }

          resolve({
            success: true,
            outputPath: outputPath,
            bookmarkCount: bookmarkCount,
            bookmarks: bookmarks,
            output: output,
          });
        } catch (parseError) {
          resolve({
            success: false,
            error: "解析输出失败: " + parseError.message,
            output: output,
          });
        }
      } else {
        resolve({
          success: false,
          error: error || "提取失败",
          output: output,
        });
      }
    });

    pythonProcess.on("error", (err) => {
      pythonProcess = null;
      
      let errorMessage = err.message;
      if (err.code === 'ENOENT') {
        errorMessage = `无法启动Python进程: ${pythonInfo.command}。${pythonInfo.type === 'embedded' ? '嵌入式Python损坏' : '请确保Python已正确安装并添加到系统PATH中'}。`;
      }
      
      resolve({
        success: false,
        error: errorMessage,
        output: output,
      });
    });
  });
});

ipcMain.handle("stop-process", async () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
    return { success: true };
  }
  return { success: false, message: "没有正在运行的进程" };
});

ipcMain.handle("stop-extraction", async () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
    return { success: true };
  }
  return { success: false, message: "没有正在运行的提取进程" };
});

ipcMain.handle("show-in-folder", async (event, filePath) => {
  const { shell } = require("electron");
  try {
    if (fs.existsSync(filePath)) {
      shell.showItemInFolder(filePath);
      return true;
    }
    return false;
  } catch (error) {
    console.error("Error showing file in folder:", error);
    return false;
  }
});

ipcMain.handle("get-app-info", async () => {
  const packageJson = require("../package.json");
  return {
    name: packageJson.name,
    version: packageJson.version,
    electronVersion: process.versions.electron,
  };
});

// 添加诊断功能
ipcMain.handle("diagnose-environment", async () => {
  const diagnostics = {
    timestamp: new Date().toISOString(),
    isPackaged: app.isPackaged,
    platform: process.platform,
    pythonBackendPath: getPythonBackendPath(),
    pythonScriptPath: getPythonScriptPath(),
    resourcesPath: app.isPackaged ? process.resourcesPath : "N/A (development)",
    embeddedPython: {},
    pythonEnvironment: {},
    fileChecks: {}
  };

  // 检查嵌入式Python
  try {
    const embeddedPython = getEmbeddedPythonPath();
    diagnostics.embeddedPython.available = !!embeddedPython;
    diagnostics.embeddedPython.path = embeddedPython || "未找到";
    
    if (embeddedPython) {
      diagnostics.embeddedPython.exists = fs.existsSync(embeddedPython);
      
      if (diagnostics.embeddedPython.exists) {
        // 尝试获取嵌入式Python版本
        const versionProcess = spawn(embeddedPython, ['--version'], { 
          stdio: 'pipe',
          shell: false 
        });
        
        versionProcess.stdout.on('data', (data) => {
          diagnostics.embeddedPython.version = data.toString().trim();
        });
        
        versionProcess.stderr.on('data', (data) => {
          diagnostics.embeddedPython.version = data.toString().trim();
        });
      }
    }
  } catch (error) {
    diagnostics.embeddedPython.error = error.message;
  }

  // 检查文件是否存在
  try {
    diagnostics.fileChecks.pythonBackendExists = fs.existsSync(getPythonBackendPath());
    diagnostics.fileChecks.pythonScriptExists = fs.existsSync(getPythonScriptPath());
    
    if (diagnostics.fileChecks.pythonBackendExists) {
      const backendFiles = fs.readdirSync(getPythonBackendPath());
      diagnostics.fileChecks.backendFiles = backendFiles;
    }
  } catch (error) {
    diagnostics.fileChecks.error = error.message;
  }

  // 检查Python环境
  try {
    const pythonInfo = await checkPythonAvailability();
    if (pythonInfo) {
      diagnostics.pythonEnvironment.command = pythonInfo.command;
      diagnostics.pythonEnvironment.type = pythonInfo.type;
      diagnostics.pythonEnvironment.available = true;
      
      // 获取Python版本信息
      const versionProcess = spawn(pythonInfo.command, ['--version'], { 
        stdio: 'pipe',
        shell: pythonInfo.type === 'system'
      });
      
      versionProcess.stdout.on('data', (data) => {
        diagnostics.pythonEnvironment.version = data.toString().trim();
      });
      
      versionProcess.stderr.on('data', (data) => {
        diagnostics.pythonEnvironment.version = data.toString().trim();
      });
    } else {
      diagnostics.pythonEnvironment.available = false;
      diagnostics.pythonEnvironment.command = "未找到";
    }
  } catch (error) {
    diagnostics.pythonEnvironment.error = error.message;
  }

  return diagnostics;
});

// 添加Markdown文件解析API
ipcMain.handle("parse-markdown-file", async (event, filePath) => {
  return new Promise(async (resolve) => {
    // 检查Python脚本是否存在
    const pythonScript = getPythonScriptPath();
    if (!fs.existsSync(pythonScript)) {
      resolve({
        success: false,
        error: `Python脚本不存在: ${pythonScript}`,
        headings: []
      });
      return;
    }

    // 检查Python是否可用
    const pythonInfo = await checkPythonAvailability();
    if (!pythonInfo) {
      resolve({
        success: false,
        error: "系统中未找到Python环境，且嵌入式Python不可用。请安装Python 3.7+并添加到系统PATH中。",
        headings: []
      });
      return;
    }

    // 安装Python依赖（仅对嵌入式Python）
    const depsInstalled = await installPythonDependencies(pythonInfo);
    if (!depsInstalled) {
      resolve({
        success: false,
        error: "Python依赖安装失败。请检查网络连接或使用系统Python环境。",
        headings: []
      });
      return;
    }

    const args = [pythonScript, "--parse-markdown", filePath];
    
    console.log("Spawning Python process for markdown parsing:", pythonInfo.command);
    console.log("Args:", args);
    
    const markdownProcess = spawn(pythonInfo.command, args, {
      cwd: getPythonBackendPath(),
      shell: pythonInfo.type === 'system',
      encoding: "utf8",
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONPATH: getPythonBackendPath(),
      },
    });

    let output = "";
    let error = "";

    markdownProcess.stdout.on("data", (data) => {
      output += data.toString("utf8");
    });

    markdownProcess.stderr.on("data", (data) => {
      error += data.toString("utf8");
    });

    markdownProcess.on("close", (code) => {
      console.log(`Markdown parsing process exited with code ${code}`);
      console.log("Output:", output);
      console.log("Error:", error);

      if (code === 0) {
        try {
          // 尝试解析JSON输出 - 直接解析整个输出
          const result = JSON.parse(output.trim());
          resolve({
            success: true,
            headings: result.headings || [],
            output: output
          });
        } catch (parseError) {
          console.error("JSON parse error:", parseError);
          console.error("Output that failed to parse:", output);
          resolve({
            success: false,
            error: `JSON解析失败: ${parseError.message}`,
            headings: []
          });
        }
      } else {
        resolve({
          success: false,
          error: error || `进程退出，代码: ${code}`,
          headings: []
        });
      }
    });

    // 添加超时处理
    setTimeout(() => {
      if (markdownProcess && !markdownProcess.killed) {
        console.log("Markdown parsing process timeout, killing process");
        markdownProcess.kill();
        resolve({
          success: false,
          error: "解析超时",
          headings: []
        });
      }
    }, 30000); // 30秒超时

    markdownProcess.on("error", (err) => {
      console.error("Markdown parsing process error:", err);
      resolve({
        success: false,
        error: `进程启动失败: ${err.message}`,
        headings: []
      });
    });
  });
});

// 窗口控制事件处理
ipcMain.handle("minimize-window", async () => {
  if (mainWindow) {
    mainWindow.minimize();
  }
});

ipcMain.handle("maximize-window", async () => {
  if (mainWindow) {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
      mainWindow.webContents.send("window-maximized", false);
    } else {
      mainWindow.maximize();
      mainWindow.webContents.send("window-maximized", true);
    }
  }
});

ipcMain.handle("close-window", async () => {
  if (mainWindow) {
    mainWindow.close();
  }
});
