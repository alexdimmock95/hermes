def get_word_counts(user_id: int):
    """
    Return word → count mapping.
    """
    # SELECT word, COUNT(*) FROM events WHERE user_id = ?
    pass


def get_chronological_events(user_id: int):
    """
    Return ordered list of word events.
    """
    # SELECT word, source, timestamp ORDER BY timestamp DESC
    pass