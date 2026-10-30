"""
Manuscript Checker
Runs ALL checks against a journal profile and writes one Excel report.

How to run (in a terminal, from this folder):
    python checker.py my_manuscript.docx                 -> one manuscript
    python checker.py my_folder                          -> every .docx in the folder
    python checker.py my_folder --profile strict_screening   -> check against another profile
    python checker.py --profiles                         -> list the available profiles
    python checker.py my_folder --sheets                 -> also send results to Google Sheets

Profiles live in the profiles/ folder; settings.json picks the default one.
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
from settings import load_settings, list_profiles
from rules import Issue, SEVERITY_LABEL

# Order the report goes in, section by section; within a section, most serious first
ORDER = ["Structure", "Abstract", "Abbreviations (Abstract)", "Abbreviations (Main text)",
         "Figures & tables", "Declarations", "Study details", "References"]
SEVERITY_RANK = {"must": 0, "should": 1, "advisory": 2}


def find_issues(path, profile):
    """Run every check. Returns a list of Issues, before the profile's severities are applied."""
    settings = profile.get("settings", {})
    sections, doc = split_into_sections(path)
    found_issues = []

    # Structure: sections this profile requires for this type of article
    # (a combined "Results and discussion" counts as both)
    found = {name for name, _ in sections}
    if "Results and discussion" in found:
        found |= {"Results", "Discussion"}
    required = profile.get("required_sections", {}).get(article_type(sections), [])
    for s in required:
        if s not in found:
            where = "Abstract" if s in ("Abstract", "Keywords") else "Structure"
            rule = {"Abstract": "abstract_missing", "Keywords": "keywords_missing"}.get(s, "section_missing")
            found_issues.append(Issue(where, f"{s} section", "Missing", f"No '{s}' heading found", rule))

    # Abstract word count
    limit = int(settings.get("abstract_word_limit", 250))
    abstract_words = sum(len(t.split()) for name, paras in sections if name == "Abstract" for t in paras)
    if abstract_words > limit:
        found_issues.append(Issue("Abstract", "Abstract length", "Concern",
                                  f"Abstract is {abstract_words} words (limit {limit})", "abstract_length"))

    # Abbreviations
    for where, check, status, details, rule in check_abbreviations(path, settings):
        found_issues.append(Issue(f"Abbreviations ({where})", check, status, details, rule))

    # Figures and tables
    _, _, fig_issues = check_figures_tables(path)
    for check, status, details, rule in fig_issues:
        found_issues.append(Issue("Figures & tables", check, status, details, rule))

    # Declarations, study details, references
    for section, check, status, details, rule in (check_declarations(sections)
                                                  + check_study_details(sections, settings)
                                                  + check_references(sections)):
        found_issues.append(Issue(section, check, status, details, rule))
    return found_issues


def apply_profile(found_issues, profile):
    """Give each issue the severity the profile sets for its rule, and drop rules that are switched off."""
    rules = profile.get("rules", {})
    issues = []
    for issue in found_issues:
        severity = rules.get(issue.rule, "should")     # a rule the profile doesn't mention: Should fix
        if severity != "off":
            issues.append(issue._replace(severity=severity))
    issues.sort(key=lambda i: (ORDER.index(i.section) if i.section in ORDER else len(ORDER),
                               SEVERITY_RANK[i.severity]))
    return issues


def check_manuscript(path, profile=None):
    """Check one manuscript. `profile` is a profile dict (from settings.load_settings), a profile
    ID such as "strict_screening", or None for the default profile chosen in settings.json."""
    if not isinstance(profile, dict):
        profile = load_settings(profile)
    return apply_profile(find_issues(path, profile), profile)


def verdict(issues):
    """Ready unless something is Must fix or Should fix; advisories alone don't block."""
    return "Needs revision" if any(i.severity in ("must", "should") for i in issues) else "Ready"


def counts(issues):
    return {s: sum(1 for i in issues if i.severity == s) for s in ("must", "should", "advisory")}


