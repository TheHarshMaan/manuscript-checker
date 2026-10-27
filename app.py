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
APP_DIR = Path(__file__).parent
# Images live in assets/, or next to app.py if they were uploaded without the folder
ASSETS = APP_DIR / "assets" if (APP_DIR / "assets").is_dir() else APP_DIR

# Branding. Paste your website address between the quotes once The Grey Swan site is live,
# e.g. "https://thegreyswan.com", and the brand name becomes a link everywhere.
BRAND = "The Grey Swan Editorial"
TAGLINE = "Smart publishing tools for authors and publishers"
SITE_URL = "https://thegreyswan.in"

# Brand colours, taken from the logo (also set in .streamlit/config.toml)
INK = "#ECE8E1"        # warm ivory text
MUTED = "#A9A49B"      # secondary text
GOLD = "#C69F70"       # antique gold accent
CARD = "#1A1D20"       # raised surfaces
LINE = "#2E2A24"       # warm hairlines
STATUS_COLOUR = {"Missing": "#E8907F", "Concern": "#E0B86A"}

STYLE = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500&family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=IBM+Plex+Sans:wght@400;500&display=swap');

html, body, .stApp, .stMarkdown, button, input, textarea, label {{
    font-family: 'IBM Plex Sans', sans-serif;
}}
h1, h2, h3 {{
    font-family: 'Cormorant Garamond', Georgia, serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.3px;
}}
.block-container {{ padding-top: 4.5rem; max-width: 1180px; }}
[data-testid="stSidebar"] {{ border-right: 1px solid {LINE}; }}

.gs-header {{ display: flex; align-items: center; gap: 28px; margin: 0 0 4px; }}
.gs-header img {{ height: 170px; width: auto; flex: none; }}
.gs-eyebrow {{ font-family: 'Cinzel', 'Trajan Pro', Georgia, serif; color: {GOLD};
               font-size: 0.95rem; letter-spacing: 5px; text-transform: uppercase; }}
.gs-eyebrow a {{ color: {GOLD}; text-decoration: none; }}
.gs-eyebrow span {{ color: {MUTED}; letter-spacing: 4px; }}
.gs-title {{ font-family: 'Cormorant Garamond', Georgia, serif; font-weight: 500;
             font-size: clamp(2.3rem, 5vw, 3.6rem); line-height: 1.02; color: {INK}; margin: 8px 0 0; }}
.gs-title em {{ color: {GOLD}; }}

.gs-ornament {{ display: flex; align-items: center; gap: 14px; margin: 22px 0 20px; max-width: 760px; }}
.gs-ornament::before, .gs-ornament::after {{ content: ""; flex: 1; height: 1px; background: {GOLD}; opacity: 0.55; }}
.gs-ornament svg {{ width: 14px; height: 14px; flex: none; }}

.gs-lead {{ color: {MUTED}; font-size: 1.02rem; line-height: 1.65; max-width: 760px; margin: 0 0 22px; }}
.gs-card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 10px;
            padding: 16px 20px; margin: 0 0 26px; color: {MUTED}; font-size: 0.93rem; line-height: 1.6; }}
.gs-card b {{ color: {INK}; font-weight: 500; }}

.gs-side-logo {{ display: block; width: 100%; max-width: 250px; margin: -10px auto 0; }}
.gs-tag {{ color: {MUTED}; font-size: 0.82rem; text-align: center; margin: 2px 0 0; }}
.gs-tag a, .gs-foot a {{ color: {GOLD}; }}
.gs-rule {{ border: 0; border-top: 1px solid {LINE}; margin: 18px 0 18px; }}
.gs-foot {{ color: {MUTED}; font-size: 0.82rem; text-align: center; padding: 10px 0 4px; }}
.gs-foot .gs-name {{ font-family: 'Cinzel', Georgia, serif; color: {GOLD}; letter-spacing: 2px; }}

