"""
Manuscript Pre-Submission Checker - web version, by The Grey Swan Editorial.

Run on your own computer:
    pip install -r requirements.txt
    python -m streamlit run app.py

Hosted version: deploy this repository on Streamlit Community Cloud (see README).
Colours live in .streamlit/config.toml; the logo lives in assets/.
"""

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from checker import check_manuscript, build_workbook
from settings import load_settings

GITHUB_URL = "https://github.com/TheHarshMaan/manuscript-checker"
ASSETS = Path(__file__).with_name("assets")

# Branding. Paste your website address between the quotes once The Grey Swan site is live,
# e.g. "https://thegreyswan.com", and the brand name becomes a link everywhere.
BRAND = "The Grey Swan Editorial"
TAGLINE = "Smart publishing tools for authors and publishers"
SITE_URL = ""

# Brand colours (also set in .streamlit/config.toml)
INK = "#E8E6E1"        # warm off-white text
MUTED = "#A3A9AE"      # secondary text
COPPER = "#C9814F"     # accent
CARD = "#1B1F23"       # raised surfaces
LINE = "#2C3238"       # hairlines
STATUS_COLOUR = {"Missing": "#E8907F", "Concern": "#E0B86A"}

STYLE = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

html, body, .stApp, .stMarkdown, button, input, textarea, label {{
    font-family: 'IBM Plex Sans', sans-serif;
}}
h1, h2, h3, .gs-serif {{
    font-family: 'Instrument Serif', Georgia, serif !important;
    font-weight: 400 !important;
    letter-spacing: 0.2px;
}}
.block-container {{ padding-top: 2.5rem; max-width: 1200px; }}
[data-testid="stSidebar"] {{ border-right: 1px solid {LINE}; }}

.gs-header {{ display: flex; align-items: center; gap: 22px; margin: 0 0 6px; }}
.gs-header svg {{ width: 76px; height: 76px; flex: none; }}
.gs-eyebrow {{ color: {COPPER}; font-size: 0.78rem; letter-spacing: 3px; text-transform: uppercase; font-weight: 500; }}
.gs-eyebrow a {{ color: {COPPER}; text-decoration: none; }}
.gs-title {{ font-family: 'Instrument Serif', Georgia, serif; font-size: clamp(2.1rem, 4.5vw, 3.2rem);
             line-height: 1.05; color: {INK}; margin: 4px 0 0; }}
.gs-title em {{ color: {MUTED}; }}
.gs-lead {{ color: {MUTED}; font-size: 1.02rem; line-height: 1.6; max-width: 760px; margin: 18px 0 22px; }}
.gs-rule {{ border: 0; border-top: 1px solid {LINE}; margin: 6px 0 22px; }}

.gs-card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 10px;
            padding: 16px 20px; margin: 0 0 26px; color: {MUTED}; font-size: 0.93rem; line-height: 1.6; }}
.gs-card b {{ color: {INK}; font-weight: 500; }}

.gs-brand {{ font-family: 'Instrument Serif', Georgia, serif; font-size: 1.45rem; color: {INK}; line-height: 1.1; }}
.gs-brand a {{ color: {INK}; text-decoration: none; }}
.gs-tag {{ color: {MUTED}; font-size: 0.82rem; margin-top: 4px; }}
.gs-foot {{ color: {MUTED}; font-size: 0.82rem; text-align: center; padding: 10px 0 4px; }}
.gs-foot a, .gs-tag a {{ color: {COPPER}; }}

