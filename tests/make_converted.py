"""
Converts some Word test papers to PDF, OpenDocument (.odt) and RTF with LibreOffice, into tests/converted/,
and compiles the LaTeX test paper to PDF with pdflatex (a second, different kind of PDF).

run_tests.py then checks that each converted file gets the SAME results as its Word original, except for
what that format can't show (see FORMAT_LIMITS in run_tests.py), plus the note saying what wasn't checked.

    python tests/make_converted.py        (needs LibreOffice: the 'soffice' command)
"""

import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
SOURCES = ["02_flawed_rct.docx", "06_case_report.docx", "16_apa_flawed.docx", "20_declarations_flawed_trial.docx",
           "28_integrity_flags.docx"]
FORMATS = ["pdf", "odt", "rtf"]

out = HERE / "converted"
out.mkdir(exist_ok=True)
soffice = shutil.which("soffice") or shutil.which("libreoffice")
if not soffice:
    raise SystemExit("LibreOffice isn't installed: can't make the converted test files.")
for fmt in FORMATS:
    subprocess.run([soffice, "--headless", "--convert-to", fmt, "--outdir", str(out)]
                   + [str(HERE / "papers" / s) for s in SOURCES], check=True, capture_output=True)
print(f"Converted {len(SOURCES)} papers to {', '.join(FORMATS)} in {out}")

# The LaTeX paper compiled to PDF (twice, so references and figure numbers are filled in)
pdflatex = shutil.which("pdflatex")
if pdflatex:
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        for _ in range(2):
            subprocess.run([pdflatex, "-interaction=nonstopmode", "-output-directory", tmp,
                            str(HERE / "papers" / "31_latex_paper.tex")], capture_output=True)
        shutil.copy(Path(tmp) / "31_latex_paper.pdf", out / "31_latex_paper.pdf")
    print("Compiled 31_latex_paper.tex to PDF with pdflatex")
else:
    print("pdflatex isn't installed: skipped the LaTeX PDF")
