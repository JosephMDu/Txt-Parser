# Gap Analysis — txt_parser NER Pipeline

**Scope:** Eight meeting transcript .docx files processed across development. Documents ranged from a 5-minute internal call (Call with David and 1 other) to a 57-minute MSP pitch (REIC Rentals NT Overview). All files were Microsoft Teams auto-transcripts sharing the same speaker-label format: `Firstname Lastname   M:SS` followed by dialogue paragraphs.

---

## What Worked

**Entity extraction accuracy improved significantly with `en_core_web_lg`.** Switching from `en_core_web_sm` reduced mis-tagging of common names and organizations. Across shorter documents like `Call with Joe Dunkle.docx` and `Call with Justin Cooley (2).docx`, the model correctly identified people (Peter Newton, Justin Cooley, Joe Dunkle) and companies (Quantica, Arctic Wolf, Microsoft Sentinel) with minimal noise.

**The regex fallback for financial figures caught real gaps.** spaCy's `MONEY` label is inconsistent with dollar-sign presence — it tagged `"no more than $80.00"` but missed `"$1970"` and `"$80.00"` when they appeared without surrounding context. The regex cross-check recovered these. It also caught range-style figures like `"1 to 99 K"` from the AWS Migration transcript that spaCy ignored entirely.

**Partial-match deduplication resolved the noisiest people entries.** The `is_covered_by()` function successfully collapsed variants like `"Jordan Martin Good"`, `"Jordan Martin Greg"`, and `"Jordan Martin Sure"` down to `"Jordan Martin"` — artifacts common across all transcript files where the transcription system bled the first word of dialogue into the speaker label.

**Cross-list filtering removed most people/company overlaps.** After adding the companies→people cross-check, entries like `"Greg"` appearing in both lists due to spaCy inconsistency were resolved cleanly without manual intervention.

---

## What Failed

**Comma-inverted speaker labels were never fully solved.** Several transcripts — notably `Transcript AWS Migration opportunity.docx` — format speaker names as `Lastname, Firstname   M:SS` (e.g., `White, Greg   2:19`). After timestamp stripping, the comma remains. spaCy tokenizes at the comma boundary, so it never sees `"White, Greg"` as a single entity. Our entity-level `split(",")` code is dead in practice — it only fires if spaCy tags a comma-containing span as a single PERSON, which it does not do consistently. The downstream effect: `"Greg"` gets extracted from line one, `"Mead"` gets picked up from the next paragraph, and spaCy combines them into `"Greg Mead"` — a name that does not exist in the document. This was observed directly in the REIC transcript.

**Products and tools were routinely mis-tagged as PERSON.** Across multiple documents, spaCy tagged `"Authenticator"`, `"Transcript"`, `"Ninjio"`, `"Dropsuite"`, `"Claude"`, and `"Fortinet"` as people. This is a fundamental limitation of a general-purpose model operating on domain-specific MSP/IT content — it has no awareness that these are product names. The workaround (a hardcoded `Not_People` and `Move_to_companies` list) works for known offenders but breaks on any new document introducing new tool names.

**Hardcoded blocklists do not scale.** The `Not_Companies` list grew to 30+ entries across the development session as each new document introduced new acronyms (`RMM`, `SSO`, `MDR`, `LLM`, `MFA`, `EDR`, `SLAS`, `QBRS`, etc.) that spaCy mis-tagged as organizations. Each new transcript file will require a manual audit and additions to all three lists (`Not_Companies`, `Not_People`, `Move_to_companies`). There is no mechanism to learn or generalize from prior corrections.

**List-marker prefixes caused duplicate people entries.** The REIC transcript used lettered sub-items (`a. Greg Gallagher`, `b. Brenda Morgan`) in dialogue. spaCy included the `a.` prefix in the entity span, and `is_covered_by()` failed to match `"a. Greg Gallagher"` against `"Greg Gallagher"` because the first words differ. This was fixed with a regex strip, but only after the duplicate appeared in production output.

**Single-word and ambiguous names produce unreliable results.** The `Phase 2` transcript refers to a customer IT lead only as `"Harvest"` throughout — a single word that may be a first name, last name, nickname, or transcription artifact. The pipeline has no way to distinguish this from noise like `"Mac"` or `"Mhm"`. Similarly, `"Bernie"` vs `"Berny Pacheco"` across the REIC transcript are the same person with inconsistent spelling — the partial-match deduplication misses this because string comparison is exact, not fuzzy.

**Amount normalization was inconsistent across documents.** spaCy sometimes included surrounding context in MONEY spans (`"no more than $80.00"`) and sometimes did not (`"700"`). The regex and spaCy results used different representations of the same figure (`"$80.00"` vs `"80.00"`), initially causing false "missed" flags until a normalization function was added. Range-style figures like `"1 to 99 K"` required a multi-pattern regex and were still not caught until the pattern was explicitly extended.

---

## Scalability Concerns

- **One SOURCE_FILE at a time.** The script has no batch mode. Running against all eight transcripts requires manually changing `SOURCE_FILE` eight times.
- **All filtering is document-specific.** Blocklists written for the REIC transcript will silently over-filter or under-filter on the NIST/CMMC transcript or the AWS Migration call.
- **No confidence scoring.** Every entity is treated as equally valid. There is no mechanism to flag low-confidence extractions for human review.
- **No output merging.** Running the script against multiple documents produces eight separate JSON files with no way to aggregate, deduplicate, or reconcile entities across them.

---

## Summary

The pipeline works well as a single-document extraction tool on clean, consistently formatted transcripts. It degrades predictably when documents introduce new acronyms, unfamiliar product names, comma-inverted speaker labels, or inconsistent name formatting — all of which are normal variation in real business transcripts. The core extraction logic is sound; the brittleness lives entirely in the post-processing layer, which is manual, document-specific, and requires a developer to update between runs.
