# Manuscript Pre-Submission Checker

A Python tool that runs the technical checks a journal's screening desk performs, before a manuscript is submitted, and produces a report with ready-to-send comments for authors.

Built from experience screening 700+ manuscripts as a journal screening editor. The tool **flags issues for a human to review**; it does not make editorial decisions.

## What it checks

| Area | Checks |
| --- | --- |
| Structure | IMRaD sections present, abstract present and within word limit, keywords |
| Abbreviations | Used before definition, never defined, defined twice, defined but not used (abstract and main text checked separately) |
| Figures & tables | Every figure/table cited, cited in numerical order, no numbering gaps, legends match citations |
| Declarations | Ethics approval (committee name, approval number, date), consent (written/verbal/waived, contradictions, minors), conflict of interest, funding, author contributions, acknowledgements, data availability |
| Study details | Sample size, study period, data collected before 2020, inclusion/exclusion criteria, questionnaires supplied, euthanasia for animal studies, trial/PROSPERO registration (only when the study type requires it) |
| References | Numbered citations match the reference list; uncited references |

Every issue comes with a status (**Missing** / **Concern**) and an author-facing comment starting with "Please…".

## Output

- **Excel report** (`screening_report.xlsx`): one colour-coded sheet per manuscript, plus a summary sheet for batch runs.
- **Google Sheets** (optional): appends results to a shared sheet as a running screening log, using the Google Sheets API.

## Setup

Requires Python 3.10+.

```
pip install -r requirements.txt
```

## Usage

```
python checker.py manuscript.docx              # one manuscript
python checker.py my_folder                    # every .docx in a folder
python checker.py my_folder --sheets           # also send results to Google Sheets
```

Try it on the included samples:

```
python checker.py samples
```

`sample_manuscript_clean.docx` should come back **Ready**; the others contain deliberately planted problems.

### Google Sheets setup (optional)

1. Create a Google Cloud project and enable the **Google Sheets API** and **Google Drive API**.
2. Create a service account, download its JSON key, and save it in this folder as `google_key.json` (never commit this file).
3. Share your Google Sheet with the service account's `client_email` as Editor.
4. Paste the sheet's link into `SHEET_URL` in `send_to_sheets.py`.

## Project structure

| File | Purpose |
| --- | --- |
| `checker.py` | Runs all checks and writes the reports |
| `step1_split_sections.py` | Reads a .docx and splits it into sections |
| `step2_figures_tables.py` | Figure and table citation checks |
| `step3_abbreviations.py` | Abbreviation checks |
| `step4_declarations.py` | Declarations, study details and reference checks |
| `send_to_sheets.py` | Google Sheets upload |

Each step file can also be run on its own, e.g. `python step3_abbreviations.py manuscript.docx`.

## Limitations

- Works on .docx only (no PDF yet).
- Rule-based: it can miss unusual phrasings and may raise false alarms, especially on abbreviations such as gene names. Treat results as flags for review.
- Does not check scientific content, language quality, plagiarism or image integrity.

## Roadmap

- Reduce false positives on real-world papers (gene/chemical names, varied heading styles)
- Settings file for journal-specific limits
- PDF input
- Reference validation against Crossref (invalid DOIs, retracted papers)
- Author verification via ORCID

## Data and ethics

The sample manuscripts are invented. No confidential or unpublished manuscripts were used in building or testing this tool.
