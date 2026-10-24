"""
Manuscript Checker - Milestone 3 (part 1)
Checks declarations (ethics, consent, COI, funding, author contributions,
acknowledgements, data availability), study details (sample size, study
period, inclusion/exclusion criteria, questionnaires, minors, animals,
trial/PROSPERO registration) and numbered reference citations.

How to run (in a terminal, from this folder):
    python step4_declarations.py my_manuscript.docx
"""

import sys
import re
from step1_split_sections import split_into_sections   # reuse your step 1 code


def has(pattern, text):
    """True if the regex pattern appears anywhere in the text (case-insensitive)."""
    return re.search(pattern, text, re.IGNORECASE) is not None


def sentences_with(pattern, text):
    """Return only the sentences that contain the pattern."""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(s for s in sentences if has(pattern, s))


NEGATION = r"\b(no|not|neither|nor|without|none)\b"


def affirmative(text):
    """Drop sentences that deny something, e.g. 'No human participants or animals were involved.'"""
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(s for s in sentences if not has(NEGATION, s))


def study_text(sections):
    """What the study itself did: Methods (and Ethics) if present, otherwise the whole body,
    with negated sentences removed. The Introduction is left out on purpose, since
    'cancer in women' there doesn't mean the study had human participants."""
    methods = " ".join(t for name, paras in sections if name in ("Methods", "Ethics") for t in paras)
    if not methods:
        methods = " ".join(t for name, paras in sections
                           if name not in ("References", "Introduction", "Front matter") for t in paras)
    return affirmative(methods)


def article_type(sections):
    """'case report', 'letter', 'narrative review' or 'research', judged from the headings
    and from how the paper describes itself in its title, abstract and keywords."""
    opening = " ".join(t for name, paras in sections if name in ("Front matter", "Abstract", "Keywords") for t in paras)
    if has(r"letter to the editor|letter to editor|\bdear editor\b", opening):
        return "letter"
    if any(name == "Case presentation" for name, _ in sections) or has(r"\bcase report\b|\bcase series\b", opening):
        return "case report"
    if (has(r"narrative review|literature review|review article|mini[- ]?review", opening)
            and not has(r"systematic review|meta-analys|scoping review", opening)):
        return "narrative review"
    return "research"


def is_case_report(sections):
    return article_type(sections) == "case report"


def study_type(sections):
    text = study_text(sections)
    human = (has(HUMAN_WORDS, text)
             or has(r"\bhospital\b|\bclinical\b|retrospective|medical records|\bconsent\b", text)
             or has(r"\bisolates\b|\bspecimens\b|\burine\b|\bsputum\b|\bswabs?\b", text))
    animal = has(ANIMAL_WORDS, text)
    return human, animal, text


# ---------------------------------------------------------------------------
# Declarations
# ---------------------------------------------------------------------------
# Each declaration: (name, heading name from step 1, words that show it is present in the text)
DECLARATIONS = [
    ("Conflict of interest", "Conflict of interest",
     r"conflicts? of interest|competing interests?|declare[sd]? no|nothing to disclose"),
    ("Funding", "Funding",
     r"\bfund(ing|ed)\b|\bgrant\b|financial support|received no specific"),
    ("Author contributions", "Author contributions",
     r"author(s'|s)? contributions?|contributed to|CRediT|conceptuali[sz]ation"),
    ("Acknowledgements", "Acknowledgements",
     r"acknowledg"),
    ("Data availability", "Data availability",
     r"data availab|available from the corresponding author|available on (reasonable )?request|deposited in"),
]

SAMPLE_WORDS = (r"patients?|participants?|subjects?|respondents?|isolates?|samples?|"
                r"specimens?|cases?|children|women|men|individuals|students|volunteers|"
                r"mice|rats|animals|studies|articles|records|trials|workers|nurses|doctors|physicians|"
                r"mothers|households|pregnant women|adults|adolescents|caregivers|teachers|pharmacists")
HUMAN_WORDS = r"\b(patients?|participants?|respondents?|subjects?|volunteers|women|men|children|students)\b"
MINOR_WORDS = r"\b(child(ren)?|minors?|adolescents?|paediatric|pediatric|infants?|neonates?|school students|under 18|<\s?18 years)\b"
ANIMAL_WORDS = r"\b(mice|mouse|rats?|rabbits?|guinea pigs?|zebrafish|animals?)\b"
DATE = (r"\b(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{4}-\d{2}-\d{2}|"
        r"(\d{1,2}(st|nd|rd|th)?\s+)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?,?\s+(\d{1,2},?\s+)?\d{4})\b")
