import re
from spellchecker import SpellChecker

def run_spellcheck():
    spell = SpellChecker()
    spell.word_frequency.load_words(['unconference'])
    
    # We only allow autocorrecting into these very common conference words
    # This prevents brands (Figma -> sigma) from being destroyed!
    safe_targets = {
        "open", "source", "summit", "conference", "developer", "engineering",
        "security", "world", "congress", "virtual", "online", "europe", "america",
        "asia", "africa", "tech", "technology", "data", "cloud", "native", 
        "artificial", "intelligence", "machine", "learning", "global", "annual",
        "event", "forum", "symposium", "expo", "festival", "workshop", "bootcamp"
    }
    
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
        
    lines = content.split('\n')
    new_lines = []
    corrections_made = 0
    
    def correct_match(match):
        nonlocal corrections_made
        word = match.group(0)
        
        # Only check alphabetic words
        if not word.isalpha():
            return word
            
        # Ignore fully uppercase words (Acronyms like AWS)
        if word.isupper():
            return word
            
        # Ignore mixed case / camelCase / PascalCase words (like CloudX, KubeCon)
        if not word.islower() and not word.istitle() and not word.isupper():
            return word
            
        lower_word = word.lower()
        
        # If it's already spelled right, skip
        if not spell.unknown([lower_word]):
            return word
            
        # Try to correct
        correction = spell.correction(lower_word)
        if correction and correction != lower_word:
            if correction in safe_targets:
                corrections_made += 1
                print(f"Corrected typo: '{word}' -> '{correction}'")
                
                # Match original casing
                if word.istitle():
                    return correction.title()
                return correction
                
        return word

    for line in lines:
        if line.strip().startswith('|') and 'Event Name' not in line and not line.strip().startswith('|-'):
            parts = line.split('|')
            if len(parts) >= 5:
                # Correct Name and Location
                parts[1] = re.sub(r'[a-zA-Z]+', correct_match, parts[1])
                parts[3] = re.sub(r'[a-zA-Z]+', correct_match, parts[3])
                line = '|'.join(parts)
        
        new_lines.append(line)
        
    if corrections_made > 0:
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        print(f"Successfully fixed {corrections_made} typos!")
    else:
        print("No typos found.")

if __name__ == '__main__':
    run_spellcheck()
