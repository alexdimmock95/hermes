# src/dictionary/wiktionary_client.py
# Wiktionary client using raw wikitext + mwparserfromhell

import requests
import mwparserfromhell
import re
from gtts import gTTS
import io
from src.dictionary.corpus_examples import fetch_corpus_examples
from src.telegram_bot.config import WIKTIONARY_LANGUAGES
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

WIKTIONARY_API_EN = "https://en.wiktionary.org/w/api.php"

# Map language codes to Wiktionary language domains
WIKTIONARY_DOMAINS = {
    "en": "https://en.wiktionary.org/w/api.php",
    "es": "https://es.wiktionary.org/w/api.php",
    "fr": "https://fr.wiktionary.org/w/api.php",
    "de": "https://de.wiktionary.org/w/api.php",
    "it": "https://it.wiktionary.org/w/api.php",
    "pt": "https://pt.wiktionary.org/w/api.php",
    "ru": "https://ru.wiktionary.org/w/api.php",
    "pl": "https://pl.wiktionary.org/w/api.php",
    "ja": "https://ja.wiktionary.org/w/api.php",
    "zh-CN": "https://zh.wiktionary.org/w/api.php",
    "zh-TW": "https://zh.wiktionary.org/w/api.php",
}

# POS section headings per Wiktionary language (en = English Wiktionary headings; fr/es/etc = local headings)
POS_HEADINGS_BY_LANG = {
    "en": {"Noun", "Verb", "Adjective", "Adverb", "Pronoun", "Preposition", "Conjunction", "Interjection", "Determiner", "Article", "Numeral", "Proper noun"},
    "fr": {"Nom", "Verbe", "Adjectif", "Adverbe", "Pronom", "Préposition", "Conjonction", "Interjection", "Déterminant", "Article", "Numéral", "Nom propre", "Noun", "Verb", "Adjective"},
    "es": {"Sustantivo", "Verbo", "Adjetivo", "Adverbio", "Pronombre", "Preposición", "Conjunción", "Interjección", "Determinante", "Artículo", "Numeral", "Nombre propio", "Noun", "Verb", "Adjective"},
    "de": {"Substantiv", "Verb", "Adjektiv", "Adverb", "Pronomen", "Präposition", "Konjunktion", "Interjektion", "Determiner", "Artikel", "Numerale", "Eigenname", "Noun", "Adjective"},
    "it": {"Sostantivo", "Verbo", "Aggettivo", "Avverbio", "Pronome", "Preposizione", "Congiunzione", "Interiezione", "Articolo", "Numeral", "Nome proprio", "Noun", "Verb", "Adjective"},
    "pt": {"Substantivo", "Verbo", "Adjetivo", "Advérbio", "Pronome", "Preposição", "Conjunção", "Interjeição", "Artigo", "Numeral", "Nome próprio", "Noun", "Verb", "Adjective"},
    "ru": {"Существительное", "Глагол", "Прилагательное", "Наречие", "Местоимение", "Предлог", "Союз", "Междометие", "Числительное", "Noun", "Verb", "Adjective"},
    "pl": {"Rzeczownik", "Czasownik", "Przymiotnik", "Przysłówek", "Zaimek", "Przyimek", "Spójnik", "Wykrzyknik", "Noun", "Verb", "Adjective"},
    "ja": {"名詞", "動詞", "形容詞", "副詞", "代名詞", "Noun", "Verb", "Adjective"},
    "zh-CN": {"名词", "动词", "形容词", "副词", "代词", "Noun", "Verb", "Adjective"},
    "zh-TW": {"名詞", "動詞", "形容詞", "副詞", "代詞", "Noun", "Verb", "Adjective"},
    "ko": {"명사", "동사", "형용사", "부사", "대명사", "Noun", "Verb", "Adjective"},
    "nl": {"Zelfstandig naamwoord", "Werkwoord", "Bijvoeglijk naamwoord", "Bijwoord", "Voornaamwoord", "Noun", "Verb", "Adjective"},
    "tr": {"Ad", "Eylem", "Sıfat", "Belirteç", "Zamir", "Noun", "Verb", "Adjective"},
    "ar": {"اسم", "فعل", "صفة", "حال", "ضمير", "Noun", "Verb", "Adjective"},
    "hi": {"संज्ञा", "क्रिया", "विशेषण", "Noun", "Verb", "Adjective"},
    "hu": {"Főnév", "Igék", "Melléknév", "Határozószó", "Noun", "Verb", "Adjective"},
    "cs": {"Podstatné jméno", "Sloveso", "Přídavné jméno", "Příslovce", "Noun", "Verb", "Adjective"},
}

