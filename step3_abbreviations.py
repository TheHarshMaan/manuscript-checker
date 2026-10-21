"""
Manuscript Checker - Milestone 2 (part 2)
Checks abbreviations: used before being defined, never defined,
defined more than once, or defined but never used again.

The abstract and the main text are checked separately, because most
journals want abbreviations defined at first use in BOTH.

How to run (in a terminal, from this folder):
    python step3_abbreviations.py my_manuscript.docx
"""

import sys
import re
from step1_split_sections import split_into_sections   # reuse your step 1 code

# Abbreviations nobody needs to define. Add or remove as you like.
IGNORE = {
    "DNA", "RNA", "mRNA", "PCR", "HIV", "AIDS", "COVID-19", "SARS-CoV-2",
    "WHO", "USA", "UK", "UN", "EU", "ID", "IDs", "OK",
}

# An abbreviation = a word with at least 2 capital letters, e.g. AMR, UTI, ESBLs, IL-6, mRNA
ABBR = re.compile(r"\b[a-z]?[A-Z][A-Za-z0-9\-]*[A-Z][A-Za-z0-9\-]*\b")

# A definition = an abbreviation alone inside brackets, e.g. "antimicrobial resistance (AMR)"
DEFINITION = re.compile(r"\(\s*(" + ABBR.pattern + r")\s*\)")

# Roman numerals like II, III, IV look like abbreviations but aren't
ROMAN = re.compile(r"^[IVXLC]+$")

# Sections we don't check for abbreviations
# (Author contributions is full of initials like "AA" and "BA")
SKIP = {"Front matter", "Keywords", "References", "Author contributions"}


def base(word):
    """Treat plurals as the same abbreviation: ESBLs -> ESBL."""
    return word[:-1] if word.endswith("s") and word[:-1].isupper() else word


def scan(paragraphs):
    """Go through the text in order and note where each abbreviation is used and defined."""
    defined_at = {}          # abbr -> position number of first definition
    times_defined = {}       # abbr -> how many definitions
    first_use = {}           # abbr -> position of first use OUTSIDE a definition
    uses = {}                # abbr -> how many uses outside a definition
    pos = 0                  # a running counter so we know what came first

    for text in paragraphs:
        def_spans = []
        for m in DEFINITION.finditer(text):
            def_spans.append(m.span(1))

        for m in ABBR.finditer(text):
            word = m.group(0)
            if word in IGNORE or ROMAN.match(word):
                continue
            # skip codes like "IEC/2024/117" or "CTRI/2023/05": part of an ID, not an abbreviation
            if text[m.end():m.end() + 1] == "/" or re.match(r"-\d{3,}", text[m.end():]):
                continue
            abbr = base(word)
            pos += 1
            if m.span() in def_spans:                        # this is a definition
                times_defined[abbr] = times_defined.get(abbr, 0) + 1
                defined_at.setdefault(abbr, pos)
            else:                                            # this is a use
                uses[abbr] = uses.get(abbr, 0) + 1
                first_use.setdefault(abbr, pos)

    return defined_at, times_defined, first_use, uses


def check_abbreviations(path):
    sections, _ = split_into_sections(path)

    parts = {
        "Abstract": [t for name, paras in sections if name == "Abstract" for t in paras],
        "Main text": [t for name, paras in sections
                      if name not in SKIP and name != "Abstract" for t in paras],
    }

    issues = []   # (where, check, status, details, comment for author)

    for where, paragraphs in parts.items():
        if not paragraphs:
            continue
        defined_at, times_defined, first_use, uses = scan(paragraphs)

        for abbr in sorted(set(first_use) | set(defined_at)):
            if abbr in first_use and abbr not in defined_at:
                issues.append((where, "Not defined", "Missing",
                               f"'{abbr}' is used but never defined",
                               f"Please define the abbreviation '{abbr}' at first use"
                               f" in the {where.lower()}."))
            elif abbr in first_use and first_use[abbr] < defined_at[abbr]:
                issues.append((where, "Used before definition", "Concern",
                               f"'{abbr}' appears before it is defined",
                               f"Please define the abbreviation '{abbr}' at its first use"
                               f" in the {where.lower()}."))
            if times_defined.get(abbr, 0) > 1:
                issues.append((where, "Defined more than once", "Concern",
                               f"'{abbr}' is defined {times_defined[abbr]} times",
                               f"Please define '{abbr}' only once in the {where.lower()}"
                               f" and use the abbreviation thereafter."))
            if abbr in defined_at and uses.get(abbr, 0) == 0:
                issues.append((where, "Defined but not used", "Concern",
                               f"'{abbr}' is defined but never used again",
                               f"Please consider spelling out the term instead of"
                               f" abbreviating it as '{abbr}', as it is not used again"
                               f" in the {where.lower()}."))
    return issues


def main():
    if len(sys.argv) < 2:
        print("Usage: python step3_abbreviations.py <manuscript.docx>")
        return

    path = sys.argv[1]
    try:
        issues = check_abbreviations(path)
    except Exception as e:
        print(f"Could not read '{path}': {e}")
        return

    print(f"\nFile: {path}\n")
    if not issues:
        print("No abbreviation issues found.")
        return

    print(f"{len(issues)} issue(s):\n")
    for where, check, status, details, comment in issues:
        print(f"[{status}] {where} - {check}: {details}")
        print(f"    -> {comment}\n")


if __name__ == "__main__":
    main()