APPROVAL_NO = r"(no\.?|number|ref(erence)?\.?|approval|protocol|letter)\s*(id)?\s*[:#]?\s*[A-Z0-9/\-]*\d[A-Z0-9/\-.]{2,}"
COMMITTEE = r"ethics committee|ethical committee|review board|\bIRB\b|\bIEC\b|\bIAEC\b|research ethics|ethics board"


def check_declarations(sections):
    issues = []   # (section, check, status, details)
    headings = {name for name, _ in sections}
    body = " ".join(t for name, paras in sections if name not in ("References",) for t in paras)
    human, animal, study = study_type(sections)

    # --- Simple present/absent declarations
    for name, heading, words in DECLARATIONS:
        if heading not in headings and not has(words, body):
            issues.append(("Declarations", name, "Missing", f"No {name.lower()} statement found"))

    if article_type(sections) in ("letter", "narrative review"):
        return issues   # no participants: ethics and consent statements don't apply

    # --- Ethics
    ethics_text = sentences_with(r"ethic|review board|\bIRB\b|\bIEC\b|\bIAEC\b", body)
    review = has(r"systematic review|meta-analys|scoping review|narrative review", body)
    if not ethics_text and review and not (human or animal):
        pass   # reviews of published studies usually don't need an ethics statement
    elif not ethics_text and not (human or animal):
        issues.append(("Declarations", "Ethics statement", "Concern",
                       "No ethics statement found (study does not appear to involve humans or animals)"))
    elif not ethics_text:
        issues.append(("Declarations", "Ethics approval", "Missing", "No ethics statement found"))
    elif has(r"not required|waived|exempt|not applicable", ethics_text) and (not (human or animal) or is_case_report(sections)):
        pass   # e.g. an in vitro study, or a single case report where consent for publication is what matters
    elif has(r"not required|waived|exempt", ethics_text) and not has(COMMITTEE, ethics_text):
        issues.append(("Declarations", "Ethics approval", "Concern",
                       "Ethics approval stated as not required/exempt, without naming a committee"))
    else:
        if not has(COMMITTEE, ethics_text):
            issues.append(("Declarations", "Ethics committee name", "Missing",
                           "Ethics statement does not name the committee"))
        if not re.search(APPROVAL_NO, ethics_text, re.IGNORECASE):
            issues.append(("Declarations", "Ethics approval number", "Missing",
                           "No approval/reference number found in the ethics statement"))
        if not has(DATE, ethics_text):
            issues.append(("Declarations", "Ethics approval date", "Missing",
                           "No approval date found in the ethics statement"))

    # --- Consent (only expected for human studies)
    consent_text = sentences_with(r"consent", body)
    if human and not consent_text:
        issues.append(("Declarations", "Consent", "Missing", "No consent statement found"))
    elif consent_text:
        written = has(r"written", consent_text)
        verbal = has(r"verbal|oral", consent_text)
        waived = has(r"waive|not required|exempt", consent_text)
        if waived and (written or verbal):
            issues.append(("Declarations", "Consent", "Concern",
                           "Consent statement is contradictory (mentions both consent and a waiver)"))
        elif waived and not has(COMMITTEE, consent_text):
            issues.append(("Declarations", "Consent", "Concern",
                           "Consent waiver does not say who granted it"))
        elif not (written or verbal or waived):
            issues.append(("Declarations", "Consent mode", "Concern",
                           "Consent mentioned but not whether written or verbal"))
        if verbal and not written:
            issues.append(("Declarations", "Verbal consent", "Concern",
                           "Only verbal consent mentioned"))

    # --- Minors
    if has(MINOR_WORDS, study) and consent_text and not has(r"parent|guardian|legally authori[sz]ed", consent_text):
        issues.append(("Declarations", "Consent for minors", "Concern",
                       "Study appears to involve minors; consent does not mention parents/guardians"))
    return issues


