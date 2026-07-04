import json
import sys
import threading
import time
from http.client import HTTPSConnection, HTTPException
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import socket
import urllib.parse
import os

TOKEN = "YOUR_TOKEN_HERE"
CHANNEL_ID = "1512956231919337482"

COMMANDS = [
    "!crime",
    "!dep all"
]

SCHEDULED_COMMANDS = {
    "!work": 60,
    "!slut": 120,
}

DELAY_BETWEEN = 0.0005
SLEEP_CYCLE = 300
NETWORK_CHECK_INTERVAL = 5
DASHBOARD_PORT = 8080

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

STATUS = {
    "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "network": "checking",
    "token_valid": False,
    "commands": {},
    "recent_log": [],
}
STATUS_LOCK = threading.Lock()

def timestamp():
    return f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"

def log_to_status(message, command=None, success=None):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "message": message,
        "command": command,
        "success": success,
    }
    with STATUS_LOCK:
        STATUS["recent_log"].append(entry)
        if len(STATUS["recent_log"]) > 50:
            STATUS["recent_log"] = STATUS["recent_log"][-50:]
        if command and command in STATUS["commands"]:
            STATUS["commands"][command]["last_sent"] = entry["time"]
            STATUS["commands"][command]["last_success"] = success
            STATUS["commands"][command]["count"] += 1

def wait_for_network():
    while True:
        try:
            conn = HTTPSConnection("discordapp.com", 443, timeout=5)
            conn.request("GET", "/api/v9/users/@me")
            resp = conn.getresponse()
            if resp.status in (200, 401):
                conn.close()
                with STATUS_LOCK:
                    STATUS["network"] = "online"
                return
            conn.close()
        except (socket.error, socket.timeout, HTTPException, ConnectionError):
            with STATUS_LOCK:
                STATUS["network"] = "offline"
            print(f"{timestamp()} ⚠ Network down. Retrying in {NETWORK_CHECK_INTERVAL}s...")
            time.sleep(NETWORK_CHECK_INTERVAL)
        except Exception:
            with STATUS_LOCK:
                STATUS["network"] = "unknown"
            print(f"{timestamp()} ⚠ Discord unreachable. Retrying...")
            time.sleep(NETWORK_CHECK_INTERVAL)

def send_message(conn, content, headers, retry_count=0):
    max_retries = 3
    try:
        payload = json.dumps({"content": content})
        conn.request("POST", f"/api/v9/channels/{CHANNEL_ID}/messages", payload, headers)
        resp = conn.getresponse()
        body = resp.read().decode()

        if 200 <= resp.status < 300:
            print(f"{timestamp()} ✓ {content}")
            log_to_status(f"✓ {content}", content, True)
            return True

        if resp.status == 401:
            print(f"{timestamp()} ❌ Invalid token")
            log_to_status("❌ Invalid token", content, False)
            sys.exit(1)
        elif resp.status == 403:
            print(f"{timestamp()} ❌ Forbidden")
            log_to_status("❌ Forbidden", content, False)
            sys.exit(1)
        elif resp.status == 404:
            print(f"{timestamp()} ❌ Channel not found")
            log_to_status("❌ Channel not found", content, False)
            sys.exit(1)
        elif resp.status == 429:
            retry_after = int(resp.headers.get('Retry-After', 1))
            print(f"{timestamp()} ⏳ Rate limited, waiting {retry_after}s...")
            log_to_status(f"⏳ Rate limited (wait {retry_after}s)", content, False)
            time.sleep(retry_after)
            return send_message(conn, content, headers, retry_count + 1)
        else:
            print(f"{timestamp()} ✗ {content} (HTTP {resp.status})")
            log_to_status(f"✗ HTTP {resp.status}", content, False)
            if body:
                print(f"{timestamp()}    Response: {body}")
            return False

    except (socket.error, socket.timeout, HTTPException, ConnectionError) as e:
        print(f"{timestamp()} ⚠ Connection lost: {e}")
        log_to_status("⚠ Connection lost", content, False)
        if retry_count < max_retries:
            print(f"{timestamp()} Retrying ({retry_count+1}/{max_retries})...")
            time.sleep(2 ** retry_count)
            new_conn = HTTPSConnection("discordapp.com", 443)
            return send_message(new_conn, content, headers, retry_count + 1)
        else:
            print(f"{timestamp()} ❌ Max retries reached, skipping.")
            log_to_status("❌ Max retries", content, False)
            return False
    except Exception as e:
        print(f"{timestamp()} ⚠ Unexpected error: {e}")
        log_to_status(f"⚠ {str(e)[:50]}", content, False)
        return False

