# backend/tests/test_chat_routes.py
"""
Tests for chat API routes.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.kb import KnowledgeBase, set_kb
from rag.retrieval import RetrievedChunk


@pytest.fixture
def mock_kb():
    """Create a mock knowledge base for testing."""
    chunks = [
        {
            "id": "chunk_001",
            "text": "Worked on FastAPI backend development at Company A. Built REST APIs and WebSocket services.",
            "metadata": {
                "section": "Experience",
                "entity": "Company A",
                "keywords": ["FastAPI", "Python", "Backend", "REST", "WebSocket"],
            },
        },
        {
            "id": "chunk_002",
            "text": "Developed RAG system using OpenAI API. Implemented chunking and retrieval.",
            "metadata": {
                "section": "Projects",
                "entity": "RAG Project",
                "keywords": ["RAG", "OpenAI", "LLM", "AI"],
            },
        },
        {
            "id": "chunk_003",
            "text": "Led team of 3 engineers. Managed sprint planning and code reviews.",
            "metadata": {
                "section": "Experience",
                "entity": "Company B",
                "keywords": ["Leadership", "Management"],
            },
        },
    ]
    
    # Create a simple inverted index
    inverted_index = {
        "fastapi": ["chunk_001"],
        "backend": ["chunk_001"],
        "rag": ["chunk_002"],
        "openai": ["chunk_002"],
        "team": ["chunk_003"],
        "leadership": ["chunk_003"],
    }
    
    chunk_by_id = {c["id"]: c for c in chunks}
    
    kb = KnowledgeBase(
        chunks=chunks,
        inverted_index=inverted_index,
        chunk_by_id=chunk_by_id,
    )
    
    # Set the global KB
    set_kb(kb)
    return kb


@pytest.fixture
def client(mock_kb):
    """Create a test client with mocked KB."""
    return TestClient(app)


def test_chat_endpoint_basic(client):
    """Test basic chat endpoint functionality."""
    response = client.post(
        "/chat",
        json={
            "query": "What backend frameworks have you used?",
            "top_k": 3,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "query" in data
    assert "top_k" in data
    assert "answer" in data
    assert "citations" in data
    assert "evidence" in data
    assert data["query"] == "What backend frameworks have you used?"
    assert data["top_k"] == 3
    assert isinstance(data["answer"], str)
    assert isinstance(data["citations"], list)
    assert isinstance(data["evidence"], list)


def test_chat_endpoint_evidence_structure(client):
    """Test that evidence has the correct structure."""
    response = client.post(
        "/chat",
        json={
            "query": "FastAPI",
            "top_k": 2,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["evidence"]) > 0
    
    for ev in data["evidence"]:
        assert "id" in ev
        assert "score" in ev
        assert "section" in ev
        assert "entity" in ev
        assert "keywords" in ev
        assert "text_preview" in ev
        assert isinstance(ev["score"], (int, float))
        assert isinstance(ev["keywords"], list)


def test_chat_endpoint_citations_structure(client):
    """Test that citations have the correct structure."""
    response = client.post(
        "/chat",
        json={
            "query": "RAG",
            "top_k": 2,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["citations"]) > 0
    
    for citation in data["citations"]:
        assert "chunk_id" in citation
        assert "section" in citation
        assert "entity" in citation
        assert isinstance(citation["chunk_id"], str)
        assert isinstance(citation["section"], str)
        assert isinstance(citation["entity"], str)


def test_chat_endpoint_citations_match_evidence(client):
    """Test that citations correspond to evidence chunks."""
    response = client.post(
        "/chat",
        json={
            "query": "backend",
            "top_k": 3,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Citations should match evidence IDs
    evidence_ids = {ev["id"] for ev in data["evidence"]}
    citation_ids = {cit["chunk_id"] for cit in data["citations"]}
    
    assert evidence_ids == citation_ids, "Citation IDs should match evidence IDs"


def test_chat_endpoint_empty_query(client):
    """Test validation for empty query."""
    response = client.post(
        "/chat",
        json={
            "query": "",
            "top_k": 3,
        },
    )
    
    # Should return validation error
    assert response.status_code == 422


def test_chat_endpoint_invalid_top_k(client):
    """Test validation for invalid top_k values."""
    # Too low
    response = client.post(
        "/chat",
        json={
            "query": "test",
            "top_k": 0,
        },
    )
    assert response.status_code == 422
    
    # Too high
    response = client.post(
        "/chat",
        json={
            "query": "test",
            "top_k": 20,
        },
    )
    assert response.status_code == 422


def test_chat_endpoint_missing_fields(client):
    """Test validation for missing required fields."""
    response = client.post(
        "/chat",
        json={
            "query": "test",
            # Missing top_k
        },
    )
    
    # Should use default top_k=6, so should succeed
    assert response.status_code == 200


def test_chat_endpoint_handles_no_results(client):
    """Test that endpoint handles queries with no matching results."""
    # Query that likely won't match anything in our mock KB
    response = client.post(
        "/chat",
        json={
            "query": "xyzabc123nonexistent",
            "top_k": 3,
        },
    )
    
    # Should still return 200, but with empty or minimal results
    assert response.status_code == 200
    data = response.json()
    assert "evidence" in data
    assert "citations" in data
    # May have empty lists or fallback results depending on retrieval logic


def test_chat_endpoint_text_preview_length(client):
    """Test that text_preview is truncated appropriately."""
    response = client.post(
        "/chat",
        json={
            "query": "test",
            "top_k": 1,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    if data["evidence"]:
        # Text preview should be at most 500 chars (as per routes.py)
        for ev in data["evidence"]:
            assert len(ev["text_preview"]) <= 500


def test_chat_endpoint_answer_field_present(client):
    """Test that answer field is always present (even if placeholder)."""
    response = client.post(
        "/chat",
        json={
            "query": "What is your experience?",
            "top_k": 2,
        },
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "answer" in data
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0


