#!/usr/bin/env python3
"""Read-only MCP stdio handshake and paginated tools/list; no tools/call."""
import argparse
import json
import queue
import subprocess
import sys
import threading
import time

MAX_LINE = 4 * 1024 * 1024
PROTOCOLS = {"2024-11-05", "2025-03-26", "2025-06-18", "2025-11-25"}


def probe(command, timeout, protocol):
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    inbox = queue.Queue(maxsize=256)

    def reader():
        try:
            while True:
                line = process.stdout.readline(MAX_LINE + 1)
                if not line:
                    inbox.put(None, timeout=1)
                    return
                if len(line) > MAX_LINE or not line.endswith(b"\n"):
                    inbox.put(ValueError("Server line exceeds limit or lacks newline"), timeout=1)
                    return
                try:
                    value = json.loads(line)
                except (ValueError, UnicodeDecodeError):
                    inbox.put(ValueError("Server stdout is not valid JSON; check protocol/log separation"), timeout=1)
                    return
                inbox.put(value, timeout=1)
        except (OSError, queue.Full):
            return

    threading.Thread(target=reader, daemon=True).start()

    def send(value):
        process.stdin.write((json.dumps(value, ensure_ascii=False) + "\n").encode())
        process.stdin.flush()

    def request(request_id, method, params):
        send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("MCP response timed out")
            try:
                value = inbox.get(timeout=remaining)
            except queue.Empty as error:
                raise TimeoutError("MCP response timed out") from error
            if value is None:
                raise ValueError("Server stdout closed before response")
            if isinstance(value, Exception):
                raise value
            if not isinstance(value, dict) or value.get("jsonrpc") != "2.0":
                raise ValueError("Unexpected non-JSON-RPC message")
            if "method" in value:
                if "id" in value:
                    send({"jsonrpc": "2.0", "id": value["id"], "error": {"code": -32601, "message": "Read-only probe does not implement client requests"}})
                continue
            if value.get("id") != request_id:
                continue
            if "error" in value:
                # Do not print raw server error bodies; they can include credentials or private data.
                code = value["error"].get("code") if isinstance(value["error"], dict) else None
                raise ValueError(f"MCP {method} returned an error (code {code})")
            result = value.get("result")
            if not isinstance(result, dict):
                raise ValueError("Expected an object result")
            return result

    try:
        initialized = request(1, "initialize", {
            "protocolVersion": protocol,
            "capabilities": {},
            "clientInfo": {"name": "desktop-mcp-copilot-probe", "version": "1.0.0"},
        })
        negotiated = initialized.get("protocolVersion")
        if negotiated not in PROTOCOLS:
            raise ValueError("Unknown negotiated protocol; update probe after checking the current MCP specification")
        if not isinstance(initialized.get("capabilities"), dict) or not isinstance(initialized.get("serverInfo"), dict):
            raise ValueError("Invalid initialize response")
        send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        names = []
        cursor = None
        cursors = set()
        for page in range(20):
            result = request(page + 2, "tools/list", {} if cursor is None else {"cursor": cursor})
            tools = result.get("tools")
            if not isinstance(tools, list) or len(tools) > 1000:
                raise ValueError("Invalid or oversized tools list")
            for tool in tools:
                if not isinstance(tool, dict) or not isinstance(tool.get("name"), str) or not isinstance(tool.get("inputSchema"), dict):
                    raise ValueError("Invalid tool schema")
                names.append(tool["name"][:160])
            cursor = result.get("nextCursor")
            if cursor is None:
                break
            if not isinstance(cursor, str) or not cursor or len(cursor) > 4096 or cursor in cursors:
                raise ValueError("Invalid or repeated pagination cursor")
            cursors.add(cursor)
        else:
            raise ValueError("Tool pagination exceeded 20 pages")
        return {"ok": True, "protocol": negotiated, "toolCount": len(names), "tools": names, "stage": "handshake-and-tool-directory-only", "documentRead": False, "toolsCalled": False}
    finally:
        if process.stdin:
            process.stdin.close()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=1)
        if process.stdout:
            process.stdout.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=10, help="Per-request timeout in seconds, 0.1 to 60")
    parser.add_argument("--protocol", choices=sorted(PROTOCOLS), default="2025-06-18")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command or not 0.1 <= args.timeout <= 60:
        parser.error("Provide -- COMMAND [ARGS...] and a timeout from 0.1 to 60")
    try:
        print(json.dumps(probe(command, args.timeout, args.protocol), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TimeoutError, subprocess.SubprocessError) as error:
        print(json.dumps({"ok": False, "error": str(error), "toolsCalled": False}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
