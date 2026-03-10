#!/usr/bin/env python3
"""
Text Generation API
REST API for text generation using Markov chains and n-gram language models.
Author: Gabriel Demetrios Lafis
"""

import re
import json
import random
import string
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from flask import Flask, request, jsonify

app = Flask(__name__)


class MarkovChainGenerator:
    """Text generator based on Markov chains with configurable n-gram order."""

    def __init__(self, order: int = 2):
        self.order = order
        self.transitions: Dict[Tuple[str, ...], List[str]] = defaultdict(list)
        self.start_tokens: List[Tuple[str, ...]] = []
        self.trained = False

    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words, preserving punctuation."""
        tokens = re.findall(r"\b\w+\b|[.,!?;:]", text)
        return [t.lower() for t in tokens]

    def train(self, text: str) -> None:
        """Train the model on a corpus of text."""
        tokens = self.tokenize(text)
        if len(tokens) < self.order + 1:
            return

        for i in range(len(tokens) - self.order):
            state = tuple(tokens[i:i + self.order])
            next_token = tokens[i + self.order]
            self.transitions[state].append(next_token)

            if i == 0 or tokens[i - 1] in ".!?":
                self.start_tokens.append(state)

        self.trained = True

    def generate(self, max_length: int = 100, seed: Optional[str] = None) -> str:
        """Generate text using the trained Markov chain."""
        if not self.trained:
            raise ValueError("Model has not been trained yet.")

        if seed:
            random.seed(seed)

        if not self.start_tokens:
            state = random.choice(list(self.transitions.keys()))
        else:
            state = random.choice(self.start_tokens)

        result = list(state)

        for _ in range(max_length - self.order):
            if state not in self.transitions:
                break
            next_token = random.choice(self.transitions[state])
            result.append(next_token)
            state = tuple(result[-self.order:])

        text = " ".join(result)
        text = re.sub(r"\s+([.,!?;:])", r"\1", text)
        if text and text[-1] not in ".!?":
            text += "."
        return text.capitalize()

    def get_stats(self) -> Dict:
        """Return model statistics."""
        return {
            "order": self.order,
            "unique_states": len(self.transitions),
            "start_states": len(self.start_tokens),
            "trained": self.trained,
        }


class NGramLanguageModel:
    """N-gram language model with Laplace smoothing for text generation."""

    def __init__(self, n: int = 3):
        self.n = n
        self.ngram_counts: Dict[Tuple[str, ...], Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        self.vocab: set = set()
        self.trained = False

    def train(self, text: str) -> None:
        """Train the n-gram model on text."""
        tokens = text.lower().split()
        self.vocab.update(tokens)

        for i in range(len(tokens) - self.n):
            context = tuple(tokens[i:i + self.n - 1])
            target = tokens[i + self.n - 1]
            self.ngram_counts[context][target] += 1

        self.trained = True

    def predict_next(self, context: Tuple[str, ...], temperature: float = 1.0) -> str:
        """Predict the next word given a context with temperature sampling."""
        if context not in self.ngram_counts:
            return random.choice(list(self.vocab)) if self.vocab else ""

        candidates = self.ngram_counts[context]
        words = list(candidates.keys())
        counts = list(candidates.values())

        if temperature != 1.0:
            weights = [c ** (1.0 / temperature) for c in counts]
        else:
            weights = counts

        total = sum(weights)
        probabilities = [w / total for w in weights]

        return random.choices(words, weights=probabilities, k=1)[0]

    def generate(
        self, prompt: str = "", max_length: int = 50, temperature: float = 1.0
    ) -> str:
        """Generate text from an optional prompt."""
        if not self.trained:
            raise ValueError("Model has not been trained yet.")

        if prompt:
            tokens = prompt.lower().split()
        else:
            context = random.choice(list(self.ngram_counts.keys()))
            tokens = list(context)

        for _ in range(max_length):
            context = tuple(tokens[-(self.n - 1):])
            next_word = self.predict_next(context, temperature)
            if not next_word:
                break
            tokens.append(next_word)

        return " ".join(tokens)

    def get_stats(self) -> Dict:
        """Return model statistics."""
        return {
            "n": self.n,
            "vocabulary_size": len(self.vocab),
            "unique_contexts": len(self.ngram_counts),
            "trained": self.trained,
        }


# --- Sample training corpus ---
SAMPLE_CORPUS = """
Natural language processing is a subfield of computer science and linguistics.
It is concerned with the interactions between computers and human language.
The goal is to enable computers to understand, interpret, and generate human language.
Machine learning algorithms are widely used in natural language processing.
Text generation is the task of producing coherent and contextually relevant text.
Language models learn the probability distribution over sequences of words.
Markov chains model the probability of each word based on the previous words.
Neural networks have revolutionized natural language processing in recent years.
Transfer learning allows models trained on large corpora to be fine-tuned for specific tasks.
Text generation has applications in chatbots, content creation, and automated writing.
Statistical methods provide a foundation for understanding language patterns.
Tokenization is the process of breaking text into individual tokens or words.
The quality of generated text depends on the size and diversity of the training data.
Language models can be evaluated using perplexity and other metrics.
Good text generation requires balancing creativity with coherence.
"""

# --- Initialize models ---
markov_model = MarkovChainGenerator(order=2)
markov_model.train(SAMPLE_CORPUS)

ngram_model = NGramLanguageModel(n=3)
ngram_model.train(SAMPLE_CORPUS)


# --- API Routes ---

@app.route("/")
def index():
    """API root endpoint with documentation."""
    return jsonify({
        "name": "Text Generation API",
        "version": "1.0.0",
        "description": "REST API for text generation using Markov chains and n-gram models",
        "endpoints": {
            "GET /": "API documentation",
            "GET /api/status": "Service health check",
            "POST /api/generate/markov": "Generate text with Markov chain",
            "POST /api/generate/ngram": "Generate text with n-gram model",
            "POST /api/train": "Train models with custom text",
            "GET /api/models": "List available models and stats",
        },
    })


@app.route("/api/status")
def status():
    """Health check endpoint."""
    return jsonify({
        "status": "running",
        "version": "1.0.0",
        "models": {
            "markov": markov_model.get_stats(),
            "ngram": ngram_model.get_stats(),
        },
    })


@app.route("/api/generate/markov", methods=["POST"])
def generate_markov():
    """Generate text using the Markov chain model."""
    data = request.get_json() or {}
    max_length = data.get("max_length", 50)
    seed = data.get("seed", None)

    try:
        max_length = min(int(max_length), 500)
        text = markov_model.generate(max_length=max_length, seed=seed)
        return jsonify({
            "model": "markov_chain",
            "generated_text": text,
            "parameters": {"max_length": max_length, "order": markov_model.order},
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/generate/ngram", methods=["POST"])
def generate_ngram():
    """Generate text using the n-gram language model."""
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    max_length = data.get("max_length", 50)
    temperature = data.get("temperature", 1.0)

    try:
        max_length = min(int(max_length), 500)
        temperature = max(0.1, min(float(temperature), 2.0))
        text = ngram_model.generate(
            prompt=prompt, max_length=max_length, temperature=temperature
        )
        return jsonify({
            "model": "ngram",
            "generated_text": text,
            "parameters": {
                "prompt": prompt,
                "max_length": max_length,
                "temperature": temperature,
                "n": ngram_model.n,
            },
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/train", methods=["POST"])
def train_models():
    """Train models with custom text corpus."""
    data = request.get_json() or {}
    text = data.get("text", "")
    model_type = data.get("model", "both")

    if not text or len(text.split()) < 10:
        return jsonify({"error": "Training text must have at least 10 words."}), 400

    results = {}
    if model_type in ("markov", "both"):
        markov_model.train(text)
        results["markov"] = markov_model.get_stats()
    if model_type in ("ngram", "both"):
        ngram_model.train(text)
        results["ngram"] = ngram_model.get_stats()

    return jsonify({"message": "Training complete", "models": results})


@app.route("/api/models")
def list_models():
    """List available models and their statistics."""
    return jsonify({
        "models": {
            "markov_chain": {
                "description": "Text generation using Markov chains",
                "stats": markov_model.get_stats(),
            },
            "ngram": {
                "description": "N-gram language model with temperature sampling",
                "stats": ngram_model.get_stats(),
            },
        }
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
