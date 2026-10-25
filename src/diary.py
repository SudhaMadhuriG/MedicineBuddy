"""Local symptom diary backed by SQLite.

All data stays in a single local SQLite file chosen by the caller. No
data is sent anywhere. Functions here are pure database helpers with
no Streamlit dependency, so they can be tested directly.
"""

import os
import sqlite3
from collections import Counter
from datetime import datetime, timedelta


DEFAULT_DB = "symptom_buddy.db"

TRIGGERS = [
    "poor sleep",
    "stress",
    "screen time",
    "dehydration",
    "caffeine",
    "missed meal",
    "weather",
    "other",
]


def connect(db_path):
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(db_path):
    """Create the diary tables if they do not exist yet."""
    directory = os.path.dirname(os.path.abspath(db_path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    connection = connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recorded_at TEXT NOT NULL,
                symptom TEXT NOT NULL,
                severity INTEGER,
                duration TEXT,
                triggers TEXT,
                tried TEXT,
                helped TEXT,
                red_flag INTEGER DEFAULT 0
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        connection.commit()
    finally:
        connection.close()


def _split_csv(value):
    if not value:
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]


def log_episode(db_path, symptom, severity=None, duration="", triggers=None,
                tried="", helped="", recorded_at=None, red_flag=False):
    """Insert one episode and return its row id."""
    init_db(db_path)
    if recorded_at is None:
        recorded_at = datetime.now().isoformat(timespec="seconds")
    triggers_text = ", ".join(triggers or [])
    connection = connect(db_path)
    try:
        cursor = connection.execute(
            """
            INSERT INTO episodes
                (recorded_at, symptom, severity, duration, triggers, tried, helped, red_flag)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recorded_at,
                str(symptom),
                int(severity) if severity is not None else None,
                str(duration or ""),
                triggers_text,
                str(tried or ""),
                str(helped or ""),
                1 if red_flag else 0,
            ),
        )
        connection.commit()
        return cursor.lastrowid
    finally:
        connection.close()


def list_episodes(db_path, limit=200):
    """Return episodes newest first, as a list of dicts."""
    init_db(db_path)
    connection = connect(db_path)
    try:
        rows = connection.execute(
            """
            SELECT id, recorded_at, symptom, severity, duration,
                   triggers, tried, helped, red_flag
            FROM episodes
            ORDER BY recorded_at DESC, id DESC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()
    finally:
        connection.close()
    episodes = []
    for row in rows:
        episode = dict(row)
        episode["triggers_list"] = _split_csv(episode.get("triggers"))
        episodes.append(episode)
    return episodes


def severity_over_time(db_path):
    """Return (dates, severities) oldest first, for charting."""
    episodes = list_episodes(db_path, limit=500)
    episodes = [e for e in episodes if e.get("severity") is not None]
    episodes.reverse()
    dates = [e["recorded_at"][:10] for e in episodes]
    severities = [int(e["severity"]) for e in episodes]
    return dates, severities


def weekly_summary(db_path, now=None):
    """Summarise the last 7 days of episodes."""
    if now is None:
        now = datetime.now()
    cutoff = (now - timedelta(days=7)).isoformat(timespec="seconds")
    episodes = list_episodes(db_path, limit=500)
    recent = [e for e in episodes if e["recorded_at"] >= cutoff]
    severities = [int(e["severity"]) for e in recent if e.get("severity") is not None]
    trigger_counts = Counter()
    helped_counts = Counter()
    for episode in recent:
        for trigger in episode["triggers_list"]:
            trigger_counts[trigger] += 1
        if episode.get("helped"):
            helped_counts[episode["helped"]] += 1
    return {
        "episode_count": len(recent),
        "average_severity": round(sum(severities) / len(severities), 1) if severities else None,
        "most_common_triggers": trigger_counts.most_common(3),
        "most_helpful": helped_counts.most_common(3),
        "red_flag_episodes": sum(1 for e in recent if e.get("red_flag")),
    }


def pattern_insights(db_path):
    """Report correlations from the user's own logs only.

    Each insight is phrased as an observed count, never as a cause or
    a diagnosis. An insight is only produced when a trigger appears in
    at least 2 episodes for the same symptom, so a single episode does
    not produce a spurious pattern.
    """
    episodes = list_episodes(db_path, limit=500)
    insights = []
    symptoms = {}
    for episode in episodes:
        symptoms.setdefault(str(episode["symptom"]).lower(), []).append(episode)
    for symptom, symptom_episodes in symptoms.items():
        total = len(symptom_episodes)
        if total < 2:
            continue
        trigger_counts = Counter()
        for episode in symptom_episodes:
            for trigger in episode["triggers_list"]:
                trigger_counts[trigger] += 1
        for trigger, count in trigger_counts.most_common(2):
            if count >= 2:
                display_symptom = symptom_episodes[0]["symptom"]
                insights.append(
                    "{} of your last {} {} episodes were on days you logged {}. "
                    "This is an observed pattern in your own notes, not a cause.".format(
                        count, total, display_symptom, trigger
                    )
                )
    return insights


def doctor_summary_text(db_path, disclaimer):
    """Build a printable doctor-visit summary as plain text."""
    episodes = list_episodes(db_path, limit=200)
    summary = weekly_summary(db_path)
    lines = []
    lines.append(disclaimer)
    lines.append("")
    lines.append("Doctor visit summary - Symptom Buddy")
    lines.append("This summary is general information from your own notes. It is not a diagnosis.")
    lines.append("")
    lines.append("Last 7 days: {} episodes recorded.".format(summary["episode_count"]))
    if summary["average_severity"] is not None:
        lines.append("Average severity (last 7 days): {} / 10".format(summary["average_severity"]))
    if summary["red_flag_episodes"]:
        lines.append("Red-flag episodes in the last 7 days: {}".format(summary["red_flag_episodes"]))
    if summary["most_common_triggers"]:
        lines.append("Most common triggers logged: " + ", ".join(
            "{} ({})".format(name, count) for name, count in summary["most_common_triggers"]
        ))
    lines.append("")
    lines.append("Episode timeline (newest first):")
    if not episodes:
        lines.append("- No episodes logged yet.")
    for episode in episodes:
        triggers = ", ".join(episode["triggers_list"]) or "no triggers logged"
        lines.append(
            "- {} | {} | severity {} | duration {} | triggers: {} | tried: {} | helped: {}".format(
                episode["recorded_at"],
                episode["symptom"],
                episode.get("severity", "?"),
                episode.get("duration") or "not recorded",
                triggers,
                episode.get("tried") or "nothing recorded",
                episode.get("helped") or "not recorded",
            )
        )
    lines.append("")
    lines.append("Questions to ask your clinician:")
    lines.append("- Could these episodes be related to anything I should check?")
    lines.append("- Are there medicines or supplements I should avoid or discuss?")
    lines.append("- What warning signs should make me seek care sooner?")
    lines.append("- How often should I follow up about this?")
    lines.append("")
    lines.append("Patterns from your own notes:")
    insights = pattern_insights(db_path)
    if insights:
        for insight in insights:
            lines.append("- " + insight)
    else:
        lines.append("- No repeated pattern yet - log a few more episodes to see one.")
    return "\n".join(lines)


def set_preference(db_path, key, value):
    init_db(db_path)
    connection = connect(db_path)
    try:
        connection.execute(
            "INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)",
            (str(key), str(value)),
        )
        connection.commit()
    finally:
        connection.close()


def get_preference(db_path, key, default=""):
    init_db(db_path)
    connection = connect(db_path)
    try:
        row = connection.execute(
            "SELECT value FROM preferences WHERE key = ?", (str(key),)
        ).fetchone()
    finally:
        connection.close()
    if row is None:
        return default
    return row["value"]


def clear_history(db_path):
    """Delete all logged episodes, keeping preferences."""
    init_db(db_path)
    connection = connect(db_path)
    try:
        connection.execute("DELETE FROM episodes")
        connection.commit()
    finally:
        connection.close()


def delete_all_data(db_path):
    """Delete all episodes and preferences, then recreate empty tables."""
    init_db(db_path)
    connection = connect(db_path)
    try:
        connection.execute("DELETE FROM episodes")
        connection.execute("DELETE FROM preferences")
        connection.commit()
    finally:
        connection.close()
