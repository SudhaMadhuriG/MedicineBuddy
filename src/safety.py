"""Safety checks for Symptom Buddy.

This module contains only general-information safety logic. It does not
diagnose anyone, it does not recommend a personal dose, and it does not
decide what care a person needs. It flags text and answers that match
well-known red-flag patterns so the app can show an urgent warning and
stop the normal information flow.
"""

DISCLAIMER = (
    "This is general information only, not medical advice. If you are "
    "worried, or symptoms are severe, worsening, or unusual for you, "
    "talk to a doctor or pharmacist. In an emergency, call your local "
    "emergency number."
)

URGENT_MESSAGE = (
    "These symptoms need urgent medical attention - seek care now or "
    "call your local emergency number. Do not wait to see if they get "
    "better on their own."
)

# Each entry is (pattern, plain-language label). Patterns are matched
# case-insensitively against the symptom text and the follow-up answers.
RED_FLAGS = [
    ("worst headache of my life", "Sudden worst headache of your life"),
    ("worst headache ever", "Sudden worst headache of your life"),
    ("thunderclap headache", "Sudden worst headache of your life"),
    ("sudden severe headache", "Sudden severe headache"),
    ("head injury", "Headache after a head injury"),
    ("hit my head", "Headache after a head injury"),
    ("stiff neck", "Fever with a stiff neck"),
    ("neck stiffness", "Fever with a stiff neck"),
    ("confusion", "Confusion"),
    ("confused", "Confusion"),
    ("slurred speech", "Slurred speech"),
    ("weakness on one side", "Weakness or numbness on one side"),
    ("numbness on one side", "Weakness or numbness on one side"),
    ("one-sided weakness", "Weakness or numbness on one side"),
    ("vision loss", "Vision loss"),
    ("lost vision", "Vision loss"),
    ("cannot see", "Vision loss"),
    ("vomiting that won't stop", "Vomiting that will not stop"),
    ("vomiting that wont stop", "Vomiting that will not stop"),
    ("rapidly worsening", "Rapidly worsening headache"),
    ("getting rapidly worse", "Rapidly worsening headache"),
    ("getting worse quickly", "Rapidly worsening headache"),
    ("pregnant", "New severe headache in pregnancy"),
]


def _normalise(text):
    if text is None:
        return ""
    return str(text).strip().lower()


def check_red_flags(symptom_text="", answers=None):
    """Return a list of red-flag labels matched, in RED_FLAGS order.

    ``answers`` may be a dict with boolean or string values, for example
    {"head_injury": True, "vision_changes": "yes"}. Any truthy value whose
    key names a red-flag area is treated as a match, and the free-text
    symptom is also scanned for red-flag phrases.
    """
    matched = []
    text = _normalise(symptom_text)
    for pattern, label in RED_FLAGS:
        if pattern in text and label not in matched:
            matched.append(label)

    if answers:
        # Map common follow-up answer keys to red-flag labels.
        key_map = {
            "head_injury": "Headache after a head injury",
            "vision_changes": "Vision loss",
            "vision_loss": "Vision loss",
            "weakness": "Weakness or numbness on one side",
            "one_sided_weakness": "Weakness or numbness on one side",
            "confusion": "Confusion",
            "slurred_speech": "Slurred speech",
            "stiff_neck": "Fever with a stiff neck",
            "fever_and_stiff_neck": "Fever with a stiff neck",
        }
        for key, label in key_map.items():
            value = answers.get(key)
            if value in (True, "yes", "Yes", "YES"):
                if label not in matched:
                    matched.append(label)
            elif isinstance(value, str) and value.strip().lower() in (
                "worst headache of my life",
                "worst headache ever",
            ):
                if "Sudden worst headache of your life" not in matched:
                    matched.append("Sudden worst headache of your life")

    # Pregnancy is only a red flag here in combination with a new
    # severe headache. The app asks severity separately, so a plain
    # mention of pregnancy alone is handled by the caller: it passes
    # answers={"pregnant": True, "severe": True} for that case.
    if answers and answers.get("pregnant") and answers.get("severe"):
        label = "New severe headache in pregnancy"
        if label not in matched:
            matched.append(label)

    return matched


def has_red_flag(symptom_text="", answers=None):
    """Return True if any red flag is matched."""
    return len(check_red_flags(symptom_text, answers)) > 0


def should_show_joke(red_flags, jokes_enabled=True, check_in=None):
    """Return True only when a joke is appropriate.

    A joke is shown only when there are no red flags, jokes are enabled,
    and the user has not reported feeling worse on check-in.
    """
    if red_flags:
        return False
    if not jokes_enabled:
        return False
    if check_in in ("Worse", "worse"):
        return False
    return True


def should_show_supplements(red_flags):
    """Supplements are shown only when there are no red flags."""
    return not red_flags


def should_show_remedies(red_flags):
    """Remedies are shown only when there are no red flags."""
    return not red_flags


def escalation_needed(check_in=None, severity=None, previous_severity=None):
    """Return True when a check-in suggests escalation is warranted.

    This is a conservative, information-only rule: feeling worse, or a
    severity that has risen by 3 or more points, triggers the escalation
    warning in the app. It is not a medical judgement.
    """
    if check_in in ("Worse", "worse"):
        return True
    if severity is not None and previous_severity is not None:
        try:
            if int(severity) - int(previous_severity) >= 3:
                return True
        except (TypeError, ValueError):
            return False
    return False
