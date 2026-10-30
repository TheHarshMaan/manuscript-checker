"""
Tests for the reference integrity checker (refcheck.py), with saved Crossref answers instead of the internet.

    python tests/test_references.py          (run from the project folder)

Each test reference has the result it should get. The Crossref answers are in
tests/references/crossref_answers.json; the Retraction Watch list is built from a small sample of the real
file's format (tests/references/retraction_watch_sample.csv). live_crossref.py checks the real API.
"""

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
import refcheck                                  # noqa: E402
from build_retractions import build             # noqa: E402

ANSWERS = json.loads((HERE / "references" / "crossref_answers.json").read_text(encoding="utf-8"))


class SavedCrossref:
    """Same questions as refcheck.Crossref, answered from crossref_answers.json."""

    def __init__(self):
        self.asked = []

    def work(self, doi):
        self.asked.append(("work", doi))
        answer = ANSWERS["work"].get(doi, {"status": 404, "message": None})
        return answer["status"], answer["message"]

    def search(self, query):
        self.asked.append(("search", query))
        for key, items in ANSWERS["search"].items():
            if key.lower() in query.lower():
                return items
        return []

    def updates(self, doi):
        self.asked.append(("updates", doi))
        return ANSWERS["updates"].get(doi, [])


# (reference, expected status, why)
CASES = [
    ("LeCun Y, Bengio Y, Hinton G. Deep learning. Nature. 2015;521(7553):436-44. doi:10.1038/nature14539",
     "verified", "correct reference with its DOI"),
    ("Wakefield AJ, Murch SH, Anthony A, et al. Ileal-lymphoid-nodular hyperplasia, non-specific colitis, and "
     "pervasive developmental disorder in children. Lancet. 1998;351(9103):637-41. doi:10.1016/S0140-6736(97)11096-0",
     "retracted", "retracted (Retraction Watch list)"),
    ("Mehra MR, Desai SS, Ruschitzka F, Patel AN. Hydroxychloroquine or chloroquine with or without a macrolide for "
     "treatment of COVID-19: a multinational registry analysis. Lancet. 2020. doi:10.1016/S0140-6736(20)31180-6",
     "retracted", "retracted (found through Crossref's notices, not in the sample list)"),
    ("LeCun Y, Bengio Y, Hinton G. Deep learning. Nature. 2015;521:436-44. doi:10.1038/nature14593",
     "doi_not_found", "typo in the DOI (digits swapped); the right DOI is suggested"),
    ("Garcia M, Lee K. Hand hygiene compliance among nurses in district hospitals. J Hosp Infect. 2021;110:1-8. "
     "doi:10.1038/nature14539",
     "mismatch", "a real DOI pasted onto the wrong reference"),
    ("Polack FP, Thomas SJ, Kitchin N, et al. Safety and efficacy of the BNT162b2 mRNA Covid-19 vaccine. "
     "N Engl J Med. 2020;383(27):2603-15.",
     "doi_missing", "no DOI given, but Crossref has one"),
    ("Sharma P, Verma R. Quantum hand hygiene interventions reduce surgical site infection by 90%. "
     "Int J Adv Infect Sci. 2023;12(4):455-61.",
     "not_found", "invented reference: nothing close in Crossref"),
    ("Said, Edward W. 1978. Orientalism. New York: Pantheon.",
     "not_checked", "a book: not in Crossref, so not flagged"),
    ("World Health Organization. Global tuberculosis report 2023. Geneva: WHO; 2023.",
     "not_checked", "a report"),
    ("LeCun Y, Bengio Y, Hinton G. Deep learning. Nature. 2012;521:436-44. doi:10.1038/nature14539",
     "details", "year wrong (2012 instead of 2015)"),
    ("Author A. Sample paper with a correction. Example Journal. 2021;7:1-5. doi:10.5555/example.2021.7",
     "corrected", "correction notice"),
    ("Author B. Sample paper under an expression of concern. Example Journal. 2020;3:1-5. doi:10.5555/example.2020.3",
     "concern", "expression of concern"),
    ("Author C. Sample paper retracted then reinstated. Example Journal. 2018;9:1-5. doi:10.5555/example.2018.9",
     "reinstated", "retracted in 2019, reinstated in 2020"),
    ("Author D. A paper on a server that's down. Example Journal. 2022;1:1-5. doi:10.1000/server.down",
     "error", "Crossref doesn't answer"),
]

failures = []
with tempfile.TemporaryDirectory() as tmp:
    sample = Path(tmp) / "retractions.json.gz"
    build(HERE / "references" / "retraction_watch_sample.csv", sample, minimum=1)
    retraction_list = refcheck.load_retraction_list(sample)

    refs = refcheck.extract(text="\n".join(f"{n}. {text}" for n, (text, _, _) in enumerate(CASES, start=1)))
    if len(refs) != len(CASES):
        failures.append(f"read {len(refs)} references from the list, expected {len(CASES)}")

    crossref = SavedCrossref()
    results = refcheck.check_all(refs, crossref, retraction_list, progress=lambda *_: None)
    # with the list available, Crossref's notices aren't asked for…
    if any(kind == "updates" for kind, _ in crossref.asked):
        failures.append("asked Crossref for notices although the Retraction Watch list was available")
    # and without the list, Crossref's notices are used instead
    results_no_list = refcheck.check_all(refs, SavedCrossref(), None, progress=lambda *_: None)

for (text, want, why), got, got_no_list in zip(CASES, results, results_no_list):
    for mode, r in (("with the Retraction Watch list", got), ("with Crossref's notices only", got_no_list)):
        if r["status"] != want:
            failures.append(f"{why}, {mode}: got '{r['status']}' ({r['details']}), expected '{want}'")
    print(f"  ok  {want:<14} {why}" if got["status"] == want == got_no_list["status"] else f"  --  {why}")

# The Surgisphere paper isn't in the sample list: with the list, it's caught by the "RETRACTED:" title;
# without it, by Crossref's notice (which gives the date and the notice's DOI)
surgisphere = [r for r in results + results_no_list if "31180-6" in r["text"]]
if "title" not in surgisphere[0]["details"] or "2020-06-05" not in surgisphere[1]["details"]:
    failures.append(f"Surgisphere: {surgisphere[0]['details']} / {surgisphere[1]['details']}")

typo = next(r for r in results if r["status"] == "doi_not_found")
if "10.1038/nature14539" not in typo["details"]:
    failures.append(f"typo'd DOI: the right DOI wasn't suggested ({typo['details']})")
missing = next(r for r in results if r["status"] == "doi_missing")
if missing["doi"] != "10.1056/nejmoa2034577":
    failures.append(f"missing DOI: suggested {missing['doi']}")

# Reports build
wb = refcheck.build_excel(results, "test references")
doc = refcheck.build_word(results, "test references")
if wb["References"].max_row < len(CASES) + 5 or len(doc.tables[0].rows) != len(CASES) + 1:
    failures.append("the reports don't list every reference")

# A manuscript: the checker's own test paper 20 (numbered references, no DOIs)
paper_refs = refcheck.extract(HERE / "papers" / "20_declarations_flawed_trial.docx", "20_declarations_flawed_trial.docx")
if len(paper_refs) != 4 or any(r["doi"] for r in paper_refs):
    failures.append(f"reading test paper 20: {len(paper_refs)} references")

if failures:
    print("\nFAILED:")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print(f"\nPASS: all {len(CASES)} reference cases, suggestions and reports")