HEADERS = {
    "User-Agent": "DictionaryBot/1.0 (Educational Project; Contact: user@example.com)"
}


from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def create_word_forms_keyboard(word: str, entries: list, language_code: str = "en") -> InlineKeyboardMarkup:
    """
    Create inline keyboard with buttons for word forms.
    
    This function looks at the parts of speech in the dictionary results
    and creates appropriate buttons (conjugate for verbs, plural for nouns, etc.)
    
    Args:
        word: The word being looked up
        entries: List of dict entries from fetch_definitions (contains POS info)
        language_code: Language code for conjugation
    
    Returns:
        InlineKeyboardMarkup with buttons, or None if no forms available
    """
    buttons = []
    
    # Track which POS we've seen to avoid duplicate buttons
    seen_pos_types = set()
    
    for entry in entries:
        pos = entry.get('pos', '').lower()
        
        # Check for verbs
        if 'verb' in pos and 'verb' not in seen_pos_types:
            # Create a callback data string that includes: action|word|pos|language
            callback_data = f"forms|{word}|Verb|{language_code}"
            buttons.append([InlineKeyboardButton("🔄 Conjugations", callback_data=callback_data)])
            seen_pos_types.add('verb')
        
        # Check for nouns
        elif 'noun' in pos and 'noun' not in seen_pos_types:
            callback_data = f"forms|{word}|Noun|{language_code}"
            buttons.append([InlineKeyboardButton("📦 Plural form", callback_data=callback_data)])
            seen_pos_types.add('noun')
        
        # Check for adjectives
        elif 'adjective' in pos and 'adjective' not in seen_pos_types:
            callback_data = f"forms|{word}|Adjective|{language_code}"
            buttons.append([InlineKeyboardButton("📊 Comparative forms", callback_data=callback_data)])
            seen_pos_types.add('adjective')
    
    # Return None if no buttons were created
    if not buttons:
        return None
    
    return InlineKeyboardMarkup(buttons)


def fetch_wikitext(word: str, language_code: str = "en", try_english_first: bool = True) -> tuple[str | None, str]:
    """
    Fetch raw Wiktionary wikitext for a given word using MediaWiki API.

    Prefer en.wiktionary.org first (best coverage; has e.g. "French" section with English POS headings).
    Then try language-specific Wiktionary if needed.

    Args:
        word: The word to look up
        language_code: Language code (e.g., "en", "fr", "es")
        try_english_first: If True, try en.wiktionary.org first for reliable parsing.

    Returns:
        Tuple of (wikitext or None, source_lang_code e.g. "en" or "fr" for POS heading lookup).
    """
    # Prefer English Wiktionary first: best coverage and consistent "== Language ==" and "=== Noun ===" structure
    if try_english_first:
        wikitext = _fetch_from_api(word, WIKTIONARY_API_EN, "en")
        if wikitext:
            print(f"DEBUG: Fetched from en.wiktionary.org for '{word}'")
            return (wikitext, "en")
        print(f"DEBUG: Word not found on en.wiktionary.org, trying language-specific")

    # Then try language-specific Wiktionary
    if language_code in WIKTIONARY_DOMAINS and language_code != "en":
        api_url = WIKTIONARY_DOMAINS[language_code]
        wikitext = _fetch_from_api(word, api_url, language_code)
        if wikitext:
            print(f"DEBUG: Fetched from {language_code}.wiktionary.org")
            return (wikitext, language_code)
        print(f"DEBUG: Word not found on {language_code}.wiktionary.org")
    elif not try_english_first:
        wikitext = _fetch_from_api(word, WIKTIONARY_API_EN, "en")
        if wikitext:
            return (wikitext, "en")

    return (None, language_code)


