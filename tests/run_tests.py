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

import yaml

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
from checker import check_manuscript, find_issues   # noqa: E402
from settings import list_profiles, load_profile, merge, check_profile   # noqa: E402

expected_all = json.loads((HERE / "expected.json").read_text(encoding="utf-8"))
# extra problems each paper should show under a double-blind profile (title pages, named institutions…)
extra_double_blind = json.loads((HERE / "expected_double_blind.json").read_text(encoding="utf-8"))
# extra problems each paper should show when a profile names a citation style (wrong system, format…)
extra_styles = json.loads((HERE / "expected_styles.json").read_text(encoding="utf-8"))
# papers whose expected results depend on the profile itself (e.g. a humanities essay under the humanities
# profile): these lists replace the paper's usual expected results for that profile
overrides = json.loads((HERE / "expected_profiles.json").read_text(encoding="utf-8"))
# problems a paper should show IN ADDITION under one profile (e.g. UK spelling under a US-spelling profile)
profile_extras = json.loads((HERE / "expected_profile_extras.json").read_text(encoding="utf-8"))


def test_profiles():
    """Test-only profiles in tests/profiles/: each lists the papers it runs on (test_papers)."""
    found = {}
    for path in sorted((HERE / "profiles").glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        papers = data.pop("test_papers")
        profile = merge(load_profile(data.pop("based_on", "generic")), data)
        profile["id"] = path.stem
        check_profile(profile)
        found[path.stem] = (profile, papers)
    return found


extra_profiles = test_profiles()

# Converted copies of some papers (tests/converted, made by make_converted.py) must get the same results as
# the Word original, plus the note on what the format can't show, minus what that format can't show:
FORMAT_LIMITS = {
    "pdf": {"Integrity|Hidden text", "Structure|Tracked changes / comments", "Formatting|Line numbers",
            "Formatting|Line spacing", "Formatting|Page numbers", "References|In-text citations"},
    "odt": {"Structure|Tracked changes / comments", "Formatting|Line numbers", "Formatting|Line spacing",
            "Formatting|Page numbers"},
    "rtf": {"Structure|Tracked changes / comments", "Formatting|Line numbers", "Formatting|Line spacing",
            "Formatting|Page numbers"},
}
converted = sorted((HERE / "converted").glob("*.*")) if (HERE / "converted").is_dir() else []
all_passed = True

for profile_id in list(list_profiles()) + list(extra_profiles):
    profile, only = extra_profiles.get(profile_id, (None, None))
    profile = profile or load_profile(profile_id)
    switched_off = {r for r, sev in profile.get("rules", {}).items() if sev == "off"}
    double_blind = profile.get("settings", {}).get("review_model") == "double_blind"
    style_extras = extra_styles.get(profile.get("settings", {}).get("citation_style", "auto"), {})
    total_caught = total_missed = total_false = 0
    print("\n" + "#" * 60 + f"\nProfile: {profile['name']} ({profile_id})")

    for name, expected in expected_all.items():
        if only is not None and name not in only:
            continue
        expected = overrides.get(profile_id, {}).get(name, expected)
        expected = list(expected) + profile_extras.get(profile_id, {}).get(name, [])
        paper = HERE / "papers" / name
        if not paper.exists():
            paper = next((HERE / "papers").glob(Path(name).stem + ".*"))
        issues = check_manuscript(paper, profile)
        found = {f"{i.section}|{i.check}": i.details for i in issues}
        # every issue before the profile is applied, to know which rule each label belongs to
        rule_of = {f"{i.section}|{i.check}": i.rule for i in find_issues(paper, profile)}
        expected = (set(expected) | (set(extra_double_blind.get(name, [])) if double_blind else set())
                    | set(style_extras.get(name, [])))
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

        # the same paper converted to PDF, ODT and RTF
        for copy in [c for c in converted if c.stem == Path(name).stem]:
            ext = copy.suffix[1:]
            got = {f"{i.section}|{i.check}" for i in check_manuscript(copy, profile)}
            want = (expected | {"Structure|File format"}) - FORMAT_LIMITS[ext]
            c_missed, c_false = (want - got) - FORMAT_LIMITS[ext], (got - want) - FORMAT_LIMITS[ext]
            c_missed = {m for m in c_missed if rule_of.get(m) not in switched_off}
            total_caught += len(want & got); total_missed += len(c_missed); total_false += len(c_false)
            if c_missed or c_false:
                all_passed = False
                print(f"\n[FAIL] {copy.name} (converted): differs from the Word original")
                for label in sorted(c_missed):
                    print(f"   MISSED       {label}")
                for label in sorted(c_false):
                    print(f"   FALSE ALARM  {label}")

    planted = total_caught + total_missed
    flagged = total_caught + total_false
    print("\n" + "=" * 60)
    print(f"Planted problems caught: {total_caught}/{planted}"
          + (f" ({100 * total_caught / planted:.0f}%)" if planted else ""))
    print(f"False alarms: {total_false}"
          + (f" ({100 * total_false / flagged:.0f}% of everything flagged)" if flagged else ""))

print("\nALL PROFILES PASS" if all_passed else "\nSOME TESTS FAILED")
sys.exit(0 if all_passed else 1)
