"""Small same-origin gateway for Windows beta testing.

It serves the compiled Vue SPA on 127.0.0.1:8080 and proxies only /api and
/uploads to FastAPI on 127.0.0.1:8000. Cloudflare Tunnel connects to this
single local listener; Vite is never exposed to the internet.
"""

from __future__ import annotations

import argparse
import http.client
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


HOP_BY_HOP_HEADERS = {"connection", "keep-alive", "proxy-authenticate", "proxy-authorization", "te", "trailer", "transfer-encoding", "upgrade"}
BLOCKED_BACKEND_PATHS = {"/docs", "/redoc", "/openapi.json", "/health/ai"}
MAX_UPLOAD_BYTES = 12 * 1024 * 1024


def cache_headers_for(file_path: Path, static_root: Path) -> dict[str, str]:
    normalized_path = str(file_path).replace("\\", "/")
    if "/assets/" in normalized_path:
        return {"Cache-Control": "public, max-age=31536000, immutable"}
    if file_path == static_root / "index.html":
        return {
            "Cache-Control": "no-cache",
            "Cloudflare-CDN-Cache-Control": "no-cache",
        }
    return {"Cache-Control": "no-cache"}


class BetaGatewayHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    static_root: Path
    backend_host: str
    backend_port: int

    def log_message(self, _format: str, *_args: object) -> None:
        # Do not log request paths because import filenames and search terms can
        # appear in URLs. Production observability belongs in the backend.
        return

    def do_GET(self) -> None:  # noqa: N802
        self._handle()

    def do_HEAD(self) -> None:  # noqa: N802
        self._handle(head_only=True)

    def do_POST(self) -> None:  # noqa: N802
        self._handle()

    def do_PUT(self) -> None:  # noqa: N802
        self._handle()

    def do_PATCH(self) -> None:  # noqa: N802
        self._handle()

    def do_DELETE(self) -> None:  # noqa: N802
        self._handle()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._handle()

    def _handle(self, head_only: bool = False) -> None:
        path = urlsplit(self.path).path
        if path == "/api" or path.startswith("/api/"):
            backend_path = path[4:] or "/"
            if backend_path in BLOCKED_BACKEND_PATHS:
                self._send_text(HTTPStatus.NOT_FOUND, "Not found", head_only=head_only)
                return
            self._proxy(backend_path, head_only=head_only)
            return
        if path == "/uploads" or path.startswith("/uploads/"):
            self._proxy(path, head_only=head_only)
            return
        self._serve_spa(path, head_only=head_only)

    def _read_body(self) -> bytes:
        raw_length = self.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError:
            self._send_text(HTTPStatus.BAD_REQUEST, "Invalid request", head_only=False)
            return b""
        if length < 0 or length > MAX_UPLOAD_BYTES:
            self._send_text(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, "File is too large", head_only=False)
            return b""
        return self.rfile.read(length) if length else b""

    def _proxy(self, backend_path: str, *, head_only: bool) -> None:
        body = self._read_body()
        # A normal empty-body POST has ``Content-Length: 0``.  It must still
        # be proxied: several resource actions (for example sharing a course
        # to a study group) intentionally carry all inputs in the URL.  The
        # previous truthiness check treated the string "0" as an incomplete
        # request and returned without ever sending a response to the client.
        if self.command not in {"GET", "HEAD", "OPTIONS"} and self.headers.get("Content-Length") not in {None, "0"} and not body:
            return
        query = urlsplit(self.path).query
        target = backend_path + (f"?{query}" if query else "")
        headers = {
            key: value
            for key, value in self.headers.items()
            if key.lower() not in HOP_BY_HOP_HEADERS | {"host", "content-length"}
        }
        headers["Host"] = f"{self.backend_host}:{self.backend_port}"
        headers["X-Forwarded-Proto"] = "https" if self.headers.get("X-Forwarded-Proto") == "https" else "http"
        # Chain the upstream X-Forwarded-For (e.g. the Cloudflare edge's client
        # IP) instead of overwriting it with the direct peer address, so the
        # backend sees the real client for auth rate limiting.
        incoming_forwarded = self.headers.get("X-Forwarded-For")
        headers["X-Forwarded-For"] = (
            f"{incoming_forwarded}, {self.client_address[0]}" if incoming_forwarded else self.client_address[0]
        )
        if body:
            headers["Content-Length"] = str(len(body))
        try:
            connection = http.client.HTTPConnection(self.backend_host, self.backend_port, timeout=120)
            connection.request(self.command, target, body=body or None, headers=headers)
            response = connection.getresponse()
            payload = response.read()
        except OSError:
            self._send_text(HTTPStatus.BAD_GATEWAY, "Backend is unavailable", head_only=head_only)
            return
        finally:
            try:
                connection.close()
            except UnboundLocalError:
                pass

        is_api_request = self.path == "/api" or self.path.startswith("/api/")
        self.send_response(response.status, response.reason)
        for key, value in response.getheaders():
            if key.lower() not in HOP_BY_HOP_HEADERS | {"content-length", "server", "date"} and not (
                is_api_request and key.lower() == "cache-control"
            ):
                self.send_header(key, value)
        # API responses can include user-specific data and must never be shared
        # by a browser cache or the Cloudflare edge cache.
        if is_api_request:
            self.send_header("Cache-Control", "no-store")
        self._send_security_headers()
        # RFC 9110 forbids a message body on 204/304 responses. In
        # particular, Windows WebRequest clients can wait indefinitely when a
        # proxy adds Content-Length to a 204 response.
        if response.status not in {HTTPStatus.NO_CONTENT, HTTPStatus.NOT_MODIFIED}:
            self.send_header("Content-Length", str(len(payload)))
        else:
            # Make the end-of-response unambiguous for older Windows clients.
            self.send_header("Connection", "close")
        self.end_headers()
        if not head_only and payload:
            self.wfile.write(payload)
        if response.status in {HTTPStatus.NO_CONTENT, HTTPStatus.NOT_MODIFIED}:
            self.close_connection = True

    def _serve_spa(self, request_path: str, *, head_only: bool) -> None:
        relative = request_path.lstrip("/")
        candidate = (self.static_root / relative).resolve()
        try:
            candidate.relative_to(self.static_root)
        except ValueError:
            self._send_text(HTTPStatus.NOT_FOUND, "Not found", head_only=head_only)
            return
        file_path = candidate if candidate.is_file() else self.static_root / "index.html"
        if not file_path.is_file():
            self._send_text(HTTPStatus.SERVICE_UNAVAILABLE, "Beta build is unavailable", head_only=head_only)
            return
        payload = file_path.read_bytes()
        if file_path.parent == self.static_root and file_path.suffix == ".txt":
            # Domain-verification services compare this root-level file byte for byte.
            # Vite copies public text files with a trailing newline, so do not expose it.
            payload = payload.rstrip(b"\r\n")
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self._send_security_headers()
        self.send_header("Content-Type", f"{content_type}; charset=utf-8" if content_type.startswith("text/") or content_type == "application/javascript" else content_type)
        for key, value in cache_headers_for(file_path, self.static_root).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if not head_only:
            self.wfile.write(payload)

    def _send_text(self, status: HTTPStatus, message: str, *, head_only: bool) -> None:
        payload = message.encode("utf-8")
        self.send_response(status)
        self._send_security_headers()
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        if not head_only:
            self.wfile.write(payload)

    def _send_security_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")


def main() -> None:
    parser = argparse.ArgumentParser(description="Xuexibao beta same-origin gateway")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--backend-host", default="127.0.0.1")
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--static-root", type=Path, required=True)
    args = parser.parse_args()

    static_root = args.static_root.resolve()
    if not static_root.is_dir():
        raise SystemExit(f"Compiled frontend directory is missing: {static_root}")

    BetaGatewayHandler.static_root = static_root
    BetaGatewayHandler.backend_host = args.backend_host
    BetaGatewayHandler.backend_port = args.backend_port
    server = ThreadingHTTPServer(("127.0.0.1", args.port), BetaGatewayHandler)
    print(f"Beta gateway listening on http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
