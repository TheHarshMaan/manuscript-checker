"""
Small tests for the parts the checks are built from, and for the rule catalogue staying consistent.

    python tests/test_parts.py          (run from the project folder; prints PASS or what failed)
"""

import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from rules import RULES, FIXES, SEVERITIES, REVIEW_MODELS, CITATION_STYLES   # noqa: E402
from settings import list_profiles, load_profile                            # noqa: E402
from step4_declarations import split_sentences                             # noqa: E402
from step6_citations import author_date_citations, numbered_citations, entry_key   # noqa: E402
from step7_policies import study_start                                     # noqa: E402
from step9_integrity import percentage_mismatches, impossible_values, TORTURED_RE  # noqa: E402
from step10_formatting import US_UK, IZE                                   # noqa: E402

failures = []


def expect(name, got, want):
    if got != want:
        failures.append(f"{name}: got {got!r}, expected {want!r}")


# ---------------------------------------------------------------------------
# The rule catalogue and the profiles agree
generic = load_profile("generic")
for rule in RULES:
    if rule not in generic["rules"]:
        failures.append(f"rule '{rule}' has no severity in profiles/generic.yaml")
    if rule not in FIXES:
        failures.append(f"rule '{rule}' has no 'how to fix' entry in rules.FIXES")
for profile_id in list_profiles():
    profile = load_profile(profile_id)           # raises on unknown rules, severities or settings
    if not profile.get("name") or not profile.get("description"):
        failures.append(f"profile '{profile_id}' needs a name and a description")

# every rule ID the checks report exists in the catalogue: run every test paper through every profile
# (with all formatting requirements switched on too) and collect what is reported
from checker import find_issues            # noqa: E402
from settings import merge                 # noqa: E402
import yaml                                # noqa: E402
profiles = [load_profile(p) for p in list_profiles()]
for path in sorted((HERE / "profiles").glob("*.yaml")):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data.pop("test_papers", None)
    profiles.append(merge(load_profile(data.pop("based_on", "generic")), data))
papers = sorted((HERE / "papers").glob("*.*")) + sorted((HERE / "converted").glob("*.*"))
reported = set()
for profile in profiles:
    for paper in papers:
        reported |= {i.rule for i in find_issues(paper, profile)}
unknown = sorted(reported - set(RULES))
if unknown:
    failures.append(f"checks report rule IDs that aren't in rules.py: {unknown}")
never = sorted(set(RULES) - reported)

# ---------------------------------------------------------------------------
# Sentence splitting keeps abbreviations together
expect("split after 'no.'", len(split_sentences("Approved (approval no. 45, dated 2 May 2024). Consent was written.")), 2)
expect("split after 'et al.'", len(split_sentences("Smith et al. reported this. It was large.")), 2)
expect("split after 'Fig.'", len(split_sentences("See Fig. 2 for details. Done.")), 2)

# Citations
expect("numbered ranges", numbered_citations("as shown [1-3] and [5, 7]"), [1, 2, 3, 5, 7])
ad = author_date_citations("(Smith & Lee, 2020; WHO, 2021a) and Garcia et al. (2019) and (Said 1978, 45) "
                           "and (January 2020) and (n = 2020)")
expect("author-date keys", sorted((a, y) for a, y, *_ in ad),
       [("garcia", "2019"), ("said", "1978"), ("smith", "2020"), ("who", "2021a")])
expect("APA entry key", entry_key("Chen, L., & Park, S. (2021). Title. Journal, 1, 1."), ("chen", "2021"))
expect("Vancouver entry key", entry_key("3. Davey P, Marwick CA. Title. Cochrane Database Syst Rev. 2017."), ("davey", "2017"))

# Study dates
expect("study start (month)", study_start("conducted between January 2024 and June 2024"), (2024, 1))
expect("study start (year)", study_start("data from 2019 to 2021"), (2019, None))

# Integrity
expect("percentage ok", percentage_mismatches("Of the 312 nurses, 241 (77.2%) were women."), [])
expect("percentage wrong", len(percentage_mismatches("45/120 (40.0%) improved")), 1)
expect("impossible p", impossible_values("p = 1.5 and p < 0.001"), ["“p = 1.5”"])
expect("150% increase is fine", impossible_values("a 150% increase"), [])
expect("tortured phrase", TORTURED_RE.search("Counterfeit consciousness is new").group(1).lower(),
       "counterfeit consciousness")

# Spelling: laboratory and literature are not "labor" and "liter"; proper nouns don't count
text = "The laboratory literature at Erasmus Medical Center on tumour and tumor; randomised and randomized."
us = [w for a, b in US_UK for w in re.findall(rf"\b(?:{a})\b", text)] + \
     [m.group(0) for m in IZE.finditer(text) if m.group(2) == "z"]
uk = [w for a, b in US_UK for w in re.findall(rf"\b(?:{b})\b", text)] + \
     [m.group(0) for m in IZE.finditer(text) if m.group(2) == "s"]
expect("US spellings", sorted(us), ["randomized", "tumor"])
expect("UK spellings", sorted(uk), ["randomised", "tumour"])

# Settings lists are complete
expect("review models", sorted(REVIEW_MODELS), ["double_blind", "open", "single_blind"])
expect("citation styles", sorted(CITATION_STYLES), ["ama", "apa", "auto", "harvard", "ieee", "vancouver"])
expect("severities", SEVERITIES, ["must", "should", "advisory", "off"])

if failures:
    print("FAILED:")
    for f in failures:
        print("  " + f)
    sys.exit(1)
print(f"PASS: {len(RULES)} rules, {len(list_profiles())} profiles and the parsing helpers all check out")
print(f"Rules reported at least once by the test papers: {len(set(RULES) - set(never))} of {len(RULES)}"
      + (f" (never: {', '.join(never)})" if never else ""))
