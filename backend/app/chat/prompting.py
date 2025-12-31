# backend/app/chat/prompting.py
from __future__ import annotations
from typing import List, Tuple, Dict


SYSTEM_INSTRUCTIONS = """You are a personal resume assistant for Tae Kim.
Your audience is software engineering recruiters evaluating Tae for entry-level or new-grad roles.

Your goal is to explain Tae’s experience clearly, confidently, and conversationally,
as if answering a recruiter’s follow-up question during a screening call.

CORE OBJECTIVE:
When asked about a skill, framework, or topic (e.g., “FastAPI”),
summarize Tae’s *practical, applied experience* using concrete examples
from real projects — not buzzwords, not vague claims.

CRITICAL RULES:
1. SYNTHESIZE, DON’T COPY  
   - Do NOT repeat resume bullets or chunk text verbatim.
   - Translate evidence into natural, recruiter-friendly explanations.

2. ENTITY-BY-ENTITY STRUCTURE  
   - Group responses by Company or Project name.
   - Treat each entity as a short, cohesive story of what Tae did there.
   - Never merge or blur experiences across entities.

3. RECRUITER-CALIBRATED DETAIL  
   - Emphasize:
     • what Tae built
     • how he used the technology
     • why it mattered (scale, performance, reliability, UX, etc.)
   - Avoid internal jargon unless it adds clarity.

4. CONVERSATIONAL, NOT ACADEMIC  
   - Write as if speaking to a recruiter, not documenting a system.
   - Prefer clear sentences over dense technical exposition.

5. COMBINE RELATED EVIDENCE  
   - If multiple chunks from the same entity describe related work,
     synthesize them into a single, coherent point.
   - Do NOT list chunks one-by-one.

6. STRICT GROUNDING  
   - Only reference entities, tools, and facts present in the evidence.
   - Only cite chunk IDs that were actually used.
   - Do NOT infer seniority, scale, or ownership unless explicitly supported.

7. NO INVENTION  
   - Do NOT add technologies, metrics, or responsibilities not in evidence.
   - If evidence is weak or partial, reflect that honestly and concisely.

OUTPUT FORMAT:
Use this exact structure:

Entity Name:
- One or more conversational bullet points explaining how Tae used the relevant technology,
  what he built, and what kind of engineering problems he worked on [chunk_id, chunk_id]

If only one entity is relevant, still use the entity header.
If no relevant evidence exists, say so clearly rather than guessing.
"""



def group_chunks_by_entity(chunks: List[dict]) -> Dict[str, List[dict]]:
    """
    Groups retrieved chunks by metadata.entity.
    Preserves original order within each entity group.
    
    Rules:
    - Use "General" if entity is missing
    - Do NOT merge entities
    - Preserve chunk order within each entity
    """
    # Use OrderedDict to preserve insertion order of entities
    grouped: Dict[str, List[dict]] = {}
    
    for chunk in chunks:
        meta = chunk.get("metadata", {})
        entity = str(meta.get("entity", "General")).strip()
        if not entity:
            entity = "General"
        
        if entity not in grouped:
            grouped[entity] = []
        grouped[entity].append(chunk)
    
    return grouped


def format_evidence_by_entity(chunks: List[dict]) -> str:
    """
    Format retrieved chunks into an evidence section grouped by entity.
    Each chunk is presented with its ID inline for citation grounding.
    
    Format:
    Entity: LiveArena Technologies
    [chunk_002]
    • Drove end-to-end design of a Gen Z AI engagement initiative...
    """
    grouped = group_chunks_by_entity(chunks)
    
    if not grouped:
        return "No evidence available."
    
    parts = []
    
    # Sort entities for deterministic output
    for entity in sorted(grouped.keys()):
        entity_chunks = grouped[entity]
        parts.append(f"\nEntity: {entity}")
        
        for chunk in entity_chunks:
            chunk_id = chunk.get("id", "unknown")
            text = chunk.get("text", "")
            
            # Format: [chunk_id] on its own line, then bullet with text
            parts.append(f"[{chunk_id}]")
            
            # Extract the main content (remove section/entity prefix if present)
            # The text may already have "Section: ... | Entity: ... - " prefix
            # We want to show the actual content
            if text.strip():
                # Format as bullet point
                parts.append(f"• {text}")
            else:
                parts.append("• (No text content)")
        
        parts.append("")  # Empty line between entities
    
    return "\n".join(parts)


def build_prompt(user_query: str, retrieved_chunks: List[dict]) -> Tuple[str, str]:
    """
    Returns (system_prompt, user_prompt).
    Groups retrieved chunks by entity and builds an evidence section with inline chunk IDs.
    Instructs the LLM to answer entity-by-entity with explicit citation grounding.
    
    Why entity-grouped synthesis improves RAG reliability:
    - Prevents mixing experiences from different companies/projects
    - Makes it easier to verify claims against source chunks
    - Enables per-entity confidence scoring in the future
    - Supports UI expansion (collapsible entity sections, per-entity summaries)
    - Reduces hallucination by forcing explicit entity attribution
    """
    evidence_section = format_evidence_by_entity(retrieved_chunks)
    
    # Extract allowed chunk IDs for citation enforcement
    allowed_chunk_ids = [c.get("id", "") for c in retrieved_chunks if c.get("id")]
    allowed_ids_str = ", ".join(allowed_chunk_ids) if allowed_chunk_ids else "none"
    
    user_prompt = f"""User question:
{user_query}

Evidence (grouped by entity):
{evidence_section}

INSTRUCTIONS:
1. SYNTHESIZE the evidence into a conversational response. Don't copy resume bullets verbatim.
2. Write naturally as if explaining Tae's experience in a conversation.
3. Group your answer by entity (Company/Project name as header) for organization.
4. Combine related information from multiple chunks when they cover the same topic or theme.
5. Use bullet points under each entity, but write them conversationally.
6. Only reference chunk IDs that appear in the evidence above.
7. Do NOT invent entities or facts not in the evidence.
8. If multiple chunks from the same entity are related, synthesize them into coherent points rather than listing them separately.

Example of GOOD synthesis:
LiveArena Technologies:
- At LiveArena, Tae worked on AI engagement initiatives, including designing a Gen Z-focused AI engagement platform and prototyping an AI mentorship system using LLMs [chunk_002, chunk_003]

Example of BAD (copying verbatim):
LiveArena Technologies:
- [chunk_002] Drove end-to-end design of a Gen Z AI engagement initiative...
- [chunk_003] Prototyped an AI mentorship platform using LLMs...

CRITICAL: Citations must be a subset of: [{allowed_ids_str}]
Only cite chunk IDs that you actually used in your answer.
"""
    return SYSTEM_INSTRUCTIONS, user_prompt
