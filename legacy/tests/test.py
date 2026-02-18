import sys
import os

# Add the project root to the Python path
# This goes up from legacy/tests/ to the project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.dictionary.wiktionary_client import fetch_wikitext, extract_definitions

# Fetch the wikitext
wikitext, source = fetch_wikitext("fottiti", language_code="it", try_english_first=True)

# Print first 2000 characters to see structure
print("=== WIKITEXT PREVIEW ===")
print(wikitext[:2000])
print("\n=== TRYING TO EXTRACT ===")

# Try to extract
entries = extract_definitions(wikitext, language="Italian", language_code="en")
print(f"Found {len(entries)} entries")
for e in entries:
    print(f"  - {e['pos']}: {len(e['definitions'])} definitions")