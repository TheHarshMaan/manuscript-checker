"""
Builds the website version of the checker.

Packs the checker's Python files, the journal profiles, and the two libraries the browser
doesn't already have (python-docx and openpyxl) into  web/checker_bundle.zip.
The page in web/ loads that file and runs the checker in the visitor's browser.

    python build_web.py                          -> builds web/checker_bundle.zip
    python build_web.py ../my-site/checker       -> also copies the finished page into your site

Run it again whenever you change a check, a rule or a profile, then upload the web/ files to the site.
"""

import importlib
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
WEB = HERE / "web"
BUNDLE = WEB / "checker_bundle.zip"

CHECKER_FILES = ["rules.py", "settings.py", "checker.py", "web_entry.py", "step1_split_sections.py",
                 "step2_figures_tables.py", "step3_abbreviations.py", "step4_declarations.py"]
# Pure-Python libraries copied from your own Python installation (pip install -r requirements.txt).
# lxml and pyyaml are not here: the browser version of Python already provides them.
LIBRARIES = ["docx", "openpyxl", "et_xmlfile"]
# Files the page needs, besides the bundle
PAGE_FILES = ["index.html", "style.css", "app.js", "worker.js", "grey_swan_emblem.png", "favicon.png"]


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
    print(f"Built {BUNDLE.relative_to(HERE)} ({BUNDLE.stat().st_size / 1e6:.1f} MB)")


def copy_to(target):
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    for name in PAGE_FILES + [BUNDLE.name]:
        shutil.copy(WEB / name, target / name)
    print(f"Copied the page to {target.resolve()}")


if __name__ == "__main__":
    build()
    if len(sys.argv) > 1:
        copy_to(sys.argv[1])
