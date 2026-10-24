"""
Manuscript Checker - Milestone 3 (part 2)
Runs ALL checks and writes one Excel report.

How to run (in a terminal, from this folder):
    python checker.py my_manuscript.docx          -> one manuscript
    python checker.py my_folder                    -> every .docx in the folder
    python checker.py my_folder --sheets           -> also send results to Google Sheets

The report is saved as  screening_report.xlsx  in this folder.
"""

import sys
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from step1_split_sections import split_into_sections
from step2_figures_tables import check_figures_tables
from step3_abbreviations import check_abbreviations
from step4_declarations import check_declarations, check_study_details, check_references, article_type
from settings import load_settings

CORE_SECTIONS = ["Abstract", "Keywords", "Introduction", "Methods", "Results", "Discussion", "References"]
# Sections each type of article is expected to have
REQUIRED_SECTIONS = {
    "research":         CORE_SECTIONS,
    "case report":      ["Abstract", "Keywords", "Introduction", "Case presentation", "Discussion", "References"],
    "narrative review": ["Abstract", "Keywords", "Introduction", "References"],
    "letter":           ["References"],
}

# Order the report goes in, section by section
ORDER = ["Structure", "Abstract", "Abbreviations (Abstract)", "Abbreviations (Main text)",
         "Figures & tables", "Declarations", "Study details", "References"]


def check_manuscript(path, settings=None):
    """Run every check. Returns a list of (section, check, status, details).
    `settings` comes from settings.json unless the website passes its own."""
    settings = settings or load_settings()
    limit = settings["abstract_word_limit"]
    sections, doc = split_into_sections(path)
    issues = []

    # Structure: missing core sections (a combined "Results and discussion" counts as both)
    found = {name for name, _ in sections}
    if "Results and discussion" in found:
        found |= {"Results", "Discussion"}
    for s in REQUIRED_SECTIONS[article_type(sections)]:
        if s not in found:
            where = "Abstract" if s in ("Abstract", "Keywords") else "Structure"
            issues.append((where, f"{s} section", "Missing", f"No '{s}' heading found"))

    # Abstract word count
    abstract_words = sum(len(t.split()) for name, paras in sections if name == "Abstract" for t in paras)
    if abstract_words > limit:
        issues.append(("Abstract", "Abstract length", "Concern",
                       f"Abstract is {abstract_words} words (limit {limit})"))

    # Abbreviations
    for where, check, status, details in check_abbreviations(path, settings):
        issues.append((f"Abbreviations ({where})", check, status, details))

    # Figures and tables
    _, _, fig_issues = check_figures_tables(path)
    for check, status, details in fig_issues:
        issues.append(("Figures & tables", check, status, details))

    # Declarations, study details, references
    issues += check_declarations(sections)
    issues += check_study_details(sections)
    issues += check_references(sections)

    issues.sort(key=lambda i: ORDER.index(i[0]) if i[0] in ORDER else len(ORDER))
    return issues


# ---------------------------------------------------------------------------
# Excel formatting
# ---------------------------------------------------------------------------
FILLS = {
    "Missing": PatternFill("solid", fgColor="F8CBAD"),   # red-ish
    "Concern": PatternFill("solid", fgColor="FFE699"),   # amber
    "OK":      PatternFill("solid", fgColor="C6EFCE"),   # green
}
HEADER_FILL = PatternFill("solid", fgColor="1F3864")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")


def safe_sheet_name(name, used):
    """Excel sheet names: max 31 characters, no []:*?/\\ and must be unique."""
    for ch in "[]:*?/\\":
        name = name.replace(ch, "_")
    name = name[:28] or "Manuscript"
    candidate, n = name, 2
    while candidate in used:
        candidate, n = f"{name[:26]}_{n}", n + 1
    used.add(candidate)
    return candidate


