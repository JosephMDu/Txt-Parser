# txt_parser

A Python script that extracts named entities from a plain text file and saves the results as JSON.

## What it does

Reads `acme_defense.txt`, runs it through a Named Entity Recognition (NER) model, and pulls out three entity types:

- **Company names** — tagged as `ORG` by the model
- **Person names** — tagged as `PERSON`
- **Dollar amounts / financial figures** — tagged as `MONEY`

Results are written to `extracted_info.json` and a short summary is printed to the console.

## Extraction approach

Uses [spaCy](https://spacy.io/) with the `en_core_web_sm` model. spaCy was chosen because it handles NER out of the box without writing custom regex patterns, and `en_core_web_sm` is small and fast enough for short documents like this one. A pure regex approach would have been brittle for company and person names; spaCy's statistical model handles natural variation better.

## Input

A plain text file named `acme_defense.txt` in the same directory as the script.

## Output

`extracted_info.json` with this structure:

```json
{
  "source_file": "acme_defense.txt",
  "extracted_on": "2026-05-21",
  "entities": {
    "companies": [],
    "people": [],
    "amounts": []
  }
}
```

A console summary is also printed, for example:

```
Extraction complete:
  Companies : 3
  People    : 2
  Amounts   : 1
```

## How to run

1. Install dependencies:

```bash
pip install spacy
python -m spacy download en_core_web_sm
```

2. Place `acme_defense.txt` in the same directory as `txt_parser.py`.

3. Run the script:

```bash
python txt_parser.py
```

## Limitations

- **Model accuracy is imperfect.** `en_core_web_sm` is a small general-purpose model. It may miss entities, mis-label them, or pick up false positives — especially for short or ambiguous names.
- **No deduplication.** If the same company or person appears multiple times in the text, they will appear multiple times in the output list.
- **MONEY label scope.** spaCy's `MONEY` label captures dollar amounts but may miss financial figures expressed without a currency symbol (e.g., "15 users" or percentages).
- **Hardcoded filename.** The input file is hardcoded as `acme_defense.txt`. To use a different file, edit the `SOURCE_FILE` variable at the top of the script.
