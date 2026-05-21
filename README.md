# txt_parser

A Python script that extracts named entities from a plain text file and saves the results as a structured JSON file.

---

## What It Does

Reads `acme_defense.txt`, runs it through a Named Entity Recognition (NER) model, and extracts three entity types:

| Entity Type | spaCy Label | Description |
|---|---|---|
| Company names | `ORG` | Organizations and companies |
| Person names | `PERSON` | Individual people mentioned |
| Dollar amounts | `MONEY` | Financial figures and currency amounts |

Results are written to `extracted_info.json` and a summary is printed to the console.

---

## Extraction Approach

Uses [spaCy](https://spacy.io/) with the `en_core_web_lg` model. spaCy was chosen because it handles NER out of the box without requiring custom regex patterns, and its statistical model handles natural variation in company and person names better than a rule-based approach would.

The larger `en_core_web_lg` model is used over `en_core_web_sm` for improved accuracy. A manual exclusion list filters known false positives (e.g. `CFO`, `CUI`, `CMMC Level 2`) that the model incorrectly tags as organizations.

---

## Input

A plain text file named `acme_defense.txt` placed in the same directory as the script.

---

## Output

**`extracted_info.json`** — structured extraction results:

```json
{
  "Source": "acme_defense.txt",
  "extracted_on": "2026-05-21",
  "entities": {
    "companies": [],
    "people": [],
    "amounts": []
  }
}
```

**Console summary:**

```
Extraction complete:
  Companies : 2
  People    : 2
  Amounts   : 0
```

---

## How to Run

1. Install dependencies:

```bash
pip install spacy
python -m spacy download en_core_web_lg
```

2. Place `acme_defense.txt` in the same directory as `txt_parser.py`.

3. Run the script:

```bash
python txt_parser.py
```

---

## Limitations

- **Model accuracy is imperfect.** `en_core_web_lg` is a general-purpose model. It may miss entities, mis-label them, or produce false positives — especially for domain-specific acronyms and abbreviations.
- **Manual exclusion list required.** Acronyms like `CFO`, `CUI`, and `CMMC Level 2` are blocked via a hardcoded list. Any new false positives must be added manually.
- **No deduplication.** If the same entity appears multiple times in the text, it will appear multiple times in the output.
- **MONEY label scope.** spaCy's `MONEY` label captures currency amounts but may miss figures expressed without a currency symbol (e.g. percentages or headcounts).
- **Hardcoded filename.** The input file is hardcoded as `acme_defense.txt`. To use a different file, edit the `SOURCE_FILE` variable at the top of the script.
