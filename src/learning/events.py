from datetime import datetime

def emit_word_event(user_id: int, word: str, source: str):
    word = word.lower().strip()

    event = {
        "user_id": user_id,
        "word": word,
        "source": source,
        "timestamp": datetime.utcnow().isoformat()
    }

    store_word_event(event)

def store_word_event(event: dict):
    """
    Persist a word event.
    """

    # TODO:
    # - SQLite INSERT
    # - OR append to JSON
    # - OR in-memory list (dev)
    pass