<div align="center">

# Health Worker Report Agent

Turns messy field reports from Community Health Workers into structured, urgency-ranked summaries for supervisors.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-F55036?style=flat-square)
![Requests](https://img.shields.io/badge/Requests-2.28%2B-2C5BB4?style=flat-square)

</div>

## Overview

Lady Health Workers in Pakistan visit households every day and submit free-text field reports to a supervisor. The reports are inconsistent and often miss key details, so the supervisor has to read each one to decide which cases are urgent. This app takes a pasted report, extracts the patient and visit details into a fixed JSON schema, asks follow-up questions when critical fields are missing, and classifies the case as routine, clinic referral or emergency. The result is a structured record and a short summary written for the supervisor.

## Demo

[Open the live app](https://chw-report-agent.streamlit.app)

## Key Features

- **Free-text intake:** accepts a pasted field report in any format, with no required template.
- **Clarification stage:** if patient name, age or chief complaint is missing, the agent returns specific questions and the user answers them inline.
- **Skip option:** the user can skip the questions, and the report is generated with the missing information listed under gaps.
- **Three-tier urgency rules:** EMERGENCY, CLINIC_REFERRAL and ROUTINE criteria are written out in the system prompt, and ambiguous cases default to the higher tier.
- **Typed JSON output:** the model must reply with a fixed schema (patient details, symptoms, vitals, medications given, urgency, urgency reason, action, escalation flag and note, gaps, supervisor summary).
- **Tolerant parsing:** the response parser also handles JSON wrapped in markdown code fences.
- **Color-coded result view:** emergency, referral and routine cases are shown with distinct alerts, plus an expandable list of information gaps and the supervisor summary.
- **Session reset:** a "Process Another Report" button clears the session state for the next report.

## Tech Stack

| Area | Technology |
| --- | --- |
| Language | Python |
| UI | Streamlit (1.35 or newer) |
| LLM API | Groq chat completions, model `llama-3.3-70b-versatile` |
| HTTP client | Requests (2.28 or newer) |
| Output format | Structured JSON schema enforced through the system prompt |
| Deployment | Streamlit Cloud |

## Project Structure

```text
.
|-- app.py              # Streamlit app: system prompt, Groq call, JSON parsing, three-phase UI
|-- requirements.txt    # streamlit and requests
|-- README.md
`-- .streamlit/
    `-- secrets.toml    # created locally, holds GROQ_API_KEY (not committed)
```

## Getting Started

### Prerequisites

- Python 3 and pip
- A Groq API key

### Installation

```bash
git clone https://github.com/shahramshafiq/chw-report-agent.git
cd chw-report-agent
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` with your key. The app reads it as `st.secrets["GROQ_API_KEY"]`:

```toml
GROQ_API_KEY = "your-key-here"
```

### Run

```bash
streamlit run app.py
```

## Usage

1. Paste a field report into the text box, for example: `Visited house 12, woman Zainab around 40 yrs, fever and body pain since 2 days, gave brufen, husband mentioned she is pregnant...`
2. Click **Process Report**.
3. If the agent needs more information, answer its questions and click **Submit Answers**, or click **Skip, generate anyway**.
4. Read the urgency banner, patient details, recommended action, information gaps and supervisor summary.
5. Click **Process Another Report** to start over.

## Limitations and Roadmap

- Urgency is decided by the model following the prompt rules. The code does not run a separate rule-based check on the returned tier, so every case still needs a human reader.
- The model name, API endpoint and token limit are fixed in `app.py`, and the repository has no automated tests yet.
- Reports are kept only in Streamlit session state. Nothing is stored or exported.

## Author

**Shahram Shafiq** - [GitHub](https://github.com/shahramshafiq) | [LinkedIn](https://www.linkedin.com/in/shahramshafiq/)
