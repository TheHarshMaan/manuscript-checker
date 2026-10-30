# Manuscript Pre-Submission Checker

A Python tool that runs the technical checks a journal's screening desk performs before peer review, and produces a clear, colour-coded report of what is missing or needs attention. Use it from the command line or as a website that runs entirely in the browser.

Built from experience screening 900+ manuscripts as a journal screening editor. The tool **flags issues for a human to review**; it does not make editorial decisions.

**Try it online:** [thegreyswan.in/checker](https://thegreyswan.in/checker/), by The Grey Swan Editorial. Manuscripts are checked inside your browser and never uploaded.

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

Every issue comes with a **severity** (Must fix / Should fix / Advisory), a status (**Missing** / **Concern**) and a plain description of what was found. How serious each check is depends on the journal profile you choose (see below).

The checker also recognises the type of article and applies the right rules: research papers are expected to follow IMRaD; case reports, narrative reviews and letters to the editor are not asked for Methods, Results or a sample size. Superscript citations (¹ ²) are read as well as bracketed ones ([1]).

## Output

- **Excel report** (`screening_report.xlsx`): one colour-coded sheet per manuscript, plus a summary sheet for batch runs.
- **Website**: add files, see results on screen, download the Excel report. Runs in the browser; nothing is uploaded.
- **Google Sheets** (optional, command line): appends results to a shared sheet as a running screening log, using the Google Sheets API.

## Setup

Requires Python 3.10+.

```
pip install -r requirements.txt
```

## Usage

### Command line

```
python checker.py manuscript.docx                            # one manuscript
python checker.py my_folder                                  # every .docx in a folder
python checker.py my_folder --profile strict_screening       # check against another journal profile
python checker.py --profiles                                 # list the available profiles
python checker.py my_folder --sheets                         # also send results to Google Sheets
```

Try it on the included samples:

```
python checker.py batch
```

`sample_manuscript_clean.docx` should come back **Ready**; the others contain deliberately planted problems.

### Website

The website (`web/`) runs the same Python checker inside the visitor's browser using [Pyodide](https://pyodide.org), so there is no server and manuscripts never leave the visitor's computer. The page is plain HTML, CSS and JavaScript and can be hosted anywhere static files can, such as GitHub Pages.

Build it after any change to a check, rule or profile:

```
python build_web.py                         # builds web/checker_bundle.zip
python build_web.py ../my-site/checker      # also copies the finished page into your site's folder
```

`checker_bundle.zip` holds the checker, the profiles and the two libraries the browser doesn't already have (python-docx and openpyxl, with their licences). To deploy, upload the files in `web/` to the site's `checker/` folder.

To try it on your own computer: `python -m http.server` from the `web/` folder, then open `http://localhost:8000`. (Opening `index.html` directly from disk won't work; browsers block the background worker for local files.)

### Journal profiles

Journals don't all screen the same way, so the rules aren't written into the code. A **profile** (a small file in `profiles/`) says which checks a journal runs and how serious each one is:

| Severity | Meaning |
| --- | --- |
| `must` | **Must fix**: the journal won't accept the manuscript without it |
| `should` | **Should fix**: expected; an editor will likely ask for it |
| `advisory` | **Advisory**: worth a look, doesn't block the manuscript |
| `off` | Not checked |

A manuscript is **Ready** when nothing is Must fix or Should fix; advisories are listed but don't block it.

Included profiles:

| Profile | For |
| --- | --- |
| `generic` | The universal core most journals share (ICMJE basics). House-specific rules are advisory. Default. |
| `strict_screening` | A strict screening desk: also follows up approval dates, data older than the cut-off year, verbal-only consent, supplied questionnaires and euthanasia statements. |

A profile can start from another one and list only what it changes:

```yaml
name: My journal
based_on: generic
settings:
  abstract_word_limit: 300
  data_cutoff_year: 2018
  extra_ignore_abbreviations: [ICU, MIC]
required_sections:
  research: [Abstract, Introduction, Methods, Results, Discussion, References]   # no Keywords
rules:
  ethics_date: must
  acknowledgements: off
```

Save it as `profiles/my_journal.yaml` and run with `--profile my_journal`. Every rule ID, and what it checks, is listed in `rules.py`. A misspelt rule ID or severity is reported straight away rather than silently ignored.

**Settings in a profile:** `abstract_word_limit`, `data_cutoff_year`, `extra_ignore_abbreviations`, `skip_gene_and_chemical_symbols` (skip names like TP53, MCF-7 and NaCl unless the authors define them), and `required_sections` for each article type (research, case report, narrative review, letter).

`settings.json` picks the default profile and can override settings on top of it, e.g. `{"profile": "generic", "abstract_word_limit": 300}`.

**On the website**, the sidebar has a profile picker, the settings, and every rule with its severity. Adjust them, click **Save these settings as a profile** to download your own `.yaml`, and load it next time with **Load a saved profile**.

## Optional extras

### Google Sheets setup (optional, command line only)

1. Create a Google Cloud project and enable the **Google Sheets API** and **Google Drive API**.
2. Create a service account, download its JSON key, and save it in this folder as `google_key.json` (never commit this file).
3. Share your Google Sheet with the service account's `client_email` as Editor.
4. Paste the sheet's link into `SHEET_URL` in `send_to_sheets.py`.

## Project structure

| File | Purpose |
| --- | --- |
| `web/` | The website: `index.html`, `style.css`, `app.js`, `worker.js` (runs Python in the browser) |
| `web_entry.py` | Bridge between the website and the checker |
| `build_web.py` | Builds `web/checker_bundle.zip` and copies the page to the site |
| `app.py` | Previous website (Streamlit), being retired |
| `checker.py` | Runs all checks and builds the Excel report |
| `step1_split_sections.py` | Reads a .docx and splits it into sections |
| `step2_figures_tables.py` | Figure and table citation checks |
| `step3_abbreviations.py` | Abbreviation checks |
| `step4_declarations.py` | Declarations, study details and reference checks |
| `rules.py` | Catalogue of every rule (ID, name, what it checks) |
| `profiles/` | Journal profiles: which rules run and how serious each is |
| `settings.py`, `settings.json` | Loads profiles; picks the default one |
| `send_to_sheets.py` | Google Sheets upload |
| `tests/` | Labelled test papers and a script that scores the checker (see Testing) |

Each step file can also be run on its own, e.g. `python step3_abbreviations.py manuscript.docx`.

## Testing

`tests/` holds 12 invented manuscripts, each with a known list of planted problems: a clean control trial, a flawed trial, a systematic review, an animal study, a school survey, a case report, a paper with unusual headings, a retrospective study, a qualitative study, a narrative review, a letter to the editor, and a paper with superscript citations.

```
python tests/make_test_papers.py    # rebuild the papers
python tests/run_tests.py           # score the checker
```

The script runs every paper against every profile and reports which planted problems were caught, which were missed, and any false alarms. Current result: **16/16 planted problems caught, 0 false alarms, for every profile.** Five of the papers were written as an unseen second round, with expected results fixed before the checker was run on them.

## Changelog

**v1.3**
- Journal profiles: rules moved out of the code into `profiles/*.yaml`, with inheritance (`based_on`).
- Every check has a rule ID and a severity (Must fix / Should fix / Advisory / off) set by the profile.
- Two profiles to start: `generic` (universal core) and `strict_screening`.
- Website: profile picker, per-rule severities, save and load your own profile.
- Website moved to thegreyswan.in/checker and now runs entirely in the browser (Pyodide): no server, nothing uploaded, no waking-up delay. Results update as settings change; filter by severity; readable on phones. Replaces the Streamlit app.
- Command line: `--profile` and `--profiles`.
- Excel and Google Sheets reports gain Severity and Profile columns; "Ready" now means nothing Must fix or Should fix.
- The data cut-off year (previously fixed at 2020) is now a setting.
- Google Sheets: if your sheet was made by an older version, delete or rename its "Summary" and "Issues" tabs once so they are recreated with the new columns.

**v1.2**
- Labelled test set (12 papers) and a scoring script.
- Article-type detection: case reports, narrative reviews and letters to the editor get their own rules.
- Superscript citations recognised.
- More heading styles recognised (e.g. "Material and Methods", "Results and Discussion", "CRediT authorship contribution statement").
- Reporting guidelines, databases and regulators (CONSORT, PRISMA, MEDLINE, CPCSEA…) no longer flagged as undefined abbreviations.
- Author-facing "Please…" comments removed: the report now lists findings only.
- The Grey Swan Editorial design for the website.

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
