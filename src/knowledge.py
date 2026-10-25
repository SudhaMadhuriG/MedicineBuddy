"""Symptom knowledge base loading and lookup.

All content here is general information only. Nothing in this module
diagnoses a person or names a condition they have. Unknown symptoms
return a clear unknown result so the app can show general self-care
information instead of guessing.
"""

import json
import os


def _data_path(filename):
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "data", filename)


def load_json(filename):
    path = _data_path(filename)
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_symptoms():
    """Return the symptoms data dict keyed by symptom key."""
    data = load_json("symptoms.json")
    if isinstance(data, dict) and "symptoms" in data:
        return data["symptoms"]
    return data


def list_symptoms():
    """Return a sorted list of display names for known symptoms."""
    symptoms = load_symptoms()
    names = []
    for key, entry in symptoms.items():
        names.append(entry.get("display_name", key))
    return sorted(names)


def normalise_symptom(text):
    """Normalise free text to a symptom key, or return None."""
    if not text:
        return None
    cleaned = str(text).strip().lower()
    # Strip common prefixes a user might type.
    for prefix in ("i have a ", "i have ", "a ", "my "):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip()
            break
    symptoms = load_symptoms()
    # Direct key match.
    if cleaned in symptoms:
        return cleaned
    # Display-name match.
    for key, entry in symptoms.items():
        if cleaned == str(entry.get("display_name", "")).lower():
            return key
    # Alias match.
    for key, entry in symptoms.items():
        for alias in entry.get("aliases", []):
            if cleaned == str(alias).lower():
                return key
    # Simple contains match, longest key first, to catch "bad headache".
    candidates = []
    for key, entry in symptoms.items():
        if key in cleaned:
            candidates.append(key)
        else:
            for alias in entry.get("aliases", []):
                if str(alias).lower() in cleaned:
                    candidates.append(key)
                    break
    if candidates:
        candidates.sort(key=len, reverse=True)
        return candidates[0]
    return None


def get_symptom_info(text):
    """Return (key, entry) for a symptom, or (None, unknown_entry).

    The unknown entry is explicit so the caller never has to invent a
    diagnosis for a symptom that is not in the knowledge base.
    """
    key = normalise_symptom(text)
    symptoms = load_symptoms()
    if key is not None and key in symptoms:
        return key, symptoms[key]
    unknown = {
        "display_name": "Unknown symptom",
        "general_causes": [
            "We do not have specific general information for this symptom in our local guide."
        ],
        "what_usually_helps": [
            "Rest, drink fluids as appropriate, and note when the symptom started, how severe it is, and whether it changes.",
            "Keep a short note of what you tried and whether it helped, so you can share it with a clinician if needed.",
        ],
        "see_doctor_if": [
            "The symptom is severe, worsening, or unusual for you.",
            "It lasts more than a few days, keeps coming back, or interferes with work, sleep, or daily life.",
            "You develop any red-flag symptoms, such as those listed in the safety check.",
        ],
        "aliases": [],
    }
    return None, unknown


def load_supplements():
    """Return the supplements data dict keyed by symptom key."""
    data = load_json("supplements.json")
    if isinstance(data, dict) and "supplements" in data:
        return data["supplements"]
    return data


def get_supplements_for(symptom_key):
    """Return the supplement list for a symptom key, or an empty list."""
    if not symptom_key:
        return []
    supplements = load_supplements()
    return supplements.get(symptom_key, [])


def filter_supplements(supplements, pregnant=False, child=False, blood_thinners=False):
    """Filter supplements for sensitive groups.

    When any sensitive flag is set, most options are hidden and the
    caller should show "Please ask a pharmacist directly" instead of
    recommending an option. This function returns only options explicitly
    marked as suitable to discuss in that situation; in practice the
    shipped data marks none as suitable, so the result is empty and the
    app shows the pharmacist message. That empty result is intentional
    and safe.
    """
    if not (pregnant or child or blood_thinners):
        return list(supplements)
    kept = []
    for item in supplements:
        if item.get("discuss_if_sensitive"):
            kept.append(item)
    return kept


def load_remedies():
    """Return the remedies data dict keyed by symptom key."""
    data = load_json("remedies.json")
    if isinstance(data, dict) and "remedies" in data:
        return data["remedies"]
    return data


def get_remedies_for(symptom_key):
    """Return the remedy list for a symptom key, or an empty list."""
    if not symptom_key:
        return []
    remedies = load_remedies()
    return remedies.get(symptom_key, [])
