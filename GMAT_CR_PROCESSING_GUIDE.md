# GMAT CR Answer Detail Processing Guide

## What This Is

The file `CR_OG_questions_extracted.csv` contains GMAT Critical Reasoning questions scraped from GMAT Club forums. The `answer-detail` column contains raw forum text — full of usernames, tutor signatures, ads, promotional content, and garbage. This guide documents how to clean and rewrite it.

---

## Step 1: Scrape New Questions

Add new questions to `CR_OG_questions_extracted.csv`. Columns needed:

| Column | Description |
|--------|-------------|
| No | Sequential row number (1, 2, 3…) |
| Question + Text | Full question including passage and stem |
| A–E | Answer choices |
| Answer | Correct answer letter (A/B/C/D/E) |
| answer-by | Leave blank — will be filled as "Claude" |
| answer-detail | Raw scraped forum explanation — will be cleaned/rewritten |

---

## Step 2: Remove Non-CR Questions

Some scraped questions are not standard CR (they are dropdown, multi-select, data sufficiency, or table problems). These have empty A–E columns and no valid answer letter.

Run a scan to find them:

```python
import csv
with open('CR_OG_questions_extracted.csv', encoding='utf-8-sig', errors='replace') as f:
    rows = list(csv.reader(f))
header = rows[0]
data = rows[1:]
a_idx = header.index('A')
ans_idx = header.index('Answer')
no_idx = header.index('No')
for row in data:
    if not row[a_idx].strip() or not row[ans_idx].strip():
        print(f"No={row[no_idx]} — possibly non-CR")
```

Delete them and renumber using `remove_non_cr_rows.py` as a template.

---

## Step 3: Automated Cleaning

Run `clean_answers.py` first. It strips:
- Usernames as first line
- "Show tags" / "Show more" markers
- Repeated question text at the start of the detail
- Tutor promotional signatures (anaprep, gmatninja, e-gmat, magoosh, GMATinsight, CrackVerbal, etc.)
- Forum navigation links and kudos requests

```bash
cd d:\git\scrapper
python clean_answers.py
```

If new tutor signatures appear in the data, add their trigger phrases to the `SIGNATURE_TRIGGERS` list in `clean_answers.py`.

---

## Step 4: Manual Reasoning & Rewriting (Claude)

This is the main task. Claude reads each question, reasons through it, and rewrites the `answer-detail` in clear student-friendly language.

### Prompt to give Claude:

> I have a GMAT Critical Reasoning CSV at `d:\git\scrapper\CR_OG_questions_extracted.csv`. The `answer-detail` column contains cleaned but still imperfect forum explanations. The `Answer` column contains the correct answer letter — treat it as the source of truth.
>
> For each row:
> 1. Read the question from `Question + Text` and the options from columns A–E
> 2. Reason through why the answer in the `Answer` column is correct
> 3. Rewrite the `answer-detail` in clear, concise, student-friendly language
> 4. Set `answer-by` to "Claude"
> 5. If the existing detail argues for a different answer letter than `Answer`, flag it as a discrepancy in chat and still write the correct reasoning using `Answer` as truth
> 6. Save every 100 rows as a checkpoint to the SAME CSV (no multiple files)
> 7. Only print discrepancies in chat — no verbose commentary
>
> Work in batches of 100. Write a separate Python update script for each batch (e.g. `update_rows_1_100.py`) and run it. Use this script template:
>
> ```python
> import csv
> INPUT_FILE = 'CR_OG_questions_extracted.csv'
> REWRITES = {
>     0: "Answer: A\n\n...",  # 0-indexed into data array
>     1: "Answer: B\n\n...",
> }
> def update_rows():
>     with open(INPUT_FILE, encoding='utf-8-sig', errors='replace', newline='') as f:
>         rows = list(csv.reader(f))
>     header = rows[0]
>     data = rows[1:]
>     detail_idx = header.index('answer-detail')
>     answer_by_idx = header.index('answer-by')
>     for row_idx, new_detail in REWRITES.items():
>         data[row_idx][detail_idx] = new_detail.strip()
>         data[row_idx][answer_by_idx] = 'Claude'
>     with open(INPUT_FILE, 'w', encoding='utf-8-sig', newline='') as f:
>         writer = csv.writer(f)
>         writer.writerow(header)
>         writer.writerows(data)
>     print(f'Updated {len(REWRITES)} rows and saved.')
> if __name__ == '__main__':
>     update_rows()
> ```
>
> After all batches, run `fix_discrepancy_rows.py` to correct any rows where the original detail cited the wrong answer letter. Keep a running discrepancy list (question No., Answer column value, what the detail said).

---

## Step 5: Fix Discrepancies

After all batches are done, collect the full discrepancy list and re-reason each flagged question using `Answer` as truth. Use `fix_discrepancy_rows.py` as a template.

---

## Files in This Folder

| File | Purpose |
|------|---------|
| `CR_OG_questions_extracted.csv` | Main data file |
| `clean_answers.py` | Step 3: automated signature/garbage cleaning |
| `update_rows_*.py` | Step 4: batch rewrite scripts (100 rows each) |
| `fix_discrepancy_rows.py` | Step 5: fix rows where detail cited wrong answer |
| `remove_non_cr_rows.py` | Template for removing non-CR rows and renumbering |

---

## Notes from Last Run (2025)

- Processed 578 CR questions (started at 584, removed 6 non-CR rows: original Nos 246, 260, 278, 279, 280, 295)
- Common signature triggers already in `clean_answers.py`: anaprep, gmatninja, e-gmat, magoosh, GMATinsight, CrackVerbal, RC|CR|SC pipe pattern, "our recent scores"
- The `No` column must stay sequential — always renumber after deletions
- The CSV uses UTF-8 BOM encoding (`utf-8-sig`) — always open with that encoding
- Claude processes ~100 rows per context window comfortably; beyond that, context gets tight
