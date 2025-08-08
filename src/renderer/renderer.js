// 使用preload脚本暴露的API

class PDFBookmarkApp {
  constructor() {
    this.initElements();
    this.initEventListeners();
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
    this.enableLlm = document.getElementById("enable-llm");
    this.enableFontFilter = document.getElementById("enable-font-filter");
    this.fontThreshold = document.getElementById("font-threshold");
    this.enableEnhancedFilter = document.getElementById(
      "enable-enhanced-filter"
    );
    this.enableDebug = document.getElementById("enable-debug");
    this.enableXFilter = document.getElementById("enable-x-filter");
    this.xTolerance = document.getElementById("x-tolerance");
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
    this.enableLlm.addEventListener("change", () => this.onLlmOptionChange());
    this.startProcess.addEventListener("click", () => this.startProcessing());
    this.stopProcess.addEventListener("click", () => this.stopProcessing());
    this.openFolder.addEventListener("click", () => this.openOutputFolder());
    this.clearLog.addEventListener("click", () => this.clearProcessLog());

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
      this.clearExtractLog.addEventListener("click", () => this.clearExtractLogOutput());
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

  onInputFileChange() {
    // 自动生成输出文件名
    if (this.inputFile.value && !this.outputFile.value) {
      const inputPath = this.inputFile.value;
      const outputPath = inputPath.replace(/\.pdf$/i, "_with_bookmarks.pdf");
      this.outputFile.value = outputPath;
    }
  }

  onLlmOptionChange() {
    // 当禁用大模型时，自动启用增强本地过滤
    if (!this.enableLlm.checked) {
      this.enableEnhancedFilter.checked = true;
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
        enableLlm: this.enableLlm.checked,
        enableFontFilter: this.enableFontFilter.checked,
        fontThreshold: this.fontThreshold.value
          ? parseFloat(this.fontThreshold.value)
          : null,
        enableEnhancedFilter: this.enableEnhancedFilter.checked,
        disableFontFilter: !this.enableFontFilter.checked,
        enableDebug: this.enableDebug.checked,
        enableXFilter: this.enableXFilter.checked,
        xTolerance: parseFloat(this.xTolerance.value) || 2.0,
        excludeTitles: excludeTitles,
        includeTitles: includeTitles,
      };

      this.appendLog("开始处理PDF文件...", "info");
      this.updateProgress(0, "正在启动处理...");

      const result = await window.electronAPI.processPDF(options);

      if (result.success) {
        // 显示详细的处理日志
        if (result.output) {
          const lines = result.output.split("\n").filter((line) => line.trim());
          lines.forEach((line) => {
            if (
              line.includes("✅") ||
              line.includes("成功") ||
              line.includes("完成")
            ) {
              this.appendLog(line, "success");
            } else if (
              line.includes("❌") ||
              line.includes("失败") ||
              line.includes("错误")
            ) {
              this.appendLog(line, "error");
            } else if (line.includes("⚠️") || line.includes("警告")) {
              this.appendLog(line, "warning");
            } else {
              this.appendLog(line, "info");
            }
          });
        }
        this.appendLog("✅ PDF处理完成!", "success");
        this.appendLog(`输出文件: ${result.outputPath}`, "info");
        this.updateProgress(100, "处理完成");
        this.openFolder.disabled = false;
      } else {
        this.appendLog("❌ 处理失败: " + result.error, "error");
        // 如果有错误输出，也显示出来
        if (result.output) {
          const lines = result.output.split("\n").filter((line) => line.trim());
          lines.forEach((line) => this.appendLog(line, "error"));
        }
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
    // 自动生成输出文件名
    if (this.extractInputFile.value && !this.extractOutputFile.value) {
      const inputPath = this.extractInputFile.value;
      const format = this.exportFormat.value;
      const extension =
        format === "json" ? ".json" : format === "csv" ? ".csv" : ".txt";
      const outputPath = inputPath.replace(/\.pdf$/i, `_bookmarks${extension}`);
      this.extractOutputFile.value = outputPath;
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
}

// 初始化应用
document.addEventListener("DOMContentLoaded", () => {
  new PDFBookmarkApp();
});
