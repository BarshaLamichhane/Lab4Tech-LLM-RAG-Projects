# HireReadyAI Raw Prototype

This folder contains the initial development phase for the HireReadyAI interview assistant idea.

It is intentionally kept separate from the current full application in `HireReadyAI/`.

## Purpose

The raw prototype was used to explore:

- adaptive interview-question generation
- personalized technical summaries
- simple answer feedback
- Streamlit-based UI flow
- early prompt-engineering experiments
- Gemini API integration

The production-style version now lives in:

```text
HireReadyAI/
```

## Tech Stack

- Python
- Streamlit
- Google Gemini API
- Prompt engineering

## Run

From the repository root:

```bash
source venv/bin/activate
streamlit run HireReadyAI-raw-prototype/app.py
```

## Status

This is a historical/raw prototype. Current active development is focused on the full FastAPI + React platform in `HireReadyAI/`.

Do not use this folder as the main app entry point.
