# src/dictionary/wiktionary_client.py
# Wiktionary client using raw wikitext + mwparserfromhell
# FIXED VERSION - Better section handling

import requests
import mwparserfromhell
import re

WIKTIONARY_API = "https://en.wiktionary.org/w/api.php"

HEADERS = {
    "User-Agent": "DictionaryBot/1.0 (Educational Project; Contact: user@example.com)"
}


def fetch_wikitext(word: str) -> str | None:
    """
    Fetch raw Wiktionary wikitext for a given word using MediaWiki API.

    Returns:
        Raw wikitext string, or None if page does not exist.
    """
    params = {
        "action": "parse",
        "page": word,
        "prop": "wikitext",
        "format": "json",
    }

    resp = requests.get(WIKTIONARY_API, params=params, headers=HEADERS, timeout=10)
    if resp.status_code != 200:
        return None

    data = resp.json()

    if "error" in data:
        print(f"DEBUG: Wiktionary API returned error for '{word}':", data["error"])
        return None

    wikitext = data["parse"]["wikitext"]["*"]
    print(f"DEBUG: Successfully fetched wikitext for '{word}' ({len(wikitext)} chars)")

    return wikitext 


def extract_pronunciation(wikitext: str, language: str = "English") -> str | None:
    """
    Extract the first/best IPA pronunciation from the wikitext.
    
    Returns:
        IPA pronunciation string, or None if not found.
    """
    code = mwparserfromhell.parse(wikitext)
    
    # Find language section
    lang_sections = code.get_sections(matches=language, include_lead=False)
    if not lang_sections:
        return None
    
    language_section = lang_sections[0]
    section_text = str(language_section)
    
    # Look for Pronunciation section
    if "===Pronunciation===" not in section_text:
        return None
    
    # Extract the pronunciation section
    parts = section_text.split("===Pronunciation===", 1)
    if len(parts) < 2:
        return None
    
    pron_section = parts[1].split("===")[0]  # Take until next section
    
    # Find first IPA entry - look for {{IPA|en|/.../ pattern
    ipa_match = re.search(r'\{\{IPA\|en\|([^}|]+)', pron_section)
    if ipa_match:
        ipa = ipa_match.group(1).strip()
        # Clean up the IPA notation
        ipa = ipa.replace('/', '').strip()
        return f"/{ipa}/"
    
    return None


def extract_etymology(wikitext: str, language: str = "English") -> str | None:
    """
    Extract etymology information from the wikitext.
    
    Returns:
        Cleaned etymology text, or None if not found.
    """
    code = mwparserfromhell.parse(wikitext)
    
    # Find language section
    lang_sections = code.get_sections(matches=language, include_lead=False)
    if not lang_sections:
        return None
    
    language_section = lang_sections[0]
    section_text = str(language_section)
    
    # Look for Etymology section (could be "Etymology" or "Etymology 1")
    etymology_pattern = r'===Etymology(?:\s+\d+)?===\s*\n(.*?)(?:===|$)'
    match = re.search(etymology_pattern, section_text, re.DOTALL)
    
    if not match:
        return None
    
    etymology_text = match.group(1).strip()
    
    # Take only the first paragraph or up to 500 characters for brevity
    lines = etymology_text.split('\n\n')
    if lines:
        first_para = lines[0]
        # Clean up templates and references
        cleaned = clean_etymology_text(first_para)
        
        # Truncate if too long
        if len(cleaned) > 600:
            cleaned = cleaned[:600] + "..."
        
        return cleaned
    
    return None


def clean_etymology_text(text: str) -> str:
    """
    Clean etymology text while keeping it readable.
    """
    # Remove reference tags like <ref>...</ref>
    text = re.sub(r'<ref[^>]*>.*?</ref>', '', text, flags=re.DOTALL)
    text = re.sub(r'<ref[^>]*/?>', '', text)
    
    # Remove complex templates but try to keep the meaningful text
    # {{m|ang|dogga}} -> dogga
    text = re.sub(r'\{\{m\|[^|]+\|([^}|]+)(?:\|[^}]*)?\}\}', r'"\1"', text)
    
    # {{cog|sco|dug}} -> Scottish "dug"
    text = re.sub(r'\{\{cog\|([^|]+)\|([^}|]+)(?:\|[^}]*)?\}\}', r'\2', text)
    
    # {{inh+|en|enm|dogge}} -> Middle English "dogge"
    text = re.sub(r'\{\{inh\+?\|en\|([^|]+)\|([^}|]+)(?:\|[^}]*)?\}\}', r'\2', text)
    
    # {{der|en|...}} and similar - just remove
    text = re.sub(r'\{\{(?:der|inh|cog|unc|etyl)[^}]+\}\}', '', text)
    
    # Remove any remaining templates
    text = re.sub(r'\{\{[^}]+\}\}', '', text)
    
    # Clean up wiki links [[word]] -> word
    text = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    
    # Remove double quotes around single words
    text = re.sub(r'""([^"]+)""', r'"\1"', text)
    
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    
    # Clean up multiple periods
    text = re.sub(r'\.{2,}', '.', text)
    
    return text.strip()


