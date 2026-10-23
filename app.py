"""
Manuscript Pre-Submission Checker - web version.

Run on your own computer:
    pip install -r requirements.txt
    streamlit run app.py

Hosted version: deploy this repository on Streamlit Community Cloud (see README).
"""

import io

import streamlit as st

from checker import check_manuscript, build_workbook
from settings import load_settings

GITHUB_URL = "https://github.com/TheHarshMaan/manuscript-checker"

# Branding. Paste your website address between the quotes once The Grey Swan site is live,
# e.g. "https://thegreyswan.com", and the brand name becomes a link everywhere.
BRAND = "The Grey Swan Editorial"
TAGLINE = "Smart publishing tools for authors and publishers"
SITE_URL = ""


def brand_name():
    """The brand name, as a link if the website address has been filled in."""
    return f"[{BRAND}]({SITE_URL})" if SITE_URL else BRAND
STATUS_LABEL = {"Missing": "🔴 Missing", "Concern": "🟠 Concern"}


def run_checks(name, data, settings):
    """Check one uploaded file entirely in memory: nothing is written to disk.
    Returns a list of issues, or None if the file can't be read."""
    try:
        return check_manuscript(io.BytesIO(data), settings)
    except Exception:
        return None


def author_comments(issues):
    """All author-facing comments as a numbered list, ready to paste into an email."""
    return "\n".join(f"{n}. {i[4]}" for n, i in enumerate(issues, start=1))


def main():
    st.set_page_config(page_title=f"Manuscript Pre-Submission Checker | {BRAND}",
                       page_icon="🦢", layout="wide")

    st.title("Manuscript Pre-Submission Checker")
    st.markdown(f"by **{brand_name()}** · {TAGLINE}")
    st.write(
        "Upload a manuscript in Word format (.docx) to run the technical checks a journal "
        "screening desk performs before peer review: structure, abbreviations, figure and table "
        "citations, ethics and consent statements, declarations and references."
    )
    st.info(
        "**Privacy:** files are processed in memory and deleted as soon as the check finishes. "
        "Nothing is stored or shared. Only upload manuscripts you are entitled to share.\n\n"
        "**This tool flags issues for a person to review.** It does not judge the science and "
        "can miss problems or raise false alarms."
    )

    # --- Settings in the sidebar
    defaults = load_settings()
    with st.sidebar:
        st.markdown(f"### 🦢 {brand_name()}")
        st.caption(TAGLINE)
        st.divider()
        st.header("Settings")
        limit = st.number_input("Abstract word limit", min_value=50, max_value=1000,
                                value=int(defaults["abstract_word_limit"]), step=10)
        extra = st.text_area("Abbreviations to ignore (comma-separated)",
                             value=", ".join(defaults["extra_ignore_abbreviations"]),
                             help="Abbreviations this journal doesn't require authors to define, e.g. ICU, MIC")
        skip_symbols = st.checkbox("Skip gene, cell-line and chemical names", value=True,
                                   help="E.g. TP53, MCF-7, NaCl are not flagged unless the authors define them.")
        st.markdown(f"[Source code on GitHub]({GITHUB_URL})")

    settings = {
        "abstract_word_limit": int(limit),
        "extra_ignore_abbreviations": [a.strip() for a in extra.split(",") if a.strip()],
        "skip_gene_and_chemical_symbols": skip_symbols,
    }

    files = st.file_uploader("Upload one or more .docx manuscripts", type=["docx"],
                             accept_multiple_files=True)
    if not files:
        st.caption("PDF and .doc files are not supported yet. In Word, use File → Save As → .docx.")
        return

    results = []
    with st.spinner("Checking…"):
        for f in files:
            results.append((f.name, run_checks(f.name, f.getvalue(), settings)))

    # --- Summary line
    readable = [(n, i) for n, i in results if i is not None]
    ready = sum(1 for _, i in readable if not i)
    st.subheader("Results")
    st.write(f"{len(results)} file(s) checked: {ready} ready, "
             f"{len(readable) - ready} need revision, {len(results) - len(readable)} could not be read.")

    # --- Excel download for everything
    if readable:
        buffer = io.BytesIO()
        build_workbook(results).save(buffer)
        st.download_button("Download Excel report", data=buffer.getvalue(),
                           file_name="screening_report.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # --- One panel per manuscript
    for name, issues in results:
        if issues is None:
            st.error(f"**{name}**: could not be read. Make sure it is a valid .docx file.")
            continue
        missing = sum(1 for i in issues if i[2] == "Missing")
        concern = sum(1 for i in issues if i[2] == "Concern")
        title = (f"✅ {name}: ready" if not issues
                 else f"{name}: {missing} missing, {concern} concern")
        with st.expander(title, expanded=len(results) == 1):
            if not issues:
                st.success("All checks passed.")
                continue
            st.dataframe(
                [{"Section": s, "Check": c, "Status": STATUS_LABEL.get(stt, stt),
                  "Details": d, "Comment for author": cm} for s, c, stt, d, cm in issues],
                use_container_width=True, hide_index=True,
            )
            st.markdown("**Comments for the author** (copy and paste):")
            st.code(author_comments(issues), language=None)

    st.divider()
    st.caption(f"© {BRAND} · Rule-based checker built in Python · [View the code]({GITHUB_URL})")


if __name__ == "__main__":
    main()
