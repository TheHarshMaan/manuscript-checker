# Manuscript Pre-Submission Checker

A Python tool that runs the technical checks a journal's screening desk performs before peer review, and produces a clear report of what is missing or needs attention, with how to fix each item. Use it from the command line or as a website that runs entirely in the browser.

Built from experience screening 900+ manuscripts as a journal screening editor. The tool **flags issues for a person to review**; it does not make editorial decisions.

**Try it online:** [thegreyswan.in/checker](https://thegreyswan.in/checker/), by The Grey Swan Editorial. Files are checked inside your browser and never uploaded.

## What it checks

Journals don't all screen the same way, so every check belongs to a **journal profile** that decides whether it runs and how serious it is (see [Journal profiles](#journal-profiles)). 95 rules in all; `rules.py` lists every one with what it checks, how to fix it and where the requirement comes from.

| Area | Checks |
| --- | --- |
| Structure | Sections each article type needs (IMRaD for research, Case presentation for case reports…), abstract and its word limit, keywords, tracked changes or comments left in the file |
| Article types | Research article, short communication, case report, letter, narrative review, commentary/editorial, study protocol, methods paper, data paper, book review, correction — each with its own required sections and checks |
| Abbreviations | Not defined, used before definition, defined twice, defined but not used (abstract and main text separately); common terms, gene, cell-line and chemical names skipped |
| Figures & tables | All cited, cited in order, no numbering gaps, captions present, tables in the file match citations, permission for reproduced figures |
| Declarations | Ethics approval (committee, number, date), consent (written/verbal/waived, minors, consent for publication in case reports), conflicts of interest, funding and grant numbers, author contributions and CRediT roles, acknowledgements, data and code availability, generative AI statement, Declaration of Helsinki, corresponding author, ORCID iDs |
| Reporting guidelines | Detects the study design and checks the EQUATOR guideline is named and its key items are present: CONSORT, SPIRIT, PRISMA, STROBE, CARE, ARRIVE, STARD, COREQ/SRQR, TRIPOD, CHEERS, SQUIRE |
| Study details | Sample size, study period, old data, inclusion/exclusion criteria, questionnaires supplied, euthanasia, trial and PROSPERO registration (only when the design needs it), registration before the study started, sex and gender reporting (SAGER) |
| References & citation style | Every citation in the list and every reference cited, for numbered and author–date systems; cited in order; alphabetical author–date lists; no mixed systems; old references. With a named style (APA 7, Harvard, AMA, Vancouver, IEEE): the right system, in-text form and reference-list format |
| Double-blind review | No title page, emails, ORCID iDs or author names in the manuscript, headers or footers; clean Word file properties; no first-person self-citation; acknowledgements and institutions blinded |
| Integrity red flags | Tortured phrases (paraphrasing-tool fingerprints), chatbot leftovers, hidden text and instructions aimed at AI reviewers, an AI tool listed as an author, free-mail corresponding author, percentages that don't match their numbers, impossible values, high self-citation |
| Formatting | Always: US/UK spelling mixed, p = 0.000, sentences starting with a numeral. When the profile asks: word, reference and figure limits per article type, title length, running title, structured or unstructured abstract and its headings, number of keywords, highlights/key points, line numbers, double spacing, page numbers, p-value style, US or UK spelling |
| Submission files | Recognises a separate title page (authors, affiliations, corresponding author) and cover letter (originality, conflicts of interest) and checks them as such |

**File formats:** Word (.docx) gives the fullest check. PDF, OpenDocument (.odt), RTF and LaTeX (.tex) are read too; the report notes what each can't show (a PDF has no tracked changes, hidden-text colour or superscripts, for example).

Every issue comes with a **severity** (Must fix / Should fix / Advisory), what was found, **how to fix it** and the **source** of the requirement (ICMJE, COPE, CONSORT, APA 7…). A file is **Ready** when nothing is Must fix or Should fix.

## Output

- **Website:** results on screen in *Author view* (most serious first, with how to fix) or *Editor view* (section by section, as a screening log); filter by severity; dismiss false alarms; download the Excel or Word report.
- **Excel report** (`screening_report.xlsx`): one sheet per file, plus a summary sheet for batches.
- **Word report** (`screening_report.docx`, with `--word`): for sending to authors or printing.
- **Google Sheets** (optional, command line): appends results to a shared sheet as a running log.

## Setup

Requires Python 3.10+.

```
pip install -r requirements.txt
```

## Usage

### Command line

```
python checker.py manuscript.docx                       # one file (.docx, .pdf, .odt, .rtf or .tex)
python checker.py my_folder                             # every file in a folder, e.g. a whole submission
python checker.py my_folder --profile apa_journal       # check against another journal profile
python checker.py --profiles                            # list the available profiles
python checker.py my_folder --word                      # also save a Word report
python checker.py my_folder --sheets                    # also send results to Google Sheets
```

Each step file can also be run on its own, e.g. `python step8_guidelines.py manuscript.docx` shows the detected study design and guideline.

### Website

The website (`web/`) runs the same Python checker inside the visitor's browser using [Pyodide](https://pyodide.org), so there is no server and files never leave the visitor's computer. The page is plain HTML, CSS and JavaScript and can be hosted anywhere static files can, such as GitHub Pages.

Build it after any change to a check, rule or profile:

```
python build_web.py                         # builds web/checker_bundle.zip
python build_web.py ../my-site/checker      # also copies the finished page into your site's folder
```

`checker_bundle.zip` holds the checker, the profiles and the libraries the browser doesn't already have (python-docx, openpyxl and pypdf, with their licences). To deploy, upload the files in `web/` to the site's `checker/` folder.

To try it on your own computer: `python -m http.server` from the `web/` folder, then open `http://localhost:8000`.

## Journal profiles

A **profile** (a small file in `profiles/`) says which checks a journal runs and how serious each one is:

| Severity | Meaning |
| --- | --- |
| `must` | **Must fix**: the journal won't accept the manuscript without it |
| `should` | **Should fix**: expected; an editor will likely ask for it |
| `advisory` | **Advisory**: worth a look, doesn't block the manuscript |
| `off` | Not checked |

Included profiles:

| Profile | For |
| --- | --- |
| `generic` | The universal core most journals share (ICMJE basics). House-specific rules are advisory. Default. |
| `generic_double_blind` | The generic core plus the anonymisation checks for double-blind review. |
| `strict_screening` | A strict screening desk: approval dates, old data, verbal-only consent, questionnaires, euthanasia, guideline checklists followed up. |
| `apa_journal` | APA 7 (psychology, social sciences): author–date citations, APA reference format, untitled introduction, p = .03, US spelling. |
| `ama_journal` | AMA (medicine): superscript numbers, AMA reference format, P = .03, US spelling. |
| `vancouver_journal` | Vancouver (biomedical): numbered citations, Vancouver reference format. |
| `ieee_journal` | IEEE (engineering, computing): bracketed numbers, IEEE reference format, engineering-style sections. |
| `humanities_journal` | History, literature, philosophy…: no IMRaD or study-design checks. |

A profile can start from another one and list only what it changes:

```yaml
name: My journal
based_on: generic
settings:
  review_model: double_blind         # single_blind / double_blind / open
  citation_style: vancouver          # auto / apa / harvard / ama / vancouver / ieee
  limits:
    research: {words: 4000, references: 50, figures_tables: 6, abstract_words: 300}
    letter: {words: 800, references: 10, figures_tables: 1}
  abstract_structure: structured
  abstract_headings: [Background, Methods, Results, Conclusions]
  keywords: {min: 3, max: 6}
  require_line_numbers: true
  spelling: uk
required_sections:
  research: [Abstract, Introduction, Methods, Results, Discussion, References]   # no Keywords
rules:
  ethics_date: must
  acknowledgements: 'off'
```

Save it as `profiles/my_journal.yaml` and run with `--profile my_journal`. A misspelt rule ID, severity or setting is reported straight away rather than silently ignored.

**Settings** (all in `profiles/generic.yaml`, with comments): `review_model`, `citation_style`, `abstract_word_limit`, `data_cutoff_year`, `old_reference_years` and `old_reference_share`, `self_citation_share`, `extra_ignore_abbreviations`, `skip_gene_and_chemical_symbols`, `limits` (per article type), `title_max_words`, `require_running_title`, `abstract_structure` and `abstract_headings`, `keywords`, `require_highlights` and `highlights`, `require_line_numbers`, `require_double_spacing`, `require_page_numbers`, `p_value_style`, `spelling`, and `required_sections` for each article type.

`settings.json` picks the default profile and can override settings on top of it, e.g. `{"profile": "generic", "abstract_word_limit": 300}`.

**On the website**, the sidebar has the profile picker, the main settings (peer review, reference style, abstract limit…), and every rule with its severity. Adjust them, click **Save these settings as a profile** to download your own `.yaml`, and load it next time with **Load a saved profile**.

## Optional extras

### Google Sheets setup (command line only)

1. Create a Google Cloud project and enable the **Google Sheets API** and **Google Drive API**.
2. Create a service account, download its JSON key, and save it in this folder as `google_key.json` (never commit this file).
3. Share your Google Sheet with the service account's `client_email` as Editor.
4. Paste the sheet's link into `SHEET_URL` in `send_to_sheets.py`.

## Project structure

| File | Purpose |
| --- | --- |
| `checker.py` | Runs all checks, applies the profile, builds the Excel and Word reports; the command line |
| `rules.py` | Catalogue of every rule: ID, name, what it checks, how to fix it, source |
| `profiles/` | Journal profiles: which rules run and how serious each is |
| `settings.py`, `settings.json` | Loads profiles; picks the default one |
| `readers.py` | Reads PDF, ODT, RTF and LaTeX files |
| `step1_split_sections.py` | Reads a file and splits it into sections |
| `step2_figures_tables.py` | Figure and table citations |
| `step3_abbreviations.py` | Abbreviations |
| `step4_declarations.py` | Article type, ethics, consent, declarations, study details |
| `step5_anonymisation.py` | Double-blind checks, and leftover tracked changes/comments |
| `step6_citations.py` | Citations and reference styles |
| `step7_policies.py` | Newer declarations: AI use, CRediT, code, consent for publication, registration timing, Helsinki, SAGER… |
| `step8_guidelines.py` | Study design and EQUATOR reporting guidelines |
| `step9_integrity.py` | Integrity red flags |
| `step10_formatting.py` | Formatting and mechanics |
| `step11_submission.py` | Title pages and cover letters |
| `web/`, `web_entry.py`, `build_web.py` | The website, its bridge to the checker, and the script that builds it |
| `send_to_sheets.py` | Google Sheets upload |
| `tests/` | Test papers, expected results and the test scripts (see Testing) |
| `.github/workflows/tests.yml` | Runs the tests on GitHub after every upload |

## Testing

`tests/papers/` holds 36 invented manuscripts, each with a known list of planted problems, and `tests/converted/` holds 16 PDF, ODT and RTF copies of six of them (made with LibreOffice, plus a PDF compiled from the LaTeX paper with pdflatex). They cover: clean and flawed trials, a systematic review, an animal study, surveys, case reports, a qualitative study, a narrative review, a letter, superscript citations, a properly blinded and a leaky double-blind paper, correct and flawed APA, AMA and IEEE papers, complete and flawed declarations, a diagnostic accuracy study, a humanities essay, a commentary, a trial protocol, a short communication, nine integrity red flags in one paper, formatting done right and wrong, LaTeX source (with and without a .bib file), a cover letter, a title page, and the basic checks.

```
python tests/test_parts.py     # rules, profiles and the text-parsing helpers
python tests/run_tests.py      # every paper under every profile
```

`run_tests.py` checks every paper under every profile, plus a test-only profile that switches every formatting requirement on (`tests/profiles/`). Expected results live in `tests/expected*.json`: the base results, the extras under double-blind review, under each citation style and under particular profiles. Each converted copy must give the same results as its Word original, apart from what its format can't show. `test_parts.py` also confirms that every one of the 95 rules is triggered by at least one test paper.

Current result: **every planted problem caught under all nine profiles, with no false alarms.** On GitHub, the same tests run automatically after every upload (the *Actions* tab shows a green tick when they pass).

To rebuild the test files: `make_test_papers.py`, `make_double_blind_papers.py`, `make_citation_papers.py`, `make_v2_papers.py`, then `make_converted.py` (needs LibreOffice), in that order.

## Changelog

**v2.0**
- Declarations for 2026: generative AI statement, CRediT roles, corresponding author, ORCID iDs and data repositories (for journals that require them), code availability, consent for publication in case reports, trial registered before the study started, Declaration of Helsinki, sex and gender reporting (SAGER), permission for reproduced figures, grant numbers.
- Reporting guidelines: study design detected and checked against CONSORT, SPIRIT, PRISMA, STROBE, CARE, ARRIVE, STARD, COREQ/SRQR, TRIPOD, CHEERS and SQUIRE (guideline named, key items present).
- Article types: short communication, commentary/editorial, study protocol, methods paper, data paper, book review and correction, each with its own required sections; more heading names recognised ("Method", "Experimental section", "Index Terms", "Works Cited"…). New humanities profile; APA and IEEE profiles adapted to their disciplines.
- Integrity red flags: tortured phrases, chatbot leftovers, hidden text and prompt injections, AI tool as author, free-mail addresses, percentage arithmetic, impossible values, self-citation share.
- Formatting: word, reference and figure limits per article type, title length, running title, abstract structure and headings, keyword count, highlights, line numbers, double spacing, page numbers, p-value style, US/UK spelling, numbers starting sentences.
- File formats: PDF, OpenDocument, RTF and LaTeX, alongside Word; title pages and cover letters recognised and checked as such.
- Report: how to fix and source for every rule; Author and Editor views; dismiss false alarms (left out of the downloads); Word report; files tagged with what they were read as.
- Fixes found by the new tests: guideline years ("STARD 2015") and "observers were trained" were misread; Chicago-style citations with page numbers ("Said 1978, 45") weren't matched.
- Tests: 36 papers and 16 converted copies under nine profiles; every rule exercised; tests run automatically on GitHub.
- The Streamlit app is retired: the website at thegreyswan.in/checker replaces it.

**v1.5**
- Citation and reference styles: author–date citations are now matched to the reference list (previously only numbered); numbered references must be cited in order; author–date lists must be alphabetical; mixed systems flagged; old references (advisory).
- New `citation_style` setting (APA 7, Harvard, AMA, Vancouver, IEEE) adding style-specific checks of the citation system, in-text form and reference-list format; four new style profiles.
- Fix: sentences are no longer split after abbreviations such as "approval no." or "et al.", which could hide an ethics approval number or date.
- Website: Reference style choice in the settings.
- Four new test papers.

**v1.4**
- Double-blind review: new anonymisation checks (title page, emails and ORCID iDs, author names in text, headers and footers, Word file properties, first-person self-citation, acknowledgements, named institutions). Placeholders such as "[blinded for review]" are recognised.
- Profiles have a `review_model` setting (single-blind, double-blind, open); new `generic_double_blind` profile.
- Every manuscript: tracked changes and comments left in the file are flagged.
- Website: Peer review choice in the settings.
- Two new test papers (properly blinded, and leaky).

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

- Rule-based: it can miss unusual phrasings and may raise false alarms. Treat results as flags for review, and use *dismiss* for false alarms.
- Reporting-guideline items, integrity flags and reference formats are pattern checks: a prompt to look, not proof.
- PDFs give a less complete check than Word files (no tracked changes, hidden-text colour, superscripts or layout); old .doc files can't be read.
- Does not check scientific content, language quality, plagiarism, image integrity, or references against external databases.

## Roadmap

- Reference validation against Crossref (invalid DOIs, retracted papers) — the planned references integrity tool
- Author verification via ORCID
- Publisher-specific profiles, verified against each publisher's current instructions

## How this was built

Built while learning Python, with AI assistance (Claude) for code generation and debugging. Design, screening rules and testing are my own.

## Data and ethics

The sample and test manuscripts are invented. No confidential or unpublished manuscripts were used in building or testing this tool.
