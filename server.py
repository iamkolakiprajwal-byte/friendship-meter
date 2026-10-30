#!/usr/bin/env python3
"""
Friendship Meter - Backend Server
Supports:
- Secure environment configuration (PRAJWAL_LAT, PRAJWAL_LON, ADMIN_PASSWORD)
- SQLite database persistence for sessions, answers, and consented location submissions
- Haversine distance calculation to Prajwal's reference coordinates (without exposing them publicly)
- Deterministic quiz and distance scoring
- Authenticated Administrator Dashboard (/admin)
"""

import os
import json
import math
import sqlite3
import hashlib
import secrets
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# --- Configuration & Environment Variables ---
PRAJWAL_LAT = float(os.environ.get("PRAJWAL_LAT", "13.103691"))
PRAJWAL_LON = float(os.environ.get("PRAJWAL_LON", "77.570392"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Prajwalvedika")
PORT = int(os.environ.get("PORT", "8000"))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "friendship_meter.db")

# Active admin tokens (in-memory session store)
active_admin_tokens = set()

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Game sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id TEXT PRIMARY KEY,
        player_alias TEXT,
        created_at TEXT,
        updated_at TEXT,
        quiz_score REAL,
        distance_km REAL,
        distance_score REAL,
        final_score REAL,
        result_band TEXT,
        destination TEXT
    )
    """)
    
    # Quiz answers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        question_idx INTEGER,
        question_text TEXT,
        selected_text TEXT,
        score_val REAL,
        created_at TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """)
    
    # Consented locations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        latitude REAL,
        longitude REAL,
        accuracy_m REAL,
        consented INTEGER,
        consent_timestamp TEXT,
        created_at TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(session_id)
    )
    """)
    
    conn.commit()
    conn.close()

# --- Distance Calculation (Haversine Formula) ---
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate great-circle distance between two points on Earth in kilometres.
    """
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def calculate_distance_score(dist_km):
    """
    Distance score bands:
    - 0–5 km: 100 points
    - >5 km up to 25 km: 80 points
    - >25 km up to 100 km: 60 points
    - >100 km up to 300 km: 40 points
    - >300 km: 20 points
    """
    if dist_km <= 5.0:
        return 100.0
    elif dist_km <= 25.0:
        return 80.0
    elif dist_km <= 100.0:
        return 60.0
    elif dist_km <= 300.0:
        return 40.0
    else:
        return 20.0

def get_distance_caption(dist_km):
    if dist_km <= 25.0:
        return "Arey, almost same area! Chai break banto."
    elif dist_km <= 300.0:
        return "Thoda travel tar banta hai. Road trip energy!"
    else:
        return "Bakbak sathi kilometres don't matter. Long distance gappa mode!"

def get_result_band(score):
    """
    Result bands:
    - 0–39: Ajun olakh vhaychi aahe
    - 40–59: Chai-pani acquaintances
    - 60–79: Gappa gang material
    - 80–94: Gappa Champion
    - 95–100: Full-time bakbak partner
    """
    score = round(score)
    if score < 40:
        return "Ajun olakh vhaychi aahe"
    elif score < 60:
        return "Chai-pani acquaintances"
    elif score < 80:
        return "Gappa gang material"
    elif score < 95:
        return "Gappa Champion"
    else:
        return "Full-time bakbak partner"

def calculate_final_score(quiz_score, distance_score):
    """
    Final score = round((Quiz score × 0.80) + (Distance score × 0.20))
    Clamped to 0..100
    """
    raw = (quiz_score * 0.80) + (distance_score * 0.20)
    score = round(raw)
    return max(0, min(100, score))

