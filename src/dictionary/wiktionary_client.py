# src/dictionary/wiktionary_client.py
# Wiktionary client using raw wikitext + mwparserfromhell
# FIXED VERSION - Better section handling

import requests
import mwparserfromhell
import re
from gtts import gTTS
import io

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
    
    # Takes up to 3 paragraphs, up to 1200 chars total
    paragraphs = [p.strip() for p in etymology_text.split('\n\n') if p.strip()]

    result_parts = []
    total_length = 0

    for para in paragraphs[:3]:  # Max 3 paragraphs
        if para.startswith('{{') or para.startswith('<'):
            continue
            
        cleaned = clean_etymology_text(para)
        
        if len(cleaned) < 20:
            continue
            
        result_parts.append(cleaned)
        total_length += len(cleaned)
        
        if total_length > 1000:
            break
        
    return ' '.join(result_parts) if result_parts else None


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
    section_text = str(language_section)
    print(f"DEBUG: Found '{language}' section ({len(section_text)} chars)")

    entries = []

    # Define allowed POS headings
    allowed_pos = {
        "Noun", "Verb", "Adjective", "Adverb", "Pronoun",
        "Preposition", "Conjunction", "Interjection",
        "Determiner", "Article", "Numeral", "Proper noun"
    }

    # Get all headings
    headings = list(language_section.filter_headings())
    print(f"DEBUG: Found {len(headings)} total headings in language section")

    # Process each POS heading
    for heading in headings:
        heading_text = heading.title.strip_code().strip()
        
        # Skip the language heading itself and non-POS headings
        if heading_text == language or heading_text not in allowed_pos:
            continue

        print(f"DEBUG: Processing POS heading: '{heading_text}' (level {heading.level})")

        definitions = []
        
        # Build the heading pattern based on the actual level
        # Level 3 = ===, Level 4 = ====, etc.
        equals = "=" * heading.level
        heading_pattern = f"{equals}{heading_text}{equals}"
        
        print(f"DEBUG: Looking for pattern: '{heading_pattern}'")
        
        if heading_pattern in section_text:
            # Split at this heading and take everything after
            parts = section_text.split(heading_pattern, 1)
            if len(parts) > 1:
                after_heading = parts[1]
                print(f"DEBUG: Content after heading (first 300 chars):\n{after_heading[:300]}\n")
                
                # Take content until next heading of same or higher level
                lines = after_heading.split('\n')
                
                for line in lines:
                    # Stop if we hit another heading of equal or higher level
                    # (fewer or equal number of = signs at the start)
                    stripped = line.strip()
                    if stripped.startswith('===') and not stripped.startswith('===='):
                        print(f"DEBUG: Hit next level 3 section, stopping")
                        break
                    
                    # Look for definition lines (start with #)
                    line_stripped = line.lstrip()
                    if line_stripped.startswith('#') and not line_stripped.startswith('##'):
                        # Remove leading # and clean
                        clean = clean_definition(line_stripped.lstrip('#:* ').strip())
                        if clean and len(definitions) < max_defs_per_pos:
                            definitions.append(clean)
                            print(f"DEBUG: Found definition: {clean[:80]}...")

        if definitions:
            entries.append({
                "pos": heading_text,
                "definitions": definitions[:max_defs_per_pos],
            })
            print(f"DEBUG: Added {len(definitions)} definitions for {heading_text}")
        else:
            print(f"DEBUG: No definitions found for {heading_text}")

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
        print("DEBUG fetch_definitions: No wikitext returned")
        return empty

    pronunciation = extract_pronunciation(wikitext)
    print(f"DEBUG fetch_definitions: pronunciation = {pronunciation}")
    
    etymology = extract_etymology(wikitext)
    print(f"DEBUG fetch_definitions: etymology exists = {etymology is not None}")
    
    entries = extract_definitions(
        wikitext,
        language="English",
        max_defs_per_pos=max_defs_per_pos,
    )
    print(f"DEBUG fetch_definitions: entries count = {len(entries)}")
    print(f"DEBUG fetch_definitions: entries = {entries}")

    result = {
        "word": word,
        "language": "English",
        "pronunciation": pronunciation,
        "etymology": etymology,
        "entries": entries,
    }
    
    print(f"DEBUG fetch_definitions: returning result with {len(result['entries'])} entries")
    return result

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


def generate_pronunciation_audio(word: str, language: str = 'en') -> io.BytesIO:
    """
    Generate pronunciation audio using Google TTS.
    
    Args:
        word: The word to pronounce
        language: Language code (default: 'en' for English)
    
    Returns:
        BytesIO object containing the audio data
    """
    tts = gTTS(text=word, lang=language, slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer


if __name__ == "__main__":
    print("Testing Wiktionary client...\n")
    for w in ["dog", "run", "cat"]:
        print("=" * 60)
        print(format_for_telegram(w))
        print()