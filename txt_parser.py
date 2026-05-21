import spacy
import json
from datetime import date

SOURCE_FILE = "acme_defense.txt"

nlp = spacy.load("en_core_web_lg")

with open(SOURCE_FILE, "r") as f:
    text = f.read()

doc = nlp(text)

companies = []
people = []
amounts = []

Not_Companies = ["CMMC Level 2", "CUI", "CFO", "CEO", "IT", "NDA"]

for ent in doc.ents:
    if ent.label_ == "ORG" and ent.text not in Not_Companies:
        companies.append(ent.text)
    elif ent.label_ == "PERSON":
        people.append(ent.text)
    elif ent.label_ == "MONEY":
        amounts.append(ent.text)

with open("extracted_info.json", "w") as f:
    json.dump({
        "source_file": SOURCE_FILE,
        "extracted_on": date.today().isoformat(),
        "entities": {
            "companies": companies,
            "people": people,
            "amounts": amounts
        }
    }, f, indent=2)

print(f"Extraction complete:")
print(f"  Companies : {len(companies)}")
print(f"  People    : {len(people)}")
print(f"  Amounts   : {len(amounts)}")