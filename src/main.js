const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const { spawn } = require("child_process");
const fs = require("fs");

let mainWindow;
let pythonProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 900,
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
  return new Promise((resolve) => {
    if (pythonProcess) {
      pythonProcess.kill();
    }

    const pythonScript = path.join(
      __dirname,
      "../python-backend/pdf_bookmark_tool.py"
    );
    const args = [pythonScript, options.inputPath];

    if (options.outputPath) {
      args.push("-o", options.outputPath);
    }
    if (options.disableFontFilter) {
      args.push("--disable-font-filter");
    }
    if (options.fontThreshold) {
      args.push("--font-threshold", options.fontThreshold.toString());
    }
    if (options.enableDebug) {
      args.push("--debug");
    }
    if (!options.enableXFilter) {
      args.push("--disable-x-filter");
    }
    if (options.xTolerance && options.xTolerance !== 5.0) {
      args.push("--x-tolerance", options.xTolerance.toString());
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
    if (options.bookmarkFilePath) {
      args.push("--bookmark-file", options.bookmarkFilePath);
    }

    console.log("Spawning Python process with args:", args);
    console.log("Manual control options:", {
      excludeTitles: options.excludeTitles,
      includeTitles: options.includeTitles,
    });
    pythonProcess = spawn("python", args, {
      cwd: path.dirname(pythonScript),
      shell: true,
      encoding: "utf8",
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
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
          mainWindow.webContents.send("process-log", {
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
          mainWindow.webContents.send("process-log", {
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
      resolve({
        success: false,
        error: err.message,
        output: output,
      });
    });
  });
});

ipcMain.handle("extract-bookmarks", async (event, options) => {
  return new Promise((resolve) => {
    if (pythonProcess) {
      pythonProcess.kill();
    }

    const pythonScript = path.join(
      __dirname,
      "../python-backend/pdf_bookmark_tool.py"
    );
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

    pythonProcess = spawn("python", args, {
      cwd: path.dirname(pythonScript),
      encoding: "utf8",
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
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
      resolve({
        success: false,
        error: err.message,
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
