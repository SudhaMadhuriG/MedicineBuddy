"""Joke helpers for Symptom Buddy.

Jokes are shown only at the end of a result, only when there are no
red flags, and never when the user has reported feeling worse. This
module contains no Streamlit code so it can be tested on its own.
"""

import json
import os

from .safety import should_show_joke


def _data_path(filename):
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(here, "..", "data", filename)


def load_jokes():
    path = _data_path("jokes.json")
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict) and "jokes" in data:
        return data["jokes"]
    return data


def get_joke(index=0):
    """Return the joke at index, wrapping around the list safely."""
    jokes = load_jokes()
    if not jokes:
        return "Why did the headache go to school? It wanted to be a little less tense."
    return jokes[int(index) % len(jokes)]


def next_joke_index(current_index):
    """Return the next joke index, wrapping around."""
    jokes = load_jokes()
    if not jokes:
        return 0
    return (int(current_index) + 1) % len(jokes)


def joke_for_result(red_flags, jokes_enabled=True, check_in=None, joke_index=0):
    """Return a joke string, or None when a joke should not be shown."""
    if not should_show_joke(red_flags, jokes_enabled, check_in):
        return None
    return get_joke(joke_index)