def write_sheet(ws, filename, issues):
    missing = sum(1 for i in issues if i[2] == "Missing")
    concern = sum(1 for i in issues if i[2] == "Concern")
    verdict = "Ready" if not issues else "Needs revision"

    # Summary block at the top
    ws["A1"] = "Manuscript"; ws["B1"] = filename
    ws["A2"] = "Result";     ws["B2"] = verdict
    ws["A3"] = "Issues";     ws["B3"] = f"{len(issues)} total ({missing} missing, {concern} concern)"
    for r in range(1, 4):
        ws.cell(r, 1).font = Font(bold=True)
    ws["B2"].fill = FILLS["OK"] if verdict == "Ready" else FILLS["Missing"]
    ws["B2"].font = Font(bold=True)

    # Table header
    headers = ["Section", "Check", "Status", "Details"]
    for col, h in enumerate(headers, start=1):
        c = ws.cell(5, col, h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEADER_FILL
        c.border = BORDER
        c.alignment = WRAP

    # One row per issue
    row = 6
    if not issues:
        ws.cell(row, 1, "All checks passed").font = Font(italic=True)
    for section, check, status, details in issues:
        for col, value in enumerate([section, check, status, details], start=1):
            c = ws.cell(row, col, value)
            c.border = BORDER
            c.alignment = WRAP
        ws.cell(row, 3).fill = FILLS.get(status, FILLS["Concern"])
        row += 1

    for col, width in zip("ABCD", [26, 28, 11, 90]):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A6"
    ws.auto_filter.ref = f"A5:D{max(row - 1, 5)}"


def build_workbook(results):
    """results = list of (file name, issues), where issues is None if the file couldn't be read.
    Returns an openpyxl Workbook: one sheet per manuscript, plus a Summary sheet for batches."""
    wb = Workbook()
    wb.remove(wb.active)
    used_names = set()
    summary = []
    for name, issues in results:
        if issues is None:
            summary.append((name, "Could not read", "", ""))
            continue
        ws = wb.create_sheet(safe_sheet_name(Path(name).stem, used_names))
        write_sheet(ws, name, issues)
        summary.append((name, "Ready" if not issues else "Needs revision",
                        sum(1 for i in issues if i[2] == "Missing"),
                        sum(1 for i in issues if i[2] == "Concern")))

    if len(results) > 1:
        ws = wb.create_sheet("Summary", 0)
        for col, h in enumerate(["Manuscript", "Result", "Missing", "Concern"], start=1):
            c = ws.cell(1, col, h)
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = HEADER_FILL
        for r, rowdata in enumerate(summary, start=2):
            for col, v in enumerate(rowdata, start=1):
                ws.cell(r, col, v)
            ws.cell(r, 2).fill = FILLS["OK"] if rowdata[1] == "Ready" else FILLS["Missing"]
        ws.column_dimensions["A"].width = 45
        ws.column_dimensions["B"].width = 16
    return wb


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    to_sheets = "--sheets" in sys.argv
    if not args:
        print("Usage: python checker.py <manuscript.docx or folder> [--sheets]")
        return

    target = Path(args[0])
    if target.is_dir():
        files = sorted(p for p in target.glob("*.docx") if not p.name.startswith("~$"))
    else:
        files = [target]
    if not files:
        print(f"No .docx files found in '{target}'.")
        return

    settings = load_settings()
    results = []          # (file name, issues or None)
    for f in files:
        try:
            issues = check_manuscript(f, settings)
        except Exception as e:
            print(f"  Skipped {f.name}: could not read it ({e})")
            results.append((f.name, None))
            continue
        results.append((f.name, issues))
        print(f"  {f.name}: {'Ready' if not issues else 'Needs revision'} ({len(issues)} issues)")

    wb = build_workbook(results)
    if not wb.sheetnames:
        print("Nothing to save.")
        return

    out = Path("screening_report.xlsx")
    try:
        wb.save(out)
    except PermissionError:
        print("Could not save: close screening_report.xlsx in Excel and run again.")
        return
    print(f"\nReport saved: {out.resolve()}")

    readable = [(name, issues) for name, issues in results if issues is not None]
    if to_sheets and readable:
        from send_to_sheets import upload
        print()
        upload(readable)


if __name__ == "__main__":
    main()
