from fastapi import APIRouter
from app.chat.schema import ChatRequest, ChatResponse, RetrievedEvidence, Citation
from app.core.kb import get_kb
from rag.retrieval import retrieve
from app.chat.prompting import build_prompt
from app.chat.llm import generate_answer_with_citations

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    kb = get_kb()

    results = retrieve(
        req.query,
        inv=kb.inverted_index,
        chunk_by_id=kb.chunk_by_id,
        top_k=req.top_k,
    )

    retrieved_chunks = [r.chunk for r in results]
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
    citations = []
    for cid in cited_ids:
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

    evidence = []
    for r in results:
        ch = r.chunk
        meta = ch.get("metadata", {})
        chunk_id = ch.get("id", "")
        if not chunk_id:
            continue  # Skip chunks without IDs
        evidence.append(
            RetrievedEvidence(
                id=chunk_id,
                score=r.score,
                section=str(meta.get("section", "")),
                entity=str(meta.get("entity", "")),
                keywords=list(meta.get("keywords", [])),
                text_preview=ch.get("text", "")[:500],
            )
        )

    return ChatResponse(
        query=req.query,
        top_k=req.top_k,
        answer=answer,
        citations=citations,
        evidence=evidence,
    )
