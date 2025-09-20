// 使用preload脚本暴露的API

class PDFBookmarkApp {
  constructor() {
    this.initElements();
    this.initEventListeners();
    this.initRealtimeLogListeners();
    this.initWindowStateListeners();
    this.loadAppInfo();
    this.currentTab = "add-bookmarks";
  }

  initElements() {
    // 标签页相关元素
    this.tabButtons = document.querySelectorAll(".tab-button");
    this.tabContents = document.querySelectorAll(".tab-content");

    // 窗口控制按钮
    this.minimizeBtn = document.getElementById("minimize-btn");
    this.maximizeBtn = document.getElementById("maximize-btn");
    this.closeBtn = document.getElementById("close-btn");

    // 自动加书签相关元素
    this.inputFile = document.getElementById("input-file");
    this.outputFile = document.getElementById("output-file");
    this.browseInput = document.getElementById("browse-input");
    this.browseOutput = document.getElementById("browse-output");
    this.bookmarkFile = document.getElementById("bookmark-file");
    // this.browseBookmark = document.getElementById("browse-bookmark");
    // this.clearBookmark = document.getElementById("clear-bookmark");
    this.enableFontFilter = document.getElementById("enable-font-filter");
    this.fontThreshold = document.getElementById("font-threshold");
    this.enableDebug = document.getElementById("enable-debug");
    this.enableXFilter = document.getElementById("enable-x-filter");
    this.xTolerance = document.getElementById("x-tolerance");
    this.requireNumericStart = document.getElementById("require-numeric-start");
    this.startProcess = document.getElementById("start-process");
    this.stopProcess = document.getElementById("stop-process");
    this.openFolder = document.getElementById("open-folder");
    this.logOutput = document.getElementById("log-output");
    this.clearLog = document.getElementById("clear-log");

    // 调试：检查关键元素是否存在
    console.log("关键元素检查:");
    console.log("fontThreshold:", this.fontThreshold);
    console.log("enableFontFilter:", this.enableFontFilter);
    console.log("inputFile:", this.inputFile);
    console.log("outputFile:", this.outputFile);

    // 手动控制相关元素
    this.excludeTitleInput = document.getElementById("exclude-title-input");
    this.includeTitleInput = document.getElementById("include-title-input");
    this.addExcludeTitle = document.getElementById("add-exclude-title");
    this.addIncludeTitle = document.getElementById("add-include-title");
    this.excludeTitles = document.getElementById("exclude-titles");
    this.includeTitles = document.getElementById("include-titles");

    // 书签文件辅助加书签相关元素
    this.bfaInputFile = document.getElementById("bfa-input-file");
    this.bfaOutputFile = document.getElementById("bfa-output-file");
    this.bfaBookmarkFile = document.getElementById("bfa-bookmark-file");
    this.bfaBrowseInput = document.getElementById("bfa-browse-input");
    this.bfaBrowseOutput = document.getElementById("bfa-browse-output");
    this.bfaBrowseBookmark = document.getElementById("bfa-browse-bookmark");
    this.bfaStartProcess = document.getElementById("bfa-start-process");
    this.bfaStopProcess = document.getElementById("bfa-stop-process");
    this.bfaOpenFolder = document.getElementById("bfa-open-folder");
    this.bfaLogOutput = document.getElementById("bfa-log-output");
    this.bfaClearLog = document.getElementById("bfa-clear-log");

    // markdown辅助加书签相关元素
    this.maInputFile = document.getElementById("ma-input-file");
    this.maOutputFile = document.getElementById("ma-output-file");
    this.maMarkdownFile = document.getElementById("ma-markdown-file");
    this.maBrowseInput = document.getElementById("ma-browse-input");
    this.maBrowseOutput = document.getElementById("ma-browse-output");
    this.maBrowseMarkdown = document.getElementById("ma-browse-markdown");
    this.maStartProcess = document.getElementById("ma-start-process");
    this.maStopProcess = document.getElementById("ma-stop-process");
    this.maOpenFolder = document.getElementById("ma-open-folder");
    this.maLogOutput = document.getElementById("ma-log-output");
    this.maClearLog = document.getElementById("ma-clear-log");
    this.markdownPreview = document.getElementById("markdown-preview");

    // 自动提取书签相关元素
    this.extractInputFile = document.getElementById("extract-input-file");
    this.extractOutputFile = document.getElementById("extract-output-file");
    this.browseExtractInput = document.getElementById("browse-extract-input");
    this.browseExtractOutput = document.getElementById("browse-extract-output");
    this.includePageInfo = document.getElementById("include-page-info");
    this.includeLevelInfo = document.getElementById("include-level-info");
    this.exportFormat = document.getElementById("export-format");
    this.startExtract = document.getElementById("start-extract");
    this.stopExtract = document.getElementById("stop-extract");
    this.openExtractFolder = document.getElementById("open-extract-folder");
    this.extractLogOutput = document.getElementById("extract-log-output");
    this.clearExtractLog = document.getElementById("clear-extract-log");
    this.bookmarkPreview = document.getElementById("bookmark-preview");
    this.previewSection = document.querySelector(".preview-section");

    // 进度条元素
    this.progressFills = document.querySelectorAll(".progress-fill");
    this.progressTexts = document.querySelectorAll(".progress-text");

    // 应用信息
    this.appVersion = document.getElementById("app-version");

    this.isProcessing = false;
    this.isExtracting = false;
    this.currentProcess = null;
  }

