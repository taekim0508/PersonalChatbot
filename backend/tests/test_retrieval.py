"""
Tests for retrieval functionality, including diversity reranking.
"""
import pytest
from pathlib import Path
from rag.retrieval import (
    retrieve,
    diversify_results,
    RetrievedChunk,
    load_chunks_and_index,
    debug_retrieval,
)


def test_retrieval_diversity_max_2_per_entity():
    """
    Test that diversity reranking limits results to at most 2 chunks per entity
    while preserving score ordering.
    
    This test FAILS if more than 2 chunks from the same entity appear in top_k
    results for a broad query like 'AI experience'.
    """
    chunks_path = Path("index/chunks.json")
    inverted_index_path = Path("index/inverted_index.json")
    
    if not chunks_path.exists() or not inverted_index_path.exists():
        pytest.skip("Index files not found. Run build_index.py first.")
    
    _, inv, by_id = load_chunks_and_index(
        chunks_path=str(chunks_path),
        inverted_index_path=str(inverted_index_path)
    )
    
    # Test with a broad query that should match multiple chunks from same entities
    query = "AI experience"
    results = retrieve(query, inv=inv, chunk_by_id=by_id, top_k=6, apply_diversity=True)
    
    # Count chunks per entity
    entity_counts = {}
    for r in results:
        entity = str(r.chunk.get("metadata", {}).get("entity", "General"))
        entity_counts[entity] = entity_counts.get(entity, 0) + 1
    
    # Assert no entity has more than 2 chunks
    # This test FAILS if diversity reranking is not working correctly
    for entity, count in entity_counts.items():
        assert count <= 2, (
            f"Entity '{entity}' has {count} chunks in top_k results, "
            f"but diversity reranking should limit to max 2 per entity. "
            f"Entity counts: {entity_counts}. "
            f"This indicates diversity reranking is not working correctly."
        )


def test_retrieval_preserves_score_ordering():
    """
    Test that diversity reranking preserves score ordering.
    """
    # Create mock chunks with known scores
    chunks = [
        {
            "id": "chunk_001",
            "text": "AI work at Company A",
            "metadata": {"entity": "Company A", "section": "Experience", "keywords": ["AI"]},
        },
        {
            "id": "chunk_002",
            "text": "More AI work at Company A",
            "metadata": {"entity": "Company A", "section": "Experience", "keywords": ["AI"]},
        },
        {
            "id": "chunk_003",
            "text": "Even more AI work at Company A",
            "metadata": {"entity": "Company A", "section": "Experience", "keywords": ["AI"]},
        },
        {
            "id": "chunk_004",
            "text": "AI project at Project B",
            "metadata": {"entity": "Project B", "section": "Projects", "keywords": ["AI"]},
        },
    ]
    
    # Create mock results with decreasing scores
    results = [
        RetrievedChunk(chunk=chunks[0], score=10.0, reasons=["token_overlap(2)"]),
        RetrievedChunk(chunk=chunks[1], score=9.0, reasons=["token_overlap(2)"]),
        RetrievedChunk(chunk=chunks[2], score=8.0, reasons=["token_overlap(1)"]),
        RetrievedChunk(chunk=chunks[3], score=7.0, reasons=["token_overlap(1)"]),
    ]
    
    # Apply diversity (max 2 per entity in first pass, but backfill can exceed)
    diversified = diversify_results(results, top_k=4, max_per_entity=2)
    
    # First pass: chunk_001, chunk_002 (Company A - 2 chunks), chunk_004 (Project B - 1 chunk) = 3 chunks
    # Backfill: chunk_003 (Company A - exceeds cap but needed to reach top_k=4)
    assert len(diversified) == 4  # Backfill allows exceeding cap to reach top_k
    
    # Verify scores are in descending order
    scores = [r.score for r in diversified]
    assert scores == sorted(scores, reverse=True), "Scores should be in descending order"
    
    # Verify first pass respected cap (first 2 Company A chunks)
    assert diversified[0].chunk["id"] == "chunk_001"  # Highest score
    assert diversified[1].chunk["id"] == "chunk_002"  # Second highest
    
    # Count Company A chunks (should be 3 after backfill)
    company_a_count = sum(1 for r in diversified if r.chunk["metadata"]["entity"] == "Company A")
    assert company_a_count == 3, "Backfill should allow exceeding cap to reach top_k"


