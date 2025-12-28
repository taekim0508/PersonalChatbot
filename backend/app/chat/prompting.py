# backend/app/chat/prompting.py
from __future__ import annotations
from typing import List, Tuple


SYSTEM_INSTRUCTIONS = """You are a personal resume assistant for Tae Kim.
Answer using ONLY the provided resume context. If the context is insufficient, say so.

Goal:
- Synthesize across multiple chunks when the question is broad (e.g., "AI experience", "backend frameworks").
- Be specific: mention projects/companies and what Tae did.
- Prefer concise bullet points for multi-part answers.
- Do not invent details not present in the context.
"""

def format_context_chunks(chunks: List[dict]) -> str:
    """
    Turn retrieved chunks into a readable context block for an LLM.
    We keep chunk_id + section/entity for citations and grounding.
    """
    parts = []
    for c in chunks:
        meta = c.get("metadata", {})
        chunk_id = c.get("id", "unknown")
        section = meta.get("section", "")
        entity = meta.get("entity", "")
        summary_context = meta.get("summary_context", "")
        text = c.get("text", "")

        parts.append(
            f"[{chunk_id}] Section={section} | Entity={entity}\n"
            f"SummaryContext: {summary_context}\n"
            f"Text:\n{text}\n"
        )
    return "\n---\n".join(parts)


def build_prompt(user_query: str, retrieved_chunks: List[dict]) -> Tuple[str, str]:
    """
    Returns (system_prompt, user_prompt).
    Keep this LLM-agnostic; you can plug into OpenAI or any provider later.
    """
    context_block = format_context_chunks(retrieved_chunks)

    user_prompt = f"""User question:
{user_query}

Resume context:
{context_block}

Instructions:
1) Answer the question using ONLY the Resume context above.
2) If the question asks for "experience", synthesize across multiple entities/sections when relevant.
3) Provide the answer as:
   - A short summary paragraph (1-3 sentences)
   - Then bullet points grouped by Entity (Company/Project) when possible
4) After the answer, output a "Citations" list containing chunk IDs you used.
"""
    return SYSTEM_INSTRUCTIONS, user_prompt
