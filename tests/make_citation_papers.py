"""
Builds the citation-style test papers (15-18) and the expected results for each reference style.

  15_apa_clean.docx     APA 7 done right: clean under APA, Harvard and "any style"
  16_apa_flawed.docx    APA with seven planted problems
  17_ama_flawed.docx    AMA (superscripts) with four planted problems
  18_ieee_clean.docx    IEEE done right

Writes tests/expected_styles.json: the EXTRA problems each paper should show when a profile names
a citation style. Papers 1-14 cite with [1] brackets and Vancouver-style lists (paper 03 is
author-date; paper 12 uses superscripts), so their extras follow from that.

    python tests/make_citation_papers.py      (after make_test_papers.py and make_double_blind_papers.py)
"""

import json
from pathlib import Path

from docx import Document

HERE = Path(__file__).parent
OUT = HERE / "papers"

DECLARATIONS = [
    ("Acknowledgements", ["We thank the participating staff for their support."]),
    ("Funding", ["This study received no specific funding."]),
    ("Conflicts of interest", ["The authors declare no conflicts of interest."]),
    ("Author contributions", ["AB: conceptualisation, analysis. CD: data collection, writing."]),
    ("Data availability statement", ["Data are available from the corresponding author on reasonable request."]),
]


def human_study(intro, discussion):
    """A small, complete survey study, so only the citation problems show up."""
    return [
        ("Abstract", ["Background: Exam stress is common among university students. Methods: This cross-sectional survey "
                      "included 240 students. Results: Two in five reported high stress. Conclusion: Support services "
                      "should be strengthened."]),
        ("Keywords", ["stress; students; survey; mental health"]),
        ("Introduction", intro),
        ("Methods", ["This cross-sectional survey was conducted between August 2024 and November 2024 at a public "
                     "university. A total of 240 students (n = 240) took part. Inclusion criteria were enrolment in an "
                     "undergraduate programme; exclusion criteria were incomplete responses.",
                     "Stress was measured with a validated questionnaire, provided as Supplementary File 1.",
                     "The study was approved by the University Research Ethics Committee (approval no. UREC/2024/077, "
                     "dated 2 July 2024). Written informed consent was obtained from all participants."]),
        ("Results", ["High stress was reported by 41% of students (Table 1; Figure 1)."]),
        ("Discussion", discussion),
        *DECLARATIONS,
        (None, ["Figure 1. Stress scores by year of study.", "Table 1. Participant characteristics."]),
    ]


def save(name, sections, refs, superscripts=None):
    d = Document()
    d.add_paragraph(sections.pop(0))
    for heading, paras in sections:
        if heading:
            d.add_heading(heading, 1)
        for text in paras:
            if superscripts and text in superscripts:
                p = d.add_paragraph()
                for part, sup in superscripts[text]:
                    p.add_run(part).font.superscript = sup
            else:
                d.add_paragraph(text)
    d.add_table(rows=2, cols=2).cell(0, 0).text = "Variable"
    d.add_heading("References", 1)
    for r in refs:
        d.add_paragraph(r)
    d.save(OUT / name)


# ---------------------------------------------------------------------------
# 15. APA, done right
save("15_apa_clean.docx",
     ["Exam stress among university students: a cross-sectional survey"] + human_study(
         ["Stress affects academic performance (Chen & Park, 2021). Garcia et al. (2022) linked exam stress to poor "
          "sleep, and national data show rising distress (World Health Organization [WHO], 2023).",
          "Support services can help (e.g., Brown, 2020; Kumar, 2022)."],
         ["Our results agree with Okafor and Lee (2023). Brown (2020) reported similar rates."]),
     ["Brown, T. (2020). Student stress in higher education. Journal of College Health, 12(3), 45–52. "
      "https://doi.org/10.1000/jch.2020.003",
      "Chen, L., & Park, S. (2021). Stress and academic performance. Educational Psychology Review, 33(2), 101–115. "
      "https://doi.org/10.1000/epr.2021.012",
      "Garcia, M., Singh, R., & Ahmed, K. (2022). Exam stress and sleep. Sleep Health, 8(1), 22–30. "
      "https://doi.org/10.1000/sh.2022.004",
      "Kumar, R. (2022). Counselling services in universities. Asian Journal of Psychiatry, 70, 103045. "
      "https://doi.org/10.1000/ajp.2022.045",
      "Okafor, C., & Lee, J. (2023). Mental health of undergraduates. BMC Psychology, 11, 88. "
      "https://doi.org/10.1000/bmcp.2023.088",
      "World Health Organization. (2023). Mental health of adolescents and young adults. WHO."])

