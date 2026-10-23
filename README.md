# Manuscript Pre-Submission Checker

A Python tool that runs the technical checks a journal's screening desk performs before peer review, and produces a report with ready-to-send comments for authors. Use it from the command line or as a website.

Built from experience screening 900+ manuscripts as a journal screening editor. The tool **flags issues for a human to review**; it does not make editorial decisions.

**Try it online:** _add your Streamlit link here after deploying_

## What it checks

| Area | Checks |
| --- | --- |
| Structure | IMRaD sections present, abstract present and within word limit, keywords |
| Abbreviations | Never defined, used before definition, defined twice, defined but not used (abstract and main text checked separately). Common lab and statistics terms, gene, cell-line and chemical names are skipped unless the authors define them |
| Figures & tables | Every figure/table cited, cited in numerical order, no numbering gaps, legends match citations |
| Declarations | Ethics approval (committee name, approval number, date), consent (written/verbal/waived, contradictions, minors), conflict of interest, funding, author contributions, acknowledgements, data availability |
| Study details | Sample size, study period, data collected before 2020, inclusion/exclusion criteria, questionnaires supplied, euthanasia for animal studies, trial/PROSPERO registration (only when the study type requires it) |
| References | Numbered citations match the reference list; uncited references |

The checker works out what kind of study it is reading. A cell-line study isn't asked for patient consent, a systematic review isn't asked for ethics approval, and sentences like "no animals were involved" aren't mistaken for an animal study.

Every issue comes with a status (**Missing** / **Concern**) and an author-facing comment starting with "Please…".

## Output

- **Excel report** (`screening_report.xlsx`): one colour-coded sheet per manuscript, plus a summary sheet for batch runs.
- **Website**: upload files, see results on screen, copy the author comments, download the Excel report.
- **Google Sheets** (optional, command line): appends results to a shared sheet as a running screening log, using the Google Sheets API.

## Setup

Requires Python 3.10+.

```
pip install -r requirements.txt
```

## Usage

### Command line

```
python checker.py manuscript.docx              # one manuscript
python checker.py my_folder                    # every .docx in a folder
python checker.py my_folder --sheets           # also send results to Google Sheets
```

Try it on the included samples:

```
python checker.py batch
```

`sample_manuscript_clean.docx` should come back **Ready**; the others contain deliberately planted problems.

### Website on your own computer

```
streamlit run app.py
```

This opens the checker in your browser at `http://localhost:8501`.

### Settings

Journal-specific options live in `settings.json`, so they can change without editing code:

| Setting | Meaning |
| --- | --- |
| `abstract_word_limit` | Abstracts longer than this are flagged (default 250) |
| `extra_ignore_abbreviations` | Abbreviations this journal doesn't require authors to define, e.g. `["ICU", "MIC"]` |
| `skip_gene_and_chemical_symbols` | Skip names like TP53, MCF-7 and NaCl unless the authors define them (default `true`) |

On the website, the same options are in the sidebar.

## Putting the website online (free)

1. Push this repository to GitHub (it must be public for the free plan).
2. Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
3. Click **Create app**, choose this repository, branch `main`, and main file `app.py`.
4. Click **Deploy**. After a few minutes you get a public link.

Uploaded files are checked in memory and never written to disk or stored.

### Google Sheets setup (optional, command line only)

1. Create a Google Cloud project and enable the **Google Sheets API** and **Google Drive API**.
2. Create a service account, download its JSON key, and save it in this folder as `google_key.json` (never commit this file).
3. Share your Google Sheet with the service account's `client_email` as Editor.
4. Paste the sheet's link into `SHEET_URL` in `send_to_sheets.py`.

## Project structure

| File | Purpose |
| --- | --- |
| `app.py` | The website (Streamlit) |
| `checker.py` | Runs all checks and builds the Excel report |
| `step1_split_sections.py` | Reads a .docx and splits it into sections |
| `step2_figures_tables.py` | Figure and table citation checks |
| `step3_abbreviations.py` | Abbreviation checks |
| `step4_declarations.py` | Declarations, study details and reference checks |
| `settings.py`, `settings.json` | Journal-specific settings |
| `send_to_sheets.py` | Google Sheets upload |
| `tests/` | A realistic test manuscript used to measure false alarms |

Each step file can also be run on its own, e.g. `python step3_abbreviations.py manuscript.docx`.

## Changelog

**v1.1**
- Far fewer false alarms on real papers: a realistic test manuscript went from 36 flags to 2, both genuine.
- Abbreviation results grouped into one row per problem type, listing every abbreviation affected.
- Gene, cell-line, chemical and brand names, and common lab and statistics terms, no longer flagged.
- Study-type detection: negated sentences, in vitro studies and reviews handled correctly.
- `settings.json` for journal-specific options.
- Website version (`app.py`) with in-memory processing.

**v1.0**: command-line checker with Excel and Google Sheets output.

## Limitations

- Works on .docx only (no PDF yet).
- Rule-based: it can miss unusual phrasings and may raise false alarms. Treat results as flags for review.
- Does not check scientific content, language quality, plagiarism or image integrity.

## Roadmap

- PDF input
- Reference validation against Crossref (invalid DOIs, retracted papers)
- Author verification via ORCID

## How this was built

Built while learning Python, with AI assistance (Claude) for code generation and debugging. Design, screening rules and testing are my own.

## Data and ethics

The sample and test manuscripts are invented. No confidential or unpublished manuscripts were used in building or testing this tool.
