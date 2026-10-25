"""Tests for Symptom Buddy safety, pharmacy, joke, and knowledge logic.

These tests run without Streamlit installed. Run them with:
    python3 tests/test_safety.py
or:
    python3 -m unittest tests.test_safety
"""

import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import jokes as jokes_module
from src import knowledge as knowledge_module
from src import pharmacy as pharmacy_module
from src import safety as safety_module


class TestRedFlags(unittest.TestCase):
    def test_worst_headache_triggers_urgent(self):
        flags = safety_module.check_red_flags("worst headache of my life")
        self.assertTrue(flags)
        self.assertIn("Sudden worst headache of your life", flags)

    def test_head_injury_answer_triggers_urgent(self):
        flags = safety_module.check_red_flags(
            "headache", answers={"head_injury": True}
        )
        self.assertIn("Headache after a head injury", flags)

    def test_plain_headache_has_no_red_flag(self):
        self.assertFalse(safety_module.has_red_flag("headache"))
        self.assertEqual(safety_module.check_red_flags("headache"), [])

    def test_disclaimer_is_present_and_complete(self):
        self.assertIn("general information only", safety_module.DISCLAIMER)
        self.assertIn("not medical advice", safety_module.DISCLAIMER)
        self.assertIn("local emergency number", safety_module.DISCLAIMER)


class TestJokeLogic(unittest.TestCase):
    def test_no_joke_when_red_flag(self):
        result = jokes_module.joke_for_result(
            ["Sudden worst headache of your life"], jokes_enabled=True
        )
        self.assertIsNone(result)

    def test_no_joke_when_check_in_worse(self):
        result = jokes_module.joke_for_result(
            [], jokes_enabled=True, check_in="Worse"
        )
        self.assertIsNone(result)

    def test_no_joke_when_disabled(self):
        result = jokes_module.joke_for_result(
            [], jokes_enabled=False, check_in="Better"
        )
        self.assertIsNone(result)

    def test_joke_shown_when_safe(self):
        result = jokes_module.joke_for_result(
            [], jokes_enabled=True, check_in="Better", joke_index=0
        )
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


class TestPharmacySorting(unittest.TestCase):
    def test_sorted_nearest_first(self):
        entries = [
            {"name": "Far", "distance_km": 5.6},
            {"name": "Near", "distance_km": 0.8},
            {"name": "Middle", "distance_km": 2.3},
        ]
        sorted_entries = pharmacy_module.sort_pharmacies_by_distance(entries)
        self.assertEqual(
            [e["name"] for e in sorted_entries], ["Near", "Middle", "Far"]
        )

    def test_search_labels_stock_not_verified(self):
        results = pharmacy_module.search_pharmacies("Springfield")
        self.assertTrue(len(results) >= 1)
        for entry in results:
            self.assertEqual(
                entry["stock_status"],
                pharmacy_module.STOCK_NOT_VERIFIED,
            )
        self.assertTrue(
            all(
                float(results[i]["distance_km"]) <= float(results[i + 1]["distance_km"])
                for i in range(len(results) - 1)
                if results[i].get("distance_km") is not None
                and results[i + 1].get("distance_km") is not None
            )
        )

    def test_count_is_pharmacy_count_not_stock_count(self):
        count = pharmacy_module.count_pharmacies_nearby("Springfield")
        self.assertEqual(count, len(pharmacy_module.search_pharmacies("Springfield")))


class TestKnowledgeBase(unittest.TestCase):
    def test_symptoms_json_loads_and_has_seven(self):
        symptoms = knowledge_module.load_symptoms()
        self.assertGreaterEqual(len(symptoms), 7)
        self.assertIn("headache", symptoms)

    def test_headache_info_has_required_fields(self):
        key, entry = knowledge_module.get_symptom_info("headache")
        self.assertEqual(key, "headache")
        for field in ("general_causes", "what_usually_helps", "see_doctor_if"):
            self.assertIn(field, entry)
            self.assertTrue(entry[field])

    def test_unknown_symptom_is_explicit(self):
        key, entry = knowledge_module.get_symptom_info("made-up-symptom-xyz")
        self.assertIsNone(key)
        self.assertEqual(entry["display_name"], "Unknown symptom")

    def test_supplements_have_no_dose_field(self):
        supplements = knowledge_module.get_supplements_for("headache")
        self.assertTrue(len(supplements) >= 1)
        for item in supplements:
            self.assertNotIn("dose", item)
            self.assertIn("cautions", item)
            self.assertIn("ask_pharmacist_about", item)

    def test_all_json_files_are_valid(self):
        for filename in (
            "symptoms.json",
            "supplements.json",
            "remedies.json",
            "jokes.json",
            "demo_pharmacies.json",
        ):
            path = os.path.join(PROJECT_ROOT, "data", filename)
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
            self.assertIsNotNone(data)


if __name__ == "__main__":
    unittest.main()
