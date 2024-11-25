import unittest
from unittest.mock import patch
from wikispeedruns.marathon import getDifficultyScore


class TestDifficultyScore(unittest.TestCase):
    @patch('wikispeedruns.scraper.util.countWords')
    @patch('wikispeedruns.scraper.util.countDigitsInTitle')
    @patch('wikispeedruns.scraper.util.convertToArticleName')
    @patch('wikispeedruns.scraper.util.articleLinkNumCheck')
    def test_get_difficulty_score(self, mock_link_num_check, mock_convert_to_article_name, mock_count_digits, mock_count_words):
        mock_link_num_check.return_value = (True, 150, 120) 
        mock_convert_to_article_name.return_value = "Test Article"
        mock_count_digits.return_value = 0
        mock_count_words.return_value = 3

        score, digits_info, words_info, incoming_info, outgoing_info = getDifficultyScore(12345, 100, 100)

        self.assertIsInstance(score, float)
        self.assertGreater(score, 0)
        self.assertEqual(digits_info[1], 0)
        self.assertEqual(words_info[1], 3)
        self.assertEqual(incoming_info[1], 150)
        self.assertEqual(outgoing_info[1], 120)

    @patch('wikispeedruns.scraper.util.articleLinkNumCheck')
    def test_get_difficulty_score_link_check_fail(self, mock_link_num_check):
        mock_link_num_check.return_value = (False, 0, 0)
        
        score, *other_metrics = getDifficultyScore(12345, 100, 100)
        
        self.assertEqual(score, -1)
        self.assertEqual(other_metrics, [0, 0, 0, 0]) 




