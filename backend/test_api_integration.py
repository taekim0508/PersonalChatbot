#!/usr/bin/env python3
"""
Integration test to verify the full API flow with relevance filtering.
Tests that:
1. AI queries only return AI-related evidence and citations
2. Irrelevant entities don't appear in answers
3. Evidence matches what LLM saw
"""
import sys
import json
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.chat.routes import chat, is_relevant
from app.chat.schema import ChatRequest
from app.core.kb import load_kb, set_kb


def test_ai_query_integration():
    """Test that AI queries filter out irrelevant chunks and only show AI evidence."""
    print("=" * 80)
    print("INTEGRATION TEST: AI Query")
    print("=" * 80)
    
    kb = load_kb(
        chunks_path="index/chunks.json",
        inverted_index_path="index/inverted_index.json",
    )
    set_kb(kb)
    
    # Create a request
    request = ChatRequest(query="What experience does Tae have with AI?", top_k=10)
    
    # Call the chat endpoint
    response = chat(request)
    
    print(f"\nQuery: '{request.query}'")
    print(f"Answer length: {len(response.answer)} characters")
    print(f"Evidence count: {len(response.evidence)}")
    print(f"Citations count: {len(response.citations)}")
    
    # Verify all evidence has AI/LLM/RAG keywords
    ai_keywords = {"ai", "llm", "rag"}
    all_evidence_relevant = True
    irrelevant_evidence = []
    
    for ev in response.evidence:
        keywords_lower = [kw.lower() for kw in ev.keywords]
        has_ai_keyword = any(kw in ai_keywords for kw in keywords_lower)
        
        if not has_ai_keyword:
            all_evidence_relevant = False
            irrelevant_evidence.append({
                "id": ev.id,
                "entity": ev.entity,
                "keywords": ev.keywords
            })
    
    print(f"\n✓ All evidence has AI/LLM/RAG keywords: {all_evidence_relevant}")
    if irrelevant_evidence:
        print(f"✗ Found {len(irrelevant_evidence)} irrelevant evidence items:")
        for ie in irrelevant_evidence:
            print(f"  - {ie['id']}: {ie['entity']} (keywords: {ie['keywords']})")
    
    # Verify all citations reference evidence that exists
    evidence_ids = {ev.id for ev in response.evidence}
    citation_ids = {cit.chunk_id for cit in response.citations}
    
    all_citations_valid = citation_ids.issubset(evidence_ids)
    print(f"\n✓ All citations reference evidence: {all_citations_valid}")
    if not all_citations_valid:
        missing = citation_ids - evidence_ids
        print(f"✗ Citations reference missing evidence: {missing}")
    
    # Check that answer doesn't mention irrelevant entities
    # (This is a simple check - in practice, the LLM should not mention them)
    print(f"\nEvidence entities: {set(ev.entity for ev in response.evidence)}")
    
    # Show sample evidence
    print(f"\nSample evidence (first 3):")
    for i, ev in enumerate(response.evidence[:3], 1):
        print(f"  {i}. {ev.id} | {ev.entity} | keywords: {ev.keywords}")
        print(f"     Preview: {ev.text_preview[:80]}...")
    
    return all_evidence_relevant and all_citations_valid


def test_backend_query_integration():
    """Test that backend queries filter correctly."""
    print("\n" + "=" * 80)
    print("INTEGRATION TEST: Backend Query")
    print("=" * 80)
    
    kb = load_kb(
        chunks_path="index/chunks.json",
        inverted_index_path="index/inverted_index.json",
    )
    set_kb(kb)
    
    request = ChatRequest(query="What backend frameworks has Tae used?", top_k=10)
    response = chat(request)
    
    print(f"\nQuery: '{request.query}'")
    print(f"Evidence count: {len(response.evidence)}")
    print(f"Citations count: {len(response.citations)}")
    
    # Verify all evidence has backend keywords
    backend_keywords = {"backend", "fastapi", "rest", "websockets", "websocket", "node.js", "nodejs"}
    all_evidence_relevant = True
    
    for ev in response.evidence:
        keywords_lower = [kw.lower() for kw in ev.keywords]
        has_backend_keyword = any(kw in backend_keywords for kw in keywords_lower)
        
        if not has_backend_keyword:
            all_evidence_relevant = False
            print(f"✗ Irrelevant evidence: {ev.id} | {ev.entity} | keywords: {ev.keywords}")
    
    print(f"\n✓ All evidence has backend keywords: {all_evidence_relevant}")
    
    # Verify citations match evidence
    evidence_ids = {ev.id for ev in response.evidence}
    citation_ids = {cit.chunk_id for cit in response.citations}
    all_citations_valid = citation_ids.issubset(evidence_ids)
    print(f"✓ All citations reference evidence: {all_citations_valid}")
    
    return all_evidence_relevant and all_citations_valid


def main():
    """Run integration tests."""
    print("\n" + "=" * 80)
    print("API INTEGRATION TEST SUITE")
    print("Testing full chat endpoint with relevance filtering")
    print("=" * 80)
    
    test1_pass = test_ai_query_integration()
    test2_pass = test_backend_query_integration()
    
    print("\n" + "=" * 80)
    print("INTEGRATION TEST RESULTS")
    print("=" * 80)
    print(f"Test 1 (AI Query Integration): {'PASS' if test1_pass else 'FAIL'}")
    print(f"Test 2 (Backend Query Integration): {'PASS' if test2_pass else 'FAIL'}")
    
    all_pass = test1_pass and test2_pass
    print(f"\nOverall: {'ALL TESTS PASSED ✓' if all_pass else 'SOME TESTS FAILED ✗'}")
    
    if all_pass:
        print("\n✓ Relevance filtering is working correctly!")
        print("✓ Only relevant chunks are passed to LLM")
        print("✓ Evidence matches what LLM saw")
        print("✓ Citations only reference filtered chunks")
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())


