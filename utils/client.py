import json
from ollama import Client

SYSTEM_PROMPT = """You are a privacy-first, on-device Legal Document Triage Assistant.
CRITICAL BOUNDARIES:
1. You are NOT a lawyer and do NOT provide definitive legal advice or decide legal validity.
2. Base your output STRICTLY on the provided document text. Never invent clauses.
3. If the document is silent on a topic, explicitly state: "The document is silent on this matter."
4. Separate explicit document statements from possible interpretations or concerns.
5. Recognise ambiguity or jurisdiction-dependent issues and recommend consulting a qualified legal professional.

Return your response ONLY as valid JSON matching this exact structure:
{
  "summary": "Plain-language explanation of what the document/clause says",
  "obligations_and_penalties": ["List of key obligations, deadlines, penalties, or termination terms found"],
  "verifiable_quotes": [
    {"page": 1, "quote": "Exact verbatim quote from the source text supporting your analysis"}
  ],
  "interpretations_and_risks": [
    "Potential concerns, ambiguities, or jurisdiction-dependent issues (kept strictly separate from explicit facts)"
  ],
  "document_is_silent": false,
  "escalation_needed": true,
  "escalation_reason": "Why a qualified legal professional should review this (e.g., ambiguous penalty clause or local tenancy law dependency)"
}
"""

def analyze_document_with_gemma(host_url: str, model_name: str, document_text: str, user_query: str) -> dict:
    """
    Sends the locally extracted document text and user query to the local Ollama instance.
    """
    try:
        client = Client(host=host_url)
        prompt = f"DOCUMENT TEXT:\n{document_text}\n\nUSER QUESTION / TRIAGE FOCUS:\n{user_query}"
        
        response = client.chat(
            model=model_name,
            format="json",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )
        content = response["message"]["content"]
        return json.loads(content)
    except Exception as e:
        return {
            "error": f"Local inference error ({host_url}): {str(e)}"
        }