def check_study_details(sections):
    issues = []
    body = " ".join(t for name, paras in sections if name != "References" for t in paras)
    methods = " ".join(t for name, paras in sections if name == "Methods" for t in paras)
    where = methods or body

    review = has(r"systematic review|meta-analys|scoping review|narrative review", body)
    human, animal, study = study_type(sections)
    if article_type(sections) != "research":
        return issues   # case reports, letters and narrative reviews have no sample, study period or criteria

    # --- Sample size ("312 patients", "80 school children", "24 community health workers", "n = 45")
    number = r"(\d[\d,]*|two|three|four|five|six|seven|eight|nine|ten|twelve|fifteen|twenty|thirty|fifty|hundred)"
    units = SAMPLE_WORDS + r"|experiments|replicates|repeats|biological replicates"
    if review:
        pass   # reviews report included studies, checked by peer review
    elif not re.search(r"\bn\s*=\s*\d+|\b" + number + r"\s+([a-z\-]+\s+){0,2}(" + units + r")\b", body, re.IGNORECASE):
        issues.append(("Study details", "Sample size", "Missing", "No sample size found"))

    # --- Study period and data age
    period = sentences_with(r"\b(19|20)\d{2}\b", where)
    period = sentences_with(r"between|from|during|collected|enrolled|recruited|conducted|period|"
                            r"retrospective|prospective|until|to\s+\w+\s+\d{4}|\bin\s+(19|20)\d{2}", period)
    years = [int(y) for y in re.findall(r"\b((?:19|20)\d{2})\b", period)]
    if review:
        pass   # in reviews, years are publication dates, not data collection
    elif not years:
        issues.append(("Study details", "Study duration", "Missing", "No study period found in the Methods"))
    elif min(years) < 2020:
        issues.append(("Study details", "Data older than 2020", "Concern",
                       f"Data collection appears to date from {min(years)}"
                       + (f"–{max(years)}" if max(years) != min(years) else ""),
))

    # --- Inclusion / exclusion criteria (human studies)
    if human:
        if not has(r"inclusion", where) or not has(r"exclusion|excluded", where):
            issues.append(("Study details", "Inclusion/exclusion criteria", "Missing",
                           "Inclusion and/or exclusion criteria not found in the Methods"))

    # --- Questionnaires / interviews
    q_text = sentences_with(r"questionnaire|survey|interview|likert|scale was used", body)
    if q_text and not has(r"supplementa|appendix|annex", q_text):
        issues.append(("Study details", "Questionnaire", "Concern",
                       "Study uses a questionnaire/survey/interview"))

    # --- Animal studies
    if animal and not has(r"euthan|sacrific|humane end", body):
        issues.append(("Study details", "Euthanasia", "Concern",
                       "Animal study without a euthanasia/humane endpoint statement"))

    # --- Registration: only when the study type needs it
    if has(r"randomi[sz]ed (controlled )?trial|clinical trial|\bRCT\b", body):
        if not has(r"CTRI/\d{4}|NCT\d{8}|ISRCTN\d+|ACTRN\d+|ChiCTR|DRKS\d+|EudraCT|trial registration", body):
            issues.append(("Study details", "Trial registration", "Missing",
                           "Appears to be a clinical trial; no registration number found"))
    if has(r"systematic review|meta-analys", body):
        if not has(r"PROSPERO|CRD\d{8,}", body):
            issues.append(("Study details", "PROSPERO registration", "Missing",
                           "Appears to be a systematic review; no PROSPERO number found"))
    return issues


def check_references(sections):
    issues = []
    refs = [t for name, paras in sections if name == "References" for t in paras]
    if not refs:
        issues.append(("References", "Reference list", "Missing", "No References section found"))
        return issues

    numbered = sum(1 for r in refs if re.match(r"^\[?\d+[.)\]]?\s", r)) >= len(refs) / 2
    if not numbered:
        return issues    # author-year style: number checks don't apply

    body = " ".join(t for name, paras in sections if name != "References" for t in paras)
    cited = set()
    for group in re.findall(r"\[([\d,\s–\-]+)\]", body):
        for part in re.split(r"\s*,\s*", group):
            rng = re.match(r"(\d+)\s*[–-]\s*(\d+)", part)
            if rng:
                cited.update(range(int(rng.group(1)), int(rng.group(2)) + 1))
            elif part.strip().isdigit():
                cited.add(int(part.strip()))

    if not cited:
        issues.append(("References", "Citation check", "Concern",
                       "No bracketed citations like [1] found (may use superscripts)"))
        return issues

    total = len(refs)
    beyond = sorted(n for n in cited if n > total)
    never = sorted(set(range(1, total + 1)) - cited)
    if beyond:
        issues.append(("References", "Citation not in list", "Missing",
                       f"Cited in text but not in the list: {', '.join(map(str, beyond))}"))
    if never:
        issues.append(("References", "Reference not cited", "Concern",
                       f"In the list but never cited: {', '.join(map(str, never))}"))
    return issues


def run_all(path):
    sections, _ = split_into_sections(path)
    return check_declarations(sections) + check_study_details(sections) + check_references(sections)


def main():
    if len(sys.argv) < 2:
        print("Usage: python step4_declarations.py <manuscript.docx>")
        return
    path = sys.argv[1]
    try:
        issues = run_all(path)
    except Exception as e:
        print(f"Could not read '{path}': {e}")
        return

    print(f"\nFile: {path}\n")
    if not issues:
        print("No declaration/study-detail issues found.")
        return
    print(f"{len(issues)} issue(s):\n")
    for section, check, status, details in issues:
        print(f"[{status}] {section} - {check}: {details}")


if __name__ == "__main__":
    main()