# ---------------------------------------------------------------------------
# Excel formatting
# ---------------------------------------------------------------------------
FILLS = {
    "must":     PatternFill("solid", fgColor="F8CBAD"),   # red-ish
    "should":   PatternFill("solid", fgColor="FFE699"),   # amber
    "advisory": PatternFill("solid", fgColor="DDEBF7"),   # pale blue
    "OK":       PatternFill("solid", fgColor="C6EFCE"),   # green
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


def count_text(issues):
    c = counts(issues)
    return f"{len(issues)} total ({c['must']} must fix, {c['should']} should fix, {c['advisory']} advisory)"


def write_sheet(ws, filename, issues, profile_name):
    result = verdict(issues)

    # Summary block at the top
    ws["A1"] = "Manuscript"; ws["B1"] = filename
    ws["A2"] = "Profile";    ws["B2"] = profile_name
    ws["A3"] = "Result";     ws["B3"] = result
    ws["A4"] = "Issues";     ws["B4"] = count_text(issues)
    for r in range(1, 5):
        ws.cell(r, 1).font = Font(bold=True)
    ws["B3"].fill = FILLS["OK"] if result == "Ready" else FILLS["must"]
    ws["B3"].font = Font(bold=True)

    # Table header
    headers = ["Section", "Check", "Severity", "Status", "Details"]
    for col, h in enumerate(headers, start=1):
        c = ws.cell(6, col, h)
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = HEADER_FILL
        c.border = BORDER
        c.alignment = WRAP

    # One row per issue
    row = 7
    if not issues:
        ws.cell(row, 1, "All checks passed").font = Font(italic=True)
    for i in issues:
        values = [i.section, i.check, SEVERITY_LABEL[i.severity], i.status, i.details]
        for col, value in enumerate(values, start=1):
            c = ws.cell(row, col, value)
            c.border = BORDER
            c.alignment = WRAP
        ws.cell(row, 3).fill = FILLS[i.severity]
        row += 1

    for col, width in zip("ABCDE", [26, 28, 12, 11, 90]):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A7"
    ws.auto_filter.ref = f"A6:E{max(row - 1, 6)}"


def build_workbook(results, profile_name=""):
    """results = list of (file name, issues), where issues is None if the file couldn't be read.
    Returns an openpyxl Workbook: one sheet per manuscript, plus a Summary sheet for batches."""
    wb = Workbook()
    wb.remove(wb.active)
    used_names = set()
    summary = []
    for name, issues in results:
        if issues is None:
            summary.append((name, "Could not read", "", "", ""))
            continue
        ws = wb.create_sheet(safe_sheet_name(Path(name).stem, used_names))
        write_sheet(ws, name, issues, profile_name)
        c = counts(issues)
        summary.append((name, verdict(issues), c["must"], c["should"], c["advisory"]))

    if len(results) > 1:
        ws = wb.create_sheet("Summary", 0)
        for col, h in enumerate(["Manuscript", "Result", "Must fix", "Should fix", "Advisory"], start=1):
            c = ws.cell(1, col, h)
            c.font = Font(bold=True, color="FFFFFF")
            c.fill = HEADER_FILL
        for r, rowdata in enumerate(summary, start=2):
            for col, v in enumerate(rowdata, start=1):
                ws.cell(r, col, v)
            ws.cell(r, 2).fill = FILLS["OK"] if rowdata[1] == "Ready" else FILLS["must"]
        ws.cell(len(summary) + 3, 1, f"Profile: {profile_name}").font = Font(italic=True)
        ws.column_dimensions["A"].width = 45
        ws.column_dimensions["B"].width = 16
        for col in "CDE":
            ws.column_dimensions[col].width = 11
    return wb


def option(name):
    """The value after --name on the command line, e.g. --profile strict_screening."""
    if name in sys.argv:
        i = sys.argv.index(name)
        if i + 1 < len(sys.argv):
            return sys.argv[i + 1]
    return None


def main():
    if "--profiles" in sys.argv:
        print("Available profiles (use with --profile <id>):")
        for pid, pname in list_profiles().items():
            print(f"  {pid:<22} {pname}")
        return

    profile_id = option("--profile")
    args = [a for a in sys.argv[1:] if not a.startswith("--") and a != profile_id]
    to_sheets = "--sheets" in sys.argv
    if not args:
        print("Usage: python checker.py <manuscript.docx or folder> [--profile <id>] [--sheets]")
        print("       python checker.py --profiles")
        return

    target = Path(args[0])
    if target.is_dir():
        files = sorted(p for p in target.glob("*.docx") if not p.name.startswith("~$"))
    else:
        files = [target]
    if not files:
        print(f"No .docx files found in '{target}'.")
        return

    try:
        profile = load_settings(profile_id)
    except (FileNotFoundError, ValueError) as e:
        print(f"Profile problem: {e}")
        return
    print(f"Profile: {profile['name']}\n")

    results = []          # (file name, issues or None)
    for f in files:
        try:
            issues = check_manuscript(f, profile)
        except Exception as e:
            print(f"  Skipped {f.name}: could not read it ({e})")
            results.append((f.name, None))
            continue
        results.append((f.name, issues))
        c = counts(issues)
        print(f"  {f.name}: {verdict(issues)} "
              f"({c['must']} must fix, {c['should']} should fix, {c['advisory']} advisory)")

    wb = build_workbook(results, profile["name"])
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
        upload(readable, profile["name"])


if __name__ == "__main__":
    main()
