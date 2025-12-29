# backend/rag/retrieval.py
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

TOKEN_RE = re.compile(r"[A-Za-z0-9\.\+#]+")


def normalize_text_for_phrase_matching(text: str) -> str:
    """
    Normalize text for phrase matching by:
    - Replacing unicode hyphens/dashes with standard hyphen
    - Converting 'real time' to 'real-time'
    - Lowercasing
    
    Used for consistent phrase matching across query and chunk text.
    """
    # Replace various unicode hyphens/dashes with standard hyphen
    text = re.sub(r'[\u2010-\u2015\u2212\u2013\u2014]', '-', text)
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)
    # Convert 'real time' to 'real-time' (handles various positions)
    text = re.sub(r'\breal\s+time\b', 'real-time', text, flags=re.IGNORECASE)
    return text.lower()


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
    apply_diversity: bool = True,
) -> List[RetrievedChunk]:
    """
    Keyword-first retriever with diversity reranking:
      1) Tokenize query
      2) Candidate generation via inverted index
      3) Score candidates with overlap + keyword boosts
      4) Apply diversity reranking (max 2 chunks per entity) if enabled
    
    Args:
        query: User query string
        inv: Inverted index mapping tokens to chunk IDs
        chunk_by_id: Dictionary mapping chunk IDs to chunk dictionaries
        top_k: Number of results to return
        max_candidates: Maximum candidate chunks to consider
        apply_diversity: If True, apply diversity reranking (max 2 per entity)
    
    Returns:
        List of RetrievedChunk objects, sorted by score (highest first)
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
    # Normalize query once for phrase matching
    normalized_query = normalize_text_for_phrase_matching(query)

    for cid in candidate_ids:
        if cid not in chunk_by_id:
            continue  # Skip missing chunks (robustness)
        
        ch = chunk_by_id[cid]
        text = ch.get("text", "")
        meta = ch.get("metadata", {})
        keywords = meta.get("keywords", [])

        if not text:
            continue  # Skip chunks without text

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
            kw_tokens.update(tokenize(str(kw)))

        kw_overlap = q_token_set.intersection(kw_tokens)
        if kw_overlap:
            score += 2.5 * len(kw_overlap)
            reasons.append(f"keyword_overlap({len(kw_overlap)})")

        # Phrase/substring boosts for tech terms (simple but effective)
        # Normalize chunk text once for phrase matching
        normalized_text = normalize_text_for_phrase_matching(text)
        
        # Tech terms including 'real-time' (normalization handles 'real time' -> 'real-time')
        tech_terms = ["fastapi", "socket.io", "socketio", "openai", "rag", "llm", "websocket", "backend", "ai", "real-time"]
        
        # Phrase matching: check each term, apply boost at most once per chunk
        for t in tech_terms:
            if t in normalized_query and t in normalized_text:
                score += 2.0
                reasons.append(f"phrase_match({t})")
                break  # Only count once per chunk

        # Entity anchor boost: use token overlap between query tokens and entity tokens
        # This avoids substring false positives like 'wa' matching 'Washington'
        entity = str(meta.get("entity", "")).lower()
        if entity:
            entity_tokens = set(tokenize(entity))
            entity_token_overlap = q_token_set.intersection(entity_tokens)
            if entity_token_overlap:
                score += 1.5
                reasons.append("entity_anchor")

        # Section boost for specific queries (deterministic)
        section = str(meta.get("section", "")).lower()
        
        # Check for experience section match
        if "experience" in query_lower and "experience" in section:
            score += 0.5
            reasons.append("section_match(experience)")
        
        # Check for projects section match: query contains 'project'/'projects', 
        # section contains 'project' (handles 'PROJECTS', 'PROJECT', future variants)
        if ("project" in query_lower or "projects" in query_lower) and "project" in section:
            score += 0.5
            reasons.append("section_match(projects)")

        if score > 0:
            scored.append(RetrievedChunk(chunk=ch, score=score, reasons=reasons))

    # Sort by score (highest first)
    scored.sort(key=lambda r: r.score, reverse=True)
    
    # Apply diversity reranking if enabled
    if apply_diversity:
        return diversify_results(scored, top_k=top_k, max_per_entity=2)
    
    return scored[:top_k]

def diversify_results(
    results: List[RetrievedChunk],
    *,
    top_k: int,
    max_per_entity: int = 2,
) -> List[RetrievedChunk]:
    """
    Enforce diversity across entities in final retrieval results.
    
    Preserves score ordering while limiting chunks per entity to ensure
    diverse evidence for broad queries.

    Why this exists:
      Keyword scoring often favors multiple chunks from the same entity.
      For broad questions ("AI experience", "backend work"), this produces
      redundant evidence and weak synthesis.

    What this does:
      - Preserves score ordering (processes results in score order)
      - Limits how many chunks from the same entity appear (max_per_entity)
      - Only backfills if we have fewer than top_k results after diversity filtering

    Args:
        results: List of RetrievedChunk objects, already sorted by score (highest first)
        top_k: Target number of results to return
        max_per_entity: Maximum chunks allowed per entity (default: 2)

    Returns:
        List of RetrievedChunk objects, diverse across entities, preserving score order

    Used later:
      The LLM sees a more representative cross-section of Tae's experience,
      enabling better, higher-level answers.
    """
    if not results:
        return []
    
    out: List[RetrievedChunk] = []
    per_entity_count: Dict[str, int] = {}
    seen_chunk_ids: set = set()  # Track by chunk ID to avoid duplicates

    # First pass: take up to max_per_entity chunks per entity, preserving score order
    for r in results:
        if len(out) >= top_k:
            break
            
        chunk_id = r.chunk.get("id", "")
        if chunk_id in seen_chunk_ids:
            continue  # Skip duplicates
        
        entity = str(r.chunk.get("metadata", {}).get("entity", "General"))
        current_count = per_entity_count.get(entity, 0)

        if current_count >= max_per_entity:
            continue  # Skip this chunk, entity limit reached

        out.append(r)
        seen_chunk_ids.add(chunk_id)
        per_entity_count[entity] = current_count + 1

    # Backfill to reach top_k if possible, even if it exceeds per-entity cap
    # This ensures we return top_k results when corpus is large enough
    # IMPORTANT: Preserve score ordering deterministically WITHOUT full re-sorting
    # Strategy: Insert backfilled items in correct position to maintain score order
    # This preserves: diverse-first picks in score order, then backfill in score order
    if len(out) < top_k:
        for r in results:
            if len(out) >= top_k:
                break
            chunk_id = r.chunk.get("id", "")
            if chunk_id in seen_chunk_ids:
                continue
            
            # Backfill: insert in correct position to maintain score order
            # Find insertion point (backfilled items should maintain score order)
            insert_idx = len(out)
            for i, existing in enumerate(out):
                if r.score > existing.score:
                    insert_idx = i
                    break
            
            out.insert(insert_idx, r)
            seen_chunk_ids.add(chunk_id)
            # Track entity count for reporting, but don't enforce limit during backfill
            entity = str(r.chunk.get("metadata", {}).get("entity", "General"))
            per_entity_count[entity] = per_entity_count.get(entity, 0) + 1

    return out


def debug_retrieval(
    query: str,
    *,
    inv: Dict[str, List[str]],
    chunk_by_id: Dict[str, dict],
    top_k: int = 6,
) -> None:
    """
    Debug helper that prints retrieval results in a readable format.
    
    Prints:
      - Retrieved chunk IDs
      - Entity for each chunk
      - Score for each chunk
      - Reasons for retrieval (token overlap, keyword overlap, etc.)
    
    Args:
        query: User query string
        inv: Inverted index mapping tokens to chunk IDs
        chunk_by_id: Dictionary mapping chunk IDs to chunk dictionaries
        top_k: Number of results to retrieve and display
    """
    results = retrieve(query, inv=inv, chunk_by_id=chunk_by_id, top_k=top_k, apply_diversity=True)
    
    print("=" * 80)
    print(f"RETRIEVAL DEBUG: '{query}'")
    print("=" * 80)
    print(f"Retrieved {len(results)} chunks (top_k={top_k})\n")
    
    if not results:
        print("No results found.")
        return
    
    for i, r in enumerate(results, 1):
        chunk = r.chunk
        meta = chunk.get("metadata", {})
        chunk_id = chunk.get("id", "unknown")
        entity = meta.get("entity", "General")
        section = meta.get("section", "Unknown")
        score = r.score
        reasons = ", ".join(r.reasons) if r.reasons else "no_reasons"
        
        print(f"{i}. Chunk ID: {chunk_id}")
        print(f"   Entity: {entity}")
        print(f"   Section: {section}")
        print(f"   Score: {score:.2f}")
        print(f"   Reasons: {reasons}")
        print(f"   Text preview: {chunk.get('text', '')[:150]}...")
        print()
    
    # Entity diversity summary with diversity behavior confirmation
    entity_counts = {}
    for r in results:
        entity = str(r.chunk.get("metadata", {}).get("entity", "General"))
        entity_counts[entity] = entity_counts.get(entity, 0) + 1
    
    print("Entity Distribution:")
    max_per_entity = 2
    diversity_violations = []
    for entity, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True):
        marker = "⚠️" if count > max_per_entity else "✓"
        print(f"  {marker} {entity}: {count} chunk(s)")
        if count > max_per_entity:
            diversity_violations.append((entity, count))
    
    # Diversity behavior confirmation
    print(f"\nDiversity Behavior:")
    print(f"  Max per entity (first pass): {max_per_entity}")
    if diversity_violations:
        print(f"  ⚠️  Backfill exceeded cap for: {', '.join(f'{e}({c})' for e, c in diversity_violations)}")
        print(f"  Note: Backfill allows exceeding cap to reach top_k={top_k}")
    else:
        print(f"  ✓ All entities within cap")
    print(f"  Total chunks: {len(results)} (requested top_k={top_k})")
    if len(results) < top_k:
        print(f"  Note: Only {len(results)} chunks available (corpus size limit)")
    
    print("=" * 80)

