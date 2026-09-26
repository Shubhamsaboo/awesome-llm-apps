import unittest
from memory_server import search_activity


class RetrievalContract(unittest.TestCase):
    def test_project_and_half_open_time_bounds(self):
        result = search_activity(project="Atlas", start="2026-01-12T09:20:00Z", end="2026-01-12T11:00:00Z")
        self.assertEqual([x["id"] for x in result["records"]], ["evt-002", "evt-003"])
        self.assertEqual(result["records"][0]["timestamp"], "2026-01-12T09:20:00Z")

    def test_truncation_keeps_total_and_order(self):
        result = search_activity(project="Atlas", limit=1)
        self.assertEqual(result["total_matches"], 3)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["records"][0]["id"], "evt-001")

    def test_keyword_search_and_missing_evidence(self):
        self.assertEqual(search_activity(query="expired invitation")["total_matches"], 2)
        self.assertEqual(search_activity(query="deployed")["records"], [])

    def test_rejects_ambiguous_time_and_unbounded_limit(self):
        for kwargs in ({"start": "2026-01-12T09:00:00"}, {"limit": 1000}, {"start": "2026-01-13T00:00:00Z", "end": "2026-01-12T00:00:00Z"}):
            with self.assertRaises(ValueError):
                search_activity(**kwargs)


if __name__ == "__main__":
    unittest.main()
