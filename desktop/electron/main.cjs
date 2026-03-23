const { app, BrowserWindow } = require("electron");
const { spawn, execSync } = require("child_process");
const path = require("path");
const http = require("http");

const PORT = 3001;
const SERVER_URL = `http://127.0.0.1:${PORT}`;

let serverProcess = null;
let mainWindow = null;

// Find system node (not Electron's bundled one)
function findSystemNode() {
  try {
    // Source shell profile to get full PATH
    const shell = process.env.SHELL || "/bin/zsh";
    const nodePath = execSync(`${shell} -ilc "which node"`, { encoding: "utf8" }).trim();
    if (nodePath) return nodePath;
  } catch {}
  return "node"; // fallback
}

// Find tsx for running TypeScript
function findTsx() {
  const localTsx = path.join(__dirname, "..", "node_modules", ".bin", "tsx");
  const { existsSync } = require("fs");
  if (existsSync(localTsx)) return localTsx;
  try {
    return execSync("which tsx", { encoding: "utf8" }).trim();
  } catch {}
  return "tsx";
}

function startServer() {
  const nodePath = findSystemNode();
  const tsxPath = findTsx();
  const serverDir = path.join(__dirname, "..");
  const serverScript = path.join(serverDir, "server", "server.ts");

  console.log(`Starting server with: ${nodePath} ${tsxPath} ${serverScript}`);

  serverProcess = spawn(nodePath, [tsxPath, serverScript], {
    cwd: serverDir,
    env: {
      ...process.env,
      PORT: String(PORT),
      NODE_ENV: "production",
      STUDIO_NODE_PATH: nodePath,
    },
    stdio: ["ignore", "pipe", "pipe"],
  });

  serverProcess.stdout.on("data", (d) => console.log(`[server] ${d.toString().trim()}`));
  serverProcess.stderr.on("data", (d) => console.error(`[server] ${d.toString().trim()}`));
  serverProcess.on("exit", (code) => console.log(`Server exited with code ${code}`));
}

async function waitForServer(maxRetries = 60) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      await new Promise((resolve, reject) => {
        http.get(`${SERVER_URL}/api/health`, (res) => {
          if (res.statusCode === 200) resolve(true);
          else reject();
        }).on("error", reject);
      });
      console.log("Server is ready");
      return;
    } catch {
      await new Promise((r) => setTimeout(r, 500));
    }
  }
  throw new Error("Server failed to start within 30 seconds");
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    title: "SwarmForge",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // In production, load from Express server (which serves built React)
  // In dev, could load Vite dev server
  mainWindow.loadURL(SERVER_URL);

  mainWindow.on("closed", () => { mainWindow = null; });
}

// App lifecycle
app.whenReady().then(async () => {
  try {
    startServer();
    await waitForServer();
    createWindow();
  } catch (err) {
    console.error("Failed to start:", err);
    app.quit();
  }
});

app.on("window-all-closed", () => {
  app.quit();
});

app.on("before-quit", () => {
  if (serverProcess) {
    serverProcess.kill("SIGTERM");
    // Force kill after 3 seconds
    setTimeout(() => {
      if (serverProcess) serverProcess.kill("SIGKILL");
    }, 3000);
  }
});
