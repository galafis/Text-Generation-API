"""
Tests for Text Generation API
Author: Gabriel Demetrios Lafis
"""

import unittest
import json
from app import app, MarkovChainGenerator, NGramLanguageModel


class TestMarkovChainGenerator(unittest.TestCase):
    """Tests for the Markov chain text generator."""

    def setUp(self):
        self.generator = MarkovChainGenerator(order=2)
        self.corpus = (
            "The cat sat on the mat. The dog sat on the log. "
            "The cat and the dog are friends."
        )
        self.generator.train(self.corpus)

    def test_train_sets_trained_flag(self):
        self.assertTrue(self.generator.trained)

    def test_generate_returns_text(self):
        text = self.generator.generate(max_length=20)
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)

    def test_generate_respects_max_length(self):
        text = self.generator.generate(max_length=5)
        words = text.replace(".", "").split()
        self.assertLessEqual(len(words), 10)

    def test_untrained_model_raises_error(self):
        gen = MarkovChainGenerator()
        with self.assertRaises(ValueError):
            gen.generate()

    def test_tokenize(self):
        tokens = self.generator.tokenize("Hello, world!")
        self.assertEqual(tokens, ["hello", ",", "world", "!"])

    def test_get_stats(self):
        stats = self.generator.get_stats()
        self.assertEqual(stats["order"], 2)
        self.assertTrue(stats["trained"])
        self.assertGreater(stats["unique_states"], 0)

    def test_seed_reproducibility(self):
        text1 = self.generator.generate(max_length=20, seed="test_seed")
        text2 = self.generator.generate(max_length=20, seed="test_seed")
        self.assertEqual(text1, text2)


class TestNGramLanguageModel(unittest.TestCase):
    """Tests for the n-gram language model."""

    def setUp(self):
        self.model = NGramLanguageModel(n=3)
        self.corpus = (
            "the quick brown fox jumps over the lazy dog "
            "the quick brown cat sleeps on the soft bed "
            "the lazy dog runs in the green park"
        )
        self.model.train(self.corpus)

    def test_train_sets_trained_flag(self):
        self.assertTrue(self.model.trained)

    def test_generate_returns_text(self):
        text = self.model.generate(max_length=10)
        self.assertIsInstance(text, str)
        self.assertGreater(len(text), 0)

    def test_generate_with_prompt(self):
        text = self.model.generate(prompt="the quick", max_length=5)
        self.assertTrue(text.startswith("the quick"))

    def test_temperature_sampling(self):
        text_low = self.model.generate(max_length=10, temperature=0.1)
        text_high = self.model.generate(max_length=10, temperature=2.0)
        self.assertIsInstance(text_low, str)
        self.assertIsInstance(text_high, str)

    def test_get_stats(self):
        stats = self.model.get_stats()
        self.assertEqual(stats["n"], 3)
        self.assertTrue(stats["trained"])
        self.assertGreater(stats["vocabulary_size"], 0)


class TestAPIEndpoints(unittest.TestCase):
    """Tests for Flask API endpoints."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_index(self):
        response = self.client.get("/")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("endpoints", data)

    def test_status(self):
        response = self.client.get("/api/status")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["status"], "running")

    def test_generate_markov(self):
        response = self.client.post(
            "/api/generate/markov",
            data=json.dumps({"max_length": 20}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("generated_text", data)

    def test_generate_ngram(self):
        response = self.client.post(
            "/api/generate/ngram",
            data=json.dumps({"max_length": 20, "temperature": 0.8}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("generated_text", data)

    def test_train_endpoint(self):
        corpus = "This is a test corpus with enough words to train a model properly and effectively."
        response = self.client.post(
            "/api/train",
            data=json.dumps({"text": corpus}),
            content_type="application/json",
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("models", data)

    def test_train_with_short_text(self):
        response = self.client.post(
            "/api/train",
            data=json.dumps({"text": "too short"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_list_models(self):
        response = self.client.get("/api/models")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("models", data)


if __name__ == "__main__":
    unittest.main()
