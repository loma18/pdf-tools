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
        console.log(
          "🔧 Installing Python dependencies from requirements.txt..."
        );

        // 依据 requirements.txt 安装依赖，写入便携 Python 的 site-packages
        const requirementsPath = path.join(
          __dirname,
          "..",
          "python-backend",
          "requirements.txt"
        );
        const requirementsExists = fs.existsSync(requirementsPath);

        const args = [
          "-m",
          "pip",
          "install",
          "--prefer-binary",
          "--no-cache-dir",
        ];
        if (requirementsExists) {
          args.push("-r", requirementsPath);
        } else {
          // 兜底：最少安装运行所需
          args.push("PyMuPDF", "python-dotenv", "requests");
        }

        // 使用官方源安装，构建机需联网；安装后被打包进 extraResources
        const installProcess = spawn(portablePython, args, {
          stdio: "inherit",
          shell: false,
        });

        installProcess.on("close", (installCode) => {
          if (installCode === 0) {
            console.log(
              "🎉 Embedded Python deps installed into portable runtime!"
            );
            console.log("");
            console.log("📋 Next steps:");
            console.log("   1. Build the application: npm run build");
            console.log(
              "   2. The packaged app will contain all Python deps (offline ready)"
            );
          } else {
            console.error("❌ Python dependencies installation failed");
            console.log("");
            console.log("🔧 Troubleshooting:");
            console.log(
              "   - Ensure the build machine can access PyPI during prebuild"
            );
            console.log("   - Check the wheel availability for this platform");
            console.log("   - You can rerun: npm run setup-python");
            process.exit(1);
          }
        });

        installProcess.on("error", (err) => {
          console.error("❌ Dependency installation error:", err.message);
          console.log("");
          console.log("🔧 Troubleshooting:");
          console.log("   - Ensure network connectivity for the build machine");
          console.log("   - Try running the application build again");
          process.exit(1);
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
      process.exit(1);
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
    process.exit(1);
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