def test_retrieval_ai_experience_query():
    """
    Test retrieval for 'what experience does Tae have with AI' query.
    """
    chunks_path = Path("index/chunks.json")
    inverted_index_path = Path("index/inverted_index.json")
    
    if not chunks_path.exists() or not inverted_index_path.exists():
        pytest.skip("Index files not found. Run build_index.py first.")
    
    _, inv, by_id = load_chunks_and_index(
        chunks_path=str(chunks_path),
        inverted_index_path=str(inverted_index_path)
    )
    
    query = "what experience does Tae have with AI"
    results = retrieve(query, inv=inv, chunk_by_id=by_id, top_k=6, apply_diversity=True)
    
    assert len(results) > 0, "Should retrieve at least one result for AI experience query"
    
    # Check that results are relevant (contain AI-related keywords or text)
    ai_keywords = ["ai", "llm", "rag", "openai", "gpt"]
    has_ai_content = False
    for r in results:
        text_lower = r.chunk.get("text", "").lower()
        keywords = [kw.lower() for kw in r.chunk.get("metadata", {}).get("keywords", [])]
        if any(kw in text_lower or kw in keywords for kw in ai_keywords):
            has_ai_content = True
            break
    
    assert has_ai_content, "Results should contain AI-related content"
    
    # Verify diversity (max 2 per entity)
    entity_counts = {}
    for r in results:
        entity = str(r.chunk.get("metadata", {}).get("entity", "General"))
        entity_counts[entity] = entity_counts.get(entity, 0) + 1
    
    for entity, count in entity_counts.items():
        assert count <= 2, f"Entity '{entity}' should have at most 2 chunks, got {count}"


def test_retrieval_backend_frameworks_query():
    """
    Test retrieval for 'what backend frameworks has Tae used' query.
    """
    chunks_path = Path("index/chunks.json")
    inverted_index_path = Path("index/inverted_index.json")
    
    if not chunks_path.exists() or not inverted_index_path.exists():
        pytest.skip("Index files not found. Run build_index.py first.")
    
    _, inv, by_id = load_chunks_and_index(
        chunks_path=str(chunks_path),
        inverted_index_path=str(inverted_index_path)
    )
    
    query = "what backend frameworks has Tae used"
    results = retrieve(query, inv=inv, chunk_by_id=by_id, top_k=6, apply_diversity=True)
    
    assert len(results) > 0, "Should retrieve at least one result for backend frameworks query"
    
    # Check that results mention backend frameworks
    backend_keywords = ["fastapi", "backend", "rest", "api", "express", "node.js"]
    has_backend_content = False
    for r in results:
        text_lower = r.chunk.get("text", "").lower()
        keywords = [kw.lower() for kw in r.chunk.get("metadata", {}).get("keywords", [])]
        if any(kw in text_lower or kw in keywords for kw in backend_keywords):
            has_backend_content = True
            break
    
    assert has_backend_content, "Results should contain backend framework content"


def test_retrieval_fastapi_query():
    """
    Test retrieval for 'what did Tae build with FastAPI' query.
    """
    chunks_path = Path("index/chunks.json")
    inverted_index_path = Path("index/inverted_index.json")
    
    if not chunks_path.exists() or not inverted_index_path.exists():
        pytest.skip("Index files not found. Run build_index.py first.")
    
    _, inv, by_id = load_chunks_and_index(
        chunks_path=str(chunks_path),
        inverted_index_path=str(inverted_index_path)
    )
    
    query = "what did Tae build with FastAPI"
    results = retrieve(query, inv=inv, chunk_by_id=by_id, top_k=6, apply_diversity=True)
    
    assert len(results) > 0, "Should retrieve at least one result for FastAPI query"
    
    # Check that results mention FastAPI
    has_fastapi = False
    for r in results:
        text_lower = r.chunk.get("text", "").lower()
        keywords = [kw.lower() for kw in r.chunk.get("metadata", {}).get("keywords", [])]
        if "fastapi" in text_lower or "fastapi" in keywords:
            has_fastapi = True
            break
    
    assert has_fastapi, "Results should contain FastAPI mentions"