# --- HTTP Request Handler ---
class FriendshipMeterHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def _send_json(self, data, status=HTTPStatus.OK):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, message, status=HTTPStatus.BAD_REQUEST):
        self._send_json({"error": message}, status=status)

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        if path == "/api/config":
            # Returns app config without exposing Prajwal's exact location coordinates
            self._send_json({
                "appName": "Friendship Meter",
                "hasReferenceLocation": bool(PRAJWAL_LAT and PRAJWAL_LON),
                "scoringRules": {
                    "quizWeight": 0.80,
                    "distanceWeight": 0.20
                }
            })
            return

        if path == "/admin":
            # Serve the built-in admin dashboard page
            self._serve_admin_page()
            return

        if path == "/api/admin/sessions":
            # Verify auth token
            auth_header = self.headers.get("Authorization", "")
            token = auth_header.replace("Bearer ", "").strip()
            if not token or token not in active_admin_tokens:
                self._send_error("Unauthorized administrator access", HTTPStatus.UNAUTHORIZED)
                return

            # Fetch all sessions & locations
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT s.*, 
                   (SELECT COUNT(*) FROM locations l WHERE l.session_id = s.session_id AND l.consented = 1) as location_count,
                   (SELECT l.latitude FROM locations l WHERE l.session_id = s.session_id AND l.consented = 1 ORDER BY l.id DESC LIMIT 1) as last_lat,
                   (SELECT l.longitude FROM locations l WHERE l.session_id = s.session_id AND l.consented = 1 ORDER BY l.id DESC LIMIT 1) as last_lon,
                   (SELECT l.accuracy_m FROM locations l WHERE l.session_id = s.session_id AND l.consented = 1 ORDER BY l.id DESC LIMIT 1) as last_accuracy
            FROM sessions s
            ORDER BY s.created_at DESC
            """)
            sessions = [dict(row) for row in cursor.fetchall()]
            conn.close()

            self._send_json({"sessions": sessions})
            return

        # Default static file serving
        return super().do_GET()

    def do_POST(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        # Read JSON body
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            raw_body = self.rfile.read(content_length).decode("utf-8")
            try:
                data = json.loads(raw_body)
            except Exception:
                self._send_error("Invalid JSON body")
                return
        else:
            data = {}

        # 1. POST /api/session -> Save or update session
        if path == "/api/session":
            session_id = data.get("sessionId")
            if not session_id:
                session_id = secrets.token_hex(8)
            alias = data.get("playerAlias", "Friend").strip()
            quiz_score = float(data.get("quizScore", 0))
            result_band = data.get("resultBand", get_result_band(quiz_score))
            now_iso = datetime.utcnow().isoformat() + "Z"

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sessions (session_id, player_alias, created_at, updated_at, quiz_score, result_band)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                player_alias=excluded.player_alias,
                updated_at=excluded.updated_at,
                quiz_score=excluded.quiz_score,
                result_band=excluded.result_band
            """, (session_id, alias, now_iso, now_iso, quiz_score, result_band))

            # Store individual answers if provided
            answers = data.get("answers", [])
            for ans in answers:
                cursor.execute("""
                INSERT INTO answers (session_id, question_idx, question_text, selected_text, score_val, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (session_id, ans.get("qIdx", 0), ans.get("qText", ""), ans.get("optText", ""), ans.get("scoreVal", 0), now_iso))

            conn.commit()
            conn.close()

            self._send_json({"sessionId": session_id, "status": "saved"})
            return

        # 2. POST /api/calculate-distance -> Distance calculation without exposing reference coordinates
        if path == "/api/calculate-distance":
            session_id = data.get("sessionId")
            try:
                user_lat = float(data.get("latitude"))
                user_lon = float(data.get("longitude"))
                accuracy = float(data.get("accuracy", 25.0))
            except (TypeError, ValueError):
                self._send_error("Invalid coordinates provided")
                return

            # Coordinate range validation
            if not (-90.0 <= user_lat <= 90.0 and -180.0 <= user_lon <= 180.0):
                self._send_error("Coordinates out of physical planetary range")
                return

            # Explicit consent check
            if not data.get("consent"):
                self._send_error("Explicit player consent required for distance calculation")
                return

            # Haversine distance to Prajwal's reference point
            dist_km = haversine_distance(user_lat, user_lon, PRAJWAL_LAT, PRAJWAL_LON)
            dist_score = calculate_distance_score(dist_km)
            caption = get_distance_caption(dist_km)

            # Format distance string
            if dist_km < 1.0:
                dist_display = f"{int(round(dist_km * 1000))} m"
            else:
                dist_display = f"{dist_km:.1f} km"

            # Retrieve quiz score for session if available, calculate final score
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT quiz_score FROM sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            quiz_score = row[0] if row and row[0] is not None else 80.0
            
            final_score = calculate_final_score(quiz_score, dist_score)
            final_band = get_result_band(final_score)

            # Update session record
            now_iso = datetime.utcnow().isoformat() + "Z"
            cursor.execute("""
            UPDATE sessions SET 
                distance_km = ?,
                distance_score = ?,
                final_score = ?,
                result_band = ?,
                updated_at = ?
            WHERE session_id = ?
            """, (dist_km, dist_score, final_score, final_band, now_iso, session_id))
            conn.commit()
            conn.close()

            self._send_json({
                "distanceKm": round(dist_km, 2),
                "distanceDisplay": dist_display,
                "distanceScore": dist_score,
                "distanceCaption": caption,
                "quizScore": quiz_score,
                "finalScore": final_score,
                "resultBand": final_band,
                "estimated": True
            })
            return

        # 3. POST /api/location -> Consented location submission
        if path == "/api/location":
            session_id = data.get("sessionId")
            if not session_id:
                self._send_error("Missing sessionId")
                return

            if not data.get("consent"):
                self._send_error("Explicit consent required to submit location")
                return

            try:
                lat = float(data.get("latitude"))
                lon = float(data.get("longitude"))
                accuracy = float(data.get("accuracy", 20.0))
            except (TypeError, ValueError):
                self._send_error("Invalid latitude or longitude")
                return

            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                self._send_error("Coordinates out of range")
                return

            consent_timestamp = data.get("consentTimestamp") or datetime.utcnow().isoformat() + "Z"
            now_iso = datetime.utcnow().isoformat() + "Z"

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO locations (session_id, latitude, longitude, accuracy_m, consented, consent_timestamp, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (session_id, lat, lon, accuracy, 1, consent_timestamp, now_iso))
            conn.commit()
            conn.close()

            self._send_json({
                "success": True,
                "message": "Location successfully submitted with verified consent",
                "accuracy": accuracy,
                "timestamp": now_iso
            })
            return

        # 4. POST /api/admin/login -> Administrator Authentication
        if path == "/api/admin/login":
            username = data.get("username", "")
            password = data.get("password", "")

            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                token = secrets.token_hex(16)
                active_admin_tokens.add(token)
                self._send_json({
                    "authenticated": True,
                    "token": token,
                    "username": username
                })
            else:
                self._send_error("Invalid administrator credentials", HTTPStatus.UNAUTHORIZED)
            return

        # 5. POST /api/admin/logout
        if path == "/api/admin/logout":
            token = data.get("token")
            if token in active_admin_tokens:
                active_admin_tokens.remove(token)
            self._send_json({"loggedOut": True})
            return

        self._send_error("Endpoint not found", HTTPStatus.NOT_FOUND)

    def _serve_admin_page(self):
        """Serve a clean administrative dashboard"""
        admin_html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Friendship Meter - Administrator Dashboard</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #FFF8F0;
      --card: #FFFFFF;
      --plum: #65536B;
      --pink: #F6DCE5;
      --yellow: #F6E8A8;
      --lavender: #DCD5F7;
    }
    body {
      font-family: 'Quicksand', sans-serif;
      background-color: var(--bg);
      color: var(--plum);
      margin: 0;
      padding: 24px;
    }
    .container {
      max-width: 900px;
      margin: 0 auto;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding-bottom: 12px;
      border-bottom: 2px solid rgba(101,83,107,0.15);
    }
    h1 { margin: 0; font-size: 24px; }
    .card {
      background: var(--card);
      border-radius: 16px;
      padding: 20px;
      border: 1.5px solid rgba(101,83,107,0.15);
      box-shadow: 0 4px 12px rgba(101,83,107,0.06);
      margin-bottom: 20px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      padding: 10px 12px;
      text-align: left;
      border-bottom: 1px solid rgba(101,83,107,0.1);
    }
    th {
      background: var(--lavender);
      color: var(--plum);
      font-weight: 700;
    }
    .badge {
      display: inline-block;
      padding: 4px 8px;
      border-radius: 12px;
      background: var(--yellow);
      font-weight: 700;
      font-size: 12px;
    }
    .btn {
      padding: 8px 16px;
      border-radius: 20px;
      border: 1.5px solid var(--plum);
      background: var(--yellow);
      font-weight: 700;
      cursor: pointer;
      color: var(--plum);
    }
    .btn-secondary {
      background: var(--pink);
    }
    input {
      padding: 8px 12px;
      border-radius: 10px;
      border: 1.5px solid rgba(101,83,107,0.2);
      margin-right: 8px;
      font-family: inherit;
    }
    #login-box { max-width: 380px; margin: 60px auto; }
  </style>
</head>
<body>
  <div class="container">
    <div id="login-section" class="card" style="display: block;">
      <h2>Administrator Login 🔐</h2>
      <p>Secure management portal for Friendship Meter.</p>
      <div style="margin: 16px 0;">
        <input type="text" id="admin-user" placeholder="Username" value="admin" style="width: 100%; box-sizing: border-box; margin-bottom: 10px;">
        <input type="password" id="admin-pass" placeholder="Password" style="width: 100%; box-sizing: border-box; margin-bottom: 14px;">
        <button class="btn" onclick="login()">Sign In →</button>
      </div>
      <div id="login-error" style="color: #b00; font-size: 13px; font-weight: 600;"></div>
    </div>

    <div id="dashboard-section" style="display: none;">
      <header>
        <div>
          <h1>Friendship Meter — Admin Dashboard</h1>
          <span style="font-size: 13px; color: #888;">Logged in as: <strong id="logged-user">admin</strong></span>
        </div>
        <div>
          <button class="btn btn-secondary" onclick="refreshData()">Refresh</button>
          <button class="btn" onclick="logout()">Sign Out</button>
        </div>
      </header>

      <div class="card">
        <h3>Recent Game Sessions & Consented Location Submissions</h3>
        <div style="overflow-x: auto;">
          <table>
            <thead>
              <tr>
                <th>Session ID</th>
                <th>Player Alias</th>
                <th>Quiz Score</th>
                <th>Distance</th>
                <th>Final Score</th>
                <th>Result Band</th>
                <th>Consented GPS</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody id="sessions-tbody">
              <tr><td colspan="8">Loading sessions...</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>

  <script>
    let token = localStorage.getItem('fm_admin_token') || '';

    if (token) {
      showDashboard();
    }

    async function login() {
      const u = document.getElementById('admin-user').value.trim();
      const p = document.getElementById('admin-pass').value.trim();
      const err = document.getElementById('login-error');
      err.textContent = '';

      try {
        const res = await fetch('/api/admin/login', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({username: u, password: p})
        });
        const data = await res.json();
        if (res.ok && data.token) {
          token = data.token;
          localStorage.setItem('fm_admin_token', token);
          showDashboard();
        } else {
          err.textContent = data.error || 'Authentication failed.';
        }
      } catch (e) {
        err.textContent = 'Server connection error.';
      }
    }

    function logout() {
      if (token) {
        fetch('/api/admin/logout', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({token})
        });
      }
      token = '';
      localStorage.removeItem('fm_admin_token');
      document.getElementById('login-section').style.display = 'block';
      document.getElementById('dashboard-section').style.display = 'none';
    }

    function showDashboard() {
      document.getElementById('login-section').style.display = 'none';
      document.getElementById('dashboard-section').style.display = 'block';
      refreshData();
    }

    async function refreshData() {
      const tbody = document.getElementById('sessions-tbody');
      tbody.innerHTML = '<tr><td colspan="8">Refreshing...</td></tr>';

      try {
        const res = await fetch('/api/admin/sessions', {
          headers: {'Authorization': 'Bearer ' + token}
        });
        if (res.status === 401) {
          logout();
          return;
        }
        const data = await res.json();
        const sessions = data.sessions || [];
        if (sessions.length === 0) {
          tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #888;">No sessions yet. Play the game to record sessions!</td></tr>';
          return;
        }

        tbody.innerHTML = sessions.map(s => {
          let gpsText = 'None';
          if (s.last_lat && s.last_lon) {
            gpsText = s.last_lat.toFixed(4) + '°, ' + s.last_lon.toFixed(4) + '° (±' + Math.round(s.last_accuracy || 20) + 'm)';
          }
          return `
            <tr>
              <td><code>${s.session_id.substring(0,8)}</code></td>
              <td><strong>${escapeHtml(s.player_alias || 'Friend')}</strong></td>
              <td>${s.quiz_score !== null ? s.quiz_score : '-'}</td>
              <td>${s.distance_km !== null ? s.distance_km.toFixed(1) + ' km' : '-'}</td>
              <td><span class="badge">${s.final_score !== null ? s.final_score : '-'}</span></td>
              <td>${escapeHtml(s.result_band || '-')}</td>
              <td>${gpsText}</td>
              <td style="font-size: 12px; color: #666;">${s.created_at ? s.created_at.substring(0,16).replace('T', ' ') : '-'}</td>
            </tr>
          `;
        }).join('');
      } catch (e) {
        tbody.innerHTML = '<tr><td colspan="8" style="color: red;">Error fetching data.</td></tr>';
      }
    }

    function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    }
  </script>
</body>
</html>
"""
        body = admin_html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

def run_server():
    init_db()
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, FriendshipMeterHandler)
    print(f"🚀 Friendship Meter Server running on port {PORT}")
    print(f"📍 Prajwal Reference Location: lat={PRAJWAL_LAT}, lon={PRAJWAL_LON} (Configured)")
    print(f"🔐 Admin Dashboard available at http://localhost:{PORT}/admin")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server gracefully...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
