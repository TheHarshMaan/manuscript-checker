"""
Scores the checker against the labelled test papers.

For each paper it reports:
  caught       planted problems the checker found
  missed       planted problems it did not find
  false alarm  things it flagged that are not real problems

    python tests/run_tests.py            (run from the project folder)

The papers are run against every profile. Profiles only change how serious an issue is,
or switch a rule off, so every rule a profile keeps on must still be caught, with no new false alarms.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from checker import check_manuscript, find_issues   # noqa: E402
from settings import list_profiles, load_profile   # noqa: E402

expected_all = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
all_passed = True

for profile_id in list_profiles():
    profile = load_profile(profile_id)
    switched_off = {r for r, sev in profile.get("rules", {}).items() if sev == "off"}
    total_caught = total_missed = total_false = 0
    print("\n" + "#" * 60 + f"\nProfile: {profile['name']} ({profile_id})")

    for name, expected in expected_all.items():
        paper = HERE / "papers" / name
        issues = check_manuscript(paper, profile)
        found = {f"{i.section}|{i.check}": i.details for i in issues}
        # every issue before the profile is applied, to know which rule each label belongs to
        rule_of = {f"{i.section}|{i.check}": i.rule for i in find_issues(paper, profile)}
        expected = set(expected)
        caught = expected & found.keys()
        missed = expected - found.keys()
        false = found.keys() - expected
        # A rule this profile switches off is allowed to go unreported
        missed = {m for m in missed if rule_of.get(m) not in switched_off}
        total_caught += len(caught); total_missed += len(missed); total_false += len(false)

        mark = "PASS" if not missed and not false else "FAIL"
        all_passed &= mark == "PASS"
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

print("\nALL PROFILES PASS" if all_passed else "\nSOME TESTS FAILED")
sys.exit(0 if all_passed else 1)