  initEventListeners() {
    // 窗口控制按钮事件
    if (this.minimizeBtn) {
      console.log("最小化按钮已找到，添加事件监听器");
      this.minimizeBtn.addEventListener("click", (e) => {
        console.log("最小化按钮被点击");
        e.preventDefault();
        e.stopPropagation();
        this.minimizeWindow();
      });
    } else {
      console.error("最小化按钮未找到");
    }
    if (this.maximizeBtn) {
      console.log("最大化按钮已找到，添加事件监听器");
      this.maximizeBtn.addEventListener("click", (e) => {
        console.log("最大化按钮被点击");
        e.preventDefault();
        e.stopPropagation();
        this.maximizeWindow();
      });
    } else {
      console.error("最大化按钮未找到");
    }
    if (this.closeBtn) {
      console.log("关闭按钮已找到，添加事件监听器");
      this.closeBtn.addEventListener("click", (e) => {
        console.log("关闭按钮被点击");
        e.preventDefault();
        e.stopPropagation();
        this.closeWindow();
      });
    } else {
      console.error("关闭按钮未找到");
    }

    // 标签页切换
    this.tabButtons.forEach((button) => {
      button.addEventListener("click", () =>
        this.switchTab(button.dataset.tab)
      );
    });

    // 自动加书签功能事件
    if (this.browseInput) {
      this.browseInput.addEventListener("click", () => this.selectInputFile());
    }
    if (this.browseOutput) {
      this.browseOutput.addEventListener("click", () => this.selectOutputFile());
    }

    if (this.startProcess) {
      this.startProcess.addEventListener("click", () => this.startProcessing());
    }
    if (this.stopProcess) {
      this.stopProcess.addEventListener("click", () => this.stopProcessing());
    }
    if (this.openFolder) {
      this.openFolder.addEventListener("click", () => this.openOutputFolder());
    }
    if (this.clearLog) {
      this.clearLog.addEventListener("click", () => this.clearProcessLog());
    }

    // 书签文件辅助加书签功能事件
    if (this.bfaBrowseInput) {
      this.bfaBrowseInput.addEventListener("click", () => this.selectBfaInputFile());
    }
    if (this.bfaBrowseOutput) {
      this.bfaBrowseOutput.addEventListener("click", () => this.selectBfaOutputFile());
    }
    if (this.bfaBrowseBookmark) {
      this.bfaBrowseBookmark.addEventListener("click", () => this.selectBfaBookmarkFile());
    }
    if (this.bfaStartProcess) {
      this.bfaStartProcess.addEventListener("click", () => this.startBfaProcessing());
    }
    if (this.bfaStopProcess) {
      this.bfaStopProcess.addEventListener("click", () => this.stopBfaProcessing());
    }
    if (this.bfaOpenFolder) {
      this.bfaOpenFolder.addEventListener("click", () => this.openBfaOutputFolder());
    }
    if (this.bfaClearLog) {
      this.bfaClearLog.addEventListener("click", () => this.clearBfaLog());
    }

    // markdown辅助加书签功能事件
    if (this.maBrowseInput) {
      this.maBrowseInput.addEventListener("click", () => this.selectMaInputFile());
    }
    if (this.maBrowseOutput) {
      this.maBrowseOutput.addEventListener("click", () => this.selectMaOutputFile());
    }
    if (this.maBrowseMarkdown) {
      this.maBrowseMarkdown.addEventListener("click", () => this.selectMaMarkdownFile());
    }
    if (this.maStartProcess) {
      this.maStartProcess.addEventListener("click", () => this.startMaProcessing());
    }
    if (this.maStopProcess) {
      this.maStopProcess.addEventListener("click", () => this.stopMaProcessing());
    }
    if (this.maOpenFolder) {
      this.maOpenFolder.addEventListener("click", () => this.openMaOutputFolder());
    }
    if (this.maClearLog) {
      this.maClearLog.addEventListener("click", () => this.clearMaLog());
    }

    // 诊断功能事件
    const diagnoseBtn = document.getElementById("diagnose-env");
    if (diagnoseBtn) {
      diagnoseBtn.addEventListener("click", () => this.showDiagnostics());
    }

    // 模态框关闭事件
    const modalClose = document.querySelector(".modal-close");
    if (modalClose) {
      modalClose.addEventListener("click", () => this.closeDiagnosticModal());
    }

    // 点击模态框外部关闭
    const modal = document.getElementById("diagnostic-modal");
    if (modal) {
      modal.addEventListener("click", (e) => {
        if (e.target === modal) {
          this.closeDiagnosticModal();
        }
      });
    }

    // 手动控制事件
    if (this.addExcludeTitle) {
      this.addExcludeTitle.addEventListener("click", () => {
        this.addExcludeTitleItem();
      });
    }

    if (this.addIncludeTitle) {
      this.addIncludeTitle.addEventListener("click", () => {
        this.addIncludeTitleItem();
      });
    }
    if (this.excludeTitleInput) {
      this.excludeTitleInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") this.addExcludeTitleItem();
      });
    }
    if (this.includeTitleInput) {
      this.includeTitleInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") this.addIncludeTitleItem();
      });
    }

    // 自动提取书签功能事件
    if (this.browseExtractInput) {
      this.browseExtractInput.addEventListener("click", () => {
        this.selectExtractInputFile();
      });
    }

    if (this.browseExtractOutput) {
      this.browseExtractOutput.addEventListener("click", () => {
        this.selectExtractOutputFile();
      });
    }

    if (this.startExtract) {
      this.startExtract.addEventListener("click", () => this.startExtraction());
    }

    if (this.stopExtract) {
      this.stopExtract.addEventListener("click", () => this.stopExtraction());
    }

    if (this.openExtractFolder) {
      this.openExtractFolder.addEventListener("click", () =>
        this.openExtractOutputFolder()
      );
    }

    if (this.clearExtractLog) {
      this.clearExtractLog.addEventListener("click", () =>
        this.clearExtractLogOutput()
      );
    }

    // 文件输入变化事件
    if (this.inputFile) {
      this.inputFile.addEventListener("change", () => this.onInputFileChange());
    }
    if (this.bfaInputFile) {
      this.bfaInputFile.addEventListener("change", () => this.onBfaInputFileChange());
    }
    if (this.maInputFile) {
      this.maInputFile.addEventListener("change", () => this.onMaInputFileChange());
    }
    if (this.maMarkdownFile) {
      this.maMarkdownFile.addEventListener("change", () => this.onMaMarkdownFileChange());
    }
    if (this.extractInputFile) {
      this.extractInputFile.addEventListener("change", () =>
        this.onExtractInputFileChange()
      );
    }

    // 导出格式变化事件
    if (this.exportFormat) {
      this.exportFormat.addEventListener("change", () =>
        this.onExportFormatChange()
      );
    }
  }

  initRealtimeLogListeners() {
    // 监听实时处理日志（自动加书签模式）
    this.processLogHandler = (event, logData) => {
      const { message, timestamp, type = "info" } = logData;

      // 判断日志类型
      let logType = type;
      if (
        message.includes("✅") ||
        message.includes("成功") ||
        message.includes("完成")
      ) {
        logType = "success";
      } else if (
        message.includes("❌") ||
        message.includes("失败") ||
        message.includes("错误")
      ) {
        logType = "error";
      } else if (message.includes("⚠️") || message.includes("警告")) {
        logType = "warning";
      }

      this.addLogMessage(message, logType, "default");

      // 简单的进度估算（基于关键词）
      if (message.includes("步骤1") || message.includes("提取文本")) {
        this.updateProgress(20, "正在提取文本...");
      } else if (message.includes("步骤2") || message.includes("过滤")) {
        this.updateProgress(40, "正在过滤内容...");
      } else if (message.includes("步骤3") || message.includes("排序")) {
        this.updateProgress(60, "正在排序...");
      } else if (message.includes("步骤4") || message.includes("层级")) {
        this.updateProgress(80, "正在构建层级...");
      } else if (message.includes("保存") || message.includes("完成")) {
        this.updateProgress(100, "处理完成");
      }
    };

    // 监听实时提取日志
    this.extractLogHandler = (event, logData) => {
      const { message, timestamp, type = "info" } = logData;

      // 判断日志类型
      let logType = type;
      if (
        message.includes("✅") ||
        message.includes("成功") ||
        message.includes("完成")
      ) {
        logType = "success";
      } else if (
        message.includes("❌") ||
        message.includes("失败") ||
        message.includes("错误")
      ) {
        logType = "error";
      } else if (message.includes("⚠️") || message.includes("警告")) {
        logType = "warning";
      }

      this.appendExtractLog(message, logType);

      // 简单的进度估算
      if (message.includes("打开PDF") || message.includes("分析")) {
        this.updateExtractProgress(30, "正在分析PDF...");
      } else if (message.includes("提取书签") || message.includes("书签")) {
        this.updateExtractProgress(70, "正在提取书签...");
      } else if (message.includes("保存") || message.includes("完成")) {
        this.updateExtractProgress(100, "提取完成");
      }
    };

    // 监听markdown辅助加书签日志
    this.maLogHandler = (event, logData) => {
      const { message, timestamp, type = "info" } = logData;

      // 判断日志类型
      let logType = type;
      if (
        message.includes("✅") ||
        message.includes("成功") ||
        message.includes("完成")
      ) {
        logType = "success";
      } else if (
        message.includes("❌") ||
        message.includes("失败") ||
        message.includes("错误")
      ) {
        logType = "error";
      } else if (message.includes("⚠️") || message.includes("警告")) {
        logType = "warning";
      }

      this.addLogMessage(message, logType, "ma");

      // 简单的进度估算（基于关键词）
      if (message.includes("开始markdown辅助加书签处理") || message.includes("解析Markdown")) {
        this.updateMaProgress(20, "正在解析Markdown文件...");
      } else if (message.includes("匹配") || message.includes("书签标题")) {
        this.updateMaProgress(50, "正在匹配书签...");
      } else if (message.includes("处理") || message.includes("添加书签")) {
        this.updateMaProgress(80, "正在添加书签...");
      } else if (message.includes("保存") || message.includes("完成")) {
        this.updateMaProgress(100, "处理完成");
      }
    };

    // 监听书签文件辅助加书签日志
    this.bfaLogHandler = (event, logData) => {
      const { message, timestamp, type = "info" } = logData;

      // 判断日志类型
      let logType = type;
      if (
        message.includes("✅") ||
        message.includes("成功") ||
        message.includes("完成")
      ) {
        logType = "success";
      } else if (
        message.includes("❌") ||
        message.includes("失败") ||
        message.includes("错误")
      ) {
        logType = "error";
      } else if (message.includes("⚠️") || message.includes("警告")) {
        logType = "warning";
      }

      this.addLogMessage(message, logType, "bfa");

      // 简单的进度估算（基于关键词）
      if (message.includes("开始书签文件辅助加书签处理") || message.includes("解析书签文件")) {
        this.updateBfaProgress(20, "正在解析书签文件...");
      } else if (message.includes("匹配") || message.includes("书签标题")) {
        this.updateBfaProgress(50, "正在匹配书签...");
      } else if (message.includes("处理") || message.includes("添加书签")) {
        this.updateBfaProgress(80, "正在添加书签...");
      } else if (message.includes("保存") || message.includes("完成")) {
        this.updateBfaProgress(100, "处理完成");
      }
    };

    // 注册监听器
    window.electronAPI.onProcessLog(this.processLogHandler);
    window.electronAPI.onExtractLog(this.extractLogHandler);
    window.electronAPI.onMALog(this.maLogHandler);
    window.electronAPI.onBFALog(this.bfaLogHandler);
  }

  // 标签页切换
  switchTab(tabName) {
    this.currentTab = tabName;

    // 更新标签按钮状态
    this.tabButtons.forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.tab === tabName);
    });

    // 显示对应的标签页内容
    this.tabContents.forEach((content) => {
      content.classList.toggle("active", content.id === tabName);
    });
  }

  // 自动加书签相关方法
  async selectInputFile() {
    try {
      const filePath = await window.electronAPI.selectInputFile();
      if (filePath) {
        this.inputFile.value = filePath;
        this.onInputFileChange();
      }
    } catch (error) {
      this.appendLog("选择文件失败: " + error.message, "error");
    }
  }

  async selectOutputFile() {
    try {
      const filePath = await window.electronAPI.selectOutputFile();
      if (filePath) {
        this.outputFile.value = filePath;
      }
    } catch (error) {
      this.appendLog("选择输出文件失败: " + error.message, "error");
    }
  }

  async selectBookmarkFile() {
    try {
      const filePath = await window.electronAPI.selectBookmarkFile();
      if (filePath) {
        this.bookmarkFile.value = filePath;
        this.appendLog(`已选择书签文件: ${filePath}`, "info");
      }
    } catch (error) {
      this.appendLog("选择书签文件失败: " + error.message, "error");
    }
  }

  clearBookmarkFile() {
    this.bookmarkFile.value = "";
    this.appendLog("已清空书签文件", "info");
  }

  onInputFileChange() {
    // 根据输入文件自动生成输出文件名
    if (this.inputFile && this.inputFile.value) {
      const inputPath = this.inputFile.value;
      const outputPath = inputPath.replace(/\.pdf$/i, "_with_bookmarks.pdf");
      if (this.outputFile) {
        this.outputFile.value = outputPath;
      }

      // 记录输出路径更新日志
      this.appendLog(`输出路径已更新为: ${outputPath}`, "info");
    }
  }

  async startProcessing() {
    if (this.isProcessing) return;

    if (!this.inputFile || !this.inputFile.value) {
      this.appendLog("请先选择输入PDF文件", "error");
      return;
    }

    this.isProcessing = true;
    this.updateProcessingState(true);

    try {
      const excludeTitles = this.getExcludeTitles();
      const includeTitles = this.getIncludeTitles();

      console.log("前端手动控制数据:", { excludeTitles, includeTitles });

      const options = {
        mode: "auto", // 自动加书签模式
        inputPath: this.inputFile.value,
        outputPath: this.outputFile.value,
        bookmarkFilePath: this.bookmarkFile?.value || null,
        enableFontFilter: this.enableFontFilter ? this.enableFontFilter.checked : false,
        fontThreshold: this.fontThreshold && this.fontThreshold.value
          ? parseFloat(this.fontThreshold.value)
          : null,
        disableFontFilter: this.enableFontFilter ? !this.enableFontFilter.checked : true,
        enableDebug: this.enableDebug ? this.enableDebug.checked : false,

        requireNumericStart: this.requireNumericStart ? this.requireNumericStart.checked : false,
        excludeTitles: excludeTitles,
        includeTitles: includeTitles,
      };

      this.appendLog("开始处理PDF文件...", "info");
      this.updateProgress(0, "正在启动处理...");

      const result = await window.electronAPI.processPDF(options);

      if (result.success) {
        this.appendLog("✅ PDF处理完成!", "success");
        this.appendLog(`输出文件: ${result.outputPath}`, "info");
        this.updateProgress(100, "处理完成");
        this.openFolder.disabled = false;
      } else {
        this.appendLog("❌ 处理失败: " + result.error, "error");
        this.updateProgress(0, "处理失败");
      }
    } catch (error) {
      this.appendLog("❌ 处理出错: " + error.message, "error");
      this.updateProgress(0, "处理出错");
    } finally {
      this.isProcessing = false;
      this.updateProcessingState(false);
    }
  }

  async stopProcessing() {
    if (!this.isProcessing) return;

    try {
      await window.electronAPI.stopProcess();
      this.appendLog("⏹️ 处理已停止", "warning");
      this.updateProgress(0, "已停止");
    } catch (error) {
      this.appendLog("停止处理失败: " + error.message, "error");
    } finally {
      this.isProcessing = false;
      this.updateProcessingState(false);
    }
  }

  async openOutputFolder() {
    if (!this.outputFile || !this.outputFile.value) return;

    try {
      await window.electronAPI.showInFolder(this.outputFile.value);
    } catch (error) {
      this.appendLog("打开文件夹失败: " + error.message, "error");
    }
  }

  // 手动控制相关方法
  addExcludeTitleItem() {
    if (!this.excludeTitleInput) return;
    const title = this.excludeTitleInput.value.trim();
    if (title) {
      this.addTitleItem(this.excludeTitles, title, "exclude");
      this.excludeTitleInput.value = "";
    }
  }

  addIncludeTitleItem() {
    if (!this.includeTitleInput) return;
    const title = this.includeTitleInput.value.trim();
    if (title) {
      this.addTitleItem(this.includeTitles, title, "include");
      this.includeTitleInput.value = "";
    }
  }

  addTitleItem(container, title, type) {
    const item = document.createElement("div");
    item.className = `title-item ${type}`;
    item.innerHTML = `
            <span>${title}</span>
            <button class="remove-btn" onclick="this.parentElement.remove()">×</button>
        `;
    container.appendChild(item);
  }

  getExcludeTitles() {
    return Array.from(this.excludeTitles.children).map(
      (item) => item.querySelector("span").textContent
    );
  }

  getIncludeTitles() {
    return Array.from(this.includeTitles.children).map(
      (item) => item.querySelector("span").textContent
    );
  }

  // 自动提取书签相关方法
  async selectExtractInputFile() {
    try {
      const filePath = await window.electronAPI.selectInputFile();
      if (filePath && this.extractInputFile) {
        this.extractInputFile.value = filePath;
        this.onExtractInputFileChange();
      }
    } catch (error) {
      this.appendExtractLog("选择文件失败: " + error.message, "error");
    }
  }

  async selectExtractOutputFile() {
    try {
      const format = this.exportFormat ? this.exportFormat.value : "json";
      const extension =
        format === "json" ? ".json" : format === "csv" ? ".csv" : ".txt";
      const filePath = await window.electronAPI.selectExtractOutputFile(
        extension
      );
      if (filePath && this.extractOutputFile) {
        this.extractOutputFile.value = filePath;
      }
    } catch (error) {
      this.appendExtractLog("选择输出文件失败: " + error.message, "error");
    }
  }

  onExtractInputFileChange() {
    // 根据输入文件自动生成输出文件名
    if (this.extractInputFile && this.extractInputFile.value) {
      const inputPath = this.extractInputFile.value;
      const format = this.exportFormat ? this.exportFormat.value : "json";
      const extension =
        format === "json" ? ".json" : format === "csv" ? ".csv" : ".txt";
      const outputPath = inputPath.replace(/\.pdf$/i, `_bookmarks${extension}`);
      if (this.extractOutputFile) {
        this.extractOutputFile.value = outputPath;
      }

      // 记录输出路径更新日志
      this.appendExtractLog(`输出路径已更新为: ${outputPath}`, "info");
    }
  }

  onExportFormatChange() {
    // 当格式改变时，更新输出文件扩展名
    this.onExtractInputFileChange();
  }

  async startExtraction() {
    if (this.isExtracting) return;

    if (!this.extractInputFile || !this.extractInputFile.value) {
      this.appendExtractLog("请先选择包含书签的PDF文件", "error");
      return;
    }

    this.isExtracting = true;
    this.updateExtractionState(true);

    try {
      const options = {
        inputPath: this.extractInputFile.value,
        outputPath: this.extractOutputFile ? this.extractOutputFile.value : "",
        includePageInfo: this.includePageInfo ? this.includePageInfo.checked : false,
        includeLevelInfo: this.includeLevelInfo ? this.includeLevelInfo.checked : false,
        format: this.exportFormat ? this.exportFormat.value : "json",
      };

      this.appendExtractLog("开始提取书签...", "info");
      this.updateExtractProgress(0, "正在分析PDF...");

      const result = await window.electronAPI.extractBookmarks(options);

      if (result.success) {
        this.appendExtractLog("✅ 书签提取完成!", "success");
        this.appendExtractLog(`输出文件: ${result.outputPath}`, "info");
        this.appendExtractLog(`共提取 ${result.bookmarkCount} 个书签`, "info");
        this.updateExtractProgress(100, "提取完成");
        this.openExtractFolder.disabled = false;

        // 显示书签预览（仅JSON格式）
        // if (result.bookmarks && this.exportFormat.value === "json") {
        //   this.showBookmarkPreview(result.bookmarks);
        // }
      } else {
        this.appendExtractLog("❌ 提取失败: " + result.error, "error");
        this.updateExtractProgress(0, "提取失败");
      }
    } catch (error) {
      this.appendExtractLog("❌ 提取出错: " + error.message, "error");
      this.updateExtractProgress(0, "提取出错");
    } finally {
      this.isExtracting = false;
      this.updateExtractionState(false);
    }
  }

  async stopExtraction() {
    if (!this.isExtracting) return;

    try {
      await window.electronAPI.stopExtraction();
      this.appendExtractLog("⏹️ 提取已停止", "warning");
      this.updateExtractProgress(0, "已停止");
    } catch (error) {
      this.appendExtractLog("停止提取失败: " + error.message, "error");
    } finally {
      this.isExtracting = false;
      this.updateExtractionState(false);
    }
  }

  async openExtractOutputFolder() {
    if (!this.extractOutputFile || !this.extractOutputFile.value) return;

    try {
      await window.electronAPI.showInFolder(this.extractOutputFile.value);
    } catch (error) {
      this.appendExtractLog("打开文件夹失败: " + error.message, "error");
    }
  }

  showBookmarkPreview(bookmarks) {
    if (!this.bookmarkPreview) return;
    
    this.bookmarkPreview.innerHTML = "";

    bookmarks.forEach((bookmark) => {
      const item = document.createElement("div");
      item.className = `bookmark-item bookmark-level-${Math.min(
        bookmark.level || 1,
        4
      )}`;

      let text = bookmark.title;
      if (this.includePageInfo && this.includePageInfo.checked && bookmark.page) {
        text += ` (第${bookmark.page}页)`;
      }
      if (this.includeLevelInfo && this.includeLevelInfo.checked && bookmark.level) {
        text += ` [层级${bookmark.level}]`;
      }

      item.textContent = text;
      this.bookmarkPreview.appendChild(item);
    });

    if (this.previewSection) {
      this.previewSection.style.display = "block";
    }
  }

  // 状态管理方法
  updateProcessingState(isProcessing) {
    if (this.startProcess) this.startProcess.disabled = isProcessing;
    if (this.stopProcess) this.stopProcess.disabled = !isProcessing;
    if (this.browseInput) this.browseInput.disabled = isProcessing;
    if (this.browseOutput) this.browseOutput.disabled = isProcessing;
    // this.browseBookmark.disabled = isProcessing;
    // this.clearBookmark.disabled = isProcessing;
    if (this.openFolder) this.openFolder.disabled = isProcessing || !this.outputFile || !this.outputFile.value;
  }

  updateExtractionState(isExtracting) {
    if (this.startExtract) this.startExtract.disabled = isExtracting;
    if (this.stopExtract) this.stopExtract.disabled = !isExtracting;
    if (this.browseExtractInput) this.browseExtractInput.disabled = isExtracting;
    if (this.browseExtractOutput) this.browseExtractOutput.disabled = isExtracting;
    if (this.openExtractFolder) this.openExtractFolder.disabled =
      isExtracting || !this.extractOutputFile || !this.extractOutputFile.value;
  }

  updateProgress(percent, text) {
    const progressFill =
      this.currentTab === "add-bookmarks"
        ? document.querySelector("#add-bookmarks .progress-fill")
        : document.querySelector("#extract-bookmarks .progress-fill");
    const progressText =
      this.currentTab === "add-bookmarks"
        ? document.querySelector("#add-bookmarks .progress-text")
        : document.querySelector("#extract-bookmarks .progress-text");

    if (progressFill) progressFill.style.width = percent + "%";
    if (progressText) progressText.textContent = text;
  }

  updateExtractProgress(percent, text) {
    const progressFill = document.querySelector(
      "#extract-bookmarks .progress-fill"
    );
    const progressText = document.querySelector(
      "#extract-bookmarks .progress-text"
    );

    if (progressFill) progressFill.style.width = percent + "%";
    if (progressText) progressText.textContent = text;
  }

  updateMaProgress(percent, text) {
    const progressFill = document.querySelector(
      "#markdown-assisted .progress-fill"
    );
    const progressText = document.querySelector(
      "#markdown-assisted .progress-text"
    );

    if (progressFill) progressFill.style.width = percent + "%";
    if (progressText) progressText.textContent = text;
  }

  updateBfaProgress(percent, text) {
    const progressFill = document.querySelector(
      "#bookmark-file-assisted .progress-fill"
    );
    const progressText = document.querySelector(
      "#bookmark-file-assisted .progress-text"
    );

    if (progressFill) progressFill.style.width = percent + "%";
    if (progressText) progressText.textContent = text;
  }

  appendLog(message, type = "info") {
    const timestamp = new Date().toLocaleTimeString();
    const logLine = `[${timestamp}] ${message}`;

    const logElement = document.createElement("div");
    logElement.className = `log-line log-${type}`;
    logElement.textContent = logLine;

    this.logOutput.appendChild(logElement);
    this.logOutput.scrollTop = this.logOutput.scrollHeight;
  }

  appendExtractLog(message, type = "info") {
    const timestamp = new Date().toLocaleTimeString();
    const logLine = `[${timestamp}] ${message}`;

    const logElement = document.createElement("div");
    logElement.className = `log-line log-${type}`;
    logElement.textContent = logLine;

    this.extractLogOutput.appendChild(logElement);
    this.extractLogOutput.scrollTop = this.extractLogOutput.scrollHeight;
  }

  async loadAppInfo() {
    try {
      const appInfo = await window.electronAPI.getAppInfo();
      if (this.appVersion) {
        this.appVersion.textContent = `v${appInfo.version}`;
      }
    } catch (error) {
      console.error("Failed to load app info:", error);
    }
  }

  // 清空处理日志
  clearProcessLog() {
    if (this.logOutput) {
      this.logOutput.innerHTML = "";
      this.appendLog("日志已清空", "info");
    }
  }

  // 清空提取日志
  clearExtractLogOutput() {
    if (this.extractLogOutput) {
      this.extractLogOutput.innerHTML = "";
      this.appendExtractLog("日志已清空", "info");
    }
  }

  // 显示诊断信息
  async showDiagnostics() {
    const modal = document.getElementById("diagnostic-modal");
    const content = document.getElementById("diagnostic-content");

    if (!modal || !content) return;

    // 显示模态框
    modal.style.display = "block";
    content.innerHTML = "<p>正在检查环境...</p>";

    try {
      const diagnostics = await window.electronAPI.diagnoseEnvironment();
      content.innerHTML = this.formatDiagnostics(diagnostics);
    } catch (error) {
      content.innerHTML = `<p class="status-error">获取诊断信息失败: ${error.message}</p>`;
    }
  }

  // 格式化诊断信息
  formatDiagnostics(diagnostics) {
    let html = '<div class="diagnostic-sections">';

    // 基本信息
    html += '<div class="diagnostic-section">';
    html += "<h4>基本信息</h4>";
    html += `<div class="diagnostic-item">`;
    html += `<span class="diagnostic-label">诊断时间:</span>`;
    html += `<span class="diagnostic-value">${new Date(
      diagnostics.timestamp
    ).toLocaleString()}</span>`;
    html += `</div>`;
    html += `<div class="diagnostic-item">`;
    html += `<span class="diagnostic-label">打包状态:</span>`;
    html += `<span class="diagnostic-value ${
      diagnostics.isPackaged ? "status-success" : "status-warning"
    }">${diagnostics.isPackaged ? "已打包" : "开发模式"}</span>`;
    html += `</div>`;
    html += `<div class="diagnostic-item">`;
    html += `<span class="diagnostic-label">操作系统:</span>`;
    html += `<span class="diagnostic-value">${diagnostics.platform}</span>`;
    html += `</div>`;
    html += "</div>";

    // 嵌入式Python
    html += '<div class="diagnostic-section">';
    html += "<h4>嵌入式Python</h4>";
    html += `<div class="diagnostic-item">`;
    html += `<span class="diagnostic-label">是否可用:</span>`;
    const embeddedStatus = diagnostics.embeddedPython.available
      ? "status-success"
      : "status-warning";
    html += `<span class="diagnostic-value ${embeddedStatus}">${
      diagnostics.embeddedPython.available ? "✅ 可用" : "⚠️ 不可用"
    }</span>`;
    html += `</div>`;

    if (diagnostics.embeddedPython.available) {
      html += `<div class="diagnostic-item">`;
      html += `<span class="diagnostic-label">Python路径:</span>`;
      html += `<span class="diagnostic-value">${diagnostics.embeddedPython.path}</span>`;
      html += `</div>`;
      html += `<div class="diagnostic-item">`;
      html += `<span class="diagnostic-label">文件存在:</span>`;
      const existsStatus = diagnostics.embeddedPython.exists
        ? "status-success"
        : "status-error";
      html += `<span class="diagnostic-value ${existsStatus}">${
        diagnostics.embeddedPython.exists ? "✅ 存在" : "❌ 不存在"
      }</span>`;
      html += `</div>`;

      if (diagnostics.embeddedPython.version) {
        html += `<div class="diagnostic-item">`;
        html += `<span class="diagnostic-label">Python版本:</span>`;
        html += `<span class="diagnostic-value">${diagnostics.embeddedPython.version}</span>`;
        html += `</div>`;
      }
    }

    if (diagnostics.embeddedPython.error) {
      html += `<div class="diagnostic-item">`;
      html += `<span class="diagnostic-label">错误信息:</span>`;
      html += `<span class="diagnostic-value status-error">${diagnostics.embeddedPython.error}</span>`;
      html += `</div>`;
    }
    html += "</div>";

    // Python环境
    html += '<div class="diagnostic-section">';
    html += "<h4>当前Python环境</h4>";
    html += `<div class="diagnostic-item">`;
    html += `<span class="diagnostic-label">Python命令:</span>`;
    const pythonStatus = diagnostics.pythonEnvironment.available
      ? "status-success"
      : "status-error";
    html += `<span class="diagnostic-value ${pythonStatus}">${diagnostics.pythonEnvironment.command}</span>`;
    html += `</div>`;
    html += `<div class="diagnostic-item">`;
    html += `<span class="diagnostic-label">Python可用性:</span>`;
    html += `<span class="diagnostic-value ${pythonStatus}">${
      diagnostics.pythonEnvironment.available ? "✅ 可用" : "❌ 不可用"
    }</span>`;
    html += `</div>`;

    if (diagnostics.pythonEnvironment.type) {
      html += `<div class="diagnostic-item">`;
      html += `<span class="diagnostic-label">Python类型:</span>`;
      const typeColor =
        diagnostics.pythonEnvironment.type === "embedded"
          ? "status-success"
          : "status-warning";
      const typeText =
        diagnostics.pythonEnvironment.type === "embedded"
          ? "🔗 嵌入式"
          : "🖥️ 系统";
      html += `<span class="diagnostic-value ${typeColor}">${typeText}</span>`;
      html += `</div>`;
    }

    if (diagnostics.pythonEnvironment.version) {
      html += `<div class="diagnostic-item">`;
      html += `<span class="diagnostic-label">Python版本:</span>`;
      html += `<span class="diagnostic-value">${diagnostics.pythonEnvironment.version}</span>`;
      html += `</div>`;
    }
    if (diagnostics.pythonEnvironment.error) {
      html += `<div class="diagnostic-item">`;
      html += `<span class="diagnostic-label">错误信息:</span>`;
      html += `<span class="diagnostic-value status-error">${diagnostics.pythonEnvironment.error}</span>`;
      html += `</div>`;
    }
    html += "</div>";

    // 文件路径
    html += '<div class="diagnostic-section">';
    html += "<h4>文件路径</h4>";
    html += `<div class="diagnostic-item">`;
    html += `<span class="diagnostic-label">Python后端目录:</span>`;
    html += `<span class="diagnostic-value">${diagnostics.pythonBackendPath}</span>`;
    html += `</div>`;
    html += `<div class="diagnostic-item">`;
    html += `<span class="diagnostic-label">Python脚本路径:</span>`;
    html += `<span class="diagnostic-value">${diagnostics.pythonScriptPath}</span>`;
    html += `</div>`;
    if (diagnostics.isPackaged) {
      html += `<div class="diagnostic-item">`;
      html += `<span class="diagnostic-label">资源路径:</span>`;
      html += `<span class="diagnostic-value">${diagnostics.resourcesPath}</span>`;
      html += `</div>`;
    }
    html += "</div>";

    // 文件检查
    html += '<div class="diagnostic-section">';
    html += "<h4>文件检查</h4>";
    html += `<div class="diagnostic-item">`;
    html += `<span class="diagnostic-label">后端目录存在:</span>`;
    const backendStatus = diagnostics.fileChecks.pythonBackendExists
      ? "status-success"
      : "status-error";
    html += `<span class="diagnostic-value ${backendStatus}">${
      diagnostics.fileChecks.pythonBackendExists ? "✅ 存在" : "❌ 不存在"
    }</span>`;
    html += `</div>`;
    html += `<div class="diagnostic-item">`;
    html += `<span class="diagnostic-label">Python脚本存在:</span>`;
    const scriptStatus = diagnostics.fileChecks.pythonScriptExists
      ? "status-success"
      : "status-error";
    html += `<span class="diagnostic-value ${scriptStatus}">${
      diagnostics.fileChecks.pythonScriptExists ? "✅ 存在" : "❌ 不存在"
    }</span>`;
    html += `</div>`;

    if (
      diagnostics.fileChecks.backendFiles &&
      diagnostics.fileChecks.backendFiles.length > 0
    ) {
      html += `<div class="diagnostic-item">`;
      html += `<span class="diagnostic-label">后端文件列表:</span>`;
      html += `<span class="diagnostic-value">${diagnostics.fileChecks.backendFiles.join(
        ", "
      )}</span>`;
      html += `</div>`;
    }

    if (diagnostics.fileChecks.error) {
      html += `<div class="diagnostic-item">`;
      html += `<span class="diagnostic-label">文件检查错误:</span>`;
      html += `<span class="diagnostic-value status-error">${diagnostics.fileChecks.error}</span>`;
      html += `</div>`;
    }
    html += "</div>";

    // 解决方案建议
    html += '<div class="diagnostic-section">';
    html += "<h4>状态总结</h4>";

    if (
      diagnostics.embeddedPython.available &&
      diagnostics.embeddedPython.exists
    ) {
      html += '<div class="diagnostic-item">';
      html +=
        '<span class="diagnostic-value status-success">✅ 嵌入式Python可用，无需额外安装</span>';
      html += "</div>";
    } else if (
      diagnostics.pythonEnvironment.available &&
      diagnostics.pythonEnvironment.type === "system"
    ) {
      html += '<div class="diagnostic-item">';
      html +=
        '<span class="diagnostic-value status-success">✅ 系统Python可用</span>';
      html += "</div>";
    } else {
      html += '<div class="diagnostic-item">';
      html +=
        '<span class="diagnostic-value status-error">❌ 无可用Python环境</span><br>';
      html +=
        '<span class="diagnostic-value">建议：重新下载安装完整版本的应用程序</span>';
      html += "</div>";
    }

    if (!diagnostics.fileChecks.pythonScriptExists) {
      html += '<div class="diagnostic-item">';
      html +=
        '<span class="diagnostic-value status-error">❌ Python脚本不存在</span><br>';
      html +=
        '<span class="diagnostic-value">应用安装可能不完整，请重新下载安装</span>';
      html += "</div>";
    }

    html += "</div>";
    html += "</div>";

    return html;
  }

  // ==================== 书签文件辅助加书签功能 ====================
  
  // 选择书签文件辅助加书签的输入文件
  async selectBfaInputFile() {
    try {
      const filePath = await window.electronAPI.selectInputFile();
      if (filePath) {
        this.bfaInputFile.value = filePath;
        this.onBfaInputFileChange();
      }
    } catch (error) {
      console.error("选择文件失败:", error);
      this.addLogMessage("选择文件失败: " + error.message, "error", "bfa");
    }
  }

  // 选择书签文件辅助加书签的输出文件
  async selectBfaOutputFile() {
    try {
      const filePath = await window.electronAPI.selectOutputFile();
      if (filePath) {
        this.bfaOutputFile.value = filePath;
      }
    } catch (error) {
      console.error("选择输出文件失败:", error);
      this.addLogMessage("选择输出文件失败: " + error.message, "error", "bfa");
    }
  }

  // 选择书签文件
  async selectBfaBookmarkFile() {
    try {
      const filePath = await window.electronAPI.selectBookmarkFile();
      if (filePath) {
        this.bfaBookmarkFile.value = filePath;
      }
    } catch (error) {
      console.error("选择书签文件失败:", error);
      this.addLogMessage("选择书签文件失败: " + error.message, "error", "bfa");
    }
  }

  // 书签文件辅助加书签输入文件变化处理
  onBfaInputFileChange() {
    const inputPath = this.bfaInputFile.value;
    if (inputPath && !this.bfaOutputFile.value) {
      this.bfaOutputFile.value = inputPath.replace(/\.pdf$/i, "_with_bookmarks.pdf");
    }
  }

  // 开始书签文件辅助加书签处理
  async startBfaProcessing() {
    if (this.isProcessing) {
      this.addLogMessage("已有任务在处理中，请等待完成", "warning", "bfa");
      return;
    }

    const inputFile = this.bfaInputFile.value.trim();
    const outputFile = this.bfaOutputFile.value.trim();
    const bookmarkFile = this.bfaBookmarkFile.value.trim();

    if (!inputFile) {
      this.addLogMessage("请选择PDF文件", "error", "bfa");
      return;
    }

    if (!bookmarkFile) {
      this.addLogMessage("请选择书签文件", "error", "bfa");
      return;
    }

    if (!outputFile) {
      this.addLogMessage("请指定输出文件路径", "error", "bfa");
      return;
    }

    try {
      this.isProcessing = true;
      this.updateBfaProcessingState(true);
      this.clearBfaLog();

      this.addLogMessage("开始书签文件辅助加书签处理...", "info", "bfa");
      this.addLogMessage(`输入文件: ${inputFile}`, "info", "bfa");
      this.addLogMessage(`书签文件: ${bookmarkFile}`, "info", "bfa");
      this.addLogMessage(`输出文件: ${outputFile}`, "info", "bfa");

      const result = await window.electronAPI.processPDF({
        inputPath: inputFile,
        outputPath: outputFile,
        bookmarkFile,
        mode: "bookmark-file-assisted"
      });

      if (result.success) {
        this.addLogMessage("✅ 书签文件辅助加书签处理完成!", "success", "bfa");
        this.bfaOpenFolder.disabled = false;
      } else {
        this.addLogMessage(`❌ 处理失败: ${result.error}`, "error", "bfa");
      }
    } catch (error) {
      console.error("处理失败:", error);
      this.addLogMessage(`❌ 处理失败: ${error.message}`, "error", "bfa");
    } finally {
      this.isProcessing = false;
      this.updateBfaProcessingState(false);
    }
  }

  // 停止书签文件辅助加书签处理
  stopBfaProcessing() {
    // 这里可以添加停止逻辑
    this.addLogMessage("停止处理", "info", "bfa");
  }

  // 打开书签文件辅助加书签输出文件夹
  async openBfaOutputFolder() {
    const outputFile = this.bfaOutputFile.value;
    if (outputFile) {
      try {
        await window.electronAPI.openFolder(outputFile);
      } catch (error) {
        console.error("打开文件夹失败:", error);
        this.addLogMessage("打开文件夹失败: " + error.message, "error", "bfa");
      }
    }
  }

  // 清空书签文件辅助加书签日志
  clearBfaLog() {
    if (this.bfaLogOutput) {
      this.bfaLogOutput.innerHTML = "";
    }
  }

  // 更新书签文件辅助加书签处理状态
  updateBfaProcessingState(isProcessing) {
    if (this.bfaStartProcess) {
      this.bfaStartProcess.disabled = isProcessing;
    }
    if (this.bfaStopProcess) {
      this.bfaStopProcess.disabled = !isProcessing;
    }
  }

  // ==================== Markdown辅助加书签功能 ====================
  
  // 选择Markdown辅助加书签的输入文件
  async selectMaInputFile() {
    try {
      const filePath = await window.electronAPI.selectInputFile();
      if (filePath) {
        this.maInputFile.value = filePath;
        this.onMaInputFileChange();
      }
    } catch (error) {
      console.error("选择文件失败:", error);
      this.addLogMessage("选择文件失败: " + error.message, "error", "ma");
    }
  }

  // 选择Markdown辅助加书签的输出文件
  async selectMaOutputFile() {
    try {
      const filePath = await window.electronAPI.selectOutputFile();
      if (filePath) {
        this.maOutputFile.value = filePath;
      }
    } catch (error) {
      console.error("选择输出文件失败:", error);
      this.addLogMessage("选择输出文件失败: " + error.message, "error", "ma");
    }
  }

  // 选择Markdown文件
  async selectMaMarkdownFile() {
    try {
      const filePath = await window.electronAPI.selectMarkdownFile();
      if (filePath) {
        this.maMarkdownFile.value = filePath;
        this.onMaMarkdownFileChange();
      }
    } catch (error) {
      console.error("选择Markdown文件失败:", error);
      this.addLogMessage("选择Markdown文件失败: " + error.message, "error", "ma");
    }
  }

  // Markdown辅助加书签输入文件变化处理
  onMaInputFileChange() {
    const inputPath = this.maInputFile.value;
    if (inputPath && !this.maOutputFile.value) {
      this.maOutputFile.value = inputPath.replace(/\.pdf$/i, "_with_bookmarks.pdf");
    }
  }

  // Markdown文件变化处理
  async onMaMarkdownFileChange() {
    const markdownFile = this.maMarkdownFile.value;
    if (markdownFile) {
      try {
        // 解析Markdown文件并显示预览
        const result = await window.electronAPI.parseMarkdownFile(markdownFile);
        if (result.success) {
          this.displayMarkdownPreview(result.headings);
        } else {
          this.addLogMessage(`解析Markdown文件失败: ${result.error}`, "error", "ma");
        }
      } catch (error) {
        console.error("解析Markdown文件失败:", error);
        this.addLogMessage("解析Markdown文件失败: " + error.message, "error", "ma");
      }
    }
  }

  // 显示Markdown预览
  displayMarkdownPreview(headings) {
    if (!this.markdownPreview) return;

    // 显示预览区域
    const previewSection = document.querySelector('#markdown-assisted .preview-section');
    if (previewSection) {
      previewSection.style.display = "block";
    }

    if (!headings || headings.length === 0) {
      this.markdownPreview.innerHTML = '<p class="help-text">未找到标题</p>';
      return;
    }

    let html = '';
    headings.forEach((heading, index) => {
      html += `
        <div class="markdown-preview-item level-${heading.level}">
          <span class="markdown-preview-prefix">${heading.prefix}</span>
          <span class="markdown-preview-title">${heading.originalTitle}</span>
          <span class="markdown-preview-level">(级别 ${heading.level})</span>
        </div>
      `;
    });

    this.markdownPreview.innerHTML = html;
    this.markdownPreview.style.display = "block";
  }

  // 开始Markdown辅助加书签处理
  async startMaProcessing() {
    if (this.isProcessing) {
      this.addLogMessage("已有任务在处理中，请等待完成", "warning", "ma");
      return;
    }

    const inputFile = this.maInputFile.value.trim();
    const outputFile = this.maOutputFile.value.trim();
    const markdownFile = this.maMarkdownFile.value.trim();

    if (!inputFile) {
      this.addLogMessage("请选择PDF文件", "error", "ma");
      return;
    }

    if (!markdownFile) {
      this.addLogMessage("请选择Markdown文件", "error", "ma");
      return;
    }

    if (!outputFile) {
      this.addLogMessage("请指定输出文件路径", "error", "ma");
      return;
    }

    try {
      this.isProcessing = true;
      this.updateMaProcessingState(true);
      this.clearMaLog();

      this.addLogMessage("开始Markdown辅助加书签处理...", "info", "ma");
      this.addLogMessage(`输入文件: ${inputFile}`, "info", "ma");
      this.addLogMessage(`Markdown文件: ${markdownFile}`, "info", "ma");
      this.addLogMessage(`输出文件: ${outputFile}`, "info", "ma");

      const result = await window.electronAPI.processPDF({
        inputPath: inputFile,
        outputPath: outputFile,
        markdownFile,
        mode: "markdown-assisted"
      });

      if (result.success) {
        this.addLogMessage("✅ Markdown辅助加书签处理完成!", "success", "ma");
        this.maOpenFolder.disabled = false;
      } else {
        this.addLogMessage(`❌ 处理失败: ${result.error}`, "error", "ma");
      }
    } catch (error) {
      console.error("处理失败:", error);
      this.addLogMessage(`❌ 处理失败: ${error.message}`, "error", "ma");
    } finally {
      this.isProcessing = false;
      this.updateMaProcessingState(false);
    }
  }

  // 停止Markdown辅助加书签处理
  stopMaProcessing() {
    // 这里可以添加停止逻辑
    this.addLogMessage("停止处理", "info", "ma");
  }

  // 打开Markdown辅助加书签输出文件夹
  async openMaOutputFolder() {
    const outputFile = this.maOutputFile.value;
    if (outputFile) {
      try {
        await window.electronAPI.openFolder(outputFile);
      } catch (error) {
        console.error("打开文件夹失败:", error);
        this.addLogMessage("打开文件夹失败: " + error.message, "error", "ma");
      }
    }
  }

  // 清空Markdown辅助加书签日志
  clearMaLog() {
    if (this.maLogOutput) {
      this.maLogOutput.innerHTML = "";
    }
  }

  // 更新Markdown辅助加书签处理状态
  updateMaProcessingState(isProcessing) {
    if (this.maStartProcess) {
      this.maStartProcess.disabled = isProcessing;
    }
    if (this.maStopProcess) {
      this.maStopProcess.disabled = !isProcessing;
    }
  }

  // 添加日志消息（支持不同tab）
  addLogMessage(message, type = "info", tab = "default") {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = document.createElement("div");
    logEntry.className = `log-entry`;
    logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;

    let logOutput;
    switch (tab) {
      case "bfa":
        logOutput = this.bfaLogOutput;
        break;
      case "ma":
        logOutput = this.maLogOutput;
        break;
      default:
        logOutput = this.logOutput;
    }

    if (logOutput) {
      logOutput.appendChild(logEntry);
      logOutput.scrollTop = logOutput.scrollHeight;
    }
  }

  // 关闭诊断模态框
  closeDiagnosticModal() {
    const modal = document.getElementById("diagnostic-modal");
    if (modal) {
      modal.style.display = "none";
    }
  }

  // 复制诊断信息
  async copyDiagnostics() {
    try {
      const diagnostics = await window.electronAPI.diagnoseEnvironment();
      const text = JSON.stringify(diagnostics, null, 2);
      await navigator.clipboard.writeText(text);

      // 显示复制成功的提示
      const button = event.target;
      const originalText = button.textContent;
      button.textContent = "已复制!";
      button.style.background = "#059669";

      setTimeout(() => {
        button.textContent = originalText;
        button.style.background = "";
      }, 2000);
    } catch (error) {
      console.error("复制失败:", error);
      alert("复制失败: " + error.message);
    }
  }

  // 窗口控制方法
  async minimizeWindow() {
    try {
      await window.electronAPI.minimizeWindow();
    } catch (error) {
      console.error("最小化窗口失败:", error);
    }
  }

  async maximizeWindow() {
    try {
      await window.electronAPI.maximizeWindow();
    } catch (error) {
      console.error("最大化窗口失败:", error);
    }
  }

  async closeWindow() {
    try {
      await window.electronAPI.closeWindow();
    } catch (error) {
      console.error("关闭窗口失败:", error);
    }
  }

  // 初始化窗口状态监听
  initWindowStateListeners() {
    // 监听窗口最大化状态变化
    window.electronAPI.onWindowMaximized((event, isMaximized) => {
      const container = document.querySelector('.container');
      if (isMaximized) {
        container.classList.add('maximized');
      } else {
        container.classList.remove('maximized');
      }
    });
  }
}

// 全局函数，供HTML中使用
function closeDiagnosticModal() {
  const modal = document.getElementById("diagnostic-modal");
  if (modal) {
    modal.style.display = "none";
  }
}

async function copyDiagnostics() {
  try {
    const diagnostics = await window.electronAPI.diagnoseEnvironment();
    const text = JSON.stringify(diagnostics, null, 2);
    await navigator.clipboard.writeText(text);

    // 显示复制成功的提示
    const button = event.target;
    const originalText = button.textContent;
    button.textContent = "已复制!";
    button.style.background = "#059669";

    setTimeout(() => {
      button.textContent = originalText;
      button.style.background = "";
    }, 2000);
  } catch (error) {
    console.error("复制失败:", error);
    alert("复制失败: " + error.message);
  }
}

// 初始化应用
document.addEventListener("DOMContentLoaded", () => {
  new PDFBookmarkApp();
});
