"""
Sends screening results to a Google Sheet.

The sheet gets two tabs, created automatically on first run:
  - "Summary": one row per manuscript checked
  - "Issues":  one row per issue found
New runs are ADDED below the old rows, so the sheet becomes a running log.

Setup (once): see the steps in the chat / README.
  1. Put your Google key file in this folder and name it  google_key.json
  2. Paste your Google Sheet's link below.
  3. Share the sheet with the "client_email" from google_key.json (as Editor).
"""

from datetime import datetime
from pathlib import Path

# >>> Paste the link to your Google Sheet here, between the quotes <<<
SHEET_URL = "PASTE_YOUR_GOOGLE_SHEET_LINK_HERE"

KEY_FILE = Path(__file__).with_name("google_key.json")

# If your sheet was created by an older version of the checker, delete or rename its
# "Summary" and "Issues" tabs once, so they are recreated with these columns.
SUMMARY_HEADERS = ["Date checked", "Manuscript", "Profile", "Result", "Must fix", "Should fix", "Advisory"]
ISSUE_HEADERS = ["Date checked", "Manuscript", "Profile", "Section", "Check", "Severity", "Status",
                 "Details"]

COLOURS = {
    "Must fix":       {"red": 0.97, "green": 0.80, "blue": 0.68},
    "Should fix":     {"red": 1.00, "green": 0.90, "blue": 0.60},
    "Advisory":       {"red": 0.87, "green": 0.92, "blue": 0.97},
    "Ready":          {"red": 0.78, "green": 0.94, "blue": 0.81},
    "Needs revision": {"red": 0.97, "green": 0.80, "blue": 0.68},
}


def colour_rule(sheet_id, column, text, colour):
    """A Google Sheets rule: colour a cell in this column when it says `text`."""
    return {"addConditionalFormatRule": {"index": 0, "rule": {
        "ranges": [{"sheetId": sheet_id, "startRowIndex": 1,
                    "startColumnIndex": column, "endColumnIndex": column + 1}],
        "booleanRule": {
            "condition": {"type": "TEXT_EQ", "values": [{"userEnteredValue": text}]},
            "format": {"backgroundColor": colour}},
    }}}


def get_tab(spreadsheet, title, headers, status_column, statuses):
    """Open a tab, or create it with headers and colours if it doesn't exist yet."""
    import gspread
    try:
        return spreadsheet.worksheet(title)
    except gspread.exceptions.WorksheetNotFound:
        pass

    ws = spreadsheet.add_worksheet(title=title, rows=1000, cols=len(headers))
    ws.append_row(headers)
    ws.format(f"A1:{chr(64 + len(headers))}1", {
        "textFormat": {"bold": True, "foregroundColor": {"red": 1, "green": 1, "blue": 1}},
        "backgroundColor": {"red": 0.12, "green": 0.22, "blue": 0.39},
    })
    ws.freeze(rows=1)
    spreadsheet.batch_update({"requests": [
        colour_rule(ws.id, status_column, s, COLOURS[s]) for s in statuses
    ]})
    return ws


def upload(results, profile_name=""):
    """results = list of (manuscript file name, list of issues); profile_name = the profile used."""
    from checker import verdict, counts
    from rules import SEVERITY_LABEL
    try:
        import gspread
    except ImportError:
        print("Google Sheets: run  pip install gspread  first.")
        return False
    if "PASTE_YOUR" in SHEET_URL:
        print("Google Sheets: paste your sheet link into SHEET_URL in send_to_sheets.py.")
        return False
    if not KEY_FILE.exists():
        print(f"Google Sheets: key file not found. Put it here: {KEY_FILE}")
        return False

    try:
        client = gspread.service_account(filename=str(KEY_FILE))
        spreadsheet = client.open_by_url(SHEET_URL)
    except gspread.exceptions.SpreadsheetNotFound:
        print("Google Sheets: can't open the sheet. Did you share it (as Editor) with the "
              "client_email in google_key.json?")
        return False
    except Exception as e:
        print(f"Google Sheets: could not connect ({e})")
        return False

    summary_tab = get_tab(spreadsheet, "Summary", SUMMARY_HEADERS, 3, ["Ready", "Needs revision"])
    issues_tab = get_tab(spreadsheet, "Issues", ISSUE_HEADERS, 5, ["Must fix", "Should fix", "Advisory"])

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    summary_rows, issue_rows = [], []
    for name, issues in results:
        c = counts(issues)
        summary_rows.append([now, name, profile_name, verdict(issues), c["must"], c["should"], c["advisory"]])
        for i in issues:
            issue_rows.append([now, name, profile_name, i.section, i.check,
                               SEVERITY_LABEL[i.severity], i.status, i.details])

    summary_tab.append_rows(summary_rows)
    if issue_rows:
        issues_tab.append_rows(issue_rows)

    # Remove the empty default "Sheet1" tab, if it's still there and empty
    try:
        default = spreadsheet.worksheet("Sheet1")
        if not any(default.get_all_values()):
            spreadsheet.del_worksheet(default)
    except Exception:
        pass

    print(f"Google Sheets: added {len(summary_rows)} manuscript(s), {len(issue_rows)} issue row(s).")
    print(f"Open: {SHEET_URL}")
    return True
