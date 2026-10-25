"""Symptom Buddy - Streamlit medical-information assistant.

General information only. This app does not diagnose anyone, does not
recommend a personal dose, and does not guarantee pharmacy stock.
Safety logic lives in src/safety.py and is checked before any
supplement, remedy, or joke is shown.
"""

import os
import sys

import streamlit as st

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from src import diary as diary_module
from src import jokes as jokes_module
from src import knowledge as knowledge_module
from src import pharmacy as pharmacy_module
from src import safety as safety_module
from src import ui as ui_module

DB_PATH = os.path.join(HERE, "symptom_buddy.db")

QUICK_CHIPS = [
    "Headache",
    "Cold",
    "Sore throat",
    "Stomach upset",
    "Back pain",
    "Tiredness",
    "Blocked nose",
]

PAGES = [
    ("Symptom guide", "🧭", "Check a symptom"),
    ("Symptom diary", "📓", "Track and spot patterns"),
    ("Doctor visit summary", "🩺", "Print for your clinician"),
    ("Comfort profile", "😌", "Your preferences, stored locally"),
]


def load_styles():
    css_path = os.path.join(HERE, "styles.css")
    if os.path.exists(css_path):
        with open(css_path, "r", encoding="utf-8") as handle:
            css = handle.read()
        st.markdown("<style>{}</style>".format(css), unsafe_allow_html=True)