def _fetch_from_api(word: str, api_url: str, lang_code: str) -> str | None:
    """
    Helper to fetch from a specific Wiktionary API.
    """
    params = {
        "action": "parse",
        "page": word,
        "prop": "wikitext",
        "format": "json",
    }

    try:
        resp = requests.get(api_url, params=params, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return None

        data = resp.json()

        if "error" in data:
            print(f"DEBUG: Wiktionary API ({lang_code}) returned error for '{word}':", data["error"])
            return None

        wikitext = data["parse"]["wikitext"]["*"]
        print(f"DEBUG: Successfully fetched wikitext for '{word}' from {lang_code} ({len(wikitext)} chars)")

        return wikitext
    except Exception as e:
        print(f"DEBUG: Error fetching from {lang_code} Wiktionary: {e}")
        return None


def extract_pronunciation(wikitext: str, language: str = "English", language_code: str = "en") -> str | None:
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
    
    # Look for Pronunciation section (English and French/local variants)
    pron_markers = ["===Pronunciation===", "===Prononciation===", "===Pronunciación===", "===Aussprache==="]
    pron_section = None
    for marker in pron_markers:
        if marker in section_text:
            parts = section_text.split(marker, 1)
            if len(parts) >= 2:
                pron_section = parts[1].split("===")[0]
                break
    if not pron_section:
        return None
    
    # Find first IPA entry - {{IPA|en|/.../}} or {{IPA|fr|...}} etc.
    ipa_match = re.search(r'\{\{IPA\|[^|]+\|([^}|]+)', pron_section)
    if ipa_match:
        ipa = ipa_match.group(1).strip()
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
    language_code: str = "en",
    max_defs_per_pos: int = 5,
):
    """
    Parse raw wikitext and extract definitions for a given language.
    Looks for the language section bounded by ==Language==

    Args:
        wikitext: Raw wikitext from Wiktionary
        language: Language to extract (e.g., "English", "Spanish", "French")
        language_code: Language code for POS headings (en, fr, es, ...)
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
    
    # Find the end of this language section (next level-2 heading: == Title ==)
    next_language_match = re.search(r'\n==\s*[^=\n]+==', after_language)
    if next_language_match:
        language_section = after_language[:next_language_match.start()]
    else:
        language_section = after_language

    print(f"DEBUG: Found '{language}' section ({len(language_section)} chars)")

    entries = []

    # Allowed POS headings (level 3) - use language-specific set so fr.wiktionary "Nom"/"Verbe" etc. match
    allowed_pos = POS_HEADINGS_BY_LANG.get(language_code, POS_HEADINGS_BY_LANG["en"])
    # Escape any regex-special chars in POS names (e.g. parentheses in "Nom propre")
    allowed_escaped = [re.escape(pos) for pos in allowed_pos]
    pos_pattern = r'===(' + '|'.join(allowed_escaped) + r')==='
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
            
            if clean and len(clean) > 0 and len(definitions) < max_defs_per_pos:
                definitions.append(clean)

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
    
    # Extract text from labels before removing them
    text = re.sub(r'\{\{lb\|[^}]+\}\}\s*', '', text)

    # Extract text from inflection of before removing them
    inflection_match = re.search(r'\{\{inflection of\|[^|]+\|([^|}\s]+)', text)
    if inflection_match:
        base_word = inflection_match.group(1)
        text = f"inflection of {base_word}"
        # If it's just an inflection, we can return early (no need to clean further)
        return text

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
    if len(text) < 3:
        return ""

    return text.strip()

def fetch_definitions(word: str, language: str = "English", language_code: str = "en", max_defs_per_pos: int = 5) -> dict:
    """
    High-level dictionary lookup.
    
    Args:
        word: The word to look up
        language: Target language name (e.g., "English", "French", "Spanish") - for backwards compatibility
        language_code: Language code for Wiktionary lookup (e.g., "en", "fr", "es")
        max_defs_per_pos: Max definitions per part of speech
    """
    empty = {"word": word, "language": language, "pronunciation": None, "etymology": None, "entries": []}

    wikitext, source_wiki = fetch_wikitext(word, language_code=language_code, try_english_first=True)
    if not wikitext:
        print("DEBUG fetch_definitions: No wikitext returned")
        return empty

    # POS headings: en.wiktionary.org uses English (Noun, Verb); fr.wiktionary uses French (Nom, Verbe)
    pos_language_code = source_wiki

    pronunciation = extract_pronunciation(wikitext, language=language, language_code=language_code)
    print(f"DEBUG fetch_definitions: pronunciation = {pronunciation}")

    etymology = extract_etymology(wikitext, language=language)
    print(f"DEBUG fetch_definitions: etymology exists = {etymology is not None}")

    entries = extract_definitions(
        wikitext,
        language=language,
        language_code=pos_language_code,
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


def format_for_telegram_with_buttons(word: str, language: str = "English", language_code: str = "en", max_defs_per_pos: int = 5):
    """
    Format dictionary output for Telegram Markdown AND return keyboard.
    
    This is a modified version that returns both the formatted text AND the keyboard.
    
    Args:
        word: The word to look up
        language: Target language name
        language_code: Language code for Wiktionary and conjugation
        max_defs_per_pos: Max definitions per part of speech
    
    Returns:
        Tuple of (formatted_text: str, keyboard: InlineKeyboardMarkup or None)
    """
    result = fetch_definitions(word, language=language, language_code=language_code, max_defs_per_pos=max_defs_per_pos)

    if not result["entries"]:
        return (f"❌ No {language} definition found for '*{word}*'.", None)

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

    formatted_text = "\n".join(lines)
    
    # Create the keyboard with word form buttons
    keyboard = create_word_forms_keyboard(word, result["entries"], language_code)
    
    return (formatted_text, keyboard)


def format_for_telegram(word: str, language: str = "English", language_code: str = "en", max_defs_per_pos: int = 5) -> str:
    """
    Format dictionary output for Telegram Markdown (text only, no keyboard).
    Used by callbacks when returning to definition view.
    """
    text, _ = format_for_telegram_with_buttons(
        word, language=language, language_code=language_code, max_defs_per_pos=max_defs_per_pos
    )
    return text


def fetch_bilingual_definitions(word: str, language: str = "English", language_code: str = "en", max_defs_per_pos: int = 3) -> dict:
    """
    Fetch definitions in BOTH English and the target language.
    
    Args:
        word: The word to look up
        language: Target language name in English (e.g., "Italian", "French")
        language_code: Language code (e.g., "it", "fr")
        max_defs_per_pos: Max definitions per part of speech
    
    Returns:
        {
            "english": {...},  # English Wiktionary definitions
            "native": {...}    # Native language definitions (or None)
        }
    """
    # Get English definitions (current behavior)
    english_result = fetch_definitions(word, language=language, language_code=language_code, max_defs_per_pos=max_defs_per_pos)
    
    # Try to get native language definitions
    native_result = None
    if language_code != "en" and language_code in WIKTIONARY_DOMAINS:
        # Fetch from native Wiktionary (e.g., it.wiktionary.org for Italian)
        wikitext, source = fetch_wikitext(word, language_code=language_code, try_english_first=False)
        if wikitext:
            # Native Wiktionary uses native language names for sections
            # e.g., on it.wiktionary.org, Italian words are under "Italiano" not "Italian"
            native_lang_names = {
                "it": "Italiano",
                "fr": "Français", 
                "es": "Español",
                "de": "Deutsch",
                "pt": "Português",
                "ru": "Русский",
                "pl": "Polski",
                "nl": "Nederlands",
                "tr": "Türkçe",
                "ja": "日本語",
                "zh-CN": "中文",
                "zh-TW": "中文",
                "ko": "한국어",
                "ar": "العربية",
                "hi": "हिन्दी",
            }
            native_lang = native_lang_names.get(language_code, language)
            
            entries = extract_definitions(
                wikitext,
                language=native_lang,
                language_code=language_code,
                max_defs_per_pos=max_defs_per_pos
            )
            
            if entries:
                # Also try to get pronunciation from native Wiktionary
                pronunciation = extract_pronunciation(wikitext, language=native_lang, language_code=language_code)
                
                native_result = {
                    "word": word,
                    "language": native_lang,
                    "pronunciation": pronunciation,
                    "entries": entries
                }
    
    return {
        "english": english_result,
        "native": native_result
    }


def format_bilingual_for_telegram(word: str, language: str = "English", language_code: str = "en", max_defs_per_pos: int = 3):
    """
    Format bilingual dictionary output (English + native language definitions).
    
    Returns:
        Tuple of (formatted_text: str, keyboard: InlineKeyboardMarkup or None)
    """
    bilingual = fetch_bilingual_definitions(word, language=language, language_code=language_code, max_defs_per_pos=max_defs_per_pos)
    
    english_result = bilingual["english"]
    native_result = bilingual["native"]
    
    # If neither has entries, return error
    if not english_result["entries"] and (not native_result or not native_result.get("entries")):
        return (f"❌ No definition found for '*{word}*'.", None)
    
    lines = [f"📖 *{word.upper()}*"]
    
    # Add pronunciation if available (prefer native, fall back to English)
    pronunciation = None
    if native_result and native_result.get("pronunciation"):
        pronunciation = native_result["pronunciation"]
    elif english_result.get("pronunciation"):
        pronunciation = english_result["pronunciation"]
    
    if pronunciation:
        lines.append(f"🔊 {pronunciation}")
    
    lines.append("")
    
    # --- English definitions ---
    if english_result["entries"]:
        lines.append(f"🇬🇧 *English Definition*")
        for entry in english_result["entries"]:
            lines.append(f"*{entry['pos']}*")
            for i, definition in enumerate(entry["definitions"], 1):
                safe = _escape_telegram_markdown(definition)
                lines.append(f"  {i}. {safe}")
            lines.append("")
    
    # --- Native language definitions ---
    if native_result and native_result.get("entries"):
        # Use flag emoji based on language
        flag_emoji = {
            "it": "🇮🇹", "fr": "🇫🇷", "es": "🇪🇸", "de": "🇩🇪",
            "pt": "🇵🇹", "ru": "🇷🇺", "pl": "🇵🇱", "ja": "🇯🇵",
            "zh-CN": "🇨🇳", "zh-TW": "🇹🇼", "ko": "🇰🇷",
        }.get(language_code, "🌍")
        
        lines.append(f"{flag_emoji} *{native_result['language']} Definition*")
        for entry in native_result["entries"]:
            lines.append(f"*{entry['pos']}*")
            for i, definition in enumerate(entry["definitions"], 1):
                safe = _escape_telegram_markdown(definition)
                lines.append(f"  {i}. {safe}")
            lines.append("")
    
    # Add examples (from English corpus)
    examples = fetch_corpus_examples(word, max_examples=2)
    if examples:
        lines.append("📝 *Examples*")
        for example in examples:
            safe_example = _escape_telegram_markdown(example)
            lines.append(f"• {safe_example}")
        lines.append("")
    
    formatted_text = "\n".join(lines)
    
    # Create keyboard (use English entries for word forms since those are more reliable)
    keyboard = create_word_forms_keyboard(word, english_result["entries"], language_code)
    
    return (formatted_text, keyboard)


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
        print(format_for_telegram_with_buttons(w))
        print()
