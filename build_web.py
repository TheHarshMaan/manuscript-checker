"""
Builds the website version of the checker.

Packs the checker's Python files, the journal profiles, and the libraries the browser doesn't already
have (python-docx, openpyxl and pypdf) into checker_bundle.zip, used by both pages:
  web/              the manuscript checker       -> thegreyswan.in/checker/
  web_references/   the reference checker        -> thegreyswan.in/references/

    python build_web.py                  -> builds both pages
    python build_web.py ../my-site       -> also copies them into your site, as checker/ and references/

Run it again whenever you change a check, a rule or a profile, then upload both folders to the site.
"""

import importlib
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
WEB = HERE / "web"
REFERENCES = HERE / "web_references"
BUNDLE = WEB / "checker_bundle.zip"
SHARED = ["style.css", "worker.js", "grey_swan_emblem.png", "favicon.png", "checker_bundle.zip"]   # copied into both

CHECKER_FILES = ["rules.py", "settings.py", "checker.py", "web_entry.py", "step1_split_sections.py",
                 "step2_figures_tables.py", "step3_abbreviations.py", "step4_declarations.py",
                 "step5_anonymisation.py", "step6_citations.py",
                 "step7_policies.py", "step8_guidelines.py",
                 "step9_integrity.py", "step10_formatting.py",
                 "step11_submission.py", "readers.py", "refcheck.py"]
# Pure-Python libraries copied from your own Python installation (pip install -r requirements.txt).
# lxml and pyyaml are not here: the browser version of Python already provides them.
LIBRARIES = ["docx", "openpyxl", "et_xmlfile", "pypdf"]
# Files the page needs, besides the bundle
PAGE_FILES = {"checker": (WEB, ["index.html", "app.js", "options.json"] + SHARED),
              "references": (REFERENCES, ["index.html", "refs.js", "refs.css"] + SHARED)}


def add_folder(zf, folder, arcname):
    for path in sorted(folder.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            zf.write(path, f"{arcname}/{path.relative_to(folder).as_posix()}")


def build():
    with zipfile.ZipFile(BUNDLE, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in CHECKER_FILES:
            zf.write(HERE / name, name)
        add_folder(zf, HERE / "profiles", "profiles")
        for lib in LIBRARIES:
            module = importlib.import_module(lib)
            folder = Path(module.__file__).parent
            add_folder(zf, folder, lib)
            # keep each library's licence alongside it
            for dist in folder.parent.glob("*.dist-info"):
                top = dist / "top_level.txt"
                names = top.read_text().split() if top.exists() else []
                if lib in names or dist.name.lower().startswith(lib.replace("docx", "python_docx")):
                    for lic in list(dist.glob("LICEN[CS]E*")) + list(dist.glob("licenses/*")):
                        zf.write(lic, f"licences/{dist.name.split('-')[0]}/{lic.name}")
    for img in ("grey_swan_emblem.png", "favicon.png"):
        if (HERE / img).exists():
            shutil.copy(HERE / img, WEB / img)
    write_options()
    for name in SHARED:                       # the reference checker uses the same styles, worker and bundle
        shutil.copy(WEB / name, REFERENCES / name)
    print(f"Built {BUNDLE.relative_to(HERE)} ({BUNDLE.stat().st_size / 1e6:.1f} MB) for web/ and web_references/")


def write_options():
    """The journal profiles, review models and citation styles, for the account page's "default profile" choice."""
    import json
    sys.path.insert(0, str(HERE))
    from settings import list_profiles
    from rules import REVIEW_MODELS, CITATION_STYLES
    options = {"profiles": [{"id": pid, "name": name} for pid, name in list_profiles().items()],
               "review_models": REVIEW_MODELS, "citation_styles": CITATION_STYLES}
    (WEB / "options.json").write_text(json.dumps(options, indent=1, ensure_ascii=False), encoding="utf-8")


def copy_to(site):
    for folder, (source, names) in PAGE_FILES.items():
        target = Path(site) / folder
        target.mkdir(parents=True, exist_ok=True)
        for name in names:
            shutil.copy(source / name, target / name)
        print(f"Copied the {folder} page to {target.resolve()}")


if __name__ == "__main__":
    build()
    if len(sys.argv) > 1:
        copy_to(sys.argv[1])
