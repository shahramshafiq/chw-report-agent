# CHW Field Report Agent

**Live app:** https://chw-report-agent.streamlit.app

---

## The Problem

Pakistan has over 100,000 Lady Health Workers who do household visits daily and submit field reports to supervisors. These reports are handwritten, inconsistent, and frequently missing critical information. A supervisor managing 25-40 workers goes through dozens of these every day, manually figuring out which cases need urgent action and which are routine.

The bottleneck is not the visit. It is what happens to the information after it.

I built an agent that handles that bottleneck.

---

## Who Uses It

Primary user: the LHW supervisor — the person reading reports, deciding what needs follow-up, and dispatching action.

Secondary user: the LHW herself, who can use it to verify her report before submitting.

---

## How It Works

**Stage 1 — Parse.** The user pastes a free-text field report. Messy, incomplete, mixed language, whatever format came naturally. The agent extracts every health-relevant field: patient name, age, complaint, symptoms, medications given, vitals.

**Stage 2 — Gap detection.** If critical fields are missing, the agent asks targeted questions rather than guessing. The user answers inline, or skips and the agent proceeds with explicit gap annotations.

**Stage 3 — Urgency classification.** Three tiers:
- ROUTINE: minor complaints, preventive care, standard follow-ups
- CLINIC_REFERRAL: symptoms persisting beyond 3 days, treatment failure, chronic disease
- EMERGENCY: unconsciousness, seizures, breathing difficulty, high fever in a child, pregnancy complications

Emergency triggers are explicitly defined in the system prompt rather than left to free LLM inference. When urgency is ambiguous, the agent defaults to the higher tier.

**Stage 4 — Output.** A structured patient record and a plain-language supervisor summary. Emergency cases surface an escalation flag with a specific note about the trigger.

**What the agent decides autonomously:** parsing, gap identification, question generation, urgency classification, report structuring, summary generation.

**What it escalates to a human:** all EMERGENCY cases, CLINIC_REFERRAL cases with full context attached, cases with irresolvable data gaps flagged explicitly.

**Stack:** Python, Streamlit, Groq API (Llama 3.3 70B), deployed on Streamlit Cloud.

---

## Failure Handling

- Messy or incomplete input: asks targeted follow-up questions
- User skips clarification: generates report with data gaps explicitly annotated
- Ambiguous urgency: defaults to the higher tier
- Off-topic input: system prompt constrains the agent to health reports only

---

## What I Learned

Two things stuck with me.

Locking the agent to a typed JSON output schema was the most important call I made. Free-text LLM output downstream creates fragile parsing. A strict schema made the urgency logic reliable and removed the need for any regex hacks.

The clarification flow taught me something less obvious: knowing when to stop and ask is as important as what the agent does when it has enough information. In a health context, asking when uncertain is always safer than guessing and proceeding. I built that as a first-class stage, not an afterthought, and it changed how the whole system behaves.

---

## Run Locally

```bash
pip install streamlit requests
streamlit run app.py
```

Add your Groq API key to `.streamlit/secrets.toml`:
```
GROQ_API_KEY = "your-key-here"
```
