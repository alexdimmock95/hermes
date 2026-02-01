from typing import Optional

NON_LATIN_LANGS = {"ru", "ja", "zh-CN", "zh-TW", "ko", "ar", "hi"}

def latinise(text: str, lang: str) -> str | None:
    """
    Returns latinised version of text if supported,
    otherwise None.
    """

    if lang == "ru":
        return _latinise_ru(text)

    if lang == "ja":
        return _latinise_ja(text)

    if lang.startswith("zh"):
        return _latinise_zh(text)

    if lang == "ko":
        return _latinise_ko(text)
    
    if lang == "ar":
        return _latinise_ar(text)

    if lang == "hi":
        return _latinise_hi(text)

    return None

def _latinise_ru(text: str) -> Optional[str]:
    try:
        from unidecode import unidecode
    except ImportError:
        return None
    
    return unidecode(text)

def _latinise_ja(text: str) -> Optional[str]:
    try:
        from pykakasi import kakasi
    except ImportError:
        return None

    kks = kakasi()
    kks.setMode("H", "a")  # Hiragana → ascii
    kks.setMode("K", "a")  # Katakana → ascii
    kks.setMode("J", "a")  # Kanji → ascii
    kks.setMode("r", "Hepburn")  # Hepburn romanisation
    kks.setMode("s", True)  # Spaces
    kks.setMode("C", True)  # Capitalise

    conv = kks.getConverter()
    return conv.do(text)

def _latinise_zh(text: str) -> Optional[str]:
    try:
        from pypinyin import pinyin, Style
    except ImportError:
        return None

    result = pinyin(text, style=Style.TONE3, strict=False)
    # Flatten list of lists
    flattened = [syllable[0] for syllable in result]
    return " ".join(flattened)

def _latinise_ko(text: str) -> Optional[str]:
    try:
        from hangul_romanize import Transliter
        from hangul_romanize.rule import academic
    except ImportError:
        return None

    trans = Transliter(academic)
    return trans.translit(text)

def _latinise_ar(text: str) -> Optional[str]:
    try:
        from unidecode import unidecode
    except ImportError:
        return None

    return unidecode(text)

def _latinise_hi(text: str) -> Optional[str]:
    try:
        from indic_transliteration import sanscript
        from indic_transliteration.sanscript import transliterate
    except ImportError:
        return None

    return transliterate(text, sanscript.DEVANAGARI, sanscript.ITRANS)