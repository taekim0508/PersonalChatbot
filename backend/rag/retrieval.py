# backend/rag/retrieval.py
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Optional

TOKEN_RE = re.compile(r"[A-Za-z0-9\.\+#]+")


def tokenize(text: str) -> List[str]:
    toks = [t.lower() for t in TOKEN_RE.findall(text)]
    # keep short tech tokens like "ai", "c", "go"? we'll keep >=2
    return [t for t in toks if len(t) >= 2]


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: dict
    score: float
    reasons: List[str]


def load_chunks_and_index(
    chunks_path: str = "index/chunks.json",
    inverted_index_path: str = "index/inverted_index.json",
) -> Tuple[List[dict], Dict[str, List[str]], Dict[str, dict]]:
    chunks = json.loads(Path(chunks_path).read_text(encoding="utf-8"))
    inv = json.loads(Path(inverted_index_path).read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in chunks}
    return chunks, inv, by_id


def retrieve(
    query: str,
    *,
    inv: Dict[str, List[str]],
    chunk_by_id: Dict[str, dict],
    top_k: int = 6,
    max_candidates: int = 80,
) -> List[RetrievedChunk]:
    """
    Keyword-first retriever:
      1) Tokenize query
      2) Candidate generation via inverted index
      3) Score candidates with overlap + keyword boosts
    """
    q_tokens = tokenize(query)
    q_token_set = set(q_tokens)

    # Candidate generation
    candidate_ids = []
    seen = set()
    for tok in q_tokens:
        for cid in inv.get(tok, []):
            if cid not in seen:
                seen.add(cid)
                candidate_ids.append(cid)
            if len(candidate_ids) >= max_candidates:
                break
        if len(candidate_ids) >= max_candidates:
            break

    # If nothing matched, fall back to scanning everything (small corpus => ok)
    if not candidate_ids:
        candidate_ids = list(chunk_by_id.keys())

    scored: List[RetrievedChunk] = []
    query_lower = query.lower()

    for cid in candidate_ids:
        ch = chunk_by_id[cid]
        text = ch["text"]
        meta = ch.get("metadata", {})
        keywords = meta.get("keywords", [])

        text_tokens = tokenize(text)
        text_token_set = set(text_tokens)

        # Base overlap score
        overlap = q_token_set.intersection(text_token_set)
        score = float(len(overlap))

        reasons = []
        if overlap:
            reasons.append(f"token_overlap({len(overlap)})")

        # Keyword boost: if query tokens overlap canonical keywords, add weight
        # This helps with abstract questions like "backend frameworks" -> FastAPI / Socket.IO
        kw_tokens = set()
        for kw in keywords:
            kw_tokens.update(tokenize(kw))

        kw_overlap = q_token_set.intersection(kw_tokens)
        if kw_overlap:
            score += 2.5 * len(kw_overlap)
            reasons.append(f"keyword_overlap({len(kw_overlap)})")

        # Phrase/substring boosts for tech terms (simple but effective)
        for t in ["fastapi", "socket.io", "socketio", "openai", "rag", "llm", "websocket", "backend"]:
            if t in query_lower and t in text.lower():
                score += 2.0
                reasons.append(f"phrase_match({t})")

        # Small section/entity “anchor” boost: if query contains company/project name tokens
        entity = str(meta.get("entity", "")).lower()
        if entity and any(tok in entity for tok in q_token_set):
            score += 1.5
            reasons.append("entity_anchor")

        if score > 0:
            scored.append(RetrievedChunk(chunk=ch, score=score, reasons=reasons))

    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:top_k]
