"""
Manuscript Checker - abbreviation check
Checks abbreviations: used before being defined, never defined,
defined more than once, or defined but never used again.

The abstract and the main text are checked separately, because most
journals want abbreviations defined at first use in BOTH.

Results are grouped: one row per type of problem, listing every
abbreviation affected, the way a screener would write the comment.

How to run (in a terminal, from this folder):
    python step3_abbreviations.py my_manuscript.docx
"""

import sys
import re
from step1_split_sections import split_into_sections   # reuse your step 1 code
from settings import load_settings

# Abbreviations most journals don't require authors to define.
# Add journal-specific ones in settings.json -> "extra_ignore_abbreviations".
COMMON = {
    # general / places / organisations
    "WHO", "USA", "UK", "UN", "EU", "ID", "IDs", "OK", "UAE",
    # molecular biology basics
    "DNA", "RNA", "mRNA", "cDNA", "tRNA", "rRNA", "miRNA", "siRNA", "PCR", "qPCR",
    "RT-PCR", "RT-qPCR", "ELISA", "SDS", "SDS-PAGE", "PAGE", "PBS", "FBS", "BSA",
    "DMSO", "EDTA", "DMEM", "RPMI", "ATCC", "ATP", "ADP", "NADH", "NADPH", "HEPES",
    "pH", "UV", "IR", "NMR", "HPLC", "LC-MS", "GC-MS", "MS",
    # diseases and infections everyone knows
    "HIV", "AIDS", "COVID-19", "SARS-CoV-2",
    # statistics and software
    "SD", "SE", "SEM", "CI", "OR", "HR", "RR", "IQR", "ANOVA", "SPSS", "BMI",
}

# An abbreviation = a word with at least 2 capital letters, e.g. AMR, UTI, ESBLs, IL-6, mRNA, TNF-α
WORD_CHARS = r"[A-Za-z0-9\-α-ωΑ-Ω]"
ABBR = re.compile(r"(?<![\w\-])[a-z]?[A-Z]" + WORD_CHARS + r"*[A-Z]" + WORD_CHARS + r"*")

# A definition = an abbreviation alone inside brackets, e.g. "antimicrobial resistance (AMR)"
DEFINITION = re.compile(r"\(\s*(" + ABBR.pattern + r")\s*\)")

# Roman numerals like II, III, IV look like abbreviations but aren't
ROMAN = re.compile(r"^[IVXLC]+$")

# A chemical formula made of element symbols, e.g. NaCl, MgCl2, CO2, KH2PO4
CHEMICAL = re.compile(r"^(?:[A-Z][a-z]?\d*)+$")

# Sections we don't check for abbreviations
# (Author contributions is full of initials like "AA" and "BA")
SKIP = {"Front matter", "Keywords", "References", "Author contributions"}

# Lines that look like references even when the References heading wasn't found
REFERENCE_LINE = re.compile(r"^\[?\d+[.)\]]\s+\S.*\b(19|20)\d{2}\b|doi\s*:|doi\.org/|\bet al\.", re.IGNORECASE)


def base(word):
    """Treat plurals as the same abbreviation: ESBLs -> ESBL."""
    return word[:-1] if word.endswith("s") and word[:-1].isupper() else word


def looks_like_symbol(word):
    """Gene, cell line, chemical or brand names rather than abbreviations to define."""
    if any(ch.isdigit() for ch in word):                 # TP53, BRCA1, MCF-7, IC50, CO2
        return True
    if CHEMICAL.match(word) and any(ch.islower() for ch in word):   # NaCl, MgCl
        return True
    if re.search(r"[a-z]{2,}", word):                    # GraphPad, TRIzol
        return True
    return False


def mostly_capitals(text):
    """An all-caps line (a title or heading) is not normal running text."""
    letters = [ch for ch in text if ch.isalpha()]
    return len(letters) > 15 and sum(ch.isupper() for ch in letters) / len(letters) > 0.8


def scan(paragraphs, ignore, skip_symbols):
    """Go through the text in order and note where each abbreviation is used and defined."""
    defined_at = {}          # abbr -> position number of first definition
    times_defined = {}       # abbr -> how many definitions
    first_use = {}           # abbr -> position of first use OUTSIDE a definition
    uses = {}                # abbr -> how many uses outside a definition
    pos = 0                  # a running counter so we know what came first

    # First pass: everything the authors define. A symbol like TP53 that the authors
    # chose to define is then tracked like any other abbreviation.
    defined_anywhere = {base(m.group(1).rstrip("-")) for text in paragraphs
                        for m in DEFINITION.finditer(text)}

    for text in paragraphs:
        if mostly_capitals(text) or REFERENCE_LINE.search(text):
            continue
        def_spans = [m.span(1) for m in DEFINITION.finditer(text)]

        for m in ABBR.finditer(text):
            word = m.group(0).rstrip("-")
            if word in ignore or ROMAN.match(word):
                continue
            # skip codes like "IEC/2024/117" or "CTRI/2023/05": part of an ID, not an abbreviation
            if text[m.end():m.end() + 1] == "/" or re.match(r"-\d{3,}", text[m.end():]):
                continue
            is_definition = m.span() in def_spans
            if skip_symbols and looks_like_symbol(word) and base(word) not in defined_anywhere:
                continue
            abbr = base(word)
            pos += 1
            if is_definition:
                times_defined[abbr] = times_defined.get(abbr, 0) + 1
                defined_at.setdefault(abbr, pos)
            else:
                uses[abbr] = uses.get(abbr, 0) + 1
                first_use.setdefault(abbr, pos)

    return defined_at, times_defined, first_use, uses


def check_abbreviations(path, settings=None):
    settings = settings or load_settings()
    ignore = COMMON | set(settings.get("extra_ignore_abbreviations", []))
    skip_symbols = settings.get("skip_gene_and_chemical_symbols", True)
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
        defined_at, times_defined, first_use, uses = scan(paragraphs, ignore, skip_symbols)
        place = where.lower()

        not_defined = sorted(a for a in first_use if a not in defined_at)
        used_early = sorted(a for a in first_use if a in defined_at and first_use[a] < defined_at[a])
        twice = sorted(a for a, n in times_defined.items() if n > 1)
        unused = sorted(a for a in defined_at if uses.get(a, 0) == 0)

        if not_defined:
            issues.append((where, "Not defined", "Missing",
                           "Used but never defined: " + ", ".join(not_defined),
                           f"Please define the following abbreviations at first use in the {place}: "
                           + ", ".join(not_defined) + "."))
        if used_early:
            issues.append((where, "Used before definition", "Concern",
                           "Appear before their definition: " + ", ".join(used_early),
                           f"Please define the following abbreviations at their first use in the {place}: "
                           + ", ".join(used_early) + "."))
        if twice:
            issues.append((where, "Defined more than once", "Concern",
                           "Defined more than once: " + ", ".join(twice),
                           f"Please define each of the following only once in the {place} and use the "
                           "abbreviation thereafter: " + ", ".join(twice) + "."))
        if unused:
            issues.append((where, "Defined but not used", "Concern",
                           "Defined but never used again: " + ", ".join(unused),
                           f"Please consider spelling out the following terms, as their abbreviations are "
                           f"not used again in the {place}: " + ", ".join(unused) + "."))
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
