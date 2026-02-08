# src/dictionary/wiktionary_client.py
# Wiktionary client using raw wikitext + mwparserfromhell
# FIXED VERSION - Better section handling

import requests
import mwparserfromhell
import re
from gtts import gTTS
import io
from src.dictionary.corpus_examples import fetch_corpus_examples

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
    Looks for the language section bounded by ==Language==
    
    Args:
        wikitext: Raw wikitext from Wiktionary
        language: Language to extract (e.g., "English", "Spanish", "French")
        max_defs_per_pos: Maximum definitions per part of speech
    
    Returns:
        List of dicts:
        [
            {"pos": "Noun", "definitions": ["def1", "def2"]},
            ...
        ]
    """
    # Look for the language section using ==Language==
    language_pattern = f"=={language}=="
    
    if language_pattern not in wikitext:
        print(f"DEBUG: No '{language}' section found (looked for {language_pattern})")
        return []
    
    # Split at the language heading
    parts = wikitext.split(language_pattern, 1)
    if len(parts) < 2:
        return []
    
    # Take everything after the language heading
    after_language = parts[1]
    
    # Find the end of this language section (next == heading of same level)
    # Stop at the next ==SomeOtherLanguage==
    next_language_match = re.search(r'\n==\w', after_language)
    if next_language_match:
        language_section = after_language[:next_language_match.start()]
    else:
        language_section = after_language
    
    print(f"DEBUG: Found '{language}' section ({len(language_section)} chars)")

    entries = []

    # Define allowed POS headings (level 3: ===POS===)
    allowed_pos = {
        "Noun", "Verb", "Adjective", "Adverb", "Pronoun",
        "Preposition", "Conjunction", "Interjection",
        "Determiner", "Article", "Numeral", "Proper noun"
    }

    # Find all POS headings (===POS===)
    pos_pattern = r'===(' + '|'.join(allowed_pos) + r')==='
    pos_matches = list(re.finditer(pos_pattern, language_section))
    
    print(f"DEBUG: Found {len(pos_matches)} POS headings in {language} section")

    for match in pos_matches:
        pos_name = match.group(1)
        pos_start = match.end()
        
        # Find where this POS section ends (next === or end of language section)
        next_section = re.search(r'\n===', language_section[pos_start:])
        if next_section:
            pos_end = pos_start + next_section.start()
        else:
            pos_end = len(language_section)
        
        pos_content = language_section[pos_start:pos_end]
        
        print(f"DEBUG: Processing {pos_name} (content length: {len(pos_content)} chars)")
        
        definitions = []
        
        # Extract definition lines (start with #, not ##)
        lines = pos_content.split('\n')
        for line in lines:
            line_stripped = line.lstrip()
            
            # Skip if it's a sub-definition (##) or example (starts with #:, #*, etc.)
            if not line_stripped.startswith('#'):
                continue
            if line_stripped.startswith('##') or line_stripped.startswith('#:') or line_stripped.startswith('#*'):
                continue
                
            # Skip if it contains example/usage markers
            if '{{ux' in line_stripped or '{{quote' in line_stripped:
                continue
            
            # Clean the definition
            clean = clean_definition(line_stripped.lstrip('#:* ').strip())
            
            if clean and len(clean) > 10 and len(definitions) < max_defs_per_pos:
                definitions.append(clean)
                print(f"DEBUG: Found definition: {clean[:80]}...")
        
        if definitions:
            entries.append({
                "pos": pos_name,
                "definitions": definitions[:max_defs_per_pos],
            })
            print(f"DEBUG: Added {len(definitions)} definitions for {pos_name}")

    print(f"DEBUG: Total POS entries found: {len(entries)}")
    return entries

def clean_definition(text: str) -> str:
    """
    Clean a single definition line while preserving meaning.
    """
    # Stop at certain markers that indicate we're leaving the actual definition
    for marker in ['{{quote', '{{ux', '{{syn', '{{ant', '{{hypo', '{{see']:
        if marker in text:
            text = text.split(marker)[0]
    
    # Remove ALL templates {{...}} including nested ones
    while '{{' in text:
        # Find outermost template
        start = text.find('{{')
        if start == -1:
            break
        
        # Find matching closing braces
        depth = 0
        end = start
        for i in range(start, len(text)):
            if text[i:i+2] == '{{':
                depth += 1
                i += 1
            elif text[i:i+2] == '}}':
                depth -= 1
                if depth == 0:
                    end = i + 2
                    break
                i += 1
        
        if end > start:
            text = text[:start] + text[end:]
        else:
            break  # Malformed template, just break
    
    # Clean up HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Replace wiki links [[dog]] -> dog
    # First handle [[word|display]] -> display
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    # Then handle [[word]] -> word
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    
    # Remove reference markers like [1], [2]
    text = re.sub(r'\[\d+\]', '', text)
    
    # Clean up taxonomy formatting
    text = re.sub(r'\{\{taxfmt\|([^|]+)\|[^}]+\}\}', r'\1', text)
    
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    
    # Remove trailing colons and periods that are artifacts
    text = text.strip().rstrip(':.')
    
    # If definition is too short after cleaning, it's probably junk
    if len(text) < 10:
        return ""

    return text.strip()

def fetch_definitions(word: str, language: str = "English", max_defs_per_pos: int = 5) -> dict:
    """
    High-level dictionary lookup.
    
    Args:
        word: The word to look up
        language: Target language (e.g., "English", "French", "Spanish")
        max_defs_per_pos: Max definitions per part of speech
    """
    empty = {"word": word, "language": language, "pronunciation": None, "etymology": None, "entries": []}

    wikitext = fetch_wikitext(word)
    if not wikitext:
        print("DEBUG fetch_definitions: No wikitext returned")
        return empty

    pronunciation = extract_pronunciation(wikitext, language=language)
    print(f"DEBUG fetch_definitions: pronunciation = {pronunciation}")
    
    etymology = extract_etymology(wikitext, language=language)
    print(f"DEBUG fetch_definitions: etymology exists = {etymology is not None}")
    
    entries = extract_definitions(
        wikitext,
        language=language,  # Pass language through
        max_defs_per_pos=max_defs_per_pos,
    )
    print(f"DEBUG fetch_definitions: entries count = {len(entries)}")

    result = {
        "word": word,
        "language": language,
        "pronunciation": pronunciation,
        "etymology": etymology,
        "entries": entries,
    }
    
    return result

def format_for_telegram(word: str, language: str = "English", max_defs_per_pos: int = 5) -> str:
    """
    Format dictionary output for Telegram Markdown.
    """
    result = fetch_definitions(word, language=language, max_defs_per_pos=max_defs_per_pos)

    if not result["entries"]:
        return f"❌ No {language} definition found for '*{word}*'."

    lines = [f"📖 *{word.upper()}* ({language})"]
    
    # Add pronunciation if available
    if result["pronunciation"]:
        lines.append(f"🔊 {result['pronunciation']}")
    
    lines.append("")  # Blank line

    for entry in result["entries"]:
        lines.append(f"*{entry['pos']}*")

        for i, definition in enumerate(entry["definitions"], 1):
            safe = _escape_telegram_markdown(definition)
            lines.append(f"  {i}. {safe}")

        lines.append("")

    examples = fetch_corpus_examples(word, max_examples=3)
    if examples:
        lines.append("📝 *Examples*")
        for example in examples:
            safe_example = _escape_telegram_markdown(example)
            lines.append(f"• {safe_example}")
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
    safe_etymology = _escape_telegram_markdown(etymology)
    
    return f"📜 *Etymology of {word.upper()}*\n\n{safe_etymology}"


def _escape_telegram_markdown(text: str) -> str:
    return (
        text.replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("`", "\\`")
    )


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
