# Symptom Buddy

Symptom Buddy is a local-first, Streamlit medical-information assistant.
Type a symptom such as "headache" and it shows, in order: a safety
check, general information, options to discuss with a pharmacist,
natural comfort measures, pharmacies and urgent care nearby, and —
only when it is safe to do so — a light joke.

It also includes a private symptom diary, pattern insights from your
own notes, a printable doctor-visit summary, a check-in with
escalation, and a comfort profile. All diary and preference data stays
on your own computer in a local SQLite file.

## What it does

- Symptom guide for headache, cold, sore throat, stomach upset, back
  pain, tiredness, and blocked nose, with quick chips for each.
- Safety check on every result, with red-flag detection and an urgent
  warning that stops supplements, remedies, and jokes when triggered.
- General information, supplement options to discuss, and natural
  comfort measures, each in its own card.
- Nearby pharmacies (demo data by default) sorted by distance, with
  phone numbers and a "Call to confirm stock" action.
- Nearby urgent-care and clinic demo entries, with a "Go now if..." vs
  "Book a regular appointment if..." guide.
- Symptom diary with severity-over-time data, weekly summaries, and
  pattern insights drawn only from your own logs.
- Doctor-visit summary you can download as text.
- Check-in (Better / Same / Worse) with escalation to urgent care
  when you report feeling worse.
- Today's comfort plan: drink fluids as appropriate, take a screen
  break, and make time for rest — labelled as general wellness
  reminders, not treatment.
- Clear history and Delete all my data buttons that actually delete
  local data.

## What it does NOT do

- It does **not** diagnose you. It never says "you have X".
- It does **not** give you a personal dose for any medicine or
  supplement. Every supplement entry says to ask a pharmacist what
  dose, if any, is right for you.
- It does **not** guarantee pharmacy stock. Every pharmacy entry is
  labelled "Stock not verified - call to confirm" unless a verified
  inventory source is supplied. The count shown is a count of
  pharmacies nearby, never a count of stores that have a medicine.
- It does **not** send your diary, preferences, or medicine names
  anywhere. Location lookup, when you use it, sends only the city or
  ZIP you entered to OpenStreetMap services, as described in the app.
- It does **not** email a doctor summary automatically. You download
  it yourself.

## Safety note

This is general information only, not medical advice. If you are
worried, or symptoms are severe, worsening, or unusual for you, talk
to a doctor or pharmacist. In an emergency, call your local emergency
number.

Red flags checked include: sudden worst headache of your life,
headache after a head injury, fever with a stiff neck, confusion,
slurred speech, weakness or numbness on one side, vision loss,
vomiting that will not stop, a rapidly worsening headache, and a new
severe headache in pregnancy. If any are matched, the app shows a red
urgent card and stops the normal supplement, remedy, and joke flow.

## How to run

### Option 1: Double-click run.bat (Windows)

1. Open the `symptom-buddy` folder in File Explorer.
2. Double-click `run.bat`.
3. It creates a virtual environment (`.venv`) if one does not exist,
   installs the dependencies from `requirements.txt`, and starts the
   app at http://localhost:8501
4. Press Ctrl+C in the run window to stop the app.

### Option 2: From a terminal

```bash
cd symptom-buddy
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.port 8501
```

Then open http://localhost:8501 in your browser.

## How the demo pharmacy data works

`data/demo_pharmacies.json` contains example pharmacies and urgent-care
entries for Springfield, Riverton, and Lakeside, with example
distances. When you search by city or ZIP, the app filters that demo
set and sorts it nearest first. If your search does not match a demo
city, the app still shows the demo set, labelled as demo data, rather
than implying there are no pharmacies anywhere.

To use real pharmacy data later, replace the demo lookup in
`src/pharmacy.py` with a mapping-service call for the city or ZIP the
user entered, and keep the honest stock rule: only label stock as
confirmed when a verified inventory source actually returns it.

## Project layout

```
symptom-buddy/
  app.py                Streamlit app, pages, and result flow
  README.md             This file
  requirements.txt      streamlit only
  run.bat               Windows launcher
  styles.css            Design system and Streamlit chrome hiding
  data/
    symptoms.json       General information for 7 symptoms
    supplements.json    Supplement options to discuss
    remedies.json       Natural comfort measures
    jokes.json          Clean, kind jokes
    demo_pharmacies.json  Demo pharmacies and urgent care
  src/
    __init__.py
    safety.py           Disclaimer, red flags, joke/escalation rules
    knowledge.py        Symptom, supplement, and remedy lookup
    pharmacy.py         Pharmacy search, sorting, urgent-care guide
    jokes.py            Joke selection and when-not-to-show rules
    diary.py            SQLite diary, patterns, doctor summary
    ui.py               HTML card, badge, and header helpers
  tests/
    test_safety.py      Tests that run without Streamlit installed
```

The modules in `src/` do not import Streamlit, so the tests in
`tests/test_safety.py` run with plain Python.

## Tests

```bash
python tests/test_safety.py
```

The tests cover red-flag detection (including "worst headache of my
life"), no-joke-when-red-flag logic, pharmacy distance sorting,
honest stock labelling, and knowledge-base JSON loading.

## Troubleshooting

- **Python not found:** install Python 3.11 or newer from
  https://www.python.org/downloads/ and tick "Add python.exe to PATH"
  during setup, then run `run.bat` again.
- **Port already in use:** stop the other app using port 8501, or run
  `streamlit run app.py --server.port 8502` and open
  http://localhost:8502
- **pip install fails:** check your internet connection, then delete
  the `.venv` folder and run `run.bat` again so the environment is
  recreated cleanly.
- **App opens but shows no styles:** make sure `styles.css` is in the
  same folder as `app.py`, then refresh the browser page.
