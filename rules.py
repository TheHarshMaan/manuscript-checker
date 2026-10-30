"""
The catalogue of every rule the checker knows.

Each check in the step files reports the ID of the rule it belongs to (e.g. "ethics_approval_date").
A journal profile (profiles/*.yaml) then decides how much each rule matters for that journal:

    must      - Must fix: the journal will not accept the manuscript without it
    should    - Should fix: expected by the journal, an editor will likely ask for it
    advisory  - Advisory: worth a look, but not required
    off       - not checked at all

To add a new check: give it an ID here, report that ID from the check, and set its
severity in profiles/generic.yaml (every other profile inherits from generic).
"""

from collections import namedtuple

# One problem found in a manuscript. `severity` is filled in from the profile.
Issue = namedtuple("Issue", "section check status details rule severity", defaults=(None,))

SEVERITIES = ["must", "should", "advisory", "off"]
SEVERITY_LABEL = {"must": "Must fix", "should": "Should fix", "advisory": "Advisory", "off": "Off"}

# rule ID -> (area, short name, what it checks)
RULES = {
    # Structure
    "section_missing":      ("Structure", "Required sections",
                             "Sections the profile requires for this article type (e.g. IMRaD) are present"),
    "abstract_missing":     ("Structure", "Abstract present", "The manuscript has an abstract"),
    "keywords_missing":     ("Structure", "Keywords present", "The manuscript has keywords"),
    "abstract_length":      ("Structure", "Abstract word limit", "The abstract is within the word limit"),

    # Abbreviations
    "abbr_not_defined":     ("Abbreviations", "Not defined", "Every abbreviation is defined at first use"),
    "abbr_used_early":      ("Abbreviations", "Used before definition",
                             "No abbreviation appears before its definition"),
    "abbr_defined_twice":   ("Abbreviations", "Defined more than once", "Each abbreviation is defined once"),
    "abbr_not_used":        ("Abbreviations", "Defined but not used",
                             "Abbreviations that are defined are used again afterwards"),

    # Figures and tables
    "figtab_numbering":     ("Figures & tables", "Numbering gaps", "Figures and tables are numbered without gaps"),
    "figtab_order":         ("Figures & tables", "Citation order", "Figures and tables are first cited in order"),
    "figtab_not_cited":     ("Figures & tables", "Cited in text", "Every figure and table is cited in the text"),
    "figtab_no_caption":    ("Figures & tables", "Caption present", "Every cited figure and table has a caption"),
    "table_count":          ("Figures & tables", "Table count",
                             "Number of tables in the file matches the tables cited"),

    # Declarations
    "coi_statement":        ("Declarations", "Conflict of interest", "A conflict of interest statement is present"),
    "funding_statement":    ("Declarations", "Funding", "A funding statement is present"),
    "author_contributions": ("Declarations", "Author contributions", "An author contributions statement is present"),
    "acknowledgements":     ("Declarations", "Acknowledgements", "An acknowledgements section is present"),
    "data_availability":    ("Declarations", "Data availability", "A data availability statement is present"),
    "ethics_statement":     ("Declarations", "Ethics statement (no humans/animals)",
                             "An ethics statement is present even when no humans or animals are involved"),
    "ethics_approval":      ("Declarations", "Ethics approval",
                             "Human/animal studies state ethics approval (or who exempted them)"),
    "ethics_committee":     ("Declarations", "Ethics committee name", "The ethics statement names the committee"),
    "ethics_number":        ("Declarations", "Ethics approval number", "The ethics statement gives an approval number"),
    "ethics_date":          ("Declarations", "Ethics approval date", "The ethics statement gives an approval date"),
    "consent":              ("Declarations", "Consent",
                             "Human studies have a clear, non-contradictory consent statement"),
    "consent_mode":         ("Declarations", "Consent mode", "The consent statement says whether written or verbal"),
    "verbal_consent":       ("Declarations", "Verbal consent only", "Flags studies that obtained only verbal consent"),
    "consent_minors":       ("Declarations", "Consent for minors",
                             "Studies involving minors mention parent/guardian consent"),

    # Study details
    "sample_size":          ("Study details", "Sample size", "Research articles state a sample size"),
    "study_period":         ("Study details", "Study period", "The Methods state when the study was done"),
    "data_age":             ("Study details", "Old data",
                             "Flags data collected before the profile's cut-off year"),
    "inclusion_exclusion":  ("Study details", "Inclusion/exclusion criteria",
                             "Human studies state inclusion and exclusion criteria"),
    "questionnaire":        ("Study details", "Questionnaire supplied",
                             "Questionnaires, surveys or interview guides are supplied"),
    "euthanasia":           ("Study details", "Euthanasia", "Animal studies describe euthanasia/humane endpoints"),
    "trial_registration":   ("Study details", "Trial registration", "Clinical trials give a registration number"),
    "prospero":             ("Study details", "PROSPERO registration",
                             "Systematic reviews give a PROSPERO (or similar) number"),

    # References
    "reference_list":       ("References", "Reference list", "The manuscript has a reference list"),
    "citation_not_in_list": ("References", "Citation not in list", "Every numbered citation is in the list"),
    "reference_not_cited":  ("References", "Reference not cited", "Every listed reference is cited"),
    "citation_format":      ("References", "Citation format", "Numbered citations could be read"),
}
