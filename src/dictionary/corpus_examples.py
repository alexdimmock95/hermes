"""Fetch real-world example sentences from public corpora."""

from __future__ import annotations

from functools import lru_cache
import re
from typing import List

import requests


TATOEBA_SEARCH_URL = "https://tatoeba.org/eng/api_v0/search"
EXAMPLES_TIMEOUT_SECONDS = 3.0
MAX_CACHED_WORDS = 2048

_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "DictionaryBot/1.0 (Educational Project; Contact: user@example.com)"
})


def fetch_corpus_examples(word: str, max_examples: int = 3) -> List[str]:
    """
    Return up to max_examples real-world sentences containing the word.
    Fast path is cached by word to minimize repeated requests.
    """
    normalized = _normalize_word(word)
    if not normalized or max_examples <= 0:
        return []

    examples = _fetch_corpus_examples_cached(normalized)
    if not examples:
        return []
    return examples[:max_examples]


@lru_cache(maxsize=MAX_CACHED_WORDS)
def _fetch_corpus_examples_cached(word: str) -> List[str]:
    try:
        params = {
            "from": "eng",
            "query": word,
            "sort": "relevance",
        }
        resp = _SESSION.get(TATOEBA_SEARCH_URL, params=params, timeout=EXAMPLES_TIMEOUT_SECONDS)
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception:
        return []

    raw_results = (
        data.get("results")
        or data.get("sentences")
        or data.get("data")
        or []
    )

    return _select_examples(word, raw_results)


def _select_examples(word: str, raw_results: List[dict]) -> List[str]:
    examples: List[str] = []
    seen = set()

    if " " in word:
        matcher = _phrase_matcher(word)
        word_re = None
    else:
        word_re = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        matcher = None

    for item in raw_results:
        text = _extract_text(item)
        if not text:
            continue

        clean = _normalize_sentence(text)
        if not clean or clean in seen:
            continue

        if word_re:
            if not word_re.search(clean):
                continue
        elif matcher and not matcher(clean):
            continue

        if len(clean) < 20 or len(clean) > 160:
            continue

        seen.add(clean)
        examples.append(clean)

        if len(examples) >= 10:
            break

    return examples


def _extract_text(item: dict) -> str:
    if not isinstance(item, dict):
        return ""
    return (
        item.get("text")
        or item.get("sentence")
        or item.get("translation")
        or item.get("content")
        or ""
    )


def _normalize_word(word: str) -> str:
    return re.sub(r"\s+", " ", word.strip())


def _normalize_sentence(text: str) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return ""
    if text[-1] not in ".!?":
        return f"{text}."
    return text


def _phrase_matcher(phrase: str):
    phrase_lower = phrase.lower()

    def _match(text: str) -> bool:
        return phrase_lower in text.lower()

    return _match
