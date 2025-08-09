#!/usr/bin/env node

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

console.log("🐍 Setting up embedded Python environment...");

try {
  // 检查是否已安装portable-python
  const packageJsonPath = path.join(__dirname, "..", "package.json");
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, "utf8"));

  if (!packageJson.dependencies["@bjia56/portable-python-3.11"]) {
    console.log("📦 Installing portable Python...");
    execSync("npm install @bjia56/portable-python-3.11@latest", {
      stdio: "inherit",
      cwd: path.join(__dirname, ".."),
    });
  } else {
    console.log("✅ Portable Python already installed");
  }

  // 验证安装
  console.log("🔍 Verifying Python installation...");
  const portablePython = require("@bjia56/portable-python-3.11");
  console.log("📍 Python executable:", portablePython);

  if (fs.existsSync(portablePython)) {
    console.log("✅ Python executable found");

    // 测试Python运行
    const { spawn } = require("child_process");
    const pythonProcess = spawn(portablePython, ["--version"], {
      stdio: "pipe",
      shell: false,
    });

    pythonProcess.stdout.on("data", (data) => {
      console.log("✅ Python version:", data.toString().trim());
    });

    pythonProcess.stderr.on("data", (data) => {
      console.log("✅ Python version:", data.toString().trim());
    });

    pythonProcess.on("close", (code) => {
      if (code === 0) {
        console.log("🔧 Installing Python dependencies...");

        // 安装必需的依赖
        const installProcess = spawn(
          portablePython,
          [
            "-m",
            "pip",
            "install",
            "PyMuPDF",
            "python-dotenv",
            "-i",
            "https://pypi.org/simple/",
          ],
          {
            stdio: "inherit",
            shell: false,
          }
        );

        installProcess.on("close", (installCode) => {
          if (installCode === 0) {
            console.log("🎉 Embedded Python setup complete!");
            console.log("");
            console.log("💡 Benefits:");
            console.log(
              "   - Users no longer need to install Python separately"
            );
            console.log(
              "   - Consistent Python environment across all installations"
            );
            console.log("   - Automatic dependency management");
            console.log("   - PyMuPDF and python-dotenv pre-installed");
            console.log("");
            console.log("📋 Next steps:");
            console.log("   1. Build the application: npm run build");
            console.log("   2. Test the embedded Python functionality");
          } else {
            console.error("❌ Python dependencies installation failed");
            console.log("");
            console.log("🔧 Troubleshooting:");
            console.log("   - Check internet connection");
            console.log(
              "   - Dependencies will be installed automatically on first use"
            );
            console.log("   - Try running the application to complete setup");
          }
        });

        installProcess.on("error", (err) => {
          console.error("❌ Dependency installation error:", err.message);
          console.log("");
          console.log("🔧 Troubleshooting:");
          console.log("   - This may be expected on first run");
          console.log(
            "   - Python dependencies will be installed automatically"
          );
          console.log("   - Try running the application to complete setup");
        });
      } else {
        console.error("❌ Python verification failed with code:", code);
        process.exit(1);
      }
    });

    pythonProcess.on("error", (err) => {
      console.error("❌ Python verification error:", err.message);
      console.log("");
      console.log("🔧 Troubleshooting:");
      console.log("   - This may be expected on first run");
      console.log("   - Python dependencies will be installed automatically");
      console.log("   - Try running the application to complete setup");
    });
  } else {
    console.error("❌ Python executable not found at:", portablePython);
    console.log("");
    console.log("🔧 Troubleshooting:");
    console.log("   1. Delete node_modules and run: npm install");
    console.log(
      "   2. Check if the portable-python package downloaded correctly"
    );
    console.log(
      "   3. Try reinstalling: npm uninstall @bjia56/portable-python-3.11 && npm install @bjia56/portable-python-3.11"
    );
  }
} catch (error) {
  console.error("❌ Setup failed:", error.message);
  console.log("");
  console.log("🔧 Troubleshooting:");
  console.log("   1. Check internet connection");
  console.log("   2. Run: npm install");
  console.log("   3. Try again: node scripts/setup-python.js");
  process.exit(1);
}
