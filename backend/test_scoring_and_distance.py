#!/usr/bin/env python3
"""
Test Suite for Friendship Meter
Tests scoring formulas, distance bands, result categories, and server logic.
"""

import unittest
import math
import sys
import os

# Import server functions
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import (
    haversine_distance,
    calculate_distance_score,
    get_distance_caption,
    get_result_band,
    calculate_final_score,
    PRAJWAL_LAT,
    PRAJWAL_LON
)

class TestScoringAndDistance(unittest.TestCase):

    def test_prajwal_reference_coordinates(self):
        """Prajwal reference coordinates must be configured as specified"""
        self.assertAlmostEqual(PRAJWAL_LAT, 13.103691, places=6)
        self.assertAlmostEqual(PRAJWAL_LON, 77.570392, places=6)

    def test_haversine_distance_self(self):
        """Distance from Prajwal's location to itself should be 0 km"""
        dist = haversine_distance(PRAJWAL_LAT, PRAJWAL_LON, PRAJWAL_LAT, PRAJWAL_LON)
        self.assertAlmostEqual(dist, 0.0, places=3)

    def test_haversine_distance_known_point(self):
        """
        Distance from Bangalore City Railway Station (12.9784, 77.5684)
        to Prajwal (13.103691, 77.570392) is roughly ~13.9 km.
        """
        dist = haversine_distance(12.9784, 77.5684, PRAJWAL_LAT, PRAJWAL_LON)
        self.assertTrue(13.0 <= dist <= 15.0, f"Expected ~13.9 km, got {dist}")

    def test_haversine_distance_mumbai(self):
        """
        Distance from Mumbai (19.0760, 72.8777) to Prajwal (~840 km)
        """
        dist = haversine_distance(19.0760, 72.8777, PRAJWAL_LAT, PRAJWAL_LON)
        self.assertTrue(800.0 <= dist <= 900.0, f"Expected ~840 km, got {dist}")

    def test_distance_score_bands(self):
        """
        Bands:
        0–5 km: 100 points
        >5 km up to 25 km: 80 points
        >25 km up to 100 km: 60 points
        >100 km up to 300 km: 40 points
        >300 km: 20 points
        """
        self.assertEqual(calculate_distance_score(0.0), 100.0)
        self.assertEqual(calculate_distance_score(5.0), 100.0)
        self.assertEqual(calculate_distance_score(5.1), 80.0)
        self.assertEqual(calculate_distance_score(25.0), 80.0)
        self.assertEqual(calculate_distance_score(25.1), 60.0)
        self.assertEqual(calculate_distance_score(100.0), 60.0)
        self.assertEqual(calculate_distance_score(100.1), 40.0)
        self.assertEqual(calculate_distance_score(300.0), 40.0)
        self.assertEqual(calculate_distance_score(300.1), 20.0)
        self.assertEqual(calculate_distance_score(1500.0), 20.0)

    def test_distance_captions(self):
        """Verify playful caption bands"""
        self.assertIn("same area", get_distance_caption(12.0))
        self.assertIn("Thoda travel", get_distance_caption(150.0))
        self.assertIn("kilometres don't matter", get_distance_caption(800.0))

    def test_result_bands(self):
        """
        Result bands:
        - 0–39: Ajun olakh vhaychi aahe
        - 40–59: Chai-pani acquaintances
        - 60–79: Gappa gang material
        - 80–94: Gappa Champion
        - 95–100: Full-time bakbak partner
        """
        # Lower bound tests
        self.assertEqual(get_result_band(0), "Ajun olakh vhaychi aahe")
        self.assertEqual(get_result_band(39), "Ajun olakh vhaychi aahe")
        self.assertEqual(get_result_band(40), "Chai-pani acquaintances")
        self.assertEqual(get_result_band(59), "Chai-pani acquaintances")
        self.assertEqual(get_result_band(60), "Gappa gang material")
        self.assertEqual(get_result_band(79), "Gappa gang material")
        self.assertEqual(get_result_band(80), "Gappa Champion")
        self.assertEqual(get_result_band(94), "Gappa Champion")
        self.assertEqual(get_result_band(95), "Full-time bakbak partner")
        self.assertEqual(get_result_band(100), "Full-time bakbak partner")

    def test_final_score_calculation(self):
        """
        Final score = round((Quiz score * 0.80) + (Distance score * 0.20))
        Clamped to 0..100
        """
        # Perfect scores
        self.assertEqual(calculate_final_score(100, 100), 100)
        # 80 quiz, 80 distance -> 64 + 16 = 80
        self.assertEqual(calculate_final_score(80, 80), 80)
        # 90 quiz, 20 distance -> 72 + 4 = 76
        self.assertEqual(calculate_final_score(90, 20), 76)
        # 40 quiz, 20 distance -> 32 + 4 = 36
        self.assertEqual(calculate_final_score(40, 20), 36)
        # 95 quiz, 100 distance -> 76 + 20 = 96
        self.assertEqual(calculate_final_score(95, 100), 96)
        # Clamping check
        self.assertEqual(calculate_final_score(120, 100), 100)
        self.assertEqual(calculate_final_score(-10, 0), 0)

if __name__ == "__main__":
    unittest.main()