@media (max-width: 640px) {{
    .gs-header {{ gap: 14px; }}
    .gs-header svg {{ width: 54px; height: 54px; }}
}}
</style>
"""


def brand_name():
    """The brand name, as a link if the website address has been filled in."""
    return f'<a href="{SITE_URL}" target="_blank">{BRAND}</a>' if SITE_URL else BRAND


def logo_svg():
    """The swan mark as inline SVG (decorative here, since the brand name sits beside it)."""
    svg = (ASSETS / "grey_swan_mark.svg").read_text(encoding="utf-8")
    return svg.replace('role="img" aria-label="The Grey Swan"', 'aria-hidden="true"')


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


def issues_table(issues):
    """The issues as a table, with the Status column coloured."""
    df = pd.DataFrame(issues, columns=["Section", "Check", "Status", "Details", "Comment for author"])
    colour = lambda v: f"color: {STATUS_COLOUR.get(v, INK)}; font-weight: 600"
    styler = df.style
    if hasattr(styler, "map"):
        return styler.map(colour, subset=["Status"])
    return styler.applymap(colour, subset=["Status"])


def footer():
    st.markdown(f'<hr class="gs-rule" style="margin-top:40px"><div class="gs-foot">© {brand_name()} · '
                f'Rule-based checker built in Python · <a href="{GITHUB_URL}" target="_blank">View the code</a></div>',
                unsafe_allow_html=True)


def main():
    icon = ASSETS / "favicon.png"
    st.set_page_config(page_title=f"Manuscript Pre-Submission Checker | {BRAND}",
                       page_icon=str(icon) if icon.exists() else None, layout="wide")
    st.markdown(STYLE, unsafe_allow_html=True)

    if hasattr(st, "logo") and (ASSETS / "grey_swan_mark.png").exists():
        st.logo(str(ASSETS / "grey_swan_mark.png"), size="large")

    # --- Header
    st.markdown(f"""
<div class="gs-header">
  {logo_svg()}
  <div>
    <div class="gs-eyebrow">{brand_name()}</div>
    <div class="gs-title">Manuscript <em>Pre-Submission</em> Checker</div>
  </div>
</div>
<p class="gs-lead">Upload a manuscript in Word format (.docx) to run the technical checks a journal
screening desk performs before peer review: structure, abbreviations, figure and table citations,
ethics and consent statements, declarations and references.</p>
<div class="gs-card">
  <b>Private by design.</b> Files are processed in memory and discarded as soon as the check finishes.
  Nothing is stored or shared. Only upload manuscripts you are entitled to share.<br>
  <b>A screening aid, not a verdict.</b> The checker flags issues for a person to review. It does not judge
  the science, and it can miss problems or raise false alarms.
</div>
""", unsafe_allow_html=True)

    # --- Sidebar: brand and settings
    defaults = load_settings()
    with st.sidebar:
        st.markdown(f'<div class="gs-brand">{brand_name()}</div><div class="gs-tag">{TAGLINE}</div>',
                    unsafe_allow_html=True)
        st.markdown('<hr class="gs-rule">', unsafe_allow_html=True)
        st.subheader("Settings")
        limit = st.number_input("Abstract word limit", min_value=50, max_value=1000,
                                value=int(defaults["abstract_word_limit"]), step=10)
        extra = st.text_area("Abbreviations to ignore (comma-separated)",
                             value=", ".join(defaults["extra_ignore_abbreviations"]),
                             help="Abbreviations this journal doesn't require authors to define, e.g. ICU, MIC")
        skip_symbols = st.checkbox("Skip gene, cell-line and chemical names", value=True,
                                   help="E.g. TP53, MCF-7, NaCl are not flagged unless the authors define them.")
        st.markdown(f'<div class="gs-tag"><a href="{GITHUB_URL}" target="_blank">Source code on GitHub</a></div>',
                    unsafe_allow_html=True)

    settings = {
        "abstract_word_limit": int(limit),
        "extra_ignore_abbreviations": [a.strip() for a in extra.split(",") if a.strip()],
        "skip_gene_and_chemical_symbols": skip_symbols,
    }

    files = st.file_uploader("Upload one or more .docx manuscripts", type=["docx"],
                             accept_multiple_files=True)
    if not files:
        st.caption("PDF and .doc files are not supported yet. In Word, use File → Save As → .docx.")
        footer()
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
        title = f"{name}: ready" if not issues else f"{name}: {missing} missing, {concern} concern"
        with st.expander(title, expanded=len(results) == 1):
            if not issues:
                st.success("All checks passed.")
                continue
            st.dataframe(issues_table(issues), use_container_width=True, hide_index=True)
            st.markdown("**Comments for the author** (copy and paste):")
            st.code(author_comments(issues), language=None)

    footer()


if __name__ == "__main__":
    main()
