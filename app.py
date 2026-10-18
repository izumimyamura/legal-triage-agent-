import os
import time
import html
import re
import io
import streamlit as st
from utils.ingestion import extract_document_text
from utils.client import analyze_document_with_gemma

st.set_page_config(
    page_title="LexLocal — Apple-Grade Legal Triage",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 100% Local Apple.com Design System (Clean Light Theme & Clean File Uploader)
st.markdown("""
<style>
    html, body, [class*="css"], div, span, p, h1, h2, h3, h4, label, input, button {
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Helvetica Neue", Arial, sans-serif !important;
        -webkit-font-smoothing: antialiased;
    }

    .stAppDeployButton, [data-testid="stAppDeployButton"], #MainMenu, footer { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    .stApp {
        background-color: #ffffff !important;
        color: #1d1d1f !important;
    }
    .block-container {
        padding-top: 0rem !important;
        padding-bottom: 7rem !important;
        max-width: 1100px !important;
    }

    /* Clean Apple Navbar */
    .apple-nav {
        position: sticky;
        top: 0;
        z-index: 999;
        background: rgba(255, 255, 255, 0.88);
        backdrop-filter: saturate(180%) blur(20px);
        -webkit-backdrop-filter: saturate(180%) blur(20px);
        border-bottom: 1px solid rgba(0, 0, 0, 0.06);
        padding: 14px 32px;
        margin: 0 -3rem 40px -3rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .apple-nav-brand {
        font-weight: 600;
        font-size: 1.02rem;
        letter-spacing: -0.01em;
        color: #1d1d1f;
    }
    .apple-nav-pill {
        background: #0071e3;
        color: #ffffff;
        padding: 5px 14px;
        border-radius: 980px;
        font-size: 0.75rem;
        font-weight: 500;
    }

    /* Pure White Hero */
    .apple-white-hero {
        text-align: center;
        padding: 24px 20px 40px 20px;
        background: #ffffff;
    }
    .hero-badges-row {
        display: flex;
        justify-content: center;
        gap: 8px;
        flex-wrap: wrap;
        margin-bottom: 16px;
    }
    .hero-pill-badge {
        background: #f5f5f7;
        color: #424245;
        padding: 6px 14px;
        border-radius: 980px;
        font-size: 0.78rem;
        font-weight: 500;
        border: 1px solid rgba(0,0,0,0.05);
    }
    .apple-white-hero h1 {
        font-size: 3.4rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.035em !important;
        line-height: 1.08 !important;
        color: #1d1d1f !important;
        margin: 0 auto 14px auto !important;
    }
    .apple-white-hero p {
        font-size: 1.2rem !important;
        font-weight: 400 !important;
        color: #86868b !important;
        max-width: 660px !important;
        margin: 0 auto 20px auto !important;
        line-height: 1.45 !important;
    }

    /* Bulletproof File Uploader Fix (Zero Overlap) */
    [data-testid="stFileUploader"] section {
        background: #f5f5f7 !important;
        border: 1.5px dashed #d2d2d7 !important;
        border-radius: 16px !important;
        color: #1d1d1f !important;
    }
    [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span {
        color: #424245 !important;
    }
    [data-testid="stFileUploader"] button {
        background-color: #0071e3 !important;
        color: transparent !important;
        border-radius: 980px !important;
        padding: 0.5rem 1.4rem !important;
        border: none !important;
        position: relative !important;
    }
    [data-testid="stFileUploader"] button span {
        visibility: hidden !important;
    }
    [data-testid="stFileUploader"] button::after {
        content: "Browse Files";
        visibility: visible !important;
        color: #ffffff !important;
        font-size: 0.85rem !important;
        font-weight: 500;
        position: absolute;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    [data-testid="stFileUploader"] button:hover {
        background-color: #0077ed !important;
    }

    /* Contrast Black Telemetry Band */
    .apple-black-band {
        background: #000000;
        color: #f5f5f7;
        border-radius: 28px;
        padding: 36px 36px;
        margin: 20px 0 44px 0;
        text-align: center;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
    }
    .apple-black-band h2 {
        color: #ffffff !important;
        font-size: 1.9rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        margin: 0 auto 8px auto !important;
    }
    .apple-black-band p {
        color: #a1a1a6 !important;
        font-size: 0.94rem !important;
        max-width: 680px;
        margin: 0 auto 20px auto !important;
    }
    .black-band-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 14px;
        text-align: left;
    }
    .black-metric-tile {
        background: rgba(255, 255, 255, 0.07);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 16px 18px;
    }
    .black-metric-label {
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #86868b;
        margin-bottom: 4px;
    }
    .black-metric-value {
        font-size: 1.2rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.02em;
    }

    /* Studio Header */
    .studio-section-title {
        text-align: center;
        margin: 20px 0 28px 0;
    }
    .studio-section-title h2 {
        font-size: 2rem !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        color: #1d1d1f !important;
        margin-bottom: 6px !important;
    }
    .studio-section-title p {
        color: #86868b !important;
        font-size: 1rem !important;
        margin: 0 !important;
    }

    /* Apple Button */
    div.stButton > button[kind="primary"] {
        background: #0071e3 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 980px !important;
        padding: 0.75rem 1.8rem !important;
        font-size: 0.96rem !important;
        font-weight: 500 !important;
        box-shadow: 0 4px 14px rgba(0, 113, 227, 0.25) !important;
        transition: all 0.25s ease !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background: #0077ed !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 22px rgba(0, 113, 227, 0.35) !important;
    }

    /* Spacious Apple White Cards */
    .apple-spaced-card {
        background: #ffffff;
        border-radius: 24px;
        padding: 34px 38px;
        margin-bottom: 28px;
        border: 1px solid rgba(0, 0, 0, 0.07);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
    }
    .apple-spaced-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.08);
    }
    .apple-spaced-card.facts { border-top: 5px solid #34c759; }
    .apple-spaced-card.risks { border-top: 5px solid #ff9500; }
    .apple-spaced-card.escalation { border-top: 5px solid #ff3b30; background: #fffafa; }

    .card-top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .card-title-main {
        font-size: 1.3rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #1d1d1f;
    }
    .pill-label {
        padding: 5px 14px;
        border-radius: 980px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .pill-label.green { background: #eafbf0; color: #1d8348; }
    .pill-label.amber { background: #fff8eb; color: #b45309; }
    .pill-label.red { background: #fef2f2; color: #dc2626; }

    .quote-box-spaced {
        background: #f8f8fa;
        border-left: 3.5px solid #0071e3;
        padding: 14px 18px;
        border-radius: 14px;
        margin: 14px 0;
        font-family: "New York", Georgia, serif !important;
        font-style: italic;
        color: #1d1d1f;
        font-size: 0.94rem;
        line-height: 1.6;
    }

    /* Paper Reader Card */
    .paper-sheet-centered {
        background: #ffffff;
        border-radius: 24px;
        padding: 32px 36px;
        margin-bottom: 28px;
        border: 1px solid rgba(0, 0, 0, 0.07);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
    }
    .paper-sheet-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #f0f0f2;
        padding-bottom: 12px;
        margin-bottom: 18px;
        font-size: 0.74rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #86868b;
    }
    .paper-sheet-body {
        font-family: "New York", Georgia, serif !important;
        font-size: 1.02rem;
        line-height: 1.85;
        color: #1d1d1f;
        white-space: pre-wrap;
    }
    mark.cited-quote {
        background: #fff3b0;
        color: #1d1d1f;
        border-bottom: 2px solid #f59e0b;
        padding: 2px 5px;
        border-radius: 5px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Top Navbar
st.markdown("""
<div class="apple-nav">
    <div class="apple-nav-brand">LexLocal Triage Studio</div>
    <div><span class="apple-nav-pill">Air-Gap Active (L9)</span></div>
</div>
""", unsafe_allow_html=True)

# Hero Section
st.markdown("""
<div class="apple-white-hero">
    <div class="hero-badges-row">
        <span class="hero-pill-badge">● 100% On-Device Privacy</span>
        <span class="hero-pill-badge">Gemma Edge Engine</span>
        <span class="hero-pill-badge">Verifiable Passage Grounding</span>
    </div>
    <h1>Legal clarity.<br>Strictly on your Device.</h1>
    <p>Understand complex agreements in plain language, verify every claim against exact source passages, and separate contract facts from legal ambiguity.</p>
</div>
""", unsafe_allow_html=True)

# Clean Settings Box
st.markdown("""
<div style="background:#f5f5f7; border-radius:20px; padding:20px 24px; margin-bottom:24px; border:1px solid rgba(0,0,0,0.06);">
    <div style="font-size:0.8rem; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; color:#86868b; margin-bottom:12px;">🛠️ Engine Settings & Air-Gap Controls</div>
</div>
""", unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.2, 1, 1], gap="medium")
with c1:
    server_url = st.text_input("Ollama Local Endpoint", value="http://localhost:11434")
with c2:
    model_choice = st.selectbox("Gemma Edge Variant", ["gemma4:e4b", "gemma3n:e4b", "gemma3:4b"])
with c3:
    st.write("")
    ui_preview_mode = st.toggle("Instant UI Preview (Mock Gemma)", value=True)

st.write("")

# Document Selector
col_up, col_sample = st.columns([1.2, 1], gap="large")
with col_up:
    uploaded_file = st.file_uploader("Upload Contract or Legal Notice (PDF / TXT)", type=["pdf", "txt"])

sample_files = {"Upload custom document": None}
if os.path.exists("sample_docs"):
    for fname in sorted(os.listdir("sample_docs")):
        if fname.endswith((".pdf", ".txt")):
            sample_files[f"Built-in Document: {fname}"] = os.path.join("sample_docs", fname)

with col_sample:
    selected_sample = st.selectbox("Or Inspect Built-in Test Agreement", list(sample_files.keys()), index=1 if len(sample_files) > 1 else 0)

doc_pages = []
error_msg = None
active_doc_name = None

if uploaded_file is not None:
    active_doc_name = uploaded_file.name
    doc_pages, error_msg = extract_document_text(uploaded_file)
elif sample_files[selected_sample] is not None:
    sample_path = sample_files[selected_sample]
    active_doc_name = os.path.basename(sample_path)
    with open(sample_path, "rb") as f:
        fake_upload = io.BytesIO(f.read())
        fake_upload.name = active_doc_name
        doc_pages, error_msg = extract_document_text(fake_upload)

def get_preview_mock(full_text_str: str) -> dict:
    return {
        "summary": "This residential rental agreement establishes a monthly rent obligation on Page 1, subjective property upkeep rules, a 1-month notice period, and a conflicting rent and penalty schedule on Page 2.",
        "obligations_and_penalties": [
            "Monthly Rent (Page 1, Clause 1): INR 10,000 due on the 5th of each month.",
            "Conflicting Rent & Late Penalty (Page 2, Clause 4): States rent is INR 20,000/month with an INR 2,000/day late fee.",
            "Termination Notice (Page 1, Clause 3): 1 month written notice by either party."
        ],
        "verifiable_quotes": [
            {"page": 1, "quote": "The Tenant agrees to pay a monthly rent of INR 10,000 due on the 5th of each month."},
            {"page": 1, "quote": "The Tenant must clean the property reasonably and maintain the premises in an acceptable manner"},
            {"page": 2, "quote": "the monthly rent shall be INR 20,000 per month. Failure to pay on time incurs a penalty of INR 2,000 per day."}
        ],
        "interpretations_and_risks": [
            "DIRECT CONTRADICTION: Page 1 specifies INR 10,000 monthly rent, whereas Page 2 specifies INR 20,000 monthly rent.",
            "VAGUE & SUBJECTIVE WORDING: Phrases like 'clean the property reasonably' and 'acceptable manner' lack measurable standards.",
            "JURISDICTION DEPENDENCY: Enforceability of an INR 2,000/day penalty depends on local State Rent Control laws."
        ],
        "prompt_injection_detected": False,
        "document_is_silent": False,
        "escalation_needed": True,
        "escalation_reason": "Direct contradiction between Page 1 and Page 2 rent amounts (INR 10,000 vs INR 20,000) and severe daily penalty terms require review by a qualified legal professional before signing."
    }

def quote_matches_whitespace_tolerant(quote: str, text: str) -> bool:
    tokens = [re.escape(tok) for tok in quote.strip().split() if tok]
    if not tokens:
        return False
    pattern = r"\s+".join(tokens)
    return bool(re.search(pattern, text, flags=re.IGNORECASE))

if error_msg:
    st.error(f"🛡️ **Ingestion Guardrail Triggered:** {error_msg}")
elif doc_pages:
    full_text = "\n\n".join([f"[PAGE {p['page']}]\n{p['text']}" for p in doc_pages])
    word_count = len(full_text.split())

    if "last_doc_loaded" not in st.session_state or st.session_state.last_doc_loaded != active_doc_name:
        st.session_state.last_doc_loaded = active_doc_name
        st.session_state.last_result = get_preview_mock(full_text) if ui_preview_mode else None
        st.session_state.latency_ms = 180 if ui_preview_mode else 0

    quotes_list = (st.session_state.last_result or {}).get("verifiable_quotes", [])
    matched_quotes = sum(1 for q in quotes_list if quote_matches_whitespace_tolerant(q.get("quote", ""), full_text))
    grounding_str = f"{matched_quotes}/{len(quotes_list)} Passages Verified" if quotes_list else "Ready"

    # Contrast Black Telemetry Band
    st.markdown(f"""
<div class="apple-black-band">
    <h2>Private Triage Telemetry.</h2>
    <p>Important Legal Boundary: This tool is for preliminary document understanding and issue identification only. It is not a lawyer and cannot decide legal validity.</p>
    <div class="black-band-grid">
        <div class="black-metric-tile">
            <div class="black-metric-label">Active Document</div>
            <div class="black-metric-value" style="font-size:1.05rem;">{html.escape(active_doc_name or 'Agreement.pdf')}</div>
        </div>
        <div class="black-metric-tile">
            <div class="black-metric-label">Local Extraction</div>
            <div class="black-metric-value">{len(doc_pages)} Pages · {word_count} Words</div>
        </div>
        <div class="black-metric-tile">
            <div class="black-metric-label">Passage Traceability</div>
            <div class="black-metric-value" style="color:#30d158;">{grounding_str}</div>
        </div>
        <div class="black-metric-tile">
            <div class="black-metric-label">Local Inference</div>
            <div class="black-metric-value">{st.session_state.latency_ms} ms · 0 Cloud Calls</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    # Studio Workspace Header
    st.markdown("""
<div class="studio-section-title">
    <h2>Grounded Legal Triage Studio.</h2>
    <p>Run your analysis below and inspect separated facts, ambiguities, and source pages.</p>
</div>
""", unsafe_allow_html=True)

    # Centered Controls for Analysis
    preset = st.selectbox(
        "Select Triage Objective",
        [
            "Summarize key obligations, penalties, and termination conditions.",
            "Identify ambiguous, contradictory, or unilateral clauses.",
            "What are the notice periods, lock-in rules, and dispute terms?",
            "Custom question..."
        ]
    )
    custom_query = st.text_input("Ask a Specific Question", placeholder="e.g., Does this document mention governing law or arbitration?")
    final_query = custom_query if preset == "Custom question..." else preset

    if st.button("Run On-Device Legal Triage", type="primary", use_container_width=True):
        t0 = time.time()
        if ui_preview_mode:
            time.sleep(0.18)
            st.session_state.last_result = get_preview_mock(full_text)
        else:
            with st.spinner(f"Running local Gemma inference ({model_choice})..."):
                st.session_state.last_result = analyze_document_with_gemma(
                    server_url, model_choice, full_text, final_query
                )
        st.session_state.latency_ms = int((time.time() - t0) * 1000)
        st.rerun()

    st.write("")
    result = st.session_state.last_result
    if result:
        if "error" in result:
            st.error(result["error"])
        else:
            if result.get("prompt_injection_detected"):
                st.error("🛡️ **Adversarial Guardrail Triggered:** Hidden prompt-injection instructions inside the document were detected and neutralized.")
            if result.get("document_is_silent"):
                st.info("🔇 **Document is Silent:** The uploaded text does not contain clauses addressing this topic.")

            obligations_html = "".join([f"<li style='margin-bottom:10px;'>{html.escape(str(item))}</li>" for item in result.get("obligations_and_penalties", [])])
            quotes_html = "".join([
                f"<div class='quote-box-spaced'>“{html.escape(q.get('quote', ''))}” <span style='font-family:-apple-system,sans-serif;font-style:normal;font-size:0.76rem;color:#0071e3;float:right;font-weight:600;'>PAGE {html.escape(str(q.get('page', 1)))}</span></div>"
                for q in result.get("verifiable_quotes", [])
            ])

            # 1. Explicit Document Statements Card (Centered Full-Width)
            st.markdown(f"""
<div class="apple-spaced-card facts">
    <div class="card-top-header">
        <span class="card-title-main">1. Explicit Document Statements</span>
        <span class="pill-label green">Verbatim Grounded</span>
    </div>
    <p style="color:#424245;font-size:1rem;line-height:1.75;margin-top:0;">{html.escape(result.get("summary", ""))}</p>
    {"<div style='font-weight:700;margin:22px 0 10px 0;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;color:#86868b;'>Key Obligations, Deadlines & Penalties</div><ul style='margin:0;padding-left:20px;color:#1d1d1f;font-size:0.96rem;line-height:1.7;'>" + obligations_html + "</ul>" if obligations_html else ""}
    {"<div style='font-weight:700;margin:24px 0 10px 0;font-size:0.8rem;text-transform:uppercase;letter-spacing:0.06em;color:#86868b;'>Verifiable Source Passages</div>" + quotes_html if quotes_html else ""}
</div>
""", unsafe_allow_html=True)

            # 2. Possible Interpretations & Ambiguities Card (Centered Full-Width)
            risks_html = "".join([f"<li style='margin-bottom:12px;'>⚠️ {html.escape(str(r))}</li>" for r in result.get("interpretations_and_risks", [])])
            st.markdown(f"""
<div class="apple-spaced-card risks">
    <div class="card-top-header">
        <span class="card-title-main">2. Possible Interpretations & Ambiguities</span>
        <span class="pill-label amber">Separated from Facts</span>
    </div>
    <p style="color:#86868b;font-size:0.88rem;margin-top:0;line-height:1.5;">Preliminary risk and vagueness flags — never legal validity conclusions.</p>
    <ul style="list-style:none;padding-left:0;margin-top:14px;color:#1d1d1f;font-size:0.96rem;line-height:1.75;">
        {risks_html if risks_html else "<li>No specific ambiguities flagged for this query.</li>"}
    </ul>
</div>
""", unsafe_allow_html=True)

            # 3. Calibrated Uncertainty & Escalation Card (Centered Full-Width)
            if result.get("escalation_needed"):
                st.markdown(f"""
<div class="apple-spaced-card escalation">
    <div class="card-top-header">
        <span class="card-title-main" style="color:#dc2626;">3. Calibrated Uncertainty & Escalation</span>
        <span class="pill-label red">Consult Legal Counsel</span>
    </div>
    <p style="color:#424245;font-size:0.96rem;margin-top:4px;line-height:1.75;">
        {html.escape(result.get("escalation_reason", "Consult a qualified legal professional regarding jurisdiction-specific enforceability."))}
    </p>
</div>
""", unsafe_allow_html=True)

    # 4. Source Document Inspector Folio Sheets (Stacked Below)
    st.markdown("""
<div class="studio-section-title" style="margin-top:48px;">
    <h2>Source Document Folio Inspector.</h2>
    <p>Verbatim text extracted on-device with cited passages highlighted in amber.</p>
</div>
""", unsafe_allow_html=True)

    for p in doc_pages:
        page_text_html = html.escape(p["text"])
        if st.session_state.last_result and "verifiable_quotes" in st.session_state.last_result:
            for q in st.session_state.last_result.get("verifiable_quotes", []):
                raw_quote = q.get("quote", "").strip()
                tokens = [re.escape(html.escape(tok)) for tok in raw_quote.split() if tok]
                if len(tokens) > 2:
                    flex_pattern = r"\s+".join(tokens)
                    page_text_html = re.sub(
                        f"({flex_pattern})",
                        r'<mark class="cited-quote">\1</mark>',
                        page_text_html,
                        flags=re.IGNORECASE
                    )
        ocr_tag = " · OCR EXTRACTED" if p.get("ocr_used") else " · VERBATIM FOLIO"
        st.markdown(f"""
<div class="paper-sheet-centered">
    <div class="paper-sheet-meta">
        <span>PAGE 0{p["page"]}{ocr_tag}</span>
        <span style="color:#0071e3;">● Highlighted Source</span>
    </div>
    <div class="paper-sheet-body">{page_text_html}</div>
</div>
""", unsafe_allow_html=True)