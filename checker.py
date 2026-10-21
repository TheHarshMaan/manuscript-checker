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
from step4_declarations import check_declarations, check_study_details, check_references

ABSTRACT_WORD_LIMIT = 250      # change to match the journal
CORE_SECTIONS = ["Abstract", "Keywords", "Introduction", "Methods", "Results", "Discussion", "References"]

# Order the report goes in, section by section
ORDER = ["Structure", "Abstract", "Abbreviations (Abstract)", "Abbreviations (Main text)",
         "Figures & tables", "Declarations", "Study details", "References"]


def check_manuscript(path):
    """Run every check. Returns a list of (section, check, status, details, comment)."""
    sections, doc = split_into_sections(path)
    issues = []

    # Structure: missing core sections
    found = {name for name, _ in sections}
    for s in CORE_SECTIONS:
        if s not in found:
            where = "Abstract" if s in ("Abstract", "Keywords") else "Structure"
            issues.append((where, f"{s} section", "Missing", f"No '{s}' heading found",
                           f"Please include a {s} section." if s != "Keywords"
                           else "Please include keywords below the abstract."))

    # Abstract word count
    abstract_words = sum(len(t.split()) for name, paras in sections if name == "Abstract" for t in paras)
    if abstract_words > ABSTRACT_WORD_LIMIT:
        issues.append(("Abstract", "Abstract length", "Concern",
                       f"Abstract is {abstract_words} words (limit {ABSTRACT_WORD_LIMIT})",
                       f"Please reduce the abstract to {ABSTRACT_WORD_LIMIT} words or fewer."))

    # Abbreviations
    for where, check, status, details, comment in check_abbreviations(path):
        issues.append((f"Abbreviations ({where})", check, status, details, comment))

    # Figures and tables
    _, _, fig_issues = check_figures_tables(path)
    for check, status, details, comment in fig_issues:
        issues.append(("Figures & tables", check, status, details, comment))

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
    headers = ["Section", "Check", "Status", "Details", "Comment for author"]
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
    for section, check, status, details, comment in issues:
        for col, value in enumerate([section, check, status, details, comment], start=1):
            c = ws.cell(row, col, value)
            c.border = BORDER
            c.alignment = WRAP
        ws.cell(row, 3).fill = FILLS.get(status, FILLS["Concern"])
        row += 1

    for col, width in zip("ABCDE", [24, 26, 11, 48, 70]):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A6"
    ws.auto_filter.ref = f"A5:E{max(row - 1, 5)}"


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

    wb = Workbook()
    wb.remove(wb.active)
    used_names = set()
    summary = []
    results = []          # (file name, issues) for Google Sheets

    for f in files:
        try:
            issues = check_manuscript(f)
        except Exception as e:
            print(f"  Skipped {f.name}: could not read it ({e})")
            summary.append((f.name, "Could not read", "", ""))
            continue
        ws = wb.create_sheet(safe_sheet_name(f.stem, used_names))
        write_sheet(ws, f.name, issues)
        verdict = "Ready" if not issues else "Needs revision"
        missing = sum(1 for i in issues if i[2] == "Missing")
        concern = sum(1 for i in issues if i[2] == "Concern")
        summary.append((f.name, verdict, missing, concern))
        results.append((f.name, issues))
        print(f"  {f.name}: {verdict} ({len(issues)} issues)")

    # A summary sheet first, when checking more than one manuscript
    if len(files) > 1:
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

    if to_sheets and results:
        from send_to_sheets import upload
        print()
        upload(results)


if __name__ == "__main__":
    main()
