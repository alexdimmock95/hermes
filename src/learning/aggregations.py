from src.learning.storage import get_connection


def get_word_counts(user_id: int):
    """
    Return word → count mapping.
    Sorted by frequency (descending).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT word, COUNT(*) as count
        FROM word_events
        WHERE user_id = ?
        GROUP BY word
        ORDER BY count DESC
    """, (user_id,))

    results = cursor.fetchall()
    conn.close()

    # Convert to dict: {word: count}
    return {word: count for word, count in results}


def get_chronological_events(user_id: int, limit=20):
    """
    Return ordered list of word events (most recent first).
    
    Args:
        user_id: User ID to query
        limit: Maximum number of events to return
    
    Returns:
        List of dicts with keys: word, source, timestamp
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT word, source, timestamp
        FROM word_events
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, limit))

    results = cursor.fetchall()
    conn.close()

    # Convert to list of dicts
    return [
        {
            "word": word,
            "source": source,
            "timestamp": timestamp
        }
        for word, source, timestamp in results
    ]


def get_top_words(user_id: int, limit=10):
    """
    Return top N most searched words.
    
    Args:
        user_id: User ID to query
        limit: Number of top words to return
    
    Returns:
        List of dicts with keys: word, count
    """
    word_counts = get_word_counts(user_id)
    
    # Sort by count descending and take top N
    sorted_words = sorted(
        word_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:limit]
    
    return [
        {"word": word, "count": count}
        for word, count in sorted_words
    ]


def get_total_words_searched(user_id: int):
    """Get total number of unique words searched."""
    word_counts = get_word_counts(user_id)
    return len(word_counts)


def get_total_searches(user_id: int):
    """Get total number of searches (including duplicates)."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM word_events WHERE user_id = ?
    """, (user_id,))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else 0