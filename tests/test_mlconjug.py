#!/usr/bin/env python3
"""Quick test to see if conjugations are working"""

import sys
sys.path.insert(0, '/Users/Alex/Documents/Coding/personal_project/hermes')

from src.dictionary.word_forms_extractor import get_verb_conjugations, format_word_forms_for_telegram

# Test English
print("=" * 60)
print("TESTING ENGLISH: run")
print("=" * 60)
forms = get_verb_conjugations("run", "en")
print(f"Forms returned: {forms}")
if forms:
    formatted = format_word_forms_for_telegram(forms, "Verb")
    print("\nFormatted:")
    print(formatted)
else:
    print("No forms returned!")

print("\n\n")

# Test French
print("=" * 60)
print("TESTING FRENCH: manger")
print("=" * 60)
forms = get_verb_conjugations("manger", "fr")
print(f"Forms returned: {forms}")
if forms:
    formatted = format_word_forms_for_telegram(forms, "Verb")
    print("\nFormatted:")
    print(formatted)
else:
    print("No forms returned!")

print("\n\n")

# Test Spanish
print("=" * 60)
print("TESTING SPANISH: hablar")
print("=" * 60)
forms = get_verb_conjugations("hablar", "es")
print(f"Forms returned: {forms}")
if forms:
    formatted = format_word_forms_for_telegram(forms, "Verb")
    print("\nFormatted:")
    print(formatted)
else:
    print("No forms returned!")