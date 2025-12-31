from fastapi import APIRouter
from app.chat.schema import ChatRequest, ChatResponse, RetrievedEvidence, Citation
from app.core.kb import get_kb
from rag.retrieval import retrieve
from app.chat.prompting import build_prompt
from app.chat.llm import generate_answer_with_citations

router = APIRouter(prefix="/chat", tags=["chat"])


def is_relevant(chunk: dict, query: str) -> bool:
    """
    Lightweight relevance filter to ensure ONLY relevant chunks are passed to the LLM.
    
    Why this exists:
      - Prevents LLM from seeing irrelevant chunks (e.g., Tic Tac Toe for AI questions)
      - Eliminates LLM explanations of why something is irrelevant
      - Ensures evidence and citations exactly match what the LLM saw
      - Deterministic keyword-based filtering (no LLM calls)
    
    Rules:
    - If query contains "ai", "llm", "machine learning", or "artificial intelligence":
        keep only chunks whose metadata.keywords include "AI", "LLM", or "RAG"
    - If query contains "backend":
        keep chunks whose keywords include Backend, FastAPI, REST, WebSockets, Node.js
    - Otherwise:
        default to keeping all chunks
    """
    query_lower = query.lower()
    meta = chunk.get("metadata", {})
    keywords = meta.get("keywords", [])
    keywords_lower = [kw.lower() for kw in keywords]
    
    # AI/LLM filtering
    ai_terms = ["ai", "llm", "machine learning", "artificial intelligence", "ml"]
    if any(term in query_lower for term in ai_terms):
        ai_keywords = ["ai", "llm", "rag"]
        return any(kw in keywords_lower for kw in ai_keywords)
    
    # Backend filtering
    if "backend" in query_lower:
        backend_keywords = ["backend", "fastapi", "rest", "websockets", "websocket", "node.js", "nodejs"]
        return any(kw in keywords_lower for kw in backend_keywords)
    
    # Default: keep all chunks if no specific filter matches
    return True


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    kb = get_kb()

    results = retrieve(
        req.query,
        inv=kb.inverted_index,
        chunk_by_id=kb.chunk_by_id,
        top_k=req.top_k,
    )

    # Filter chunks for relevance BEFORE building prompt
    # This ensures LLM only sees relevant chunks and doesn't explain why others are irrelevant
    retrieved_chunks = [r.chunk for r in results if is_relevant(r.chunk, req.query)]
    allowed_chunk_ids = [c.get("id", "") for c in retrieved_chunks if c.get("id")]

    system_prompt, user_prompt = build_prompt(req.query, retrieved_chunks)

    # REAL ANSWER (replaces placeholder)
    answer, cited_ids, _raw = generate_answer_with_citations(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        allowed_chunk_ids=allowed_chunk_ids,
        model="gpt-4.1-nano",
    )

    # Build citations from cited chunk ids (map back to metadata)
    # Only cite chunks that were actually passed to the LLM (filtered list)
    citations = []
    filtered_chunk_ids = {c.get("id") for c in retrieved_chunks if c.get("id")}
    for cid in cited_ids:
        # Only include citations for chunks that were in the filtered set
        if cid not in filtered_chunk_ids:
            continue
        ch = kb.chunk_by_id.get(cid)
        if not ch:
            continue
        meta = ch.get("metadata", {})
        citations.append(
            Citation(
                chunk_id=cid,
                section=str(meta.get("section", "")),
                entity=str(meta.get("entity", "")),
            )
        )

    # Build evidence from the SAME filtered chunks that were passed to the LLM
    # This ensures evidence exactly matches what the model saw
    evidence = []
    # Create a mapping from chunk ID to result for score lookup
    result_by_chunk_id = {r.chunk.get("id"): r for r in results}
    
    for chunk in retrieved_chunks:
        chunk_id = chunk.get("id", "")
        if not chunk_id:
            continue  # Skip chunks without IDs
        meta = chunk.get("metadata", {})
        # Get score from original results if available
        result = result_by_chunk_id.get(chunk_id)
        score = result.score if result else 0.0
        
        evidence.append(
            RetrievedEvidence(
                id=chunk_id,
                score=score,
                section=str(meta.get("section", "")),
                entity=str(meta.get("entity", "")),
                keywords=list(meta.get("keywords", [])),
                text_preview=chunk.get("text", "")[:500],
            )
        )

    return ChatResponse(
        query=req.query,
        top_k=req.top_k,
        answer=answer,
        citations=citations,
        evidence=evidence,
    )
