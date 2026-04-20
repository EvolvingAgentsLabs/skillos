//! Python forge server sidecar.
//!
//! Spawns `python -m forge serve` in a child process, waits for /health
//! to come up, and stops the process on Drop or explicit shutdown.
//!
//! Kept deliberately minimal — no process supervision, restart policies,
//! or health monitoring.  The app exits if the sidecar dies.  A future
//! iteration should add backoff + restart.

use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::time::{Duration, Instant};

#[derive(Clone, Debug)]
pub struct SidecarConfig {
    pub host: String,
    pub port: u16,
    pub token: String,
    pub repo_root: PathBuf,
}

pub struct Sidecar {
    child: Option<Child>,
    #[allow(dead_code)]
    cfg: SidecarConfig,
}

impl Sidecar {
    pub fn spawn(cfg: SidecarConfig) -> std::io::Result<Self> {
        let python = which_python();
        let child = Command::new(&python)
            .current_dir(&cfg.repo_root)
            .args([
                "-m", "forge", "serve",
                "--host", &cfg.host,
                "--port", &cfg.port.to_string(),
            ])
            .env("FORGE_API_TOKEN", &cfg.token)
            .env("PYTHONUNBUFFERED", "1")
            .stdout(Stdio::inherit())
            .stderr(Stdio::inherit())
            .spawn()?;

        // Block until /health responds or a generous timeout.  This keeps
        // the UI from rendering against a dead backend on first paint.
        wait_for_health(&cfg, Duration::from_secs(15));

        Ok(Self { child: Some(child), cfg })
    }

    pub fn shutdown(&mut self) -> std::io::Result<()> {
        if let Some(mut child) = self.child.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
        Ok(())
    }
}

impl Drop for Sidecar {
    fn drop(&mut self) {
        let _ = self.shutdown();
    }
}

/// Pick the Python interpreter.  We prefer ``python3`` on POSIX and
/// ``python`` on Windows; override with ``SKILLOS_PYTHON`` when
/// distributing a bundled interpreter.
fn which_python() -> String {
    if let Ok(p) = std::env::var("SKILLOS_PYTHON") {
        return p;
    }
    if cfg!(target_os = "windows") {
        "python".into()
    } else {
        "python3".into()
    }
}

fn wait_for_health(cfg: &SidecarConfig, budget: Duration) {
    let url = format!("http://{}:{}/health", cfg.host, cfg.port);
    let deadline = Instant::now() + budget;
    while Instant::now() < deadline {
        if let Ok(resp) = ureq_get(&url) {
            if resp {
                return;
            }
        }
        std::thread::sleep(Duration::from_millis(150));
    }
    eprintln!("[sidecar] health check timed out after {}ms — continuing anyway",
              budget.as_millis());
}

/// Minimal synchronous GET using reqwest's blocking feature is overkill
/// here; use a tiny hand-rolled TCP probe instead so we do not have to
/// link reqwest's blocking code.
fn ureq_get(url: &str) -> std::io::Result<bool> {
    // Parse host:port and issue a trivial HTTP/1.0 GET.
    let (host, port, path) = parse_url(url)
        .ok_or_else(|| std::io::Error::new(std::io::ErrorKind::InvalidInput,
                                           "bad url"))?;
    use std::io::{Read, Write};
    let mut stream = std::net::TcpStream::connect_timeout(
        &format!("{host}:{port}").parse().map_err(|_| {
            std::io::Error::new(std::io::ErrorKind::InvalidInput, "addr parse")
        })?,
        Duration::from_millis(500),
    )?;
    stream.set_read_timeout(Some(Duration::from_millis(500)))?;
    let req = format!("GET {path} HTTP/1.0\r\nHost: {host}\r\n\r\n");
    stream.write_all(req.as_bytes())?;
    let mut buf = [0u8; 128];
    let n = stream.read(&mut buf).unwrap_or(0);
    let text = std::str::from_utf8(&buf[..n]).unwrap_or("");
    Ok(text.contains("200 OK"))
}

fn parse_url(url: &str) -> Option<(String, u16, String)> {
    let stripped = url.strip_prefix("http://")?;
    let (hostport, path) = match stripped.find('/') {
        Some(i) => (&stripped[..i], &stripped[i..]),
        None => (stripped, "/"),
    };
    let (host, port) = match hostport.rsplit_once(':') {
        Some((h, p)) => (h.to_string(), p.parse().ok()?),
        None => (hostport.to_string(), 80),
    };
    Some((host, port, path.to_string()))
}