# ---------------------------------------------------------------------------
# 16. APA with planted problems:
#   cited but not listed (Nguyen, 2021) · listed but never cited (Okafor, 2020) · "and" inside brackets ·
#   no comma before the year · list not alphabetical · doi: instead of https://doi.org · year not in brackets ·
#   numbered citations mixed in
save("16_apa_flawed.docx",
     ["Exam stress among university students: a cross-sectional survey"] + human_study(
         ["Stress affects academic performance (Chen and Park, 2021). Garcia et al. (2022) linked exam stress to poor "
          "sleep [3], and loneliness adds to it (Nguyen, 2021).",
          "Support services can help (Brown 2020; Kumar, 2022) [4]."],
         ["Our results agree with earlier surveys (Brown, 2020)."]),
     ["Brown, T. (2020). Student stress in higher education. Journal of College Health, 12(3), 45–52. "
      "doi:10.1000/jch.2020.003",
      "Garcia, M., Singh, R., & Ahmed, K. (2022). Exam stress and sleep. Sleep Health, 8(1), 22–30. "
      "https://doi.org/10.1000/sh.2022.004",
      "Chen, L., & Park, S. (2021). Stress and academic performance. Educational Psychology Review, 33(2), 101–115. "
      "https://doi.org/10.1000/epr.2021.012",
      "Kumar, R. 2022. Counselling services in universities. Asian Journal of Psychiatry, 70, 103045.",
      "Okafor, C. (2020). Loneliness among students. BMC Psychology, 8, 12. https://doi.org/10.1000/bmcp.2020.012"])

# ---------------------------------------------------------------------------
# 17. AMA (superscripts) with planted problems:
#   first cited out of order (1, 3, 2) · initials with full stops · more than six authors without et al ·
#   a doi.org link instead of doi:10…
intro_17 = "Exam stress is common among students."
intro_17b = "It worsens sleep and mood, and support services help."
save("17_ama_flawed.docx",
     ["Exam stress among university students: a cross-sectional survey"] + human_study(
         [intro_17, intro_17b], ["Our findings agree with earlier surveys."]),
     ["1. Brown T, Lee J. Student stress in higher education. J Coll Health. 2020;12(3):45-52. doi:10.1000/jch.2020.003",
      "2. Rao, S. K., Iyer, M. Exam stress and sleep. Sleep Health. 2022;8(1):22-30. doi:10.1000/sh.2022.004",
      "3. Chen L, Park S, Ahmed K, Singh R, Das P, Gupta N, Roy A. Stress and academic performance. "
      "Educ Psychol Rev. 2021;33(2):101-115. https://doi.org/10.1000/epr.2021.012",
      "4. Kumar R. Counselling services in universities. Asian J Psychiatr. 2022;70:103045. doi:10.1000/ajp.2022.045"],
     superscripts={
         intro_17: [("Exam stress is common among students.", False), ("1", True)],
         intro_17b: [("It worsens sleep and mood,", False), ("3", True), (" and support services help.", False), ("2", True)],
         "Our findings agree with earlier surveys.": [("Our findings agree with earlier surveys.", False), ("4", True)],
     })

# ---------------------------------------------------------------------------
# 18. IEEE, done right (a computing paper with no human participants)
d = Document()
d.add_paragraph("Lightweight convolutional networks for chest radiograph classification")
for heading, paras in [
    ("Abstract", ["Background: Deep learning can read chest radiographs. Methods: We trained a lightweight network on "
                  "12000 public radiograph samples. Results: Accuracy reached 94%. Conclusion: Small models perform well."]),
    ("Keywords", ["deep learning; radiography; classification; edge computing"]),
    ("Introduction", ["Convolutional networks classify medical images well [1]. Lightweight designs suit low-power "
                      "devices [2], [3]."]),
    ("Methods", ["We used 12000 samples from a public dataset collected between 2021 and 2023. The network was trained "
                 "between January 2025 and March 2025 [4].",
                 "No human participants or animals were involved; ethical approval was therefore not required."]),
    ("Results", ["Accuracy reached 94% (Table 1; Figure 1)."]),
    ("Discussion", ["Results compare well with larger models [2], [5]."]),
    *DECLARATIONS,
    (None, ["Figure 1. Training accuracy by epoch.", "Table 1. Model performance."]),
]:
    d.add_heading(heading, 1)
    for t in paras:
        d.add_paragraph(t)
