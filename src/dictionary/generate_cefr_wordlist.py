"""
generate_cefr_wordlist.py

Run this once to populate cefr_data/en.txt with real CEFR word data.

Usage (run from your hermes/ project root):
    python generate_cefr_wordlist.py
"""

import os
from cefrpy import CEFRAnalyzer

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "cefr_data", "en.txt")

LEVEL_MAP = {1: "A1", 2: "A2", 3: "B1", 4: "B2", 5: "C1", 6: "C2"}
VALID_LEVELS = list(LEVEL_MAP.values())

analyzer = CEFRAnalyzer()

total = analyzer.get_total_words()
print(f"Total words in cefrpy: {total}")

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

word_count = 0
skipped = 0

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write("# English CEFR word list - generated from cefrpy\n")

    # yield_words() iterates every word in the database one at a time
    # This is the correct method — confirmed from CEFRAnalyzer source code
    for word in analyzer.yield_words():
        avg_level = analyzer.get_average_word_level_float(word)

        if avg_level is None:
            skipped += 1
            continue

        # Round float to nearest level: 2.3 → 2 → "A2"
        level_str = LEVEL_MAP.get(round(avg_level))

        if level_str not in VALID_LEVELS:
            skipped += 1
            continue

        f.write(f"{word.lower().strip()}\t{level_str}\n")
        word_count += 1

        # Print progress every 1000 words so you can see it's working
        if word_count % 1000 == 0:
            print(f"  {word_count} words written...")

print(f"Done! Wrote {word_count} words to {OUTPUT_PATH}")
if skipped > 0:
    print(f"(Skipped {skipped} words — no level data)")