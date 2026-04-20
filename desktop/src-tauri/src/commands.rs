//! `tauri::command` wrappers over the forge HTTP API.
//!
//! The WebView could call the API directly, but routing through the Rust
//! host gives us:
//!
//! * one place to inject the bearer token,
//! * a stable surface that does not depend on fetch semantics,
//! * the option to short-circuit calls when the sidecar is down.

use crate::AppState;
use serde::Serialize;
use serde_json::Value;
use tauri::State;

#[derive(Serialize)]
pub struct ApiError {
    pub status: u16,
    pub message: String,
}

async fn client(state: &AppState) -> reqwest::Client {
    reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(30))
        .build()
        .unwrap_or_else(|_| reqwest::Client::new())
}

async fn get_json(state: &AppState, path: &str) -> Result<Value, ApiError> {
    let url = format!("{}{}", state.api_base, path);
    let resp = client(state).await
        .get(&url)
        .bearer_auth(&state.api_token)
        .send()
        .await
        .map_err(|e| ApiError { status: 0, message: format!("request: {e}") })?;
    let status = resp.status().as_u16();
    let body: Value = resp.json().await.unwrap_or(Value::Null);
    if status >= 400 {
        return Err(ApiError {
            status,
            message: body["error"].as_str().unwrap_or("http error").to_string(),
        });
    }
    Ok(body)
}

async fn post_json(state: &AppState, path: &str,
                   body: Value) -> Result<Value, ApiError> {
    let url = format!("{}{}", state.api_base, path);
    let resp = client(state).await
        .post(&url)
        .bearer_auth(&state.api_token)
        .json(&body)
        .send()
        .await
        .map_err(|e| ApiError { status: 0, message: format!("request: {e}") })?;
    let status = resp.status().as_u16();
    let body: Value = resp.json().await.unwrap_or(Value::Null);
    if status >= 400 {
        return Err(ApiError {
            status,
            message: body["error"].as_str().unwrap_or("http error").to_string(),
        });
    }
    Ok(body)
}

#[tauri::command]
pub async fn get_api_base(state: State<'_, AppState>) -> Result<String, String> {
    Ok(state.api_base.clone())
}

#[tauri::command]
pub async fn get_health(state: State<'_, AppState>) -> Result<Value, ApiError> {
    get_json(&state, "/health").await
}

#[tauri::command]
pub async fn route_goal(state: State<'_, AppState>,
                        body: Value) -> Result<Value, ApiError> {
    post_json(&state, "/api/route", body).await
}

#[tauri::command]
pub async fn get_budget(state: State<'_, AppState>,
                        project: String) -> Result<Value, ApiError> {
    let path = format!("/api/budget?project={}", urlencoding(&project));
    get_json(&state, &path).await
}

#[tauri::command]
pub async fn get_journal(state: State<'_, AppState>,
                         project: String,
                         tail: Option<u32>) -> Result<Value, ApiError> {
    let path = format!(
        "/api/journal?project={}&tail={}",
        urlencoding(&project),
        tail.unwrap_or(0),
    );
    get_json(&state, &path).await
}

#[tauri::command]
pub async fn get_audit(state: State<'_, AppState>,
                       model: Option<String>) -> Result<Value, ApiError> {
    let m = model.unwrap_or_else(|| "gemma4:e2b".to_string());
    let path = format!("/api/audit?model={}", urlencoding(&m));
    get_json(&state, &path).await
}

#[tauri::command]
pub async fn run_forge_job(state: State<'_, AppState>,
                           body: Value) -> Result<Value, ApiError> {
    post_json(&state, "/api/forge/run", body).await
}

// Tiny URL-encoder — we only need it for loopback paths, so the subset
// of characters handled is intentionally narrow.
fn urlencoding(s: &str) -> String {
    s.bytes()
        .flat_map(|b| -> Box<dyn Iterator<Item = u8>> {
            match b {
                b'A'..=b'Z' | b'a'..=b'z' | b'0'..=b'9'
                    | b'-' | b'_' | b'.' | b'~' | b'/' | b':' =>
                    Box::new(std::iter::once(b)),
                _ => Box::new(format!("%{:02X}", b).into_bytes().into_iter()),
            }
        })
        .map(|b| b as char)
        .collect()
}
