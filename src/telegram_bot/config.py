"""Configuration constants for the Telegram bot."""

# Languages organized by family with dividers for the UI
LANGUAGES_BY_FAMILY = {
    "Romance": {
        "es": "🇪🇸 Español",
        "fr": "🇫🇷 Français",
        "it": "🇮🇹 Italiano",
        "pt": "🇵🇹 Português",
    },
    "Germanic": {
        "de": "🇩🇪 Deutsch",
        "en": "🇬🇧 English",
        "nl": "🇳🇱 Nederlands",
    },
    "Slavic": {
        "cs": "🇨🇿 Čeština",
        "pl": "🇵🇱 Polski",
        "ru": "🇷🇺 Русский",
    },
    "Uralic": {
        "hu": "🇭🇺 Magyar",
    },
    "Semitic and Turkic": {
        "ar": "🇸🇦 العربية (al-ʿArabiyyah)",
        "tr": "🇹🇷 Türkçe",
    },
    "Asian": {
        "hi": "🇮🇳 हिन्दी (Hindi)",
        "ja": "🇯🇵 日本語 (Nihongo)",
        "ko": "🇰🇷 한국어 (Hangugeo)",
        "zh-CN": "🇨🇳 简体中文 (Jiǎntǐ Zhōngwén)",
        "zh-TW": "🇨🇳 中文 (Fántǐ Zhōngwén)",
    },
}

# Flat mapping for quick lookups by language code
LANGUAGES = {
    "en": "🇬🇧 English",
    "es": "🇪🇸 Español",
    "fr": "🇫🇷 Français",
    "it": "🇮🇹 Italiano",
    "pt": "🇵🇹 Português",
    "de": "🇩🇪 Deutsch",
    "nl": "🇳🇱 Nederlands",
    "cs": "🇨🇿 Čeština",
    "pl": "🇵🇱 Polski",
    "ru": "🇷🇺 Русский",
    "hu": "🇭🇺 Magyar",
    "ar": "🇸🇦 العربية (al-ʿArabiyyah)",
    "tr": "🇹🇷 Türkçe",
    "hi": "🇮🇳 हिन्दी (Hindi)",
    "ja": "🇯🇵 日本語 (Nihongo)",
    "ko": "🇰🇷 한국어 (Hangugeo)",
    "zh-CN": "🇨🇳 简体中文 (Jiǎntǐ Zhōngwén)",
    "zh-TW": "🇨🇳 中文 (Fántǐ Zhōngwén)",
}

# Map language codes to Wiktionary language section names
# Wiktionary uses full language names for section headers
WIKTIONARY_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "tr": "Turkish",
    "ru": "Russian",
    "nl": "Dutch",
    "cs": "Czech",
    "ar": "Arabic",
    "zh-CN": "Chinese",  # Wiktionary uses "Chinese" for both
    "zh-TW": "Chinese",
    "ja": "Japanese",
    "hu": "Hungarian",
    "ko": "Korean",
    "hi": "Hindi"
}