def send_command_periodically(command, interval, headers):
    print(f"{timestamp()} 🔄 Scheduler started: '{command}' every {interval}s")
    log_to_status(f"🔄 Started: {command} ({interval}s)", command, None)
    while True:
        wait_for_network()
        conn = HTTPSConnection("discordapp.com", 443)
        send_message(conn, command, headers)
        conn.close()
        time.sleep(interval)

class DashboardHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/dashboard.html":
            self.serve_file("dashboard.html", "text/html")
        elif path == "/style.css":
            self.serve_file("style.css", "text/css")
        elif path == "/status":
            self.serve_status()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(f"404 Not Found: {path}".encode())

    def serve_file(self, filename, content_type):
        possible_paths = [
            os.path.join(SCRIPT_DIR, filename),
            os.path.join(os.getcwd(), filename),
            filename,
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'rb') as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header('Content-type', content_type)
                    self.end_headers()
                    self.wfile.write(content)
                    return
                except Exception as e:
                    print(f"{timestamp()} ⚠ Error reading {path}: {e}")
                    continue
        self.send_response(404)
        self.end_headers()
        self.wfile.write(f"File '{filename}' not found.".encode())

    def serve_status(self):
        with STATUS_LOCK:
            status_copy = {
                "started_at": STATUS["started_at"],
                "network": STATUS["network"],
                "token_valid": STATUS["token_valid"],
                "commands": STATUS["commands"].copy(),
                "recent_log": STATUS["recent_log"].copy(),
            }
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(status_copy).encode())

def run_dashboard():
    server = HTTPServer(('0.0.0.0', DASHBOARD_PORT), DashboardHandler)
    print(f"{timestamp()} 🌐 Dashboard: http://localhost:{DASHBOARD_PORT}")
    server.serve_forever()

def main():
    print(f"{timestamp()} Starting auto‑sender")
    print(f"{timestamp()} Main: {', '.join(COMMANDS)}")
    print(f"{timestamp()} Scheduled:")
    for cmd, interval in SCHEDULED_COMMANDS.items():
        print(f"  - {cmd}: every {interval}s ({interval//60}m)")
    print(f"{timestamp()} Dashboard: http://localhost:{DASHBOARD_PORT}\n")

    all_cmds = list(COMMANDS) + list(SCHEDULED_COMMANDS.keys())
    with STATUS_LOCK:
        for cmd in all_cmds:
            STATUS["commands"][cmd] = {
                "last_sent": None,
                "last_success": None,
                "count": 0,
            }

    print(f"{timestamp()} Checking network...")
    wait_for_network()
    print(f"{timestamp()} ✅ Network available!")

    print(f"{timestamp()} Validating token...")
    test_conn = HTTPSConnection("discordapp.com", 443)
    test_headers = {"authorization": TOKEN, "host": "discordapp.com"}
    try:
        test_conn.request("GET", "/api/v9/users/@me", headers=test_headers)
        test_resp = test_conn.getresponse()
        if test_resp.status == 200:
            print(f"{timestamp()} ✅ Token valid!\n")
            with STATUS_LOCK:
                STATUS["token_valid"] = True
            log_to_status("✅ Token validated", None, None)
        elif test_resp.status == 401:
            print(f"{timestamp()} ❌ Invalid token")
            log_to_status("❌ Invalid token", None, False)
            sys.exit(1)
        else:
            print(f"{timestamp()} ⚠ Unexpected response: {test_resp.status}")
            with STATUS_LOCK:
                STATUS["token_valid"] = False
    except Exception as e:
        print(f"{timestamp()} ⚠ Could not validate: {e}")
        with STATUS_LOCK:
            STATUS["token_valid"] = False
    finally:
        test_conn.close()

    headers = {
        "content-type": "application/json",
        "authorization": TOKEN,
        "host": "discordapp.com",
    }

    threading.Thread(target=run_dashboard, daemon=True).start()

    for cmd, interval in SCHEDULED_COMMANDS.items():
        threading.Thread(
            target=send_command_periodically,
            args=(cmd, interval, headers),
            daemon=True
        ).start()

    cycle = 0
    while True:
        cycle += 1
        print(f"{timestamp()} === Main cycle {cycle} ===")

        for cmd in COMMANDS:
            wait_for_network()
            conn = HTTPSConnection("discordapp.com", 443)
            send_message(conn, cmd, headers)
            conn.close()
            time.sleep(DELAY_BETWEEN)

        print(f"{timestamp()} Main cycle complete. Sleeping {SLEEP_CYCLE//60} min...\n")
        time.sleep(SLEEP_CYCLE)

if __name__ == "__main__":
    main()
