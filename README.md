# txt_parser

A Python script that extracts named entities from a plain text or Word document and saves the results as a structured JSON file.

---

## What It Does

Reads a `.txt` or `.docx` file, runs it through a Named Entity Recognition (NER) model, and extracts three entity types:

| Entity Type | spaCy Label | Description |
|---|---|---|
| Company names | `ORG` | Organizations and companies |
| Person names | `PERSON` | Individual people mentioned |
| Dollar amounts | `MONEY` | Financial figures and currency amounts |

Results are written to `extracted_info.json` and a summary is printed to the console. A `verification` block in the JSON shows what the regex cross-check found independently of spaCy, making it possible to distinguish between "no amounts exist" and "the extractor missed them."

---

## Extraction Approach

Uses [spaCy](https://spacy.io/) with the `en_core_web_lg` model. spaCy was chosen because it handles NER out of the box without requiring custom regex patterns. `en_core_web_sm` and `en_core_web_md` were tested first but produced less accurate results — the larger model handles ambiguous names and organizations better.

Several post-processing steps are applied on top of spaCy's raw output:

- **Timestamp stripping** — elapsed timestamps in speaker labels (e.g. `0:13`, `16:11`) are stripped from the text before NER runs, preventing artifacts like `"Greg 0:13"` appearing as names
- **Company blocklist (`Not_Companies`)** — acronyms and titles frequently mis-tagged as `ORG` (e.g. `CFO`, `SSO`, `MDR`, `RMM`) are excluded
- **People blocklist (`Not_People`)** — known product names and non-person words mis-tagged as `PERSON` (e.g. `Authenticator`, `Transcript`) are dropped
- **Move to companies (`Move_to_companies`)** — known company/product names mis-tagged as `PERSON` (e.g. `Fortinet`, `Ninjio`, `Claude`) are routed into the companies list instead
- **People filters** — all-caps tokens, entries with hyphens, and entries shorter than 3 characters are dropped at extraction time
- **List marker stripping** — lettered or numbered list prefixes (e.g. `a. Greg Gallagher` → `Greg Gallagher`) are removed before deduplication
- **Whitespace normalization** — multiple spaces left by timestamp stripping are collapsed to single spaces
- **People deduplication** — partial name matches are resolved using a word-prefix comparison. Among overlapping entries (`Jordan`, `Jordan Martin`, `Jordan Martin Good`), the cleanest 2-word version is kept
- **Cross-list deduplication** — anything in the companies list already covered by a people entry is removed, resolving cases where spaCy tags the same name as both `ORG` and `PERSON`
- **Regex cross-check for amounts** — a separate regex scan runs independently of spaCy to catch financial figures it may have missed (e.g. `$99k`, `1 to 99 K`, range patterns). Results are normalized and merged before output

---

## Input

A `.txt` or `.docx` file. Set the `SOURCE_FILE` variable at the top of the script to the filename. The file must be in the same directory as the script, and if it is a `.docx`, it must not be open in Word when the script runs.

---

## Output

**`extracted_info.json`** — structured extraction results:

```json
{
  "source_file": "acme_defense.txt",
  "extracted_on": "2026-05-26",
  "entities": {
    "companies": [],
    "people": [],
    "amounts": []
  },
  "verification": {
    "regex_amounts_found": [],
    "amounts_missed_by_spacy": []
  }
}
```

**Console summary:**

```
Extraction complete:
  Companies : 12
  People    : 8
  Amounts   : 3

Verification:
  Regex found 3 financial figure(s) — spaCy missed 1
  Missed: ['1 to 99 K']
```

---

## How to Run

1. Install dependencies:

```bash
pip install spacy python-docx
python -m spacy download en_core_web_lg
```

2. Place your input file in the same directory as `txt_parser.py` and set `SOURCE_FILE` at the top of the script.

3. Run the script from the same directory:

```bash
python txt_parser.py
```

---

## Limitations

- **Model accuracy is imperfect.** `en_core_web_lg` is a general-purpose model not trained on MSP/IT transcripts. It regularly mis-tags product names, acronyms, and tools as people or organizations.
- **Blocklists require manual upkeep.** `Not_Companies`, `Not_People`, and `Move_to_companies` are hardcoded and document-specific. Every new transcript may introduce new entries that need to be added manually.
- **Comma-inverted speaker labels are not fully handled.** Transcripts that format names as `Lastname, Firstname` (e.g. `White, Greg`) are not reliably parsed. spaCy splits at the comma before tagging, so the entity never contains the full name in the expected order.
- **No fuzzy name matching.** Spelling variations of the same person (`Bernie` vs `Berny`) are treated as different entries. The deduplication is exact, not approximate.
- **One file at a time.** There is no batch mode. Running against multiple documents requires changing `SOURCE_FILE` manually for each run.
- **MONEY label scope.** spaCy's `MONEY` label is inconsistent with currency symbols and context. The regex fallback improves coverage but is not exhaustive.
- **File must be closed.** On Windows, `.docx` files open in Word are locked and cannot be read by the script.

---

## See Also

See `gap_analysis.md` for a full breakdown of what worked, what failed, and specific examples from the documents tested during development.