d.add_table(rows=2, cols=2).cell(0, 0).text = "Metric"
d.add_heading("References", 1)
for r in ["[1] A. Krishnan and B. Rao, “Deep learning for radiology,” IEEE Trans. Med. Imaging, vol. 40, no. 2, "
          "pp. 210–219, 2021.",
          "[2] C. Li, D. Wang, and E. Zhou, “Compact networks for edge devices,” IEEE Access, vol. 10, pp. 1001–1010, 2022.",
          "[3] F. Silva, “Pruning convolutional networks,” in Proc. IEEE Conf. Comput. Vis., 2023, pp. 55–63.",
          "[4] G. Okoro and H. Patel, “Training schedules for small models,” IEEE Trans. Neural Netw., vol. 35, no. 1, "
          "pp. 12–20, 2024.",
          "[5] I. Novak, “Benchmarking chest radiograph classifiers,” IEEE J. Biomed. Health Inform., vol. 28, no. 4, "
          "pp. 400–409, 2024."]:
    d.add_paragraph(r)
d.save(OUT / "18_ieee_clean.docx")

# ---------------------------------------------------------------------------
# Expected results
expected_path = HERE / "expected.json"
expected = json.loads(expected_path.read_text(encoding="utf-8"))
expected["15_apa_clean.docx"] = []
expected["16_apa_flawed.docx"] = ["References|Citation not in list", "References|Reference not cited",
                                  "References|Reference list order", "References|Mixed citation systems"]
expected["17_ama_flawed.docx"] = ["References|Citation order"]
expected["18_ieee_clean.docx"] = []
expected_path.write_text(json.dumps(expected, indent=2), encoding="utf-8")

# Double-blind: papers 15-18 have no title page and name no institution
db_path = HERE / "expected_double_blind.json"
db = json.loads(db_path.read_text(encoding="utf-8"))
for name in ["15_apa_clean.docx", "16_apa_flawed.docx", "17_ama_flawed.docx", "18_ieee_clean.docx"]:
    db[name] = []
db_path.write_text(json.dumps(db, indent=2), encoding="utf-8")

STYLE = "References|Citation style"
INTEXT = "References|In-text citations"
FORMAT = "References|Reference format"
bracketed = [n for n in expected if n[:2].isdigit() and int(n[:2]) <= 14 and n[:2] not in ("03", "12")]
numbered_old = bracketed + ["12_superscript_citations.docx"]

styles = {s: {} for s in ("apa", "harvard", "ama", "vancouver", "ieee")}
def add(style, papers, label):
    for p in papers:
        styles[style].setdefault(p, []).append(label)

# author-date styles: every numbered paper is the wrong system
for s in ("apa", "harvard"):
    add(s, numbered_old + ["17_ama_flawed.docx", "18_ieee_clean.docx"], STYLE)
add("apa", ["03_systematic_review.docx"], FORMAT)          # Vancouver-format list in an author-date paper
add("harvard", ["03_systematic_review.docx"], FORMAT)
add("apa", ["16_apa_flawed.docx"], INTEXT)                 # "and" in brackets, no comma
add("apa", ["16_apa_flawed.docx"], FORMAT)                 # doi:, year not in brackets
add("harvard", ["16_apa_flawed.docx"], FORMAT)             # year not in brackets

# numbered styles: the author-date papers are the wrong system
for s in ("ama", "vancouver", "ieee"):
    add(s, ["03_systematic_review.docx", "15_apa_clean.docx", "16_apa_flawed.docx"], STYLE)
add("ama", bracketed + ["18_ieee_clean.docx"], INTEXT)     # AMA wants superscripts
add("ama", ["17_ama_flawed.docx"], FORMAT)                 # initials with full stops, >6 authors, doi.org link
add("vancouver", ["17_ama_flawed.docx"], FORMAT)           # initials with full stops, >6 authors
add("ama", ["18_ieee_clean.docx"], FORMAT)                 # IEEE entries aren't Year;Volume:Pages
add("vancouver", ["18_ieee_clean.docx"], FORMAT)
add("ieee", numbered_old + ["17_ama_flawed.docx"], FORMAT)  # "1." not "[1]", surname first
add("ieee", ["12_superscript_citations.docx", "17_ama_flawed.docx"], INTEXT)   # superscripts, not [1]

(HERE / "expected_styles.json").write_text(
    json.dumps({s: {p: sorted(v) for p, v in sorted(d.items())} for s, d in styles.items()}, indent=2),
    encoding="utf-8")
print("Built papers 15-18; wrote expected.json, expected_double_blind.json and expected_styles.json")
