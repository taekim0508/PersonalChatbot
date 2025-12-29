# backend/app/chat/llm.py
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

from openai import OpenAI


def _safe_json_loads(s: str) -> Dict[str, Any] | None:
    """
    Best-effort JSON parser. Returns None if parsing fails.
    Handles cases where the model wraps JSON in text.
    """
    s = s.strip()

    # If it already looks like JSON
    if s.startswith("{") and s.endswith("}"):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return None

    # Try to extract the first JSON object in the string
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(s[start : end + 1])
        except json.JSONDecodeError:
            return None

    return None


def generate_answer_with_citations(
    *,
    system_prompt: str,
    user_prompt: str,
    allowed_chunk_ids: List[str],
    model: str = "gpt-4o-mini",
) -> Tuple[str, List[str], str]:
    """
    Calls the LLM and returns:
      (answer_text, cited_chunk_ids, raw_model_text)

    We constrain citations to only chunk IDs we provided.
    """
    client = OpenAI()

    # Ask for strict JSON output to make your API response predictable.
    # We also constrain citations to the retrieved chunk IDs to avoid hallucinated ids.
    json_instruction = f"""
Return ONLY valid JSON with this shape:
{{
  "answer": "string",
  "citations": ["chunk_000", "chunk_005"]
}}

Rules:
- citations must be a subset of: {allowed_chunk_ids}
- If context is insufficient, answer must say so explicitly and citations can be [].
"""

    # Use chat completions API - note: json_object response_format requires gpt-4o or newer
    try:
        # Try with JSON mode first (for newer models like gpt-4o)
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt + "\n\n" + json_instruction},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
        except Exception:
            # Fallback for models that don't support json_object format (like gpt-4o-mini)
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt + "\n\n" + json_instruction},
                ],
                temperature=0.3,
            )
        
        raw_text = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        # Return error message instead of crashing
        error_msg = f"Error calling OpenAI API: {str(e)}. Please check your API key and model availability."
        return error_msg, [], error_msg

    parsed = _safe_json_loads(raw_text)
    if not parsed:
        # Fallback: return raw output and use no citations
        return raw_text, [], raw_text

    answer = str(parsed.get("answer", "")).strip()
    citations = parsed.get("citations", [])
    if not isinstance(citations, list):
        citations = []

    # Filter citations to allowed ids only
    citations = [c for c in citations if isinstance(c, str) and c in set(allowed_chunk_ids)]

    if not answer:
        # If answer missing, fallback to raw text
        answer = raw_text

    return answer, citations, raw_text
