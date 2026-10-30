"""
Builds data/retractions.json.gz, the compact list of retracted and corrected papers the reference
checker uses, from the Retraction Watch database (published by Crossref, updated every working day).

    git clone --depth 1 https://gitlab.com/crossref/retraction-watch-data rw
    python build_retractions.py rw/retraction_watch.csv [output path]

A GitHub Action (.github/workflows/retractions.yml) does this every day and publishes the result on this
repository's "retraction-data" branch, where the website and the command line read it.

Format: {"built": "2026-10-30", "source": …, "count": N,
         "notices": {"10.1016/s0140-6736(97)11096-0": [["R", "2010-02-02", "10.1016/s0140-6736(10)60175-4"]], …}}
Codes: R retraction, E expression of concern, C correction, I reinstatement.
Data: Retraction Watch Database, Center for Scientific Integrity, via Crossref (https://www.crossref.org/).
"""

import csv
import gzip
import json
import sys
from datetime import date, datetime
from pathlib import Path

CODES = {"retraction": "R", "expression of concern": "E", "correction": "C", "reinstatement": "I"}
REQUIRED = ["OriginalPaperDOI", "RetractionNature", "RetractionDate", "RetractionDOI"]


def iso(value):
    value = (value or "").strip()
    for fmt in ("%m/%d/%Y %H:%M", "%m/%d/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass
    return value.split(" ")[0]


def clean_doi(value):
    value = (value or "").strip().lower()
    for prefix in ("https://doi.org/", "http://dx.doi.org/", "doi:"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value if value.startswith("10.") else ""


def build(csv_path, out_path="retractions.json.gz", minimum=10000):
    text = Path(csv_path).read_bytes().decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(text.splitlines())
    missing = [c for c in REQUIRED if c not in (reader.fieldnames or [])]
    if missing:
        raise SystemExit(f"The Retraction Watch file has changed: columns missing: {missing}")
    notices = {}
    for row in reader:
        doi = clean_doi(row["OriginalPaperDOI"])
        code = CODES.get((row["RetractionNature"] or "").strip().lower())
        if not doi or not code:
            continue
        entry = [code, iso(row["RetractionDate"]), clean_doi(row["RetractionDOI"])]
        if entry not in notices.setdefault(doi, []):
            notices[doi].append(entry)
    if len(notices) < minimum:
        raise SystemExit(f"Only {len(notices)} papers found; expected at least {minimum}. Not saving.")
    out = {"built": date.today().isoformat(), "count": len(notices),
           "source": "Retraction Watch Database (Center for Scientific Integrity), via Crossref",
           "notices": notices}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(out, separators=(",", ":"), sort_keys=True).encode("utf-8")
    with open(out_path, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0) as gz:   # no timestamp inside the file
        gz.write(data)
    print(f"Saved {out_path}: {len(notices)} papers with notices")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
    else:
        build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "retractions.json.gz",
              minimum=int(sys.argv[3]) if len(sys.argv) > 3 else 10000)
