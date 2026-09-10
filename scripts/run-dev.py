"""Own two server processes, verify readiness and stop only those processes."""
import argparse
import json
import shutil
import socket
import subprocess
import sys
import time
from contextlib import ExitStack
from pathlib import Path
from urllib.request import ProxyHandler, build_opener

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / ".runtime"
BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"
# Local readiness checks must not use a machine's external HTTP proxy.
OPENER = build_opener(ProxyHandler({}))


def check_port(port: int) -> None:
    with socket.socket() as connection:
        if sys.platform == "win32":
            connection.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            connection.bind(("127.0.0.1", port))
        except OSError as exc:
            raise RuntimeError(f"Port {port} is busy. Stop the existing server; no process was killed.") from exc


def check_response(url: str, is_health: bool) -> None:
    with OPENER.open(url, timeout=2) as response:
        body = response.read()
        if response.status != 200:
            raise ValueError("Unexpected HTTP status")
        if is_health:
            data = json.loads(body)
            if data.get("status") != "ok" or data.get("database") != "ok":
                raise ValueError("Health response did not report a working database")
        elif b'id="root"' not in body:
            raise ValueError("Frontend HTML root not found")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Validate readiness and stop automatically")
    args = parser.parse_args()
    processes = []
    try:
        python = ROOT / "backend/.venv/Scripts/python.exe"
        vite = ROOT / "frontend/node_modules/vite/bin/vite.js"
        node = shutil.which("node")
        if not python.exists() or not vite.exists() or not node:
            raise RuntimeError("Dependencies missing. Run scripts/setup.ps1 first.")
        for folder in ("backend", "frontend"):
            if not (ROOT / folder / ".env").exists():
                raise RuntimeError(f"{folder}/.env missing. Run scripts/setup.ps1 first.")
        for port in (8000, 5173):
            check_port(port)
        RUNTIME.mkdir(exist_ok=True)
        # Keep file handles open until child processes have been stopped.
        with ExitStack() as stack:
            flags = (subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP) if sys.platform == "win32" else 0
            commands = [
                ("backend", [str(python), "-m", "uvicorn", "app.main:app", "--app-dir", str(ROOT / "backend"), "--host", "127.0.0.1", "--port", "8000"], ROOT),
                ("frontend", [node, str(vite), "--host", "127.0.0.1", "--port", "5173", "--strictPort"], ROOT / "frontend"),
            ]
            try:
                for name, command, cwd in commands:
                    log = stack.enter_context((RUNTIME / f"{name}.log").open("w", encoding="utf-8"))
                    process = subprocess.Popen(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
                    processes.append(process)
                deadline = time.monotonic() + 45
                last_error = ""
                while time.monotonic() < deadline:
                    if any(process.poll() is not None for process in processes):
                        raise RuntimeError(f"A server exited during startup. See logs in {RUNTIME}")
                    try:
                        check_response(f"{BACKEND_URL}/api/health", True)
                        check_response(FRONTEND_URL, False)
                        check_response(f"{FRONTEND_URL}/api/health", True)
                        break
                    except Exception as exc:
                        last_error = type(exc).__name__
                        time.sleep(0.25)
                else:
                    raise RuntimeError(f"Readiness timed out ({last_error}). See logs in {RUNTIME}")
                print(f"Frontend: {FRONTEND_URL}\nAPI docs: {BACKEND_URL}/docs", flush=True)
                print(f"Health and Vite /api proxy verified. Logs: {RUNTIME}", flush=True)
                if args.smoke:
                    print("Smoke check passed.", flush=True)
                    return 0
                print("Press Ctrl+C here to stop both servers. Backend reload is disabled; restart after backend edits.", flush=True)
                while True:
                    if any(process.poll() is not None for process in processes):
                        raise RuntimeError(f"A server stopped. See logs in {RUNTIME}")
                    time.sleep(0.5)
            finally:
                for process in reversed(processes):
                    if process.poll() is None:
                        process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
                if processes:
                    print("Project server processes stopped.", flush=True)
    except KeyboardInterrupt:
        print("Stopped.", flush=True)
        return 0
    except Exception as exc:
        print(f"Startup failed: {exc}", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
