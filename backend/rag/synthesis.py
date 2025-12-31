# backend/rag/synthesis.py
from typing import Dict, List
from collections import defaultdict

from rag.retrieval import RetrievedChunk


def group_chunks_by_entity(
    retrieved: List[RetrievedChunk],
) -> Dict[str, List[RetrievedChunk]]:
    """
    Group retrieved chunks by entity (company/project).

    Why this exists:
      - Prevents mixing multiple experiences together
      - Enables structured, entity-by-entity synthesis
      - Enables clean citations later
    """
    groups = defaultdict(list)
    for r in retrieved:
        meta = r.chunk.get("metadata", {})
        entity = str(meta.get("entity", "General")).strip()
        if not entity:
            entity = "General"
        groups[entity].append(r)
    return dict(groups)


def build_synthesis_prompt(
    query: str,
    grouped_chunks: Dict[str, List[RetrievedChunk]],
) -> str:
    """
    Build a structured prompt that forces entity-level reasoning.

    Why:
      LLMs answer much better when:
        - Evidence is grouped
        - Hallucination is explicitly forbidden
        - Output structure is specified
    """
    lines = [
        "You are answering a question about Tae Kim using ONLY the evidence provided.",
        "Rules:",
        "- Do not invent or assume experience",
        "- Group information by company or project",
        "- Be concise and factual",
        "- If evidence is insufficient, say so",
        "",
        f"Question:\n{query}",
        "",
        "Evidence:",
    ]

    for entity, chunks in grouped_chunks.items():
        lines.append(f"[Entity: {entity}]")
        for r in chunks:
            cid = r.chunk.get("id", "unknown")
            text = r.chunk.get("text", "")
            lines.append(f"- ({cid}) {text}")
        lines.append("")

    lines.append(
        "Now write the answer grouped by entity. "
        "Use bullet points under each entity."
    )

    return "\n".join(lines)
