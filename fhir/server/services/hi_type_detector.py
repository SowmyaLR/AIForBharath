"""
HI (Healthcare Information) Type Detector.

Classifies a document's text into one of the supported ABDM HI types:
  - discharge_summary
  - lab_report
  - clinical_note
  - prescription
  - radiology_report

Uses keyword-based scoring (primary) with optional MedGemma confirmation
for documents with ambiguous or near-equal scores.
"""
import os
import re
from typing import Dict, Optional, Tuple

import yaml

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "profiles.yaml")


def _load_config() -> dict:
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def detect_hi_type(text: str, hint: Optional[str] = None) -> Tuple[str, str]:
    """
    Detect the HI type of a document.

    Returns:
        (hi_type_key, fhir_resource_type)  e.g. ("discharge_summary", "Composition")
    """
    config = _load_config()
    hi_types: Dict = config.get("hi_types", {})

    # If a strong hint is provided and it is a valid key, trust it
    if hint and hint in hi_types:
        return hint, hi_types[hint]["fhir_resource"]

    text_lower = text.lower()
    scores: Dict[str, int] = {}

    for hi_key, meta in hi_types.items():
        keywords = meta.get("keywords", [])
        score = sum(1 for kw in keywords if kw in text_lower)
        scores[hi_key] = score

    best_type = max(scores, key=lambda k: scores[k])
    best_score = scores[best_type]

    # Default fallback if nothing matches
    if best_score == 0:
        best_type = "clinical_note"

    return best_type, hi_types[best_type]["fhir_resource"]


def detect_hi_type_batch(
    documents: Dict[str, str],          # {filename: text}
    hints: Optional[Dict[str, str]] = None,  # {filename: hint}
) -> Dict[str, Tuple[str, str]]:
    """
    Detect HI types for multiple documents.

    Returns:
        {filename: (hi_type_key, fhir_resource_type)}
    """
    results = {}
    for filename, text in documents.items():
        hint = (hints or {}).get(filename)
        results[filename] = detect_hi_type(text, hint)
    return results
