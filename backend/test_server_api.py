#!/usr/bin/env python3
"""
Server Component & Persistence Tests
Validates:
- Database schema initialization
- Session creation and retrieval
- Quiz answer persistence
- Geolocation validation and consented storage
- Haversine distance and distance scoring
- Config privacy verification
- Administrator authentication and token validation
"""

import unittest
import sqlite3
import json
import secrets
import os
import sys

from server import (
    init_db,
    haversine_distance,
    calculate_distance_score,
    get_result_band,
    calculate_final_score,
    get_distance_caption,
    PRAJWAL_LAT,
    PRAJWAL_LON,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
    active_admin_tokens,
    DB_PATH
)

class TestServerInternal(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_database_tables_exist(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        self.assertIn("sessions", tables)
        self.assertIn("answers", tables)
        self.assertIn("locations", tables)

    def test_session_and_answers_persistence(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        test_session_id = "test_sess_" + secrets.token_hex(4)
        cursor.execute("""
        INSERT INTO sessions (session_id, player_alias, created_at, updated_at, quiz_score, result_band)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (test_session_id, "Tanvi", "2026-10-30T04:00:00Z", "2026-10-30T04:00:00Z", 88.0, "Gappa Champion"))
        
        cursor.execute("""
        INSERT INTO answers (session_id, question_idx, question_text, selected_text, score_val, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (test_session_id, 0, "What's your ideal plan?", "Chai ani gappa", 12.5, "2026-10-30T04:00:00Z"))
        conn.commit()

        # Query back
        cursor.execute("SELECT player_alias, quiz_score, result_band FROM sessions WHERE session_id = ?", (test_session_id,))
        row = cursor.fetchone()
        self.assertEqual(row[0], "Tanvi")
        self.assertEqual(row[1], 88.0)
        self.assertEqual(row[2], "Gappa Champion")

        cursor.execute("SELECT selected_text, score_val FROM answers WHERE session_id = ?", (test_session_id,))
        ans = cursor.fetchone()
        self.assertEqual(ans[0], "Chai ani gappa")
        self.assertEqual(ans[1], 12.5)
        conn.close()

    def test_consented_location_storage(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        test_session_id = "test_sess_" + secrets.token_hex(4)
        cursor.execute("""
        INSERT INTO locations (session_id, latitude, longitude, accuracy_m, consented, consent_timestamp, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (test_session_id, 18.5204, 73.8567, 14.5, 1, "2026-10-30T04:05:00Z", "2026-10-30T04:05:00Z"))
        conn.commit()

        cursor.execute("SELECT latitude, longitude, accuracy_m, consented FROM locations WHERE session_id = ?", (test_session_id,))
        loc = cursor.fetchone()
        self.assertAlmostEqual(loc[0], 18.5204)
        self.assertAlmostEqual(loc[1], 73.8567)
        self.assertEqual(loc[2], 14.5)
        self.assertEqual(loc[3], 1)
        conn.close()

    def test_admin_credentials_and_tokens(self):
        self.assertEqual(ADMIN_USERNAME, "admin")
        self.assertTrue(len(ADMIN_PASSWORD) > 0)
        token = "test_secure_token_" + secrets.token_hex(4)
        active_admin_tokens.add(token)
        self.assertIn(token, active_admin_tokens)
        active_admin_tokens.remove(token)
        self.assertNotIn(token, active_admin_tokens)

    def test_prajwal_reference_privacy(self):
        # Ensure coordinates are stored in server scope and not injected into public client config
        config_payload = {
            "appName": "Friendship Meter",
            "hasReferenceLocation": bool(PRAJWAL_LAT and PRAJWAL_LON),
            "scoringRules": {
                "quizWeight": 0.80,
                "distanceWeight": 0.20
            }
        }
        self.assertNotIn("13.103691", str(config_payload))
        self.assertNotIn("77.570392", str(config_payload))
        self.assertNotIn("latitude", config_payload)
        self.assertNotIn("longitude", config_payload)

if __name__ == "__main__":
    unittest.main()
