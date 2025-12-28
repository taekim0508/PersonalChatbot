# backend/tests/test_chat_edge_cases.py
"""
Tests for edge cases and error handling in chat functionality.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.kb import KnowledgeBase, set_kb
from rag.retrieval import RetrievedChunk


@pytest.fixture
def mock_kb_with_edge_cases():
    """Create a mock KB with edge case chunks (missing fields, etc.)."""
    chunks = [
        {
            "id": "chunk_001",
            "text": "Normal chunk with all fields",
            "metadata": {
                "section": "Experience",
                "entity": "Company A",
                "keywords": ["Python", "FastAPI"],
            },
        },
        {
            "id": "chunk_002",
            "text": "Chunk with empty metadata",
            "metadata": {},
        },
        {
            "id": "chunk_003",
            "text": "Chunk with missing keywords",
            "metadata": {
                "section": "Projects",
                "entity": "Project X",
                # keywords missing
            },
        },
        {
            "id": "chunk_004",
            "text": "Very long text. " * 100,  # Long text to test truncation
            "metadata": {
                "section": "Experience",
                "entity": "Company B",
                "keywords": ["Tech"],
            },
        },
    ]
    
    inverted_index = {
        "normal": ["chunk_001"],
        "empty": ["chunk_002"],
        "missing": ["chunk_003"],
        "long": ["chunk_004"],
    }
    
    chunk_by_id = {c["id"]: c for c in chunks}
    
    kb = KnowledgeBase(
        chunks=chunks,
        inverted_index=inverted_index,
        chunk_by_id=chunk_by_id,
    )
    
    set_kb(kb)
    return kb


@pytest.fixture
def client_edge_cases(mock_kb_with_edge_cases):
    """Create a test client with edge case KB."""
    return TestClient(app)


def test_chat_handles_empty_metadata(client_edge_cases):
    """Test that chat handles chunks with empty metadata gracefully."""
    response = client_edge_cases.post(
        "/chat",
        json={
            "query": "empty",
            "top_k": 2,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should handle empty metadata without errors
    for ev in data["evidence"]:
        assert "section" in ev
        assert "entity" in ev
        assert "keywords" in ev
        # Should be empty strings or empty lists, not None
        assert isinstance(ev["section"], str)
        assert isinstance(ev["keywords"], list)


def test_chat_handles_missing_keywords(client_edge_cases):
    """Test that chat handles chunks with missing keywords field."""
    response = client_edge_cases.post(
        "/chat",
        json={
            "query": "missing",
            "top_k": 2,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should convert missing keywords to empty list
    for ev in data["evidence"]:
        assert isinstance(ev["keywords"], list)


def test_chat_handles_long_text_truncation(client_edge_cases):
    """Test that text_preview is properly truncated for long chunks."""
    response = client_edge_cases.post(
        "/chat",
        json={
            "query": "long",
            "top_k": 1,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if data["evidence"]:
        for ev in data["evidence"]:
            # Text preview should be at most 500 chars
            assert len(ev["text_preview"]) <= 500


def test_chat_handles_empty_results():
    """Test chat endpoint when retrieval returns no results."""
    # Create KB with no matching chunks
    chunks = [{"id": "chunk_001", "text": "test", "metadata": {}}]
    inverted_index = {}  # Empty index
    chunk_by_id = {c["id"]: c for c in chunks}
    
    kb = KnowledgeBase(
        chunks=chunks,
        inverted_index=inverted_index,
        chunk_by_id=chunk_by_id,
    )
    set_kb(kb)
    
    client = TestClient(app)
    response = client.post(
        "/chat",
        json={
            "query": "nonexistent_query_xyz",
            "top_k": 3,
        },
    )
    
    # Should still return 200, but may have empty or fallback results
    assert response.status_code == 200
    data = response.json()
    assert "evidence" in data
    assert "citations" in data
    assert isinstance(data["evidence"], list)
    assert isinstance(data["citations"], list)


def test_prompting_handles_missing_text_field():
    """Test that prompting handles chunks with missing text field."""
    from app.chat.prompting import format_context_chunks
    
    chunks = [
        {
            "id": "chunk_001",
            # text field missing
            "metadata": {"section": "Test", "entity": "Test"},
        },
    ]
    
    result = format_context_chunks(chunks)
    
    # Should handle gracefully, using empty string for missing text
    assert "chunk_001" in result
    assert "Text:\n" in result  # Should have Text: label even if empty


def test_prompting_handles_missing_summary_context():
    """Test that prompting handles missing summary_context in metadata."""
    from app.chat.prompting import format_context_chunks
    
    chunks = [
        {
            "id": "chunk_001",
            "text": "Some text",
            "metadata": {
                "section": "Test",
                "entity": "Test",
                # summary_context missing
            },
        },
    ]
    
    result = format_context_chunks(chunks)
    
    # Should handle missing summary_context (defaults to empty string)
    assert "chunk_001" in result
    assert "SummaryContext: " in result  # Should have label even if empty

