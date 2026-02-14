# src/dictionary/word_forms_extractor.py
"""
Extract word inflections and conjugations using external libraries.
This module handles:
- Verb conjugations (using mlconjug3 for multiple languages)
- Noun plurals (using inflect for English)
- Adjective comparative/superlative forms (using inflect for English)
"""

from typing import Dict, List, Optional
import inflect

# We'll use lazy loading for mlconjug3 since it's heavy
_conjugators = {}  # Cache conjugators by language


def _get_conjugator(language_code: str):
    """
    Get or create a conjugator for the given language.
    Uses lazy loading to avoid importing heavy libraries at startup.
    
    Args:
        language_code: Two-letter language code (e.g., 'en', 'es', 'fr')
    
    Returns:
        Conjugator instance or None if language not supported
    """
    if language_code in _conjugators:
        return _conjugators[language_code]
    
    try:
        import mlconjug3
        
        # mlconjug3 supports: en, es, fr, it, pt, ro
        supported_languages = ['en', 'es', 'fr', 'it', 'pt', 'ro']
        
        if language_code not in supported_languages:
            print(f"DEBUG: Language '{language_code}' not supported by mlconjug3")
            return None
        
        print(f"DEBUG: Loading conjugator for language '{language_code}'...")
        conjugator = mlconjug3.Conjugator(language=language_code)
        _conjugators[language_code] = conjugator
        print(f"DEBUG: Conjugator loaded successfully")
        return conjugator
        
    except ImportError:
        print("DEBUG: mlconjug3 not installed. Install with: pip install mlconjug3")
        return None
    except Exception as e:
        print(f"DEBUG: Error loading conjugator: {e}")
        return None


def get_verb_conjugations(verb: str, language_code: str = 'en') -> Optional[Dict[str, str]]:
    """
    Get verb conjugations using mlconjug3.
    
    Args:
        verb: The verb to conjugate (infinitive form)
        language_code: Two-letter language code (e.g., 'en', 'es', 'fr')
    
    Returns:
        Dict with key conjugation forms, or None if not found
        Example for English: {
            'infinitive': 'go',
            'present_3sg': 'goes',
            'present_participle': 'going',
            'past': 'went',
            'past_participle': 'gone'
        }
    """
    conjugator = _get_conjugator(language_code)
    if not conjugator:
        return None
    
    try:
        # Conjugate the verb
        conjugation = conjugator.conjugate(verb)
        
        # Extract the most useful forms depending on language
        if language_code == 'en':
            return _extract_english_verb_forms(conjugation, verb)
        elif language_code == 'es':
            return _extract_spanish_verb_forms(conjugation, verb)
        elif language_code == 'fr':
            return _extract_french_verb_forms(conjugation, verb)
        else:
            # Generic extraction for other languages
            return _extract_generic_verb_forms(conjugation, verb)
            
    except Exception as e:
        print(f"DEBUG: Error conjugating '{verb}': {e}")
        return None


def _extract_english_verb_forms(conjugation, verb: str) -> Dict[str, str]:
    """Extract key English verb forms from mlconjug3 conjugation object."""
    forms = {'infinitive': verb}
    
    try:
        # Present tense - 3rd person singular
        if hasattr(conjugation, 'iterate'):
            for mood, tense, person, conj_form in conjugation.iterate():
                if mood == 'indicative' and tense == 'present':
                    if person == '3s':  # 3rd person singular
                        forms['present_3sg'] = conj_form
                elif mood == 'indicative' and tense == 'present participle':
                    forms['present_participle'] = conj_form
                elif mood == 'indicative' and tense == 'past':
                    if person == '1s':  # All persons same in English past
                        forms['past'] = conj_form
                elif mood == 'indicative' and tense == 'past participle':
                    forms['past_participle'] = conj_form
    except:
        # Fallback: try to access conjugation as dict
        try:
            conj_dict = dict(conjugation)
            if 'indicative' in conj_dict:
                ind = conj_dict['indicative']
                if 'present' in ind and '3s' in ind['present']:
                    forms['present_3sg'] = ind['present']['3s']
                if 'present participle' in ind:
                    forms['present_participle'] = list(ind['present participle'].values())[0]
                if 'past' in ind and '1s' in ind['past']:
                    forms['past'] = ind['past']['1s']
                if 'past participle' in ind:
                    forms['past_participle'] = list(ind['past participle'].values())[0]
        except:
            pass
    
    return forms if len(forms) > 1 else None