def test_retrieval_realtime_systems_query():
    """
    Test retrieval for 'what real-time systems has Tae worked on' query.
    """
    chunks_path = Path("index/chunks.json")
    inverted_index_path = Path("index/inverted_index.json")
    
    if not chunks_path.exists() or not inverted_index_path.exists():
        pytest.skip("Index files not found. Run build_index.py first.")
    
    _, inv, by_id = load_chunks_and_index(
        chunks_path=str(chunks_path),
        inverted_index_path=str(inverted_index_path)
    )
    
    query = "what real-time systems has Tae worked on"
    results = retrieve(query, inv=inv, chunk_by_id=by_id, top_k=6, apply_diversity=True)
    
    assert len(results) > 0, "Should retrieve at least one result for real-time systems query"
    
    # Check that results mention real-time systems
    realtime_keywords = ["real-time", "realtime", "websocket", "socket.io", "socketio"]
    has_realtime_content = False
    for r in results:
        text_lower = r.chunk.get("text", "").lower()
        keywords = [kw.lower() for kw in r.chunk.get("metadata", {}).get("keywords", [])]
        if any(kw in text_lower or kw in keywords for kw in realtime_keywords):
            has_realtime_content = True
            break
    
    assert has_realtime_content, "Results should contain real-time system content"


def test_real_time_phrase_matching():
    """
    Test that query 'real time systems' triggers phrase_match(real-time) 
    when chunk contains 'real-time' or 'real time'.
    """
    chunks = [
        {
            "id": "chunk_001",
            "text": "Built real-time systems using WebSockets",
            "metadata": {"entity": "Entity A", "section": "PROJECTS", "keywords": []},
        },
        {
            "id": "chunk_002",
            "text": "Developed real time communication systems",
            "metadata": {"entity": "Entity B", "section": "PROJECTS", "keywords": []},
        },
        {
            "id": "chunk_003",
            "text": "Worked on backend systems",
            "metadata": {"entity": "Entity C", "section": "PROJECTS", "keywords": []},
        },
    ]
    
    # Create inverted index
    inv = {
        "built": ["chunk_001"],
        "real": ["chunk_001", "chunk_002"],
        "time": ["chunk_001", "chunk_002"],
        "systems": ["chunk_001", "chunk_002", "chunk_003"],
        "developed": ["chunk_002"],
        "worked": ["chunk_003"],
        "backend": ["chunk_003"],
    }
    
    chunk_by_id = {c["id"]: c for c in chunks}
    
    query = "real time systems"
    results = retrieve(query, inv=inv, chunk_by_id=chunk_by_id, top_k=3, apply_diversity=False)
    
    assert len(results) > 0, "Should retrieve at least one result"
    
    # Find chunks with real-time content
    realtime_chunks = []
    for r in results:
        reasons_str = ", ".join(r.reasons)
        if "phrase_match(real-time)" in reasons_str:
            realtime_chunks.append(r)
    
    # At least one chunk with 'real-time' or 'real time' should have phrase_match(real-time)
    assert len(realtime_chunks) >= 1, (
        f"Query 'real time systems' should trigger phrase_match(real-time) for chunks "
        f"containing 'real-time' or 'real time', but got reasons: "
        f"{[', '.join(r.reasons) for r in results]}"
    )
    
    # Verify the chunks with real-time content have the phrase match
    for r in results:
        text_lower = r.chunk.get("text", "").lower()
        if "real-time" in text_lower or "real time" in text_lower:
            reasons_str = ", ".join(r.reasons)
            assert "phrase_match(real-time)" in reasons_str, (
                f"Chunk with text '{r.chunk.get('text', '')}' should have "
                f"phrase_match(real-time) reason, but got: {r.reasons}"
            )


