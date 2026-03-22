use std::process::{Child, Command};
use std::sync::Mutex;
use std::path::PathBuf;
use serde::{Deserialize, Serialize};
use tauri::State;

struct SidecarProcesses {
    backend: Mutex<Option<Child>>,
    frontend: Mutex<Option<Child>>,
}

#[derive(Serialize, Deserialize)]
struct BackendStatus {
    running: bool,
    port: u16,
}

fn data_dir() -> PathBuf {
    dirs::home_dir().unwrap_or_default().join(".swarmforge")
}

fn project_root() -> PathBuf {
    // Dev: cwd is the project root
    let cwd = std::env::current_dir().unwrap_or_default();
    if cwd.join("backend").exists() {
        return cwd;
    }
    // .app bundle: executable is at SwarmForge.app/Contents/MacOS/swarmforge-desktop
    std::env::current_exe()
        .unwrap_or_default()
        .parent()
        .unwrap_or(std::path::Path::new("."))
        .join("../Resources")
        .to_path_buf()
}

fn find_python() -> Option<String> {
    let venv_python = data_dir().join("venv/bin/python3");
    if venv_python.exists() {
        return Some(venv_python.to_string_lossy().to_string());
    }
    which::which("python3").ok().map(|p| p.to_string_lossy().to_string())
}

fn find_node() -> Option<String> {
    which::which("node").ok().map(|p| p.to_string_lossy().to_string())
}

#[tauri::command]
async fn start_backend(state: State<'_, SidecarProcesses>) -> Result<String, String> {
    // Start Python backend
    {
        let mut guard = state.backend.lock().map_err(|e| e.to_string())?;
        if guard.is_some() {
            return Ok("already running".to_string());
        }

        let python = find_python().ok_or("Python3 not found")?;
        let data = data_dir();
        std::fs::create_dir_all(&data).map_err(|e| e.to_string())?;

        let db_path = data.join("swarmforge.db");
        let db_url = format!("sqlite+aiosqlite:///{}", db_path.display());
        let root = project_root();

        let child = Command::new(&python)
            .args(["-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"])
            .current_dir(root.join("backend"))
            .env("SWARMFORGE_DESKTOP_MODE", "true")
            .env("DATABASE_URL", &db_url)
            .env("DATABASE_URL_SYNC", db_url.replace("sqlite+aiosqlite", "sqlite"))
            .env("CORS_ORIGINS", "tauri://localhost,http://localhost:3000")
            .spawn()
            .map_err(|e| format!("Failed to start backend: {}", e))?;

        *guard = Some(child);
    }

    // Start Next.js standalone frontend
    {
        let mut guard = state.frontend.lock().map_err(|e| e.to_string())?;
        if guard.is_none() {
            let node = find_node().ok_or("Node.js not found")?;
            let root = project_root();
            let standalone_dir = root.join("frontend/.next/standalone");

            if standalone_dir.exists() {
                let child = Command::new(&node)
                    .args(["server.js"])
                    .current_dir(&standalone_dir)
                    .env("PORT", "3000")
                    .env("HOSTNAME", "127.0.0.1")
                    .spawn()
                    .map_err(|e| format!("Failed to start frontend: {}", e))?;
                *guard = Some(child);
            }
        }
    }

    Ok("started".to_string())
}

#[tauri::command]
async fn stop_backend(state: State<'_, SidecarProcesses>) -> Result<String, String> {
    if let Ok(mut guard) = state.backend.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
    if let Ok(mut guard) = state.frontend.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
    Ok("stopped".to_string())
}

#[tauri::command]
async fn get_backend_status(state: State<'_, SidecarProcesses>) -> Result<BackendStatus, String> {
    let guard = state.backend.lock().map_err(|e| e.to_string())?;
    Ok(BackendStatus {
        running: guard.is_some(),
        port: 8000,
    })
}

#[tauri::command]
async fn get_data_dir() -> Result<String, String> {
    Ok(data_dir().to_string_lossy().to_string())
}

#[tauri::command]
async fn save_settings(settings: serde_json::Value) -> Result<(), String> {
    let path = data_dir().join("settings.json");
    std::fs::create_dir_all(data_dir()).map_err(|e| e.to_string())?;
    let json = serde_json::to_string_pretty(&settings).map_err(|e| e.to_string())?;
    std::fs::write(path, json).map_err(|e| e.to_string())
}

#[tauri::command]
async fn load_settings() -> Result<serde_json::Value, String> {
    let path = data_dir().join("settings.json");
    if !path.exists() {
        return Ok(serde_json::json!({}));
    }
    let content = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&content).map_err(|e| e.to_string())
}

fn kill_sidecars(state: &SidecarProcesses) {
    if let Ok(mut guard) = state.backend.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
    if let Ok(mut guard) = state.frontend.lock() {
        if let Some(mut child) = guard.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .manage(SidecarProcesses {
            backend: Mutex::new(None),
            frontend: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            start_backend,
            stop_backend,
            get_backend_status,
            get_data_dir,
            save_settings,
            load_settings,
        ])
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                if let Some(state) = window.try_state::<SidecarProcesses>() {
                    kill_sidecars(&state);
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
