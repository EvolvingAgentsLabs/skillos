//! SkillOS desktop shell.
//!
//! This is a thin Tauri 2 host over the forge HTTP API.  Responsibilities:
//!
//! 1. Start the Python forge sidecar (`python -m forge serve`) on launch.
//! 2. Generate a bearer token and pass it to both the sidecar and the
//!    frontend so API calls are authenticated.
//! 3. Expose a small set of `tauri::command` wrappers that call the local
//!    HTTP API from Rust, sparing the WebView from CORS and CSP pain.
//! 4. Shut down the sidecar on window close.
//!
//! The sidecar and the WebView never talk to the network except to
//! 127.0.0.1, and the CSP in `tauri.conf.json` enforces that.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod commands;
mod sidecar;

use std::sync::Mutex;

use sidecar::{Sidecar, SidecarConfig};

/// Shared app state.  Held behind a mutex because sidecar shutdown races
/// with window events on app exit.
pub struct AppState {
    pub sidecar: Mutex<Option<Sidecar>>,
    pub api_base: String,
    pub api_token: String,
}

fn generate_token() -> String {
    // 32 hex chars from the system RNG — enough for a local-only token.
    use rand::RngCore;
    let mut buf = [0u8; 16];
    rand::thread_rng().fill_bytes(&mut buf);
    buf.iter().map(|b| format!("{:02x}", b)).collect()
}

fn main() {
    let token = generate_token();
    let port = std::env::var("FORGE_PORT")
        .ok()
        .and_then(|s| s.parse::<u16>().ok())
        .unwrap_or(8765);
    let api_base = format!("http://127.0.0.1:{port}");

    let sidecar_cfg = SidecarConfig {
        host: "127.0.0.1".into(),
        port,
        token: token.clone(),
        repo_root: std::env::current_dir().unwrap_or_default(),
    };

    tauri::Builder::default()
        .manage(AppState {
            sidecar: Mutex::new(None),
            api_base,
            api_token: token,
        })
        .setup(move |app| {
            let handle = app.handle().clone();
            let state: tauri::State<AppState> = handle.state();
            let sidecar = Sidecar::spawn(sidecar_cfg.clone())?;
            *state.sidecar.lock().unwrap() = Some(sidecar);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::get_health,
            commands::get_api_base,
            commands::route_goal,
            commands::get_budget,
            commands::get_journal,
            commands::get_audit,
            commands::run_forge_job,
        ])
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::Destroyed) {
                let state: tauri::State<AppState> = window.state();
                if let Some(mut sc) = state.sidecar.lock().unwrap().take() {
                    let _ = sc.shutdown();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("failed to launch SkillOS desktop");
}
