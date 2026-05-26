import spacy
import json
import re
from docx import Document
from datetime import date

SOURCE_FILE = "Transcript AWS Migration opportunity.docx"

nlp = spacy.load("en_core_web_lg")

# Read text from either a .txt or .docx file
if SOURCE_FILE.endswith(".docx"):
    doc_file = Document(SOURCE_FILE)
    text = "\n".join([para.text for para in doc_file.paragraphs])
else:
    with open(SOURCE_FILE, "r") as f:
        text = f.read()

# Strip timestamps (e.g. [00:01:23], (10:23), 10:23 AM)
text = re.sub(r'\[?\(?\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM)?\)?\]?', '', text)


doc = nlp(text)

companies = []
people = []
amounts = []
skipped_entities = []

Not_Companies = ["CMMC Level 2", "MSP", "RMM", "SSO", "MDR", "LLM", "COOCFO", "MFA", "EDR", "DNS", "SLAS", "MSB", "ITS", "QBRS", "IDP" "SOC","CUI", "CFO", "CEO", "IT", "NDA", "PTO", "HR", "R&D", "CTO", "CIO", "COO", "VP", "SVP", "EVP", "MD", "GM", "Director", "Manager"]
Not_People = ["Transcript", "Mac", "Disneys", "Authenticator"]
Move_to_companies = ["Fortinet", "Ninjio", "Dropsuite", "Claude"]

for ent in doc.ents:
    if ent.label_ == "ORG" and ent.text not in Not_Companies and len(ent.text) > 2:
        companies.append(ent.text) 
    elif (ent.label_ == "PERSON"
            and not ent.text.isupper()                        # block all-caps like "SE"
            and not ent.text.split()[0].isupper()             # block "TD Senex" style
            and not re.search(r'-', ent.text)                 # block "Hyper-V." style
            and len(ent.text.replace(".", "").replace(" ", "")) > 2):
        # Normalize whitespace and handle comma-separated names e.g. "Thanarajoo, Marie"
        clean = re.sub(r'\s+', ' ', ent.text).strip()
        clean = re.sub(r'^[a-zA-Z]\.\s+|^\d+\.\s+', '', clean)
        for name in clean.split(","):
            name = name.strip()
        # Strip leading list markers e.g. "a. Greg Gallagher" → "Greg Gallagher"
            if not name:
                continue
            if name in Move_to_companies:
                companies.append(name)
            elif name not in Not_People:
                people.append(name)
    elif ent.label_ == "MONEY":
        amounts.append(ent.text)
    else:
        skipped_entities.append({"text": ent.text, "label": ent.label_})

# Deduplication
companies = list(set(companies))
amounts = list(set(amounts))

def is_covered_by(name, name_list):
    name_words = name.lower().split()
    for other in name_list:
        other_words = other.lower().split()
        n = min(len(name_words), len(other_words))
        if name_words[:n] == other_words[:n]:
            return True
    return False

def sort_key(name):
    words = name.split()
    if len(words) == 2: return 0   # 2-word names first — most likely clean full names
    elif len(words) == 1: return 1
    else: return len(words)        # longer = more likely noise, processed last

sorted_people = sorted(set(people), key=sort_key)
deduped_people = []
for name in sorted_people:
    if not is_covered_by(name, deduped_people):
        deduped_people.append(name)
people = deduped_people

# Remove from companies anything already covered by a name in people
companies = [c for c in companies if not is_covered_by(c, people)]
people = [p for p in people if p not in companies]

# Regex cross-check for financial figures spaCy may have missed
# Covers: $X, $X million/k, X to Y k/million, X million/thousand/k etc.
MONEY_PATTERN = (
    r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand|k))?\b'
    r'|\d+[\d,]*(?:\.\d+)?\s+to\s+\d+[\d,]*(?:\.\d+)?\s*(?:k|million|billion|thousand|dollars?|USD)\b'
    r'|\d+[\d,]*(?:\.\d+)?\s*(?:million|billion|thousand|k|dollars?|USD)\b'
)
regex_amounts = re.findall(MONEY_PATTERN, text, re.IGNORECASE)
def normalize_amount(s):
    return re.sub(r'[\$,\s]', '', s).lower()

spacy_normalized = [normalize_amount(a) for a in amounts]
missed_amounts = [m for m in regex_amounts if normalize_amount(m) not in spacy_normalized]

amounts = list(set(amounts + missed_amounts))

with open("extracted_info.json", "w") as f:
    json.dump({
        "source_file": SOURCE_FILE,
        "extracted_on": date.today().isoformat(),
        "entities": {
            "companies": companies,
            "people": people,
            "amounts": amounts
        },
        "verification": {
            "regex_amounts_found": regex_amounts,
            "amounts_missed_by_spacy": missed_amounts,
        }
    }, f, indent=2)

print(f"Extraction complete:")
print(f"  Companies : {len(companies)}")
print(f"  People    : {len(people)}")
print(f"  Amounts   : {len(amounts)}")

print(f"\nVerification:")
print(f"  Regex found {len(regex_amounts)} financial figure(s) — spaCy missed {len(missed_amounts)}")
if missed_amounts:
    print(f"  Missed: {missed_amounts}")