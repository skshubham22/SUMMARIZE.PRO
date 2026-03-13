from django.test import TestCase
from .utils import get_page_summary, get_search_summary, smart_wiki_search
import wikipedia

class SummarizationTests(TestCase):
    def test_smart_wiki_search_success(self):
        """Test that smart_wiki_search finds a well-known page."""
        page = smart_wiki_search("Python (programming language)")
        self.assertIsNotNone(page)
        self.assertEqual(page.title, "Python (programming language)")

    def test_smart_wiki_search_typo_correction(self):
        """Test that smart_wiki_search handles typos via its internal logic (using wikipedia.suggest)."""
        # Note: test_wiki.py showed "Albrt Einstin" suggests "albert einstein"
        page = smart_wiki_search("Albrt Einstin")
        self.assertIsNotNone(page)
        self.assertIn("Albert Einstein", page.title)

    def test_get_search_summary_success(self):
        """Test that get_search_summary returns a successful result for a valid query."""
        result = get_search_summary("Quantum Mechanics")
        self.assertTrue(result['success'])
        self.assertIn("summary_data", result)
        self.assertIn("overview", result['summary_data'])
        self.assertIn("metrics", result)

    def test_get_page_summary_wikipedia(self):
        """Test that get_page_summary works for a Wikipedia URL."""
        url = "https://en.wikipedia.org/wiki/Django_(framework)"
        result = get_page_summary(url)
        self.assertTrue(result['success'])
        self.assertIn("Django", result['title'])

    def test_get_search_summary_failure(self):
        """Test that get_search_summary handles non-existent topics gracefully."""
        # Using a very obscure/random string
        result = get_search_summary("asdfghjklqwertyuiop1234567890")
        self.assertFalse(result['success'])
        self.assertIn("error", result)

    def test_natural_language_queries(self):
        """Test a variety of natural language question formats."""
        test_cases = [
            ("Who is Elon Musk?", "Elon Musk"),
            ("What are Quantum Mechanics?", "Quantum mechanics"),
            ("Tell me about the Eiffel Tower", "Eiffel Tower"),
            ("How does photosynthesis work?", "Photosynthesis"),
            ("summarize Artificial Intelligence", "Artificial intelligence"),
            ("define Machine Learning", "Machine learning"),
        ]
        
        for query, expected_title_part in test_cases:
            result = get_search_summary(query)
            self.assertTrue(result['success'], f"Failed on query: {query}")
            self.assertIn(expected_title_part.lower(), result['title'].lower(), f"Expected {expected_title_part} in {result['title']}")
