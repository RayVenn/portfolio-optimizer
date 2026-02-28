"""Minimal HTTP health server running in a background daemon thread."""

import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer


@dataclass
class HealthState:
    produced: int = 0
    dlq_count: int = 0
    ws_connected: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def increment_produced(self) -> None:
        with self._lock:
            self.produced += 1

    def increment_dlq(self) -> None:
        with self._lock:
            self.dlq_count += 1

    def set_ws_connected(self, connected: bool) -> None:
        with self._lock:
            self.ws_connected = connected

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "status": "ok",
                "produced": self.produced,
                "dlq": self.dlq_count,
                "ws_connected": self.ws_connected,
            }


_state = HealthState()


def get_state() -> HealthState:
    return _state


def _make_handler(state: HealthState) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path == "/health":
                body = json.dumps(state.snapshot()).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, fmt: str, *args: object) -> None:
            pass  # silence default access logs

    return Handler


def start(port: int) -> HealthState:
    state = get_state()
    server = HTTPServer(("0.0.0.0", port), _make_handler(state))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return state
