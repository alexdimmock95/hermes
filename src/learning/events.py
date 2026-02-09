from datetime import datetime
from src.learning.storage import store_word_event

def emit_word_event(user_id: int, word: str, source: str):
    word = word.lower().strip()

    event = {
        "user_id": user_id,
        "word": word,
        "source": source,
        "timestamp": datetime.utcnow().isoformat()
    }

    store_word_event(event)