def init_state():
    defaults = {
        "page": "Symptom guide",
        "symptom_input": "",
        "result": None,
        "joke_index": 0,
        "jokes_enabled": True,
        "check_in": None,
        "confirm_delete": False,
        "confirm_clear": False,
        "pregnant": False,
        "child": False,
        "blood_thinners": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def sidebar():
    with st.sidebar:
        st.markdown("## Your private workspace")
        st.markdown(
            "All diary, preferences, and medicine names are stored only "
            "in this computer's SQLite file. Optional location lookup "
            "sends only your entered city/ZIP to OpenStreetMap services."
        )
        st.markdown("---")
        for page_name, icon, subtitle in PAGES:
            is_active = st.session_state["page"] == page_name
            label = "{} {} - {}".format(icon, page_name, subtitle)
            if st.button(
                label,
                key="nav_{}".format(page_name),
                type="primary" if is_active else "secondary",
                use_container_width=True,
            ):
                st.session_state["page"] = page_name
                st.rerun()
        st.markdown("---")
        st.markdown("### Local history")
        if st.button("Clear history", key="clear_history_btn", use_container_width=True):
            if not st.session_state["confirm_clear"]:
                st.session_state["confirm_clear"] = True
                st.warning("Click Clear history again to confirm deleting all logged episodes.")
            else:
                diary_module.clear_history(DB_PATH)
                st.session_state["confirm_clear"] = False
                st.success("History cleared.")
        if st.button("Delete all my data", key="delete_data_btn", use_container_width=True):
            if not st.session_state["confirm_delete"]:
                st.session_state["confirm_delete"] = True
                st.warning("Click Delete all my data again to confirm deleting all episodes and preferences.")
            else:
                diary_module.delete_all_data(DB_PATH)
                st.session_state["confirm_delete"] = False
                st.success("All local data deleted.")


def show_disclaimer():
    st.markdown(
        ui_module.card_html(
            "General information only",
            safety_module.DISCLAIMER,
            icon="⚕️",
            variant="warning",
        ),
        unsafe_allow_html=True,
    )


def show_comfort_plan():
    body = (
        "<ul>"
        "<li>Drink fluids as appropriate</li>"
        "<li>Take a screen break</li>"
        "<li>Make time for rest</li>"
        "</ul>"
        "<p><small>General wellness reminders, not treatment.</small></p>"
    )
    st.markdown(
        ui_module.card_html("Today's comfort plan", body, icon="🌿", variant="mint"),
        unsafe_allow_html=True,
    )


def symptom_guide_page():
    show_disclaimer()
    st.markdown(
        '<div class="sb-hero"><h1>Symptom Buddy</h1>'
        "<p>Tell me how you're feeling, and I'll help you sort the next step - calmly.</p></div>",
        unsafe_allow_html=True,
    )
    show_comfort_plan()

    st.markdown("### What are you feeling?")
    symptom_input = st.text_input(
        "What are you feeling? e.g. headache",
        value=st.session_state["symptom_input"],
        placeholder="headache",
        key="symptom_text_input",
        label_visibility="collapsed",
    )
    st.markdown("Quick choices:")
    chip_columns = st.columns(len(QUICK_CHIPS))
    for column, chip in zip(chip_columns, QUICK_CHIPS):
        with column:
            if st.button(chip, key="chip_{}".format(chip)):
                st.session_state["symptom_input"] = chip
                st.rerun()

    st.markdown("### 1. Safety check")
    st.markdown("Answer these before you see results. They help the safety check work.")
    duration = st.selectbox(
        "How long have you felt this? (optional)",
        ["", "Less than a day", "1-3 days", "More than 3 days", "More than a week"],
        key="duration_select",
    )
    severity = st.slider("How severe is it? (1 = mild, 10 = very severe)", 1, 10, 5, key="severity_slider")
    fever = st.checkbox("I have a fever", key="fever_check")
    st.markdown("Tick any that apply:")
    head_injury = st.checkbox("Head injury", key="injury_check")
    vision_changes = st.checkbox("Vision changes or vision loss", key="vision_check")
    weakness = st.checkbox("Weakness or numbness on one side", key="weakness_check")
    confusion = st.checkbox("Confusion", key="confusion_check")
    slurred = st.checkbox("Slurred speech", key="slurred_check")
    stiff_neck = st.checkbox("Stiff neck", key="stiff_neck_check")

    st.markdown("### Sensitive situations (optional)")
    st.markdown("These only affect which options are shown. They are stored locally only if you save a comfort profile.")
    pregnant = st.checkbox("Pregnant", value=st.session_state["pregnant"], key="pregnant_check")
    child = st.checkbox("For a child", value=st.session_state["child"], key="child_check")
    blood_thinners = st.checkbox("Taking blood thinners", value=st.session_state["blood_thinners"], key="thinners_check")
    st.session_state["pregnant"] = pregnant
    st.session_state["child"] = child
    st.session_state["blood_thinners"] = blood_thinners

    location = st.text_input(
        "City or ZIP for nearby pharmacies (optional)",
        placeholder="e.g. Springfield or 12345",
        key="location_input",
    )
    st.markdown(
        "Voice input: on Windows, click the symptom box and press Win + H to use "
        "Windows voice typing, if enabled. Windows voice typing may use online speech services."
    )

    if st.button("Check my symptom", type="primary", use_container_width=True):
        symptom_text = symptom_input.strip()
        if not symptom_text:
            st.warning("Please type a symptom, or tap one of the quick choices above.")
            return
        st.session_state["symptom_input"] = symptom_text
        answers = {
            "head_injury": head_injury,
            "vision_changes": vision_changes,
            "weakness": weakness,
            "confusion": confusion,
            "slurred_speech": slurred,
            "stiff_neck": stiff_neck and fever,
        }
        if pregnant and severity >= 8:
            answers["pregnant"] = True
            answers["severe"] = True
        red_flags = safety_module.check_red_flags(symptom_text, answers)
        key, info = knowledge_module.get_symptom_info(symptom_text)
        st.session_state["result"] = {
            "symptom_text": symptom_text,
            "symptom_key": key,
            "info": info,
            "red_flags": red_flags,
            "duration": duration,
            "severity": severity,
            "fever": fever,
            "location": location,
            "pregnant": pregnant,
            "child": child,
            "blood_thinners": blood_thinners,
        }
        st.session_state["check_in"] = None
        st.rerun()

    result = st.session_state.get("result")
    if not result:
        return

    st.markdown("---")
    st.markdown(ui_module.section_header_html("1", "Safety check"), unsafe_allow_html=True)
    red_flags = result["red_flags"]
    if red_flags:
        body = "<p>{}</p><ul>{}</ul>".format(
            safety_module.URGENT_MESSAGE,
            "".join("<li>{}</li>".format(flag) for flag in red_flags),
        )
        st.markdown(
            ui_module.card_html("Urgent warning", body, icon="🚨", variant="urgent"),
            unsafe_allow_html=True,
        )
        st.markdown("### Urgent care nearby")
        for entry in pharmacy_module.search_urgent_care(result["location"]):
            st.markdown(ui_module.urgent_care_card_html(entry), unsafe_allow_html=True)
        st.markdown(
            "This app cannot tell you where to go for care. If you are worried, "
            "seek care now or call your local emergency number."
        )
        return

    st.markdown(
        ui_module.card_html(
            "No red flags found from your answers",
            "No red-flag pattern was matched from what you entered. This does not rule out "
            "a serious problem. If symptoms are severe, worsening, or unusual for you, "
            "talk to a doctor or pharmacist.",
            icon="✅",
            variant="mint",
        ),
        unsafe_allow_html=True,
    )

    info = result["info"]
    st.markdown(ui_module.section_header_html("2", "General info", info["display_name"]), unsafe_allow_html=True)
    if result["symptom_key"] is None:
        st.markdown(
            ui_module.card_html(
                "We do not have specific information for this symptom",
                "The general self-care information below is shown instead of guessing a diagnosis.",
                icon="ℹ️",
                variant="warning",
            ),
            unsafe_allow_html=True,
        )
    st.markdown(ui_module.card_html("What this can mean in general", "<ul>{}</ul>".format(
        "".join("<li>{}</li>".format(item) for item in info["general_causes"])
    ), icon="ℹ️"), unsafe_allow_html=True)
    st.markdown(ui_module.card_html("What usually helps in general", "<ul>{}</ul>".format(
        "".join("<li>{}</li>".format(item) for item in info["what_usually_helps"])
    ), icon="💡"), unsafe_allow_html=True)
    st.markdown(ui_module.card_html("See a doctor if", "<ul>{}</ul>".format(
        "".join("<li>{}</li>".format(item) for item in info["see_doctor_if"])
    ), icon="🩺"), unsafe_allow_html=True)

    st.markdown(ui_module.section_header_html("3", "Options to discuss"), unsafe_allow_html=True)
    supplements = knowledge_module.get_supplements_for(result["symptom_key"])
    if result["pregnant"] or result["child"] or result["blood_thinners"]:
        st.markdown(
            ui_module.card_html(
                "Please ask a pharmacist directly",
                "Because you selected a sensitive situation, most supplement and medicine "
                "options are hidden here. Please ask a pharmacist directly before starting anything new.",
                icon="⚠️",
                variant="warning",
            ),
            unsafe_allow_html=True,
        )
    elif supplements:
        for item in supplements:
            body = (
                "<p><strong>Commonly used for:</strong> {}</p>"
                "<p><strong>Cautions:</strong> {}</p>"
                "<p><strong>Ask pharmacist about:</strong> {}</p>"
                "<p><small>Ask a pharmacist what dose, if any, is right for you. "
                "No personal dose is given here.</small></p>".format(
                    item["commonly_used_for"], item["cautions"], item["ask_pharmacist_about"]
                )
            )
            st.markdown(ui_module.card_html(item["name"], body, icon="💊"), unsafe_allow_html=True)
    else:
        st.markdown("No specific supplement options are listed for this symptom in the local guide. Ask a pharmacist if you are considering anything new.")

    st.markdown(ui_module.section_header_html("4", "Natural comfort", "Comfort measures, not medical treatment"), unsafe_allow_html=True)
    remedies = knowledge_module.get_remedies_for(result["symptom_key"])
    if remedies:
        for item in remedies:
            body = "<p>{}</p>".format(item["description"])
            if item.get("caution"):
                body += "<p><strong>Caution:</strong> {}</p>".format(item["caution"])
            st.markdown(ui_module.card_html(item["name"], body, icon=item.get("icon", "🌿")), unsafe_allow_html=True)
    else:
        st.markdown("No specific natural comfort measures are listed for this symptom in the local guide.")

    st.markdown(ui_module.section_header_html("5", "Nearby help"), unsafe_allow_html=True)
    pharmacies = pharmacy_module.search_pharmacies(result["location"])
    st.markdown(
        "**{} pharmacies nearby** (Demo data - distances are examples. Stock is not verified for any entry.)".format(len(pharmacies))
    )
    for pharmacy in pharmacies:
        st.markdown(ui_module.pharmacy_card_html(pharmacy), unsafe_allow_html=True)
        if pharmacy.get("phone"):
            st.markdown("Call to confirm stock: {}".format(pharmacy["phone"]))
    st.markdown("### When to go now vs book an appointment")
    st.markdown("**Go now if:**")
    for item in pharmacy_module.GO_NOW_GUIDE:
        st.markdown("- {}".format(item))
    st.markdown("**Book a regular appointment if:**")
    for item in pharmacy_module.BOOK_APPOINTMENT_GUIDE:
        st.markdown("- {}".format(item))
    st.markdown("### Urgent care nearby")
    for entry in pharmacy_module.search_urgent_care(result["location"]):
        st.markdown(ui_module.urgent_care_card_html(entry), unsafe_allow_html=True)

    st.markdown("### How are you feeling now? (check-in)")
    check_in = st.radio(
        "How are you feeling now?",
        ["Not yet checked", "Better", "Same", "Worse"],
        index=0,
        key="check_in_radio",
        horizontal=True,
    )
    if check_in != "Not yet checked":
        st.session_state["check_in"] = check_in
    if st.session_state["check_in"] == "Worse":
        st.markdown(
            ui_module.card_html(
                "Your symptoms are worsening - please consider seeking medical care promptly",
                "You reported feeling worse. Please consider seeking medical care promptly, "
                "or call your local emergency number if you are worried.",
                icon="🚨",
                variant="urgent",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("### Log this in your diary")
    triggers = st.multiselect(
        "Possible triggers logged today (optional)",
        diary_module.TRIGGERS,
        key="diary_triggers",
    )
    tried = st.text_input("What did you try? (optional)", key="diary_tried")
    helped = st.selectbox(
        "Did it help?",
        ["", "Yes", "A little", "No", "Not sure"],
        key="diary_helped",
    )
    if st.button("Save to diary", key="save_diary_btn"):
        diary_module.log_episode(
            DB_PATH,
            symptom=result["symptom_text"],
            severity=result["severity"],
            duration=result["duration"],
            triggers=triggers,
            tried=tried,
            helped=helped,
            red_flag=bool(red_flags),
        )
        st.success("Saved to your diary.")

    st.markdown(ui_module.section_header_html("6", "Lighten the mood"), unsafe_allow_html=True)
    joke = jokes_module.joke_for_result(
        red_flags,
        jokes_enabled=st.session_state["jokes_enabled"],
        check_in=st.session_state["check_in"],
        joke_index=st.session_state["joke_index"],
    )
    if joke is None:
        if st.session_state["check_in"] == "Worse":
            st.markdown("No joke is shown because you reported feeling worse. Focus on getting care first.")
        elif not st.session_state["jokes_enabled"]:
            st.markdown("Jokes are turned off in your comfort profile.")
        else:
            st.markdown("No joke is shown because a safety check was triggered.")
    else:
        st.markdown(ui_module.card_html("A little lift", joke, icon="😄", variant="mint"), unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Tell me another joke", key="another_joke_btn"):
                st.session_state["joke_index"] = jokes_module.next_joke_index(st.session_state["joke_index"])
                st.rerun()
        with col_b:
            if st.button("No jokes, thanks", key="no_jokes_btn"):
                st.session_state["jokes_enabled"] = False
                st.rerun()


def diary_page():
    show_disclaimer()
    st.markdown("## 📓 Symptom diary")
    st.markdown("Your diary is stored locally only. Patterns below report only what is in your own notes, never a cause.")
    episodes = diary_module.list_episodes(DB_PATH)
    summary = diary_module.weekly_summary(DB_PATH)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("Episodes (last 7 days)", summary["episode_count"])
    with col_b:
        st.metric("Average severity (last 7 days)", summary["average_severity"] if summary["average_severity"] is not None else "No data")
    with col_c:
        st.metric("Red-flag episodes (last 7 days)", summary["red_flag_episodes"])
    if summary["most_common_triggers"]:
        st.markdown("**Most common triggers logged:** " + ", ".join(
            "{} ({})".format(name, count) for name, count in summary["most_common_triggers"]
        ))
    st.markdown("### Patterns from your own notes")
    insights = diary_module.pattern_insights(DB_PATH)
    if insights:
        for insight in insights:
            st.markdown("- {}".format(insight))
    else:
        st.markdown("No repeated pattern yet - log a few more episodes to see one.")
    st.markdown("### Severity over time")
    dates, severities = diary_module.severity_over_time(DB_PATH)
    if severities:
        try:
            st.line_chart(severities)
        except Exception:
            st.markdown("Severity values: {}".format(", ".join(str(value) for value in severities)))
        st.markdown("Dates: {}".format(", ".join(dates)))
    else:
        st.markdown("No severity data yet. Log an episode from the Symptom guide page.")
    st.markdown("### All episodes (newest first)")
    if not episodes:
        st.markdown("No episodes logged yet.")
    for episode in episodes:
        st.markdown(
            "- {} | {} | severity {} | duration {} | triggers: {} | tried: {} | helped: {}".format(
                episode["recorded_at"],
                episode["symptom"],
                episode.get("severity", "?"),
                episode.get("duration") or "not recorded",
                ", ".join(episode["triggers_list"]) or "none logged",
                episode.get("tried") or "nothing recorded",
                episode.get("helped") or "not recorded",
            )
        )


def doctor_summary_page():
    show_disclaimer()
    st.markdown("## 🩺 Doctor visit summary")
    st.markdown("This summary is built from your own diary notes. It is not a diagnosis.")
    summary_text = diary_module.doctor_summary_text(DB_PATH, safety_module.DISCLAIMER)
    st.text_area("Doctor visit summary", value=summary_text, height=400, key="doctor_summary_area")
    st.download_button(
        "Download summary as text",
        data=summary_text,
        file_name="doctor_visit_summary.txt",
        mime="text/plain",
    )


def comfort_profile_page():
    show_disclaimer()
    st.markdown("## 😌 Comfort profile")
    st.markdown("Optional preferences, stored locally only. They only affect what is shown and how it is displayed.")
    allergies = st.text_input("Allergies you want to note (optional)", key="profile_allergies")
    conditions = st.text_input("Conditions you want to note (optional)", key="profile_conditions")
    jokes_enabled = st.checkbox("Show jokes", value=st.session_state["jokes_enabled"], key="profile_jokes")
    large_text = st.checkbox("Large text mode", key="profile_large_text")
    if st.button("Save comfort profile", type="primary"):
        diary_module.set_preference(DB_PATH, "allergies", allergies)
        diary_module.set_preference(DB_PATH, "conditions", conditions)
        diary_module.set_preference(DB_PATH, "jokes_enabled", "yes" if jokes_enabled else "no")
        diary_module.set_preference(DB_PATH, "large_text", "yes" if large_text else "no")
        st.session_state["jokes_enabled"] = jokes_enabled
        st.success("Comfort profile saved locally.")
    if large_text:
        st.markdown("Large text mode is on for this session. Increase your browser zoom for the largest text.")
    st.markdown("Saved allergies: {}".format(diary_module.get_preference(DB_PATH, "allergies", "none saved")))
    st.markdown("Saved conditions: {}".format(diary_module.get_preference(DB_PATH, "conditions", "none saved")))


def main():
    st.set_page_config(page_title="Symptom Buddy", page_icon="⚕️", layout="wide")
    load_styles()
    init_state()
    diary_module.init_db(DB_PATH)
    sidebar()
    page = st.session_state["page"]
    if page == "Symptom guide":
        symptom_guide_page()
    elif page == "Symptom diary":
        diary_page()
    elif page == "Doctor visit summary":
        doctor_summary_page()
    elif page == "Comfort profile":
        comfort_profile_page()
    else:
        symptom_guide_page()
    st.markdown("---")
    st.markdown("<small>{}</small>".format(safety_module.DISCLAIMER), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
