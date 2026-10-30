"""
The bridge between the website (web/) and the checker.

The website runs this Python inside the visitor's browser (with Pyodide), so manuscripts are
checked on their own computer and never uploaded anywhere. Every function here takes and
returns plain JSON text, which is easy to pass to and from JavaScript.
"""

import json
from pathlib import Path

import yaml

from checker import check_manuscript, build_workbook, verdict, counts
from settings import list_profiles, load_profile, merge, check_profile
from rules import RULES, SEVERITY_LABEL

UPLOADS = Path("/tmp/uploads")        # where the page puts uploaded files (in the browser's memory)
REPORT = Path("/tmp/screening_report.xlsx")


def catalogue():
    """Every profile and every rule, for building the sidebar."""
    return json.dumps({
        "profiles": [{"id": pid, "name": name} for pid, name in list_profiles().items()],
        "rules": [{"id": rid, "area": area, "label": label, "what": what}
                  for rid, (area, label, what) in RULES.items()],
        "severity_labels": SEVERITY_LABEL,
    })


def profile(profile_id):
    """One profile, combined with everything it is based on."""
    return json.dumps(load_profile(profile_id))


def read_profile(text, filename):
    """A profile file the visitor loaded (one saved from the page, or written by hand)."""
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise ValueError("this file doesn't look like a profile")
    parent = data.pop("based_on", None) or "generic"     # anything not set falls back to generic
    result = merge(load_profile(parent), data)
    result["id"] = Path(filename).stem
    result.setdefault("name", result["id"])
    result["based_on"] = parent
    check_profile(result)
    return json.dumps(result)


def save_profile(profile_json, base_json):
    """The adjusted profile as YAML, listing only what differs from the profile it started from."""
    current, base = json.loads(profile_json), json.loads(base_json)
    parent = base.get("based_on") if base["id"] not in list_profiles() else base["id"]
    parent_profile = load_profile(parent or "generic")
    out = {"name": current.get("name") or f"{base['name']} (adjusted)", "based_on": parent or "generic"}
    for part in ("settings", "required_sections", "rules"):
        changed = {k: v for k, v in current.get(part, {}).items() if parent_profile.get(part, {}).get(k) != v}
        if changed:
            out[part] = changed
    return yaml.safe_dump(out, sort_keys=False, allow_unicode=True)


def check(files_json, profile_json):
    """Check the uploaded files (already written to /tmp/uploads by the page) and build the Excel report."""
    files, prof = json.loads(files_json), json.loads(profile_json)    # files: [{"path", "name"}]
    check_profile(prof)
    results, out = [], []
    for f in files:
        name = f["name"]
        try:
            issues = check_manuscript(UPLOADS / f["path"], prof)
        except Exception as e:
            results.append((name, None))
            out.append({"name": name, "error": f"Could not read this file ({type(e).__name__})"})
            continue
        results.append((name, issues))
        out.append({"name": name, "verdict": verdict(issues), "counts": counts(issues),
                    "issues": [{"section": i.section, "check": i.check, "status": i.status,
                                "details": i.details, "rule": i.rule, "severity": i.severity}
                               for i in issues]})
    wb = build_workbook(results, prof.get("name", ""))
    has_report = bool(wb.sheetnames)
    if has_report:
        wb.save(REPORT)
    return json.dumps({"results": out, "report": str(REPORT) if has_report else None})
