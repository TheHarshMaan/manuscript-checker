"""
Loads settings.json so journal-specific options can change without editing code.
If the file is missing or broken, sensible defaults are used.
"""

import json
from pathlib import Path

DEFAULTS = {
    "abstract_word_limit": 250,
    "extra_ignore_abbreviations": [],
    "skip_gene_and_chemical_symbols": True,
}


def load_settings():
    path = Path(__file__).with_name("settings.json")
    settings = dict(DEFAULTS)
    try:
        settings.update(json.loads(path.read_text(encoding="utf-8")))
    except FileNotFoundError:
        pass
    except json.JSONDecodeError as e:
        print(f"Warning: settings.json has a mistake ({e}); using default settings.")
    return settings
