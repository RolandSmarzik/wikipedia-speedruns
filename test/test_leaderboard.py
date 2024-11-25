import unittest
import json
from unittest.mock import patch, MagicMock
from wikispeedruns.leaderboards import get_leaderboard_runs, get_leaderboard_stats, LEADERBOARD_COLUMNS
from flask import Flask


class TestLeaderboardFunctions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.config['TESTING'] = True
        cls.app.config['MYSQL_USER'] = 'testuser'
        cls.app.config['MYSQL_HOST'] = 'localhost'
        cls.app.config['MYSQL_PASSWORD'] = 'testpassword'
        cls.app.config['DATABASE'] = 'test'

        cls.app_context = cls.app.app_context()
        cls.app_context.push()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()

    @patch('wikispeedruns.leaderboards.get_db')
    def test_get_leaderboard_runs_basic(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            {**{col: f"{col}_value" for col in LEADERBOARD_COLUMNS}, "numRuns": 2, "path": json.dumps({"path": ["page1", "page2"]})},
            {"run_id": 1, "path": json.dumps({"path": ["page1", "page2"]}), "numRuns": 2}
        ]

        result = get_leaderboard_runs(prompt_id=22)
        print(result)

        self.assertIn("numRuns", result)
        self.assertIn("runs", result)
        self.assertEqual(result["numRuns"], 2)
        self.assertEqual(result["runs"][1]["path"], ["page1", "page2"])

    @patch('wikispeedruns.leaderboards.get_db')
    def test_get_leaderboard_runs_sorting(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            {"run_id": 3, "play_time": 50, "path": json.dumps({"path": ["page1", "page2", "page3"]}), "numRuns": 2},
            {"run_id": 2, "play_time": 100, "path": json.dumps({"path": ["page1", "page2"]}), "numRuns": 2}
        ]

        result = get_leaderboard_runs(prompt_id=22, sort_mode='time', sort_asc=True)

        self.assertEqual(len(result["runs"]), 2)
        self.assertEqual(result["runs"][0]["run_id"], 3) 

    @patch('wikispeedruns.leaderboards.get_db')
    def test_get_leaderboard_runs_with_pagination(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [
            {"run_id": i, "path": json.dumps({"path": ["page1"]}), "numRuns": 20} for i in range(11, 16)
        ]

        result = get_leaderboard_runs(prompt_id=22, offset=10, limit=5)

        self.assertEqual(len(result["runs"]), 5)
        self.assertEqual(result["runs"][0]["run_id"], 11)
        self.assertEqual(result["runs"][-1]["run_id"], 15)

    @patch('wikispeedruns.leaderboards.get_db')
    def test_get_leaderboard_stats(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        mock_cursor.fetchall.return_value = [{
            "finish_pct": 75,
            "avg_path_len": 3.5,
            "avg_play_time": 150.0
        }]

        result = get_leaderboard_stats(prompt_id=22)

        self.assertEqual(result["finish_pct"], 75)
        self.assertEqual(result["avg_path_len"], 3.5)
        self.assertEqual(result["avg_play_time"], 150.0)

    @patch('wikispeedruns.leaderboards.get_db')
    def test_get_leaderboard_runs_invalid_sort_mode(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        with self.assertRaises(ValueError):
            get_leaderboard_runs(prompt_id=22, sort_mode='invalid_mode')

    @patch('wikispeedruns.leaderboards.get_db')
    def test_get_leaderboard_runs_query_only(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

        result = get_leaderboard_runs(prompt_id=22, query_only=True)

        self.assertIn("query", result)
        self.assertIn("args", result)
        self.assertIsInstance(result["query"], str)
        self.assertIsInstance(result["args"], dict)

if __name__ == "__main__":
    unittest.main()