@media (max-width: 680px) {{
    .gs-header {{ flex-direction: column; align-items: flex-start; gap: 12px; }}
    .gs-header img {{ height: 120px; }}
    .gs-eyebrow {{ letter-spacing: 3px; font-size: 0.8rem; }}
}}
</style>
"""

STAR = (f'<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 0 C10.8 6.5 13.5 9.2 20 10 '
        f'C13.5 10.8 10.8 13.5 10 20 C9.2 13.5 6.5 10.8 0 10 C6.5 9.2 9.2 6.5 10 0 Z" fill="{GOLD}"/></svg>')


def find_asset(filename):
    """Path to an image in assets/ or next to app.py, or None if it's in neither."""
    for folder in (APP_DIR / "assets", APP_DIR):
        if (folder / filename).exists():
            return str(folder / filename)
    st.warning(f"Image not found: {filename}. Upload it to the assets folder or next to app.py.")
    return None


def brand_name():
    """The brand name, as a link if the website address has been filled in."""
    return f'<a href="{SITE_URL}" target="_blank">{BRAND}</a>' if SITE_URL else BRAND


def run_checks(name, data, settings):
    """Check one uploaded file entirely in memory: nothing is written to disk.
    Returns a list of issues, or None if the file can't be read."""
    try:
        return check_manuscript(io.BytesIO(data), settings)
    except Exception:
        return None


def issues_table(issues):
    """The issues as a table, with the Status column coloured."""
    df = pd.DataFrame(issues, columns=["Section", "Check", "Status", "Details"])
    colour = lambda v: f"color: {STATUS_COLOUR.get(v, INK)}; font-weight: 600"
    styler = df.style
    if hasattr(styler, "map"):
        return styler.map(colour, subset=["Status"])
    return styler.applymap(colour, subset=["Status"])


def eyebrow():
    """'THE GREY SWAN · EDITORIAL' in Roman capitals, linked to the website when there is one."""
    name = "The Grey Swan"
    if SITE_URL:
        name = f'<a href="{SITE_URL}" target="_blank">{name}</a>'
    return f'{name} <span>· Editorial</span>'


def footer():
    st.markdown(f'<div class="gs-ornament" style="margin:44px auto 8px">{STAR}</div>'
                f'<div class="gs-foot">© <span class="gs-name">{BRAND}</span> · Rule-based checker built in Python · '
                f'<a href="{GITHUB_URL}" target="_blank">View the code</a></div>',
                unsafe_allow_html=True)


def main():
    icon = next((str(f / "favicon.png") for f in (APP_DIR / "assets", APP_DIR) if (f / "favicon.png").exists()), None)
    st.set_page_config(page_title=f"Manuscript Pre-Submission Checker | {BRAND}",
                       page_icon=icon, layout="wide")
    st.markdown(STYLE, unsafe_allow_html=True)

    icon_image = find_asset("grey_swan_icon.png")
    if hasattr(st, "logo") and icon_image:
        st.logo(icon_image, size="large")

    # --- Header: the emblem (Streamlit's own image display) beside the title
    try:
        emblem_col, title_col = st.columns([1, 5], vertical_alignment="center")
    except TypeError:                      # older Streamlit without vertical_alignment
        emblem_col, title_col = st.columns([1, 5])
    with emblem_col:
        emblem = find_asset("grey_swan_emblem.png")
        if emblem:
            st.image(emblem, width=170)
    with title_col:
        st.markdown(f"""
<div class="gs-eyebrow">{eyebrow()}</div>
<div class="gs-title">Manuscript <em>Pre-Submission</em> Checker</div>
""", unsafe_allow_html=True)

    st.markdown(f"""
<div class="gs-ornament">{STAR}</div>
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
        logo = find_asset("the_grey_swan_logo.png")
        if logo:
            st.image(logo, width=250)
        st.markdown(f'<div class="gs-tag">Editorial · {TAGLINE}</div>', unsafe_allow_html=True)
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

    footer()


if __name__ == "__main__":
    main()