def _extract_spanish_verb_forms(conjugation, verb: str) -> Dict[str, str]:
    """Extract key Spanish verb forms."""
    forms = {'infinitive': verb}
    
    try:
        for mood, tense, person, conj_form in conjugation.iterate():
            # Present indicative yo/tú/él forms
            if mood == 'indicativo' and tense == 'presente':
                if person == '1s':
                    forms['present_1sg'] = conj_form
                elif person == '2s':
                    forms['present_2sg'] = conj_form
                elif person == '3s':
                    forms['present_3sg'] = conj_form
            # Preterite (past)
            elif mood == 'indicativo' and tense == 'pretérito':
                if person == '1s':
                    forms['preterite_1sg'] = conj_form
            # Gerund
            elif 'gerundio' in tense.lower():
                forms['gerund'] = conj_form
            # Past participle
            elif 'participio' in tense.lower():
                forms['past_participle'] = conj_form
    except:
        pass
    
    return forms if len(forms) > 1 else None


def _extract_french_verb_forms(conjugation, verb: str) -> Dict[str, str]:
    """Extract key French verb forms."""
    forms = {'infinitive': verb}
    
    try:
        for mood, tense, person, conj_form in conjugation.iterate():
            # Present indicative
            if mood == 'indicatif' and tense == 'présent':
                if person == '1s':
                    forms['present_1sg'] = conj_form
                elif person == '2s':
                    forms['present_2sg'] = conj_form
                elif person == '3s':
                    forms['present_3sg'] = conj_form
            # Passé composé (need auxiliary + past participle)
            elif 'participe passé' in tense.lower():
                forms['past_participle'] = conj_form
            # Imparfait
            elif mood == 'indicatif' and 'imparfait' in tense.lower():
                if person == '1s':
                    forms['imperfect_1sg'] = conj_form
    except:
        pass
    
    return forms if len(forms) > 1 else None


def _extract_generic_verb_forms(conjugation, verb: str) -> Dict[str, str]:
    """Generic extraction for languages we don't have specific handling for."""
    forms = {'infinitive': verb}
    
    try:
        # Just grab first few forms from each tense
        count = 0
        for mood, tense, person, conj_form in conjugation.iterate():
            key = f"{tense}_{person}".replace(' ', '_').lower()
            forms[key] = conj_form
            count += 1
            if count >= 10:  # Limit to avoid overwhelming output
                break
    except:
        pass
    
    return forms if len(forms) > 1 else None


def get_noun_forms(noun: str, language_code: str = 'en') -> Optional[Dict[str, str]]:
    """
    Get noun inflections (primarily plural for English).
    
    Args:
        noun: The noun to inflect
        language_code: Two-letter language code (currently only 'en' supported)
    
    Returns:
        Dict with forms like {'plural': 'dogs'}, or None if not found
    """
    if language_code != 'en':
        # For non-English, we could add other libraries later
        return None
    
    try:
        p = inflect.engine()
        plural = p.plural(noun)
        
        if plural and plural != noun:
            return {'plural': plural}
        else:
            return None
            
    except Exception as e:
        print(f"DEBUG: Error getting plural for '{noun}': {e}")
        return None


def get_adjective_forms(adjective: str, language_code: str = 'en') -> Optional[Dict[str, str]]:
    """
    Get adjective forms (comparative and superlative for English).
    
    Args:
        adjective: The adjective to inflect
        language_code: Two-letter language code (currently only 'en' supported)
    
    Returns:
        Dict with forms like {'comparative': 'bigger', 'superlative': 'biggest'}
    """
    if language_code != 'en':
        return None
    
    try:
        p = inflect.engine()
        
        forms = {}
        
        # inflect library has comparative/superlative methods
        comparative = p.compare(adjective, 'er')
        superlative = p.compare(adjective, 'est')
        
        # If the library returns results, use them
        # Otherwise, apply basic rules
        if comparative:
            forms['comparative'] = comparative
        else:
            forms['comparative'] = _make_comparative(adjective)
        
        if superlative:
            forms['superlative'] = superlative
        else:
            forms['superlative'] = _make_superlative(adjective)
        
        return forms if forms else None
        
    except Exception as e:
        print(f"DEBUG: Error getting adjective forms for '{adjective}': {e}")
        return None


def _make_comparative(adjective: str) -> str:
    """
    Simple rule-based comparative formation.
    This is a backup in case inflect doesn't work.
    """
    # Long adjectives (3+ syllables) use 'more'
    if len(adjective) > 6:  # Rough heuristic for syllables
        return f'more {adjective}'
    
    # Ending in -y: happy -> happier
    if adjective.endswith('y') and len(adjective) > 1 and adjective[-2] not in 'aeiou':
        return adjective[:-1] + 'ier'
    
    # Ending in -e: large -> larger
    if adjective.endswith('e'):
        return adjective + 'r'
    
    # Short words with CVC pattern: big -> bigger
    if (len(adjective) <= 4 and 
        len(adjective) >= 3 and
        adjective[-1] not in 'aeiou' and 
        adjective[-2] in 'aeiou' and 
        adjective[-3] not in 'aeiou'):
        return adjective + adjective[-1] + 'er'
    
    # Default: add -er
    return adjective + 'er'


