"""
Scores the checker against the labelled test papers.

For each paper it reports:
  caught       planted problems the checker found
  missed       planted problems it did not find
  false alarm  things it flagged that are not real problems

    python tests/run_tests.py            (run from the project folder)
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from checker import check_manuscript   # noqa: E402

expected_all = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
total_caught = total_missed = total_false = 0

for name, expected in expected_all.items():
    issues = check_manuscript(HERE / "papers" / name)
    found = {f"{section}|{check}": details for section, check, status, details in issues}
    expected = set(expected)
    caught = expected & found.keys()
    missed = expected - found.keys()
    false = found.keys() - expected
    total_caught += len(caught); total_missed += len(missed); total_false += len(false)

    mark = "PASS" if not missed and not false else "FAIL"
    print(f"\n[{mark}] {name}: {len(caught)}/{len(expected)} caught, {len(false)} false alarm(s)")
    for label in sorted(missed):
        print(f"   MISSED       {label}")
    for label in sorted(false):
        print(f"   FALSE ALARM  {label}: {found[label]}")

planted = total_caught + total_missed
flagged = total_caught + total_false
print("\n" + "=" * 60)
print(f"Planted problems caught: {total_caught}/{planted}"
      + (f" ({100 * total_caught / planted:.0f}%)" if planted else ""))
print(f"False alarms: {total_false}"
      + (f" ({100 * total_false / flagged:.0f}% of everything flagged)" if flagged else ""))
