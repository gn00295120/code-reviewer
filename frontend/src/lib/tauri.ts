/**
 * Tauri IPC wrapper — provides typed access to Rust backend commands.
 * Falls back gracefully in web (non-Tauri) mode.
 */

export function isTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI__" in window;
}

async function invoke<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  if (!isTauri()) throw new Error("Not running in Tauri");
  const { invoke: tauriInvoke } = await import("@tauri-apps/api/core");
  return tauriInvoke<T>(cmd, args);
}

export interface BackendStatus {
  running: boolean;
  port: number;
}

export async function startBackend(): Promise<string> {
  return invoke<string>("start_backend");
}

export async function stopBackend(): Promise<string> {
  return invoke<string>("stop_backend");
}

export async function getBackendStatus(): Promise<BackendStatus> {
  return invoke<BackendStatus>("get_backend_status");
}

export async function getDataDir(): Promise<string> {
  return invoke<string>("get_data_dir");
}

export async function saveSettings(settings: Record<string, unknown>): Promise<void> {
  return invoke<void>("save_settings", { settings });
}

export async function loadSettings(): Promise<Record<string, unknown>> {
  return invoke<Record<string, unknown>>("load_settings");
}
