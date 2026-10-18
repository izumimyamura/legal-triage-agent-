import streamlit as st
from utils.ingestion import extract_document_text
from utils.client import analyze_document_with_gemma

st.set_page_config(page_title="Private Legal Document Triage Agent", layout="wide")

# Mandatory Legal Boundary Banner (L8)
st.warning(
    "⚠️ **IMPORTANT BOUNDARY:** This tool is for **preliminary document understanding and issue identification only**. "
    "It is **not a lawyer**, is **not a source of definitive legal advice**, and **cannot decide legal validity**. "
    "Always consult a qualified legal professional before signing or acting on legal documents."
)

st.title("🔒 Private On-Device Legal Document Triage Agent")
st.caption("100% Local Processing via PyMuPDF & Gemma (Ollama) • Zero Cloud Telemetry")

with st.sidebar:
    st.header("⚙️ Local Inference Config")
    server_url = st.text_input("Ollama Local Host", value="http://localhost:11434", help="Use http://<LAN_IP>:11434 during team testing, and http://localhost:11434 for offline demo.")
    model_choice = st.selectbox("Gemma Edge Model", ["gemma4:e4b", "gemma3n:e4b", "gemma3:4b"])
    st.divider()
    st.markdown("**Privacy Status:** 🟢 On-Device Only")
    st.caption("Document contents, chunks, and queries remain strictly inside local memory.")

uploaded_file = st.file_uploader("Upload a Legal Document (Rental Agreement, Employment Contract, Notice, Service Agreement)", type=["pdf", "txt"])

if uploaded_file is not None:
    with st.spinner("Extracting text strictly on-device..."):
        doc_pages, error_msg = extract_document_text(uploaded_file)

    if error_msg:
        st.error(f"⚠️ **Ingestion Guardrail Triggered:** {error_msg}")
    else:
        full_text = "\n\n".join([f"[PAGE {p['page']}]\n{p['text']}" for p in doc_pages])
        st.success(f"✅ Extracted {len(doc_pages)} page(s) locally on-device.")

        col_source, col_analysis = st.columns([1, 1.2])

        with col_source:
            st.subheader("📄 Source Document Text")
            st.caption("Explicit verbatim text extracted from your file.")
            st.text_area("Extracted Pages", full_text, height=520)

        with col_analysis:
            st.subheader("🔍 Document-Grounded Triage")
            preset = st.selectbox(
                "Quick Triage Presets (or type your own question below):",
                [
                    "Custom question...",
                    "Summarize key obligations, penalties, and termination conditions.",
                    "Are there any ambiguous, unilateral, or high-risk clauses?",
                    "What are the notice periods and lock-in requirements?"
                ]
            )
            custom_query = st.text_input("Your Question:", value="" if preset != "Custom question..." else "")
            final_query = custom_query if preset == "Custom question..." else preset

            if st.button("Run Local Triage Analysis", type="primary"):
                if not final_query.strip():
                    st.warning("Please enter a question or select a preset.")
                else:
                    with st.spinner(f"Running local inference via {model_choice}..."):
                        result = analyze_document_with_gemma(server_url, model_choice, full_text, final_query)

                    if "error" in result:
                        st.error(result["error"])
                    else:
                        if result.get("document_is_silent"):
                            st.info("🔇 **Document is Silent:** The uploaded document does not contain clauses addressing this specific question.")

                        # SECTION 1: EXPLICIT STATEMENTS & VERIFIABLE QUOTES (L3, L4, L5)
                        st.markdown("### 1️⃣ Explicit Document Statements (Facts)")
                        st.info(f"**Plain-Language Summary:**\n\n{result.get('summary', 'No summary returned.')}")

                        obligations = result.get("obligations_and_penalties", [])
                        if obligations:
                            st.markdown("**Identified Obligations, Deadlines & Penalties:**")
                            for item in obligations:
                                st.markdown(f"- {item}")

                        quotes = result.get("verifiable_quotes", [])
                        if quotes:
                            st.markdown("**📌 Verifiable Source Passages:**")
                            for q in quotes:
                                st.markdown(f"> *\"{q.get('quote', '')}\"* — **(Page {q.get('page', '?')})**")

                        st.divider()

                        # SECTION 2: POSSIBLE INTERPRETATIONS & AMBIGUITIES (L6, L7)
                        st.markdown("### 2️⃣ Possible Interpretations, Ambiguities & Concerns")
                        st.caption("Separated from explicit text above. These are preliminary issue flags, not legal conclusions.")
                        risks = result.get("interpretations_and_risks", [])
                        if risks:
                            for r in risks:
                                st.warning(f"⚠️ {r}")
                        else:
                            st.write("No specific ambiguities flagged for this query.")

                        # SECTION 3: SAFE ESCALATION (L8)
                        if result.get("escalation_needed"):
                            st.error(
                                f"👩‍⚖️ **Recommended Escalation to Legal Professional:**\n\n"
                                f"{result.get('escalation_reason', 'This clause involves jurisdiction-dependent or ambiguous terms. Please consult a qualified lawyer.')}"
                            )
