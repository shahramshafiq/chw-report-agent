import streamlit as st
import requests
import json

SYSTEM = """You are a health report processing agent for Community Health Workers (CHWs) in Pakistan.

Process messy field reports submitted by Lady Health Workers after household visits.
Extract structured data, identify missing information, classify urgency, and generate clean supervisor summaries.

URGENCY RULES:
- EMERGENCY: unconsciousness, seizures, difficulty breathing, chest pain, stroke signs, severe bleeding, child fever above 40C, pregnancy complications, suicidal ideation
- CLINIC_REFERRAL: symptoms persisting more than 3 days, medication not effective, patient requests referral, chronic disease unmanaged
- ROUTINE: minor complaints, standard follow-ups, preventive care visits

BEHAVIOR:
- If critical fields are missing (patient name, age, chief complaint), output CLARIFICATION stage with specific questions
- If enough information exists, output FINAL_REPORT directly
- When urgency is ambiguous, always default to the higher tier

Respond ONLY in valid JSON. No text outside the JSON. No markdown fences. No explanations.

CLARIFICATION format:
{"stage": "CLARIFICATION", "questions": ["question1", "question2"]}

FINAL_REPORT format:
{
  "stage": "FINAL_REPORT",
  "report": {
    "patient_name": "",
    "age": "",
    "gender": "",
    "chief_complaint": "",
    "symptoms": [],
    "vitals": {},
    "medications_given": [],
    "urgency": "ROUTINE",
    "urgency_reason": "",
    "action": "",
    "escalate": false,
    "escalation_note": "",
    "gaps": []
  },
  "supervisor_summary": ""
}"""


def ask_agent(hist):
    key = st.secrets["GEMINI_API_KEY"]
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"

    contents = []
    for msg in hist:
        role = "user" if msg["role"] == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})

    body = {
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 1000}
    }

    res = requests.post(url, json=body)
    data = res.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def parse_json(raw):
    txt = raw.strip()
    if "```" in txt:
        for chunk in txt.split("```"):
            chunk = chunk.strip().lstrip("json").strip()
            try:
                return json.loads(chunk)
            except:
                continue
    try:
        return json.loads(txt)
    except:
        return None


def wipe():
    for k in list(st.session_state.keys()):
        del st.session_state[k]


def boot():
    defaults = {"hist": [], "phase": "input", "result": None, "pending_qs": []}
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def show_report(parsed):
    r = parsed.get("report", {})
    urg = r.get("urgency", "ROUTINE")

    if urg == "EMERGENCY":
        st.error("🚨 EMERGENCY — Escalate Immediately")
        if r.get("escalation_note"):
            st.error(r["escalation_note"])
    elif urg == "CLINIC_REFERRAL":
        st.warning("⚠️ Clinic Referral Required — " + r.get("urgency_reason", ""))
    else:
        st.success("✅ Routine Case")

    st.subheader("Patient Details")
    c1, c2, c3 = st.columns(3)
    c1.metric("Name", r.get("patient_name") or "—")
    c2.metric("Age", r.get("age") or "—")
    c3.metric("Gender", r.get("gender") or "—")

    if r.get("chief_complaint"):
        st.write("**Complaint:**", r["chief_complaint"])
    if r.get("symptoms"):
        st.write("**Symptoms:**", "  ·  ".join(r["symptoms"]))
    if r.get("medications_given"):
        st.write("**Medications Given:**", "  ·  ".join(r["medications_given"]))
    if r.get("vitals"):
        st.write("**Vitals:**", str(r["vitals"]))

    st.subheader("Recommended Action")
    st.write(r.get("action") or "Follow standard protocol.")

    if r.get("gaps"):
        with st.expander("⚠️ Information Gaps in This Report"):
            for g in r["gaps"]:
                st.write(f"- {g}")

    st.subheader("Supervisor Summary")
    st.info(parsed.get("supervisor_summary") or "—")


def main():
    st.set_page_config(page_title="CHW Report Agent", page_icon="🏥")
    st.title("🏥 CHW Field Report Agent")
    st.caption("Automated triage and structuring for Community Health Worker field reports")

    boot()

    if st.session_state.phase == "input":
        st.markdown("Paste the field report below. It can be messy, incomplete, or in any format.")
        report = st.text_area(
            "Field Report",
            height=180,
            placeholder="e.g. Visited house 12, woman Zainab around 40 yrs, fever and body pain since 2 days, gave brufen, husband mentioned she is pregnant..."
        )

        if st.button("Process Report", type="primary"):
            if not report.strip():
                st.warning("Please enter a report.")
                return
            with st.spinner("Analyzing report..."):
                st.session_state.hist = [{"role": "user", "content": f"Field report:\n\n{report}"}]
                raw = ask_agent(st.session_state.hist)
                st.session_state.hist.append({"role": "assistant", "content": raw})
                parsed = parse_json(raw)
                if not parsed:
                    st.error("Failed to process. Please try again.")
                    return
                if parsed["stage"] == "CLARIFICATION":
                    st.session_state.pending_qs = parsed.get("questions", [])
                    st.session_state.phase = "clarify"
                else:
                    st.session_state.result = parsed
                    st.session_state.phase = "done"
                st.rerun()

    elif st.session_state.phase == "clarify":
        st.warning("Some information is missing. Please answer the questions below.")
        answers = {}
        for i, q in enumerate(st.session_state.pending_qs):
            answers[q] = st.text_input(f"{i+1}. {q}", key=f"q{i}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Submit Answers", type="primary", use_container_width=True):
                block = "\n".join([f"Q: {q}\nA: {a or 'Not available'}" for q, a in answers.items()])
                with st.spinner("Generating report..."):
                    st.session_state.hist.append({
                        "role": "user",
                        "content": f"Clarification answers:\n\n{block}\n\nNow produce FINAL_REPORT."
                    })
                    raw = ask_agent(st.session_state.hist)
                    st.session_state.hist.append({"role": "assistant", "content": raw})
                    st.session_state.result = parse_json(raw)
                    st.session_state.phase = "done"
                    st.rerun()
        with col2:
            if st.button("Skip, generate anyway", use_container_width=True):
                with st.spinner("Generating report with available data..."):
                    st.session_state.hist.append({
                        "role": "user",
                        "content": "No clarifications available. Generate FINAL_REPORT and note all gaps in the gaps field."
                    })
                    raw = ask_agent(st.session_state.hist)
                    st.session_state.hist.append({"role": "assistant", "content": raw})
                    st.session_state.result = parse_json(raw)
                    st.session_state.phase = "done"
                    st.rerun()

    elif st.session_state.phase == "done":
        if not st.session_state.result or "report" not in st.session_state.result:
            st.error("Something went wrong. Please start over.")
        else:
            show_report(st.session_state.result)

        st.divider()
        if st.button("Process Another Report", use_container_width=True):
            wipe()
            st.rerun()


if __name__ == "__main__":
    main()
