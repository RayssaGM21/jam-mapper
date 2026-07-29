import unittest

import pandas as pd

from jam_mapper.web.views.training import filter_training_candidates


class TrainingFilterTests(unittest.TestCase):
    def test_filters_by_category_and_status(self):
        df = pd.DataFrame(
            [
                {"title": "Challenge A", "category": "Networking", "status": "done"},
                {"title": "Challenge B", "category": "Security", "status": "review"},
                {"title": "Challenge C", "category": "Networking", "status": "not_started"},
            ]
        )

        filtered = filter_training_candidates(df, category=["Networking"], status_filter="Concluidos", status_col="status")

        self.assertEqual(list(filtered["title"]), ["Challenge A"])

    def test_filters_by_review_status(self):
        df = pd.DataFrame(
            [
                {"title": "Challenge A", "category": "Networking", "status": "done"},
                {"title": "Challenge B", "category": "Security", "status": "review"},
            ]
        )

        filtered = filter_training_candidates(df, category=None, status_filter="Revisao", status_col="status")

        self.assertEqual(list(filtered["title"]), ["Challenge B"])


if __name__ == "__main__":
    unittest.main()