def extract_definitions(
    wikitext: str,
    language: str = "English",
    max_defs_per_pos: int = 5,
):
    """
    Parse raw wikitext and extract definitions for a given language.

    Returns:
        List of dicts:
        [
            {"pos": "Noun", "definitions": ["def1", "def2"]},
            ...
        ]
    """
    code = mwparserfromhell.parse(wikitext)

    # --- Step 1: isolate language section ---
    lang_sections = code.get_sections(matches=language, include_lead=False)
    if not lang_sections:
        print(f"DEBUG: No '{language}' section found")
        return []

    language_section = lang_sections[0]
    print(f"DEBUG: Found '{language}' section")

    entries = []

    # Define allowed POS headings
    allowed_pos = {
        "Noun", "Verb", "Adjective", "Adverb", "Pronoun",
        "Preposition", "Conjunction", "Interjection",
        "Determiner", "Article", "Numeral", "Proper noun"
    }

    # KEY FIX: Get all headings within the language section
    for heading in language_section.filter_headings():
        heading_text = heading.title.strip_code().strip()
        
        if heading_text not in allowed_pos:
            continue

        print(f"DEBUG: Processing POS heading: '{heading_text}'")

        # FIX: Instead of trying to get_sections again, we need to find the content
        # that follows this heading until the next heading of the same or higher level
        
        definitions = []
        
        # Convert section to string and process line by line
        section_text = str(language_section)
        
        # Find where this POS heading starts
        heading_pattern = f"==={heading_text}==="
        
        if heading_pattern not in section_text:
            # Try level 4 heading
            heading_pattern = f"===={heading_text}===="
        
        if heading_pattern in section_text:
            # Split at this heading and take everything after
            parts = section_text.split(heading_pattern, 1)
            if len(parts) > 1:
                after_heading = parts[1]
                
                # Take content until next heading of same or higher level
                # Stop at === or ====
                lines = after_heading.split('\n')
                
                for line in lines:
                    # Stop if we hit another heading
                    if line.strip().startswith('==='):
                        break
                    
                    # Look for definition lines (start with #)
                    stripped = line.lstrip()
                    if stripped.startswith('#') and not stripped.startswith('##'):
                        # Remove leading # and clean
                        clean = clean_definition(stripped.lstrip('#:* ').strip())
                        if clean and len(definitions) < max_defs_per_pos:
                            definitions.append(clean)
                            print(f"DEBUG: Found definition: {clean[:50]}...")

        if definitions:
            entries.append({
                "pos": heading_text,
                "definitions": definitions[:max_defs_per_pos],
            })
            print(f"DEBUG: Added {len(definitions)} definitions for {heading_text}")

    print(f"DEBUG: Total POS entries found: {len(entries)}")
    return entries


def clean_definition(text: str) -> str:
    """
    Clean a single definition line while preserving meaning.
    """
    # Remove templates {{...}}
    text = re.sub(r"\{\{[^}]+\}\}", "", text)

    # Replace wiki links [[dog]] -> dog
    # First handle [[word|display]] -> display
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    # Then handle [[word]] -> word
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def fetch_definitions(word: str, max_defs_per_pos: int = 5) -> dict:
    """
    High-level dictionary lookup.
    """
    empty = {"word": word, "language": "English", "pronunciation": None, "etymology": None, "entries": []}

    wikitext = fetch_wikitext(word)
    if not wikitext:
        return empty

    pronunciation = extract_pronunciation(wikitext)
    etymology = extract_etymology(wikitext)
    entries = extract_definitions(
        wikitext,
        language="English",
        max_defs_per_pos=max_defs_per_pos,
    )

    return {
        "word": word,
        "language": "English",
        "pronunciation": pronunciation,
        "etymology": etymology,
        "entries": entries,
    }


def format_for_telegram(word: str, max_defs_per_pos: int = 5) -> str:
    """
    Format dictionary output for Telegram Markdown.
    """
    result = fetch_definitions(word, max_defs_per_pos)

    if not result["entries"]:
        return f"❌ No definition found for '*{word}*'."

    lines = [f"📖 *{word.upper()}*"]
    
    # Add pronunciation if available
    if result["pronunciation"]:
        lines.append(f"🔊 {result['pronunciation']}")
    
    lines.append("")  # Blank line

    for entry in result["entries"]:
        lines.append(f"*{entry['pos']}*")

        for i, definition in enumerate(entry["definitions"], 1):
            safe = (
                definition.replace("*", "\\*")
                .replace("_", "\\_")
                .replace("[", "\\[")
                .replace("]", "\\]")
                .replace("`", "\\`")
            )
            lines.append(f"  {i}. {safe}")

        lines.append("")

    return "\n".join(lines)


def format_etymology_for_telegram(word: str) -> str:
    """
    Format just the etymology for Telegram display.
    """
    result = fetch_definitions(word)
    
    if not result["etymology"]:
        return f"❌ No etymology found for '*{word}*'."
    
    # Escape markdown special characters
    etymology = result["etymology"]
    safe_etymology = (
        etymology.replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("`", "\\`")
    )
    
    return f"📜 *Etymology of {word.upper()}*\n\n{safe_etymology}"


if __name__ == "__main__":
    print("Testing Wiktionary client...\n")
    for w in ["dog", "run", "cat"]:
        print("=" * 60)
        print(format_for_telegram(w))
        print()