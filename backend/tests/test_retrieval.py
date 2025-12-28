# backend/tests/test_retrieval.py
from rag.pdf_extract import extract_text_from_pdf
from rag.chunking import create_contextual_chunks
from scripts.build_index import build_inverted_index
from rag.retrieval import retrieve

def test_ai_query_returns_ai_chunks(tmp_path):
    text = extract_text_from_pdf("data/KimTae-SWE-Resume.pdf")
    chunks = create_contextual_chunks(text, source="KimTae-SWE-Resume.pdf")
    inv = build_inverted_index(chunks)
    by_id = {c["id"]: c for c in chunks}

    results = retrieve("what experience does Tae have with AI", inv=inv, chunk_by_id=by_id, top_k=5)
    assert results, "No retrieval results for AI query"
    assert any("AI" in r.chunk["metadata"].get("keywords", []) or "LLM" in r.chunk["metadata"].get("keywords", [])
               for r in results), "Expected AI/LLM-related chunks in top results"
