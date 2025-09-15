const { contextBridge, ipcRenderer } = require('electron');

// 在渲染进程中暴露受保护的API
contextBridge.exposeInMainWorld("electronAPI", {
  // 文件选择相关
  selectInputFile: () => ipcRenderer.invoke("select-input-file"),
  selectOutputFile: () => ipcRenderer.invoke("select-output-file"),
  selectBookmarkFile: () => ipcRenderer.invoke("select-bookmark-file"),
  selectMarkdownFile: () => ipcRenderer.invoke("select-markdown-file"),
  selectExtractOutputFile: (extension) =>
    ipcRenderer.invoke("select-extract-output-file", extension),

  // PDF处理相关
  processPDF: (options) => ipcRenderer.invoke("process-pdf", options),
  stopProcess: () => ipcRenderer.invoke("stop-process"),

  // 书签提取相关
  extractBookmarks: (options) =>
    ipcRenderer.invoke("extract-bookmarks", options),
  stopExtraction: () => ipcRenderer.invoke("stop-extraction"),

  // 文件系统相关
  showInFolder: (filePath) => ipcRenderer.invoke("show-in-folder", filePath),

  // 应用信息
  getAppInfo: () => ipcRenderer.invoke("get-app-info"),

  // 诊断功能
  diagnoseEnvironment: () => ipcRenderer.invoke("diagnose-environment"),

  // Markdown文件解析
  parseMarkdownFile: (filePath) => ipcRenderer.invoke("parse-markdown-file", filePath),

  // 实时日志监听
  onProcessLog: (callback) => ipcRenderer.on("process-log", callback),
  onExtractLog: (callback) => ipcRenderer.on("extract-log", callback),
  onMALog: (callback) => ipcRenderer.on("ma-log", callback),
  onBFALog: (callback) => ipcRenderer.on("bfa-log", callback),
  removeProcessLogListener: (callback) =>
    ipcRenderer.removeListener("process-log", callback),
  removeExtractLogListener: (callback) =>
    ipcRenderer.removeListener("extract-log", callback),
  removeMALogListener: (callback) =>
    ipcRenderer.removeListener("ma-log", callback),
  removeBFALogListener: (callback) =>
    ipcRenderer.removeListener("bfa-log", callback),

  // 窗口控制相关
  minimizeWindow: () => ipcRenderer.invoke("minimize-window"),
  maximizeWindow: () => ipcRenderer.invoke("maximize-window"),
  closeWindow: () => ipcRenderer.invoke("close-window"),
  
  // 窗口状态监听
  onWindowMaximized: (callback) => ipcRenderer.on("window-maximized", callback),
  removeWindowMaximizedListener: (callback) => ipcRenderer.removeListener("window-maximized", callback),
}); 