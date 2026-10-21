"""
Manuscript Checker - Milestone 1
Reads a .docx manuscript and splits it into sections.

How to run (in a terminal, from this folder):
    python step1_split_sections.py my_manuscript.docx
"""

import sys
import re
from docx import Document

# Section names we look for. Each key is the "official" name;
# the list holds other ways authors write it.
SECTION_NAMES = {
    "Abstract":              ["abstract", "summary"],
    "Keywords":              ["keywords", "key words"],
    "Introduction":          ["introduction", "background"],
    "Methods":               ["methods", "materials and methods", "methodology",
                              "patients and methods", "methods and materials"],
    "Results":               ["results", "findings"],
       "Discussion":          ["discussion", "results and discussion", "comment"],
    "Conclusion":            ["conclusion", "conclusions"],
    "Acknowledgements":      ["acknowledgements", "acknowledgments", "acknowledgement"],
    "Funding":               ["funding", "funding statement", "financial support"],
    "Conflict of interest":  ["conflict of interest", "conflicts of interest",
                              "competing interests", "declaration of interest"],
    "Author contributions":  ["author contributions", "authors' contributions",
                              "contributorship"],
    "Ethics":                ["ethics", "ethical approval", "ethics statement",
                              "ethics approval and consent to participate"],
    "Data availability":     ["data availability", "data availability statement"],
    "References":            ["references", "bibliography", "literature cited"],
}


def clean(text):
    """Lowercase, strip numbering like '2.' or 'II.' and trailing colons."""
    text = text.strip().lower()
    text = re.sub(r"^([0-9]+(\.[0-9]+)*|[ivx]+)[.)]?\s+", "", text)  # remove "2." / "II."
    return text.rstrip(":. ").strip()


def match_section(paragraph):
    """Return the official section name if this paragraph is a heading, else None."""
    text = paragraph.text.strip()
    if not text:
        return None

    # "Keywords: x, y, z" written on one line counts as the Keywords section
    if re.match(r"^key\s?words\s*[:\-]", text, re.IGNORECASE):
        return "Keywords"

    if len(text) > 60:                      # real headings are short
        return None

    cleaned = clean(text)
    for official, variants in SECTION_NAMES.items():
        if cleaned in variants:
            return official
    return None


def split_into_sections(path):
    """Read the .docx and return a list of (section_name, [paragraph texts])."""
    doc = Document(path)
    sections = [("Front matter", [])]        # title, authors etc. before the first heading

    for p in doc.paragraphs:
        name = match_section(p)
        if name:
            sections.append((name, []))
            # keep inline text, e.g. "Keywords: x, y" -> "x, y"
            rest = re.split(r"[:\-]", p.text, maxsplit=1)
            if name == "Keywords" and len(rest) == 2 and rest[1].strip():
                sections[-1][1].append(rest[1].strip())
        elif p.text.strip():
            sections[-1][1].append(p.text.strip())

    return sections, doc


def main():
    if len(sys.argv) < 2:
        print("Usage: python step1_split_sections.py <manuscript.docx>")
        return

    path = sys.argv[1]
    try:
        sections, doc = split_into_sections(path)
    except Exception as e:
        print(f"Could not read '{path}': {e}")
        return

    print(f"\nFile: {path}")
    print(f"Tables in document: {len(doc.tables)}\n")
    print(f"{'Section':<24}{'Paragraphs':>11}{'Words':>8}")
    print("-" * 43)
    for name, paras in sections:
        words = sum(len(t.split()) for t in paras)
        print(f"{name:<24}{len(paras):>11}{words:>8}")

    found = {name for name, _ in sections}
    missing = [s for s in ["Abstract", "Keywords", "Introduction", "Methods",
                           "Results", "Discussion", "References"] if s not in found]
    print()
    if missing:
        print("Not found: " + ", ".join(missing))
    else:
        print("All core sections found.")


if __name__ == "__main__":
    main()
