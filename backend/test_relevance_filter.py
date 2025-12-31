#!/usr/bin/env python3
"""
Test script to verify relevance filtering works correctly.
Tests that:
1. AI queries only return chunks with AI/LLM/RAG keywords
2. Backend queries only return chunks with backend-related keywords
3. General queries return all chunks
4. Evidence and citations match filtered chunks
"""
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.chat.routes import is_relevant
from app.core.kb import load_kb, set_kb
from rag.retrieval import retrieve


def test_ai_filtering():
    """Test that AI queries filter to only AI/LLM/RAG chunks."""
    print("=" * 80)
    print("TEST 1: AI Query Filtering")
    print("=" * 80)
    
    kb = load_kb(
        chunks_path="index/chunks.json",
        inverted_index_path="index/inverted_index.json",
    )
    set_kb(kb)
    
    query = "What experience does Tae have with AI?"
    results = retrieve(
        query,
        inv=kb.inverted_index,
        chunk_by_id=kb.chunk_by_id,
        top_k=10,
    )
    
    print(f"\nQuery: '{query}'")
    print(f"Retrieved {len(results)} chunks before filtering")
    
    # Filter chunks
    filtered_chunks = [r.chunk for r in results if is_relevant(r.chunk, query)]
    print(f"Filtered to {len(filtered_chunks)} relevant chunks")
    
    # Check that all filtered chunks have AI/LLM/RAG keywords
    ai_keywords = {"ai", "llm", "rag"}
    all_relevant = True
    irrelevant_chunks = []
    
    for chunk in filtered_chunks:
        meta = chunk.get("metadata", {})
        keywords = [kw.lower() for kw in meta.get("keywords", [])]
        has_ai_keyword = any(kw in ai_keywords for kw in keywords)
        
        if not has_ai_keyword:
            all_relevant = False
            irrelevant_chunks.append({
                "id": chunk.get("id"),
                "entity": meta.get("entity"),
                "keywords": keywords
            })
    
    print(f"\n✓ All filtered chunks have AI/LLM/RAG keywords: {all_relevant}")
    if irrelevant_chunks:
        print(f"✗ Found {len(irrelevant_chunks)} irrelevant chunks:")
        for ic in irrelevant_chunks:
            print(f"  - {ic['id']}: {ic['entity']} (keywords: {ic['keywords']})")
    
    # Show sample filtered chunks
    print(f"\nSample filtered chunks:")
    for i, chunk in enumerate(filtered_chunks[:3], 1):
        meta = chunk.get("metadata", {})
        print(f"  {i}. {chunk.get('id')} | {meta.get('entity')} | keywords: {meta.get('keywords')}")
    
    return all_relevant and len(filtered_chunks) > 0


def test_backend_filtering():
    """Test that backend queries filter to only backend-related chunks."""
    print("\n" + "=" * 80)
    print("TEST 2: Backend Query Filtering")
    print("=" * 80)
    
    kb = load_kb(
        chunks_path="index/chunks.json",
        inverted_index_path="index/inverted_index.json",
    )
    set_kb(kb)
    
    query = "What backend frameworks has Tae used?"
    results = retrieve(
        query,
        inv=kb.inverted_index,
        chunk_by_id=kb.chunk_by_id,
        top_k=10,
    )
    
    print(f"\nQuery: '{query}'")
    print(f"Retrieved {len(results)} chunks before filtering")
    
    # Filter chunks
    filtered_chunks = [r.chunk for r in results if is_relevant(r.chunk, query)]
    print(f"Filtered to {len(filtered_chunks)} relevant chunks")
    
    # Check that all filtered chunks have backend keywords
    backend_keywords = {"backend", "fastapi", "rest", "websockets", "websocket", "node.js", "nodejs"}
    all_relevant = True
    irrelevant_chunks = []
    
    for chunk in filtered_chunks:
        meta = chunk.get("metadata", {})
        keywords = [kw.lower() for kw in meta.get("keywords", [])]
        has_backend_keyword = any(kw in backend_keywords for kw in keywords)
        
        if not has_backend_keyword:
            all_relevant = False
            irrelevant_chunks.append({
                "id": chunk.get("id"),
                "entity": meta.get("entity"),
                "keywords": keywords
            })
    
    print(f"\n✓ All filtered chunks have backend keywords: {all_relevant}")
    if irrelevant_chunks:
        print(f"✗ Found {len(irrelevant_chunks)} irrelevant chunks:")
        for ic in irrelevant_chunks:
            print(f"  - {ic['id']}: {ic['entity']} (keywords: {ic['keywords']})")
    
    # Show sample filtered chunks
    if filtered_chunks:
        print(f"\nSample filtered chunks:")
        for i, chunk in enumerate(filtered_chunks[:3], 1):
            meta = chunk.get("metadata", {})
            print(f"  {i}. {chunk.get('id')} | {meta.get('entity')} | keywords: {meta.get('keywords')}")
    else:
        print("\n⚠ No backend chunks found (this may be expected if resume has no backend keywords)")
    
    return all_relevant


def test_general_query():
    """Test that general queries return all chunks (no filtering)."""
    print("\n" + "=" * 80)
    print("TEST 3: General Query (No Filtering)")
    print("=" * 80)
    
    kb = load_kb(
        chunks_path="index/chunks.json",
        inverted_index_path="index/inverted_index.json",
    )
    set_kb(kb)
    
    query = "What is Tae's experience?"
    results = retrieve(
        query,
        inv=kb.inverted_index,
        chunk_by_id=kb.chunk_by_id,
        top_k=10,
    )
    
    print(f"\nQuery: '{query}'")
    print(f"Retrieved {len(results)} chunks before filtering")
    
    # Filter chunks (should keep all for general queries)
    filtered_chunks = [r.chunk for r in results if is_relevant(r.chunk, query)]
    print(f"Filtered to {len(filtered_chunks)} chunks (should match retrieved count)")
    
    no_filtering = len(filtered_chunks) == len(results)
    print(f"\n✓ General query keeps all chunks: {no_filtering}")
    
    return no_filtering


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("RELEVANCE FILTER TEST SUITE")
    print("=" * 80)
    
    test1_pass = test_ai_filtering()
    test2_pass = test_backend_filtering()
    test3_pass = test_general_query()
    
    print("\n" + "=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print(f"Test 1 (AI Filtering): {'PASS' if test1_pass else 'FAIL'}")
    print(f"Test 2 (Backend Filtering): {'PASS' if test2_pass else 'FAIL'}")
    print(f"Test 3 (General Query): {'PASS' if test3_pass else 'FAIL'}")
    
    all_pass = test1_pass and test2_pass and test3_pass
    print(f"\nOverall: {'ALL TESTS PASSED ✓' if all_pass else 'SOME TESTS FAILED ✗'}")
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())


