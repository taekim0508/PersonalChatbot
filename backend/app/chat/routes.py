from fastapi import APIRouter
from app.chat.schema import ChatRequest, ChatResponse, RetrievedEvidence, Citation
from app.core.kb import get_kb
from rag.retrieval import retrieve
from app.chat.prompting import build_prompt

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

    # Convert retrieval results → raw chunk dicts
    retrieved_chunks = [r.chunk for r in results]

    # Build prompt (LLM-agnostic). You can log this for debugging.
    system_prompt, user_prompt = build_prompt(req.query, retrieved_chunks)

    # Placeholder answer (until LLM is wired in)
    answer = (
        "Retrieval succeeded. Next step: wire an LLM call to synthesize an answer.\n\n"
        "For debugging, here are the top retrieved sources (section/entity)."
    )

    citations = []
    evidence = []
    for r in results:
        ch = r.chunk
        meta = ch.get("metadata", {})
        citations.append(
            Citation(
                chunk_id=ch["id"],
                section=str(meta.get("section", "")),
                entity=str(meta.get("entity", "")),
            )
        )
        evidence.append(
            RetrievedEvidence(
                id=ch["id"],
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
