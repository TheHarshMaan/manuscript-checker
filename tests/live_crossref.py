"""
Checks the reference checker against the REAL Crossref API, with papers whose answers are known.
Needs the internet; runs on GitHub (see .github/workflows/tests.yml) and on your own computer.

    python tests/live_crossref.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import refcheck   # noqa: E402

CASES = [
    ("LeCun Y, Bengio Y, Hinton G. Deep learning. Nature. 2015;521(7553):436-44. doi:10.1038/nature14539",
     {"verified"}, "a correct reference"),
    ("Wakefield AJ, Murch SH, Anthony A, et al. Ileal-lymphoid-nodular hyperplasia, non-specific colitis, and pervasive "
     "developmental disorder in children. Lancet. 1998;351(9103):637-41. doi:10.1016/S0140-6736(97)11096-0",
     {"retracted"}, "the Wakefield MMR paper, retracted in 2010"),
    ("Mehra MR, Desai SS, Ruschitzka F, Patel AN. Hydroxychloroquine or chloroquine with or without a macrolide for "
     "treatment of COVID-19: a multinational registry analysis. Lancet. 2020. doi:10.1016/S0140-6736(20)31180-6",
     {"retracted"}, "the Surgisphere paper, retracted in 2020"),
    ("LeCun Y, Bengio Y, Hinton G. Deep learning. Nature. 2015;521:436-44. doi:10.9999/not.a.real.doi.2015",
     {"doi_not_found"}, "a DOI that doesn't exist"),
    ("Polack FP, Thomas SJ, Kitchin N, et al. Safety and efficacy of the BNT162b2 mRNA Covid-19 vaccine. "
     "N Engl J Med. 2020;383(27):2603-15.",
     {"doi_missing"}, "a reference without its DOI"),
]

crossref = refcheck.Crossref()
retraction_list = refcheck.load_retraction_list()
failures = []
for use_list in (True, False):
    print(f"\n--- {'with' if use_list else 'without'} the Retraction Watch list"
          f"{'' if retraction_list or not use_list else ' (not available yet: Crossref only)'}")
    refs = refcheck.extract(text="\n".join(f"{n}. {t}" for n, (t, _, _) in enumerate(CASES, start=1)))
    results = refcheck.check_all(refs, crossref, retraction_list if use_list else None, progress=lambda *_: None)
    for (text, want, why), r in zip(CASES, results):
        mark = "ok " if r["status"] in want else "FAIL"
        print(f"  {mark} {why}: {r['label']} — {r['details'][:150]}")
        if r["status"] not in want:
            failures.append(f"{why}: got {r['status']}")

# What Crossref returns, for reference when something changes
status, record = crossref.work("10.1016/s0140-6736(97)11096-0")
print("\nWakefield record:", status, "title:", (record or {}).get("title"), "| updated-by:", (record or {}).get("updated-by"))
print("Notices that update it:", [(i.get("DOI"), i.get("update-to")) for i in (crossref.updates("10.1016/s0140-6736(97)11096-0") or [])][:3])

if failures:
    print("\nFAILED:", *failures, sep="\n  ")
    sys.exit(1)
print("\nPASS: the real Crossref API gives the expected results")