def test_diversity_cap_respected_first_pass():
    """
    Test that diversity cap is respected in first-pass selection.
    When enough entities exist, no entity should exceed max_per_entity in first pass.
    """
    chunks = [
        {"id": "chunk_001", "text": "Text 1", "metadata": {"entity": "Entity A", "section": "Section1"}},
        {"id": "chunk_002", "text": "Text 2", "metadata": {"entity": "Entity A", "section": "Section1"}},
        {"id": "chunk_003", "text": "Text 3", "metadata": {"entity": "Entity A", "section": "Section1"}},
        {"id": "chunk_004", "text": "Text 4", "metadata": {"entity": "Entity B", "section": "Section1"}},
        {"id": "chunk_005", "text": "Text 5", "metadata": {"entity": "Entity B", "section": "Section1"}},
        {"id": "chunk_006", "text": "Text 6", "metadata": {"entity": "Entity C", "section": "Section1"}},
        {"id": "chunk_007", "text": "Text 7", "metadata": {"entity": "Entity C", "section": "Section1"}},
    ]
    
    results = [
        RetrievedChunk(chunk=chunks[0], score=10.0, reasons=[]),  # Entity A
        RetrievedChunk(chunk=chunks[1], score=9.0, reasons=[]),   # Entity A
        RetrievedChunk(chunk=chunks[2], score=8.0, reasons=[]),   # Entity A (should be skipped in first pass)
        RetrievedChunk(chunk=chunks[3], score=7.0, reasons=[]),   # Entity B
        RetrievedChunk(chunk=chunks[4], score=6.0, reasons=[]),   # Entity B
        RetrievedChunk(chunk=chunks[5], score=5.0, reasons=[]),   # Entity C
        RetrievedChunk(chunk=chunks[6], score=4.0, reasons=[]),   # Entity C
    ]
    
    diversified = diversify_results(results, top_k=6, max_per_entity=2)
    
    # First pass should give us: 2 from A, 2 from B, 2 from C = 6 chunks (exactly top_k)
    # No backfill needed, so all chunks should respect the cap
    
    # Count chunks per entity
    entity_counts = {}
    for r in diversified:
        entity = r.chunk["metadata"]["entity"]
        entity_counts[entity] = entity_counts.get(entity, 0) + 1
    
    # Verify all entities respect the cap (no backfill happened since we have exactly 6)
    for entity, count in entity_counts.items():
        assert count <= 2, (
            f"Entity '{entity}' has {count} chunks, "
            f"but diversity cap should limit to 2 per entity when enough entities exist"
        )
    
    # Verify we got exactly 6 chunks (2 from each entity)
    assert len(diversified) == 6
    assert entity_counts["Entity A"] == 2
    assert entity_counts["Entity B"] == 2
    assert entity_counts["Entity C"] == 2


def test_returns_exactly_top_k_when_enough_chunks_exist():
    """
    Test that diversify_results returns exactly top_k when enough chunks exist (via backfill).
    """
    chunks = [
        {"id": f"chunk_{i:03d}", "text": f"Text {i}", "metadata": {"entity": f"Entity {i % 3}", "section": "Section1"}}
        for i in range(10)
    ]
    
    results = [
        RetrievedChunk(chunk=chunks[i], score=10.0 - i, reasons=[])
        for i in range(10)
    ]
    
    diversified = diversify_results(results, top_k=6, max_per_entity=2)
    
    # Should return exactly top_k=6 chunks
    assert len(diversified) == 6, (
        f"Expected exactly 6 chunks (top_k=6), got {len(diversified)}"
    )


def test_projects_query_returns_projects_chunk():
    """
    Test that a 'projects' query gives at least one PROJECTS chunk in top_k.
    """
    chunks = [
        {
            "id": "chunk_001",
            "text": "Built a chatbot project",
            "metadata": {"entity": "Entity A", "section": "PROJECTS", "keywords": []},
        },
        {
            "id": "chunk_002",
            "text": "Worked on backend systems",
            "metadata": {"entity": "Entity B", "section": "PROFESSIONAL EXPERIENCE", "keywords": []},
        },
        {
            "id": "chunk_003",
            "text": "Developed web applications",
            "metadata": {"entity": "Entity C", "section": "PROFESSIONAL EXPERIENCE", "keywords": []},
        },
    ]
    
    # Create inverted index
    inv = {
        "built": ["chunk_001"],
        "chatbot": ["chunk_001"],
        "project": ["chunk_001"],
        "worked": ["chunk_002"],
        "backend": ["chunk_002"],
        "developed": ["chunk_003"],
        "web": ["chunk_003"],
    }
    
    chunk_by_id = {c["id"]: c for c in chunks}
    
    query = "what projects have you built"
    results = retrieve(query, inv=inv, chunk_by_id=chunk_by_id, top_k=3, apply_diversity=True)
    
    assert len(results) > 0, "Should retrieve at least one result"
    
    # At least one result should be from PROJECTS section
    projects_chunks = [r for r in results if r.chunk["metadata"]["section"] == "PROJECTS"]
    assert len(projects_chunks) >= 1, (
        f"Query 'projects' should return at least one PROJECTS chunk, "
        f"but got sections: {[r.chunk['metadata']['section'] for r in results]}"
    )


