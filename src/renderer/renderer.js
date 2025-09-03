// 使用preload脚本暴露的API

class PDFBookmarkApp {
  constructor() {
    this.initElements();
    this.initEventListeners();
    this.initRealtimeLogListeners();
    this.loadAppInfo();
    this.currentTab = "add-bookmarks";
  }

  initElements() {
    // 标签页相关元素
    this.tabButtons = document.querySelectorAll(".tab-button");
    this.tabContents = document.querySelectorAll(".tab-content");

    // 自动加书签相关元素
    this.inputFile = document.getElementById("input-file");
    this.outputFile = document.getElementById("output-file");
    this.browseInput = document.getElementById("browse-input");
    this.browseOutput = document.getElementById("browse-output");
    this.bookmarkFile = document.getElementById("bookmark-file");
    this.browseBookmark = document.getElementById("browse-bookmark");
    this.clearBookmark = document.getElementById("clear-bookmark");
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

    // 手动控制相关元素
    this.excludeTitleInput = document.getElementById("exclude-title-input");
    this.includeTitleInput = document.getElementById("include-title-input");
    this.addExcludeTitle = document.getElementById("add-exclude-title");
    this.addIncludeTitle = document.getElementById("add-include-title");
    this.excludeTitles = document.getElementById("exclude-titles");
    this.includeTitles = document.getElementById("include-titles");

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
    // 标签页切换
    this.tabButtons.forEach((button) => {
      button.addEventListener("click", () =>
        this.switchTab(button.dataset.tab)
      );
    });

    // 自动加书签功能事件
    this.browseInput.addEventListener("click", () => this.selectInputFile());
    this.browseOutput.addEventListener("click", () => this.selectOutputFile());
    this.browseBookmark.addEventListener("click", () =>
      this.selectBookmarkFile()
    );
    this.clearBookmark.addEventListener("click", () =>
      this.clearBookmarkFile()
    );

    this.startProcess.addEventListener("click", () => this.startProcessing());
    this.stopProcess.addEventListener("click", () => this.stopProcessing());
    this.openFolder.addEventListener("click", () => this.openOutputFolder());
    this.clearLog.addEventListener("click", () => this.clearProcessLog());

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
    this.excludeTitleInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") this.addExcludeTitleItem();
    });
    this.includeTitleInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") this.addIncludeTitleItem();
    });

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
    this.inputFile.addEventListener("change", () => this.onInputFileChange());
    this.extractInputFile.addEventListener("change", () =>
      this.onExtractInputFileChange()
    );

    // 导出格式变化事件
    this.exportFormat.addEventListener("change", () =>
      this.onExportFormatChange()
    );
  }

  initRealtimeLogListeners() {
    // 监听实时处理日志
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

      this.appendLog(message, logType);

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

    // 注册监听器
    window.electronAPI.onProcessLog(this.processLogHandler);
    window.electronAPI.onExtractLog(this.extractLogHandler);
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
    if (this.inputFile.value) {
      const inputPath = this.inputFile.value;
      const outputPath = inputPath.replace(/\.pdf$/i, "_with_bookmarks.pdf");
      this.outputFile.value = outputPath;

      // 记录输出路径更新日志
      this.appendLog(`输出路径已更新为: ${outputPath}`, "info");
    }
  }

  async startProcessing() {
    if (this.isProcessing) return;

    if (!this.inputFile.value) {
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
        inputPath: this.inputFile.value,
        outputPath: this.outputFile.value,
        bookmarkFilePath: this.bookmarkFile.value || null,
        enableFontFilter: this.enableFontFilter.checked,
        fontThreshold: this.fontThreshold.value
          ? parseFloat(this.fontThreshold.value)
          : null,
        disableFontFilter: !this.enableFontFilter.checked,
        enableDebug: this.enableDebug.checked,

        requireNumericStart: this.requireNumericStart.checked,
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
    if (!this.outputFile.value) return;

    try {
      await window.electronAPI.showInFolder(this.outputFile.value);
    } catch (error) {
      this.appendLog("打开文件夹失败: " + error.message, "error");
    }
  }

  // 手动控制相关方法
  addExcludeTitleItem() {
    const title = this.excludeTitleInput.value.trim();
    if (title) {
      this.addTitleItem(this.excludeTitles, title, "exclude");
      this.excludeTitleInput.value = "";
    }
  }

  addIncludeTitleItem() {
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
      if (filePath) {
        this.extractInputFile.value = filePath;
        this.onExtractInputFileChange();
      }
    } catch (error) {
      this.appendExtractLog("选择文件失败: " + error.message, "error");
    }
  }

  async selectExtractOutputFile() {
    try {
      const format = this.exportFormat.value;
      const extension =
        format === "json" ? ".json" : format === "csv" ? ".csv" : ".txt";
      const filePath = await window.electronAPI.selectExtractOutputFile(
        extension
      );
      if (filePath) {
        this.extractOutputFile.value = filePath;
      }
    } catch (error) {
      this.appendExtractLog("选择输出文件失败: " + error.message, "error");
    }
  }

  onExtractInputFileChange() {
    // 根据输入文件自动生成输出文件名
    if (this.extractInputFile.value) {
      const inputPath = this.extractInputFile.value;
      const format = this.exportFormat.value;
      const extension =
        format === "json" ? ".json" : format === "csv" ? ".csv" : ".txt";
      const outputPath = inputPath.replace(/\.pdf$/i, `_bookmarks${extension}`);
      this.extractOutputFile.value = outputPath;

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

    if (!this.extractInputFile.value) {
      this.appendExtractLog("请先选择包含书签的PDF文件", "error");
      return;
    }

    this.isExtracting = true;
    this.updateExtractionState(true);

    try {
      const options = {
        inputPath: this.extractInputFile.value,
        outputPath: this.extractOutputFile.value,
        includePageInfo: this.includePageInfo.checked,
        includeLevelInfo: this.includeLevelInfo.checked,
        format: this.exportFormat.value,
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
        if (result.bookmarks && this.exportFormat.value === "json") {
          this.showBookmarkPreview(result.bookmarks);
        }
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
    if (!this.extractOutputFile.value) return;

    try {
      await window.electronAPI.showInFolder(this.extractOutputFile.value);
    } catch (error) {
      this.appendExtractLog("打开文件夹失败: " + error.message, "error");
    }
  }

  showBookmarkPreview(bookmarks) {
    this.bookmarkPreview.innerHTML = "";

    bookmarks.forEach((bookmark) => {
      const item = document.createElement("div");
      item.className = `bookmark-item bookmark-level-${Math.min(
        bookmark.level || 1,
        4
      )}`;

      let text = bookmark.title;
      if (this.includePageInfo.checked && bookmark.page) {
        text += ` (第${bookmark.page}页)`;
      }
      if (this.includeLevelInfo.checked && bookmark.level) {
        text += ` [层级${bookmark.level}]`;
      }

      item.textContent = text;
      this.bookmarkPreview.appendChild(item);
    });

    this.previewSection.style.display = "block";
  }

  // 状态管理方法
  updateProcessingState(isProcessing) {
    this.startProcess.disabled = isProcessing;
    this.stopProcess.disabled = !isProcessing;
    this.browseInput.disabled = isProcessing;
    this.browseOutput.disabled = isProcessing;
    this.browseBookmark.disabled = isProcessing;
    this.clearBookmark.disabled = isProcessing;
    this.openFolder.disabled = isProcessing || !this.outputFile.value;
  }

  updateExtractionState(isExtracting) {
    this.startExtract.disabled = isExtracting;
    this.stopExtract.disabled = !isExtracting;
    this.browseExtractInput.disabled = isExtracting;
    this.browseExtractOutput.disabled = isExtracting;
    this.openExtractFolder.disabled =
      isExtracting || !this.extractOutputFile.value;
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
