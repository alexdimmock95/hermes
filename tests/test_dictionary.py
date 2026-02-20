'''import requests
from bs4 import BeautifulSoup

# Test with "dog"
word = "dog"
url = f"https://en.wiktionary.org/api/rest_v1/page/mobile-sections/{word}"

# ═══════════════════════════════════════════════════════════════════
# ✨ ADD THIS - User-Agent header to avoid 403
# ═══════════════════════════════════════════════════════════════════
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# ═══════════════════════════════════════════════════════════════════

try:
    resp = requests.get(url, headers=headers, timeout=5)  # ← Added headers here
    print(f"✓ HTTP Status: {resp.status_code}")
    
    data = resp.json()
    sections = data.get("remaining", {}).get("sections", [])
    
    print(f"✓ Total sections: {len(sections)}\n")
    
    # Show all section headers
    print("=" * 60)
    print("ALL SECTION HEADERS:")
    print("=" * 60)
    for i, sec in enumerate(sections):
        line = sec.get("line", "").strip()
        print(f"{i:2d}. {line}")
    
    # Now trace through the logic
    print("\n" + "=" * 60)
    print("TRACING LOGIC:")
    print("=" * 60)
    
    in_english_section = False
    other_languages = ["french", "spanish", "german", "italian", "latin"]
    pos_candidates = ["noun", "verb", "adjective", "adverb", "pronoun"]
    
    for i, sec in enumerate(sections):
        section_line = sec.get("line", "").strip()
        section_text = sec.get("text", "")
        
        # Check for English
        if section_line.lower() == "english":
            in_english_section = True
            print(f"\n{i:2d}. '{section_line}' → Set in_english_section = True")
            continue
        
        # Check if left English
        if in_english_section and section_line.lower() in other_languages:
            print(f"\n{i:2d}. '{section_line}' → Left English section, BREAK")
            break
        
        # Check if in English
        if not in_english_section:
            print(f"{i:2d}. '{section_line}' → NOT in English, skip")
            continue
        
        # Check if POS
        is_pos = any(pos in section_line.lower() for pos in pos_candidates)
        has_text = len(section_text) > 10
        
        if is_pos:
            print(f"\n{i:2d}. '{section_line}' → POS section! (has_text={has_text})")
            
            if has_text:
                # Try to parse
                soup = BeautifulSoup(section_text, "html.parser")
                lists = soup.find_all(["ol", "ul"], recursive=False)
                print(f"     Found {len(lists)} lists")
                
                for j, list_tag in enumerate(lists[:1]):  # Just first list
                    items = list_tag.find_all("li", recursive=False)
                    print(f"     List {j} has {len(items)} items")
                    
                    for k, li in enumerate(items[:3]):  # First 3 items
                        # Remove nested
                        for nested in li.find_all(["ul", "ol"]):
                            nested.decompose()
                        
                        text = li.get_text(" ", strip=True)
                        if "—" in text:
                            text = text.split("—")[0].strip()
                        
                        print(f"       Item {k}: {text[:80]}...")
        else:
            print(f"{i:2d}. '{section_line}' → Not a POS, skip")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()'''

import requests

word = "dog"
url = f"https://en.wiktionary.org/api/rest_v1/page/mobile-sections/{word}"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print("Testing Wiktionary API...")
print(f"URL: {url}")
print(f"Headers: {headers}")
print()

try:
    resp = requests.get(url, headers=headers, timeout=10)
    
    print(f"Status Code: {resp.status_code}")
    print(f"Response Headers: {dict(resp.headers)}")
    print(f"\nResponse Text (first 500 chars):")
    print(resp.text[:500])
    print()
    
    if resp.status_code == 200:
        try:
            data = resp.json()
            print("✓ Successfully parsed JSON")
            sections = data.get("remaining", {}).get("sections", [])
            print(f"✓ Found {len(sections)} sections")
        except Exception as e:
            print(f"✗ Failed to parse JSON: {e}")
    else:
        print(f"✗ Got status code {resp.status_code} instead of 200")
        
except requests.exceptions.RequestException as e:
    print(f"✗ Request failed: {e}")
    import traceback
    traceback.print_exc()