def test_ai_experience_returns_multiple_entities():
    """
    Test that 'AI experience' query returns chunks from at least 2 distinct entities when available.
    """
    chunks_path = Path("index/chunks.json")
    inverted_index_path = Path("index/inverted_index.json")
    
    if not chunks_path.exists() or not inverted_index_path.exists():
        pytest.skip("Index files not found. Run build_index.py first.")
    
    _, inv, by_id = load_chunks_and_index(
        chunks_path=str(chunks_path),
        inverted_index_path=str(inverted_index_path)
    )
    
    query = "AI experience"
    results = retrieve(query, inv=inv, chunk_by_id=by_id, top_k=6, apply_diversity=True)
    
    assert len(results) > 0, "Should retrieve at least one result"
    
    # Get distinct entities
    entities = set(str(r.chunk.get("metadata", {}).get("entity", "General")) for r in results)
    
    # Should have at least 2 distinct entities (diversity reranking should ensure this)
    assert len(entities) >= 2, (
        f"'AI experience' query should return chunks from at least 2 distinct entities "
        f"when available, but got {len(entities)} entity(ies): {entities}"
    )


def test_diversity_reranker_handles_empty_results():
    """Test that diversity reranker handles empty results gracefully."""
    results = []
    diversified = diversify_results(results, top_k=6, max_per_entity=2)
    assert diversified == []


def test_diversity_reranker_handles_single_entity():
    """
    Test diversity reranker when all results are from the same entity.
    Backfill should allow exceeding cap to reach top_k.
    """
    chunks = [
        {"id": "chunk_001", "text": "Text 1", "metadata": {"entity": "Company A"}},
        {"id": "chunk_002", "text": "Text 2", "metadata": {"entity": "Company A"}},
        {"id": "chunk_003", "text": "Text 3", "metadata": {"entity": "Company A"}},
    ]
    
    results = [
        RetrievedChunk(chunk=chunks[0], score=10.0, reasons=[]),
        RetrievedChunk(chunk=chunks[1], score=9.0, reasons=[]),
        RetrievedChunk(chunk=chunks[2], score=8.0, reasons=[]),
    ]
    
    diversified = diversify_results(results, top_k=6, max_per_entity=2)
    
    # First pass: 2 chunks (max_per_entity limit)
    # Backfill: 1 more chunk to reach top_k=6 (but we only have 3 total, so get all 3)
    assert len(diversified) == 3  # Backfill allows exceeding cap
    assert all(r.chunk["metadata"]["entity"] == "Company A" for r in diversified)
    
    # Verify all chunks are included (backfill exceeded cap)
    entity_counts = {}
    for r in diversified:
        entity = r.chunk["metadata"]["entity"]
        entity_counts[entity] = entity_counts.get(entity, 0) + 1
    
    assert entity_counts["Company A"] == 3, "Backfill should allow exceeding cap when needed"


def test_diversity_cap_applied_first_pass():
    """
    Test that diversity cap (max 2 per entity) is applied in the first pass
    when enough entities exist to fill top_k.
    """
    chunks = [
        {"id": "chunk_001", "text": "Text 1", "metadata": {"entity": "Entity A", "section": "Section1"}},
        {"id": "chunk_002", "text": "Text 2", "metadata": {"entity": "Entity A", "section": "Section1"}},
        {"id": "chunk_003", "text": "Text 3", "metadata": {"entity": "Entity A", "section": "Section1"}},
        {"id": "chunk_004", "text": "Text 4", "metadata": {"entity": "Entity B", "section": "Section1"}},
        {"id": "chunk_005", "text": "Text 5", "metadata": {"entity": "Entity B", "section": "Section1"}},
        {"id": "chunk_006", "text": "Text 6", "metadata": {"entity": "Entity C", "section": "Section1"}},
        {"id": "chunk_007", "text": "Text 7", "metadata": {"entity": "Entity C", "section": "Section1"}},
    ]
    
    # Create results with decreasing scores
    results = [
        RetrievedChunk(chunk=chunks[0], score=10.0, reasons=[]),  # Entity A
        RetrievedChunk(chunk=chunks[1], score=9.0, reasons=[]),   # Entity A
        RetrievedChunk(chunk=chunks[2], score=8.0, reasons=[]),   # Entity A (should be skipped in first pass)
        RetrievedChunk(chunk=chunks[3], score=7.0, reasons=[]),   # Entity B
        RetrievedChunk(chunk=chunks[4], score=6.0, reasons=[]),   # Entity B
        RetrievedChunk(chunk=chunks[5], score=5.0, reasons=[]),   # Entity C
        RetrievedChunk(chunk=chunks[6], score=4.0, reasons=[]),   # Entity C
    ]
    
    diversified = diversify_results(results, top_k=6, max_per_entity=2)
    
    # First pass should give us: 2 from A, 2 from B, 2 from C = 6 total
    # No backfill needed since we have enough entities
    assert len(diversified) == 6
    
    # Count per entity
    entity_counts = {}
    for r in diversified:
        entity = r.chunk["metadata"]["entity"]
        entity_counts[entity] = entity_counts.get(entity, 0) + 1
    
    # Each entity should have exactly 2 chunks (cap applied in first pass)
    assert entity_counts["Entity A"] == 2
    assert entity_counts["Entity B"] == 2
    assert entity_counts["Entity C"] == 2


def test_backfill_hits_top_k_when_possible():
    """
    Test that backfill reaches top_k when corpus size >= top_k,
    even if it means exceeding per-entity cap.
    """
    chunks = [
        {"id": "chunk_001", "text": "Text 1", "metadata": {"entity": "Entity A", "section": "Section1"}},
        {"id": "chunk_002", "text": "Text 2", "metadata": {"entity": "Entity A", "section": "Section1"}},
        {"id": "chunk_003", "text": "Text 3", "metadata": {"entity": "Entity A", "section": "Section1"}},
        {"id": "chunk_004", "text": "Text 4", "metadata": {"entity": "Entity A", "section": "Section1"}},
        {"id": "chunk_005", "text": "Text 5", "metadata": {"entity": "Entity B", "section": "Section1"}},
    ]
    
    # All chunks from Entity A except one from Entity B
    results = [
        RetrievedChunk(chunk=chunks[0], score=10.0, reasons=[]),  # Entity A
        RetrievedChunk(chunk=chunks[1], score=9.0, reasons=[]),   # Entity A
        RetrievedChunk(chunk=chunks[2], score=8.0, reasons=[]),   # Entity A
        RetrievedChunk(chunk=chunks[3], score=7.0, reasons=[]),   # Entity A
        RetrievedChunk(chunk=chunks[4], score=6.0, reasons=[]),   # Entity B
    ]
    
    diversified = diversify_results(results, top_k=5, max_per_entity=2)
    
    # Should return top_k=5 chunks
    # First pass: 2 from A, 1 from B = 3 chunks
    # Backfill: 2 more from A (exceeding cap) = 5 total
    assert len(diversified) == 5
    
    # Entity A should have 4 chunks (exceeded cap during backfill)
    entity_counts = {}
    for r in diversified:
        entity = r.chunk["metadata"]["entity"]
        entity_counts[entity] = entity_counts.get(entity, 0) + 1
    
    assert entity_counts["Entity A"] == 4
    assert entity_counts["Entity B"] == 1


def test_projects_section_boost():
    """
    Test that a query containing 'projects' increases score for PROJECTS chunks
    vs non-PROJECTS chunks given equal token overlap.
    """
    chunks = [
        {
            "id": "chunk_001",
            "text": "Built a chatbot project",
            "metadata": {"entity": "Entity A", "section": "PROJECTS", "keywords": []},
        },
        {
            "id": "chunk_002",
            "text": "Built a chatbot project",
            "metadata": {"entity": "Entity B", "section": "PROFESSIONAL EXPERIENCE", "keywords": []},
        },
    ]
    
    # Create a simple inverted index
    inv = {
        "built": ["chunk_001", "chunk_002"],
        "chatbot": ["chunk_001", "chunk_002"],
        "project": ["chunk_001", "chunk_002"],
    }
    
    chunk_by_id = {c["id"]: c for c in chunks}
    
    # Query with 'projects' should boost PROJECTS chunk
    query = "what projects have you built"
    results = retrieve(query, inv=inv, chunk_by_id=chunk_by_id, top_k=2, apply_diversity=False)
    
    assert len(results) == 2
    
    # Find the PROJECTS chunk and non-PROJECTS chunk
    projects_chunk = None
    experience_chunk = None
    for r in results:
        section = r.chunk["metadata"]["section"]
        if section == "PROJECTS":
            projects_chunk = r
        elif "EXPERIENCE" in section:
            experience_chunk = r
    
    assert projects_chunk is not None
    assert experience_chunk is not None
    
    # PROJECTS chunk should have higher score due to section boost
    assert projects_chunk.score > experience_chunk.score, (
        f"PROJECTS chunk score ({projects_chunk.score}) should be higher than "
        f"EXPERIENCE chunk score ({experience_chunk.score}) due to section boost"
    )
    
    # Verify section_match reason is present
    assert any("section_match" in reason for reason in projects_chunk.reasons), (
        "PROJECTS chunk should have section_match reason"
    )