def _make_superlative(adjective: str) -> str:
    """Simple rule-based superlative formation."""
    # Long adjectives use 'most'
    if len(adjective) > 6:
        return f'most {adjective}'
    
    if adjective.endswith('y') and len(adjective) > 1 and adjective[-2] not in 'aeiou':
        return adjective[:-1] + 'iest'
    
    if adjective.endswith('e'):
        return adjective + 'st'
    
    if (len(adjective) <= 4 and 
        len(adjective) >= 3 and
        adjective[-1] not in 'aeiou' and 
        adjective[-2] in 'aeiou' and 
        adjective[-3] not in 'aeiou'):
        return adjective + adjective[-1] + 'est'
    
    return adjective + 'est'


def get_word_forms(word: str, pos: str, language_code: str = 'en') -> Optional[Dict[str, str]]:
    """
    Get word forms based on part of speech.
    This is the main entry point that delegates to the appropriate function.
    
    Args:
        word: The word to get forms for
        pos: Part of speech (e.g., "Verb", "Noun", "Adjective")
        language_code: Two-letter language code
    
    Returns:
        Dict of word forms or None
    """
    pos_lower = pos.lower()
    
    if 'verb' in pos_lower:
        return get_verb_conjugations(word, language_code)
    elif 'noun' in pos_lower or 'proper noun' in pos_lower:
        return get_noun_forms(word, language_code)
    elif 'adjective' in pos_lower:
        return get_adjective_forms(word, language_code)
    
    return None


def format_word_forms_for_telegram(forms: Dict[str, List[str]], pos: str) -> str:
    """
    Format word forms for display in Telegram.
    
    Args:
        forms: Dictionary of word forms
        pos: Part of speech
    
    Returns:
        Formatted string for Telegram
    """
    if not forms:
        return "No forms available."
    
    lines = [f"*{pos} Forms*\n"]
    
    # Define friendly labels for each form type
    labels = {
        'third_person_singular': '3rd person singular',
        'present_participle': 'Present participle',
        'simple_past': 'Simple past',
        'past_participle': 'Past participle',
        'plural': 'Plural',
        'comparative': 'Comparative',
        'superlative': 'Superlative'
    }
    
    for form_type, form_values in forms.items():
        label = labels.get(form_type, form_type.replace('_', ' ').title())
        values_str = ', '.join(form_values)
        
        # Escape markdown
        values_str = _escape_telegram_markdown(values_str)
        
        lines.append(f"• *{label}*: {values_str}")
    
    return '\n'.join(lines)


def _escape_telegram_markdown(text: str) -> str:
    """Escape special Telegram markdown characters."""
    return (
        text.replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("`", "\\`")
    )


def format_word_forms_for_telegram(forms: Dict[str, str], pos: str) -> str:
    """
    Format word forms for display in Telegram.
    
    Args:
        forms: Dictionary of word forms
        pos: Part of speech
    
    Returns:
        Formatted string for Telegram with proper markdown escaping
    """
    if not forms:
        return "No forms available."
    
    lines = [f"📝 *{pos} Forms*\n"]
    
    # Define friendly labels for each form type
    labels = {
        # English verb forms
        'infinitive': 'Infinitive',
        'present_3sg': '3rd person singular',
        'present_participle': 'Present participle (-ing)',
        'past': 'Past tense',
        'past_participle': 'Past participle',
        
        # Spanish verb forms
        'present_1sg': 'Present (yo)',
        'present_2sg': 'Present (tú)',
        'present_3sg': 'Present (él/ella)',
        'preterite_1sg': 'Preterite (yo)',
        'gerund': 'Gerund',
        
        # French verb forms
        'imperfect_1sg': 'Imperfect (je)',
        
        # Noun forms
        'plural': 'Plural',
        
        # Adjective forms
        'comparative': 'Comparative',
        'superlative': 'Superlative'
    }
    
    for form_type, form_value in forms.items():
        label = labels.get(form_type, form_type.replace('_', ' ').title())
        
        # Escape markdown characters in the form value
        safe_value = _escape_telegram_markdown(form_value)
        
        lines.append(f"  • *{label}*: {safe_value}")
    
    return '\n'.join(lines)


def _escape_telegram_markdown(text: str) -> str:
    """Escape special Telegram markdown characters."""
    return (
        text.replace("*", "\\*")
        .replace("_", "\\_")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("`", "\\`")
    )