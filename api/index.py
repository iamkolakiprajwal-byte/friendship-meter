#!/usr/bin/env python3
"""
Friendship Meter - Vercel Serverless Function & Supabase Integration
Supports:
- Vercel Serverless HTTP Handler
- Supabase REST API persistence (with SQLite local fallback)
- Prajwal reference location configuration (PRAJWAL_LAT, PRAJWAL_LON)
- Haversine distance calculation and 80/20 scoring
- Admin dashboard authentication and data retrieval
"""

import os
import json
import math
import secrets
import sqlite3
import urllib.request
import urllib.error
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# --- Environment Configuration ---
PRAJWAL_LAT = float(os.environ.get("PRAJWAL_LAT", "13.103691"))
PRAJWAL_LON = float(os.environ.get("PRAJWAL_LON", "77.570392"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Prajwalvedika")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists("/tmp") and os.access("/tmp", os.W_OK):
    DB_PATH = "/tmp/friendship_meter.db"
else:
    DB_PATH = os.path.join(BASE_DIR, "friendship_meter.db")

def init_sqlite():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            player_alias TEXT,
            quiz_score REAL,
            distance_km REAL,
            distance_score REAL,
            final_score REAL,
            result_band TEXT,
            destination TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            latitude REAL,
            longitude REAL,
            accuracy_m REAL,
            consented INTEGER,
            consent_timestamp TEXT,
            created_at TEXT
        )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        print("init_sqlite error:", e)

init_sqlite()

active_admin_tokens = set()

# --- Distance & Scoring Logic ---
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def calculate_distance_score(dist_km):
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
    raw = (quiz_score * 0.80) + (distance_score * 0.20)
    return max(0, min(100, round(raw)))

# --- Supabase Database Helper ---
def supabase_request(endpoint, method="GET", payload=None, query=""):
    if not (SUPABASE_URL and SUPABASE_KEY):
        return None
    url = f"{SUPABASE_URL}/rest/v1/{endpoint}{query}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=representation"
    }
    if method in ("POST", "PATCH") and payload:
        data = json.dumps(payload).encode("utf-8")
    else:
        data = None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else []
    except urllib.error.HTTPError as he:
        err_body = he.read().decode("utf-8")
        print(f"Supabase HTTP {he.code} for {endpoint}:", err_body)
        return {"_error": err_body, "code": he.code}
    except Exception as e:
        print("Supabase request error:", e)
        return {"_error": str(e)}

# --- Main HTTP Handler (Works on Vercel & Standard Python) ---
class handler(BaseHTTPRequestHandler):

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

    def _serve_file(self, filename, content_type):
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(content)
        else:
            self._send_error(f"File {filename} not found", HTTPStatus.NOT_FOUND)

    def _get_route(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        action = qs.get("action", [""])[0].strip("/")
        path = parsed.path
        forwarded = (self.headers.get("x-forwarded-uri") or 
                     self.headers.get("x-matched-path") or 
                     self.headers.get("x-invoke-path") or "")
        return {
            "action": action,
            "path": path,
            "forwarded": forwarded
        }

    def _matches(self, r, target):
        action = r["action"]
        path = r["path"]
        fwd = r["forwarded"]
        return (
            action == target or
            action.endswith("/" + target) or
            action.startswith(target) or
            path.endswith("/" + target) or
            path.endswith("/api/" + target) or
            target in fwd or
            target in path
        )

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        r = self._get_route()
        path = r["path"]

        # Root static file serving
        if path in ("/", "/index.html", "") or r["action"] in ("", "index.html"):
            self._serve_file("index.html", "text/html; charset=utf-8")
            return

        if self._matches(r, "style.css"):
            self._serve_file("style.css", "text/css; charset=utf-8")
            return

        if self._matches(r, "app.js"):
            self._serve_file("app.js", "application/javascript; charset=utf-8")
            return

        if self._matches(r, "config"):
            self._send_json({
                "appName": "Friendship Meter",
                "hasReferenceLocation": bool(PRAJWAL_LAT and PRAJWAL_LON),
                "scoringRules": {
                    "quizWeight": 0.80,
                    "distanceWeight": 0.20
                }
            })
            return

        if self._matches(r, "admin/sessions"):
            auth_header = self.headers.get("Authorization", "")
            token = auth_header.replace("Bearer ", "").strip()
            if not token or token not in active_admin_tokens:
                self._send_error("Unauthorized administrator access", HTTPStatus.UNAUTHORIZED)
                return

            sessions = []
            db_status = "sqlite"
            error_hint = None

            if SUPABASE_URL and SUPABASE_KEY:
                db_status = "supabase"
                s_resp = supabase_request("sessions", query="?select=*&order=created_at.desc")
                l_resp = supabase_request("locations", query="?select=*&order=created_at.desc")

                if isinstance(s_resp, list):
                    loc_map = {}
                    if isinstance(l_resp, list):
                        for loc in l_resp:
                            sid = loc.get("session_id")
                            if sid and sid not in loc_map:
                                loc_map[sid] = loc
                    for s in s_resp:
                        last_loc = loc_map.get(s.get("session_id"), {})
                        sessions.append({
                            "session_id": s.get("session_id"),
                            "player_alias": s.get("player_alias"),
                            "quiz_score": s.get("quiz_score"),
                            "distance_km": s.get("distance_km"),
                            "final_score": s.get("final_score"),
                            "result_band": s.get("result_band"),
                            "last_lat": last_loc.get("latitude"),
                            "last_lon": last_loc.get("longitude"),
                            "last_accuracy": last_loc.get("accuracy_m"),
                            "created_at": s.get("created_at")
                        })
                elif isinstance(s_resp, dict) and "_error" in s_resp:
                    error_hint = f"Supabase notice: {s_resp.get('_error')}"
            else:
                error_hint = "SUPABASE_URL and SUPABASE_KEY not added in Vercel settings. Using temporary SQLite."

            # Merge SQLite sessions
            try:
                init_sqlite()
                conn = sqlite3.connect(DB_PATH)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                SELECT s.*, 
                       (SELECT l.latitude FROM locations l WHERE l.session_id = s.session_id ORDER BY l.id DESC LIMIT 1) as last_lat,
                       (SELECT l.longitude FROM locations l WHERE l.session_id = s.session_id ORDER BY l.id DESC LIMIT 1) as last_lon,
                       (SELECT l.accuracy_m FROM locations l WHERE l.session_id = s.session_id ORDER BY l.id DESC LIMIT 1) as last_accuracy
                FROM sessions s
                ORDER BY s.created_at DESC
                """)
                sqlite_rows = [dict(row) for row in cursor.fetchall()]
                conn.close()

                existing_ids = {s.get("session_id") for s in sessions}
                for sq in sqlite_rows:
                    if sq.get("session_id") not in existing_ids:
                        sessions.append(sq)
            except Exception as e:
                print("SQLite read error:", e)

            self._send_json({
                "sessions": sessions,
                "db_status": db_status,
                "error_hint": error_hint
            })
            return

        if self._matches(r, "admin"):
            self._serve_admin_html()
            return

        self._send_error("Not found", HTTPStatus.NOT_FOUND)

    def do_POST(self):
        r = self._get_route()

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

        # 1. /api/session -> Save or update session
        if self._matches(r, "session"):
            session_id = data.get("sessionId") or secrets.token_hex(8)
            alias = data.get("playerAlias", "Friend").strip()
            quiz_score = float(data.get("quizScore", 0))
            result_band = data.get("resultBand", get_result_band(quiz_score))
            distance_km = data.get("distanceKm")
            final_score = data.get("finalScore")
            now_iso = datetime.utcnow().isoformat() + "Z"

            if SUPABASE_URL and SUPABASE_KEY:
                # Supabase Upsert
                s_payload = {
                    "session_id": session_id,
                    "player_alias": alias,
                    "quiz_score": quiz_score,
                    "result_band": result_band,
                    "updated_at": now_iso
                }
                if distance_km is not None:
                    s_payload["distance_km"] = float(distance_km)
                if final_score is not None:
                    s_payload["final_score"] = float(final_score)

                supabase_request("sessions", method="POST", payload=s_payload)
                
                # Insert individual answers if present
                answers = data.get("answers", [])
                for ans in answers:
                    supabase_request("answers", method="POST", payload={
                        "session_id": session_id,
                        "question_idx": ans.get("qIdx", 0),
                        "question_text": ans.get("qText", ""),
                        "selected_text": ans.get("optText", ""),
                        "score_val": ans.get("scoreVal", 0)
                    })

            # Always save to local SQLite container as well
            try:
                init_sqlite()
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute("""
                INSERT INTO sessions (session_id, player_alias, created_at, updated_at, quiz_score, result_band, distance_km, final_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    player_alias=excluded.player_alias,
                    updated_at=excluded.updated_at,
                    quiz_score=excluded.quiz_score,
                    result_band=excluded.result_band,
                    distance_km=COALESCE(excluded.distance_km, sessions.distance_km),
                    final_score=COALESCE(excluded.final_score, sessions.final_score)
                """, (session_id, alias, now_iso, now_iso, quiz_score, result_band, distance_km, final_score))
                conn.commit()
                conn.close()
            except Exception as e:
                print("SQLite session write error:", e)

            self._send_json({"sessionId": session_id, "status": "saved"})
            return

        # 2. /api/calculate-distance -> Secure distance calculation
        if self._matches(r, "calculate-distance"):
            session_id = data.get("sessionId")
            try:
                user_lat = float(data.get("latitude"))
                user_lon = float(data.get("longitude"))
            except (TypeError, ValueError):
                self._send_error("Invalid coordinates provided")
                return

            if not (-90.0 <= user_lat <= 90.0 and -180.0 <= user_lon <= 180.0):
                self._send_error("Coordinates out of range")
                return

            if not data.get("consent"):
                self._send_error("Explicit player consent required for distance calculation")
                return

            dist_km = haversine_distance(user_lat, user_lon, PRAJWAL_LAT, PRAJWAL_LON)
            dist_score = calculate_distance_score(dist_km)
            caption = get_distance_caption(dist_km)
            dist_display = f"{int(round(dist_km * 1000))} m" if dist_km < 1.0 else f"{dist_km:.1f} km"

            # Fetch existing quiz score
            quiz_score = 80.0
            if SUPABASE_URL and SUPABASE_KEY:
                s_data = supabase_request(f"sessions?session_id=eq.{session_id}")
                if s_data and len(s_data) > 0 and s_data[0].get("quiz_score") is not None:
                    quiz_score = float(s_data[0]["quiz_score"])
            else:
                try:
                    conn = sqlite3.connect(DB_PATH)
                    c = conn.cursor()
                    c.execute("SELECT quiz_score FROM sessions WHERE session_id = ?", (session_id,))
                    row = c.fetchone()
                    if row and row[0] is not None:
                        quiz_score = float(row[0])
                    conn.close()
                except Exception:
                    pass

            final_score = calculate_final_score(quiz_score, dist_score)
            final_band = get_result_band(final_score)

            # Update session record
            if SUPABASE_URL and SUPABASE_KEY:
                supabase_request(f"sessions?session_id=eq.{session_id}", method="PATCH", payload={
                    "distance_km": round(dist_km, 2),
                    "distance_score": dist_score,
                    "final_score": final_score,
                    "result_band": final_band
                })

            try:
                init_sqlite()
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("""
                UPDATE sessions SET 
                    distance_km = ?,
                    distance_score = ?,
                    final_score = ?,
                    result_band = ?
                WHERE session_id = ?
                """, (dist_km, dist_score, final_score, final_band, session_id))
                conn.commit()
                conn.close()
            except Exception as e:
                print("SQLite distance update error:", e)

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

        # 3. /api/location -> Consented Location Submission
        if self._matches(r, "location"):
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
                self._send_error("Invalid coordinates")
                return

            now_iso = datetime.utcnow().isoformat() + "Z"
            if SUPABASE_URL and SUPABASE_KEY:
                supabase_request("locations", method="POST", payload={
                    "session_id": session_id,
                    "latitude": lat,
                    "longitude": lon,
                    "accuracy_m": accuracy,
                    "consented": 1,
                    "consent_timestamp": data.get("consentTimestamp") or now_iso
                })

            try:
                init_sqlite()
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("""
                INSERT INTO locations (session_id, latitude, longitude, accuracy_m, consented, consent_timestamp, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (session_id, lat, lon, accuracy, 1, data.get("consentTimestamp") or now_iso, now_iso))
                conn.commit()
                conn.close()
            except Exception as e:
                print("SQLite location write error:", e)

            self._send_json({
                "success": True,
                "message": "Location submitted successfully",
                "accuracy": accuracy,
                "timestamp": now_iso
            })
            return

        # 4. /api/admin/login -> Admin Login
        if self._matches(r, "admin/login"):
            username = data.get("username", "")
            password = data.get("password", "")

            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                token = secrets.token_hex(16)
                active_admin_tokens.add(token)
                self._send_json({"authenticated": True, "token": token, "username": username})
            else:
                self._send_error("Invalid administrator credentials", HTTPStatus.UNAUTHORIZED)
            return

        # 5. /api/admin/logout
        if self._matches(r, "admin/logout"):
            token = data.get("token")
            if token in active_admin_tokens:
                active_admin_tokens.remove(token)
            self._send_json({"loggedOut": True})
            return

        self._send_error("Endpoint not found", HTTPStatus.NOT_FOUND)

    def _serve_admin_html(self):
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
    .btn-secondary { background: var(--pink); }
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
    if (token) showDashboard();

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
        if (res.status === 401) { logout(); return; }
        const data = await res.json();
        const sessions = data.sessions || [];
        if (sessions.length === 0) {
          tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: #888;">No sessions recorded yet. Play the game to record entries!</td></tr>';
          return;
        }
        tbody.innerHTML = sessions.map(s => {
          let gpsText = 'None';
          if (s.last_lat && s.last_lon) {
            gpsText = Number(s.last_lat).toFixed(4) + '°, ' + Number(s.last_lon).toFixed(4) + '° (±' + Math.round(s.last_accuracy || 20) + 'm)';
          }
          return `
            <tr>
              <td><code>${(s.session_id || '').substring(0,8)}</code></td>
              <td><strong>${escapeHtml(s.player_alias || 'Friend')}</strong></td>
              <td>${s.quiz_score !== null && s.quiz_score !== undefined ? s.quiz_score : '-'}</td>
              <td>${s.distance_km ? Number(s.distance_km).toFixed(1) + ' km' : '-'}</td>
              <td><span class="badge">${s.final_score !== null && s.final_score !== undefined ? s.final_score : '-'}</span></td>
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

# Vercel entrypoint exports
app = handler


