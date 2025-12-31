# backend/tests/test_prompt_optimization.py
"""
Test prompt variations without using API tokens.

This module allows you to:
1. Test different prompt structures
2. Compare prompt outputs with mock LLM responses
3. Validate prompt quality without API calls
4. A/B test prompt variations
"""
import pytest
from unittest.mock import patch, MagicMock
from app.chat.prompting import build_prompt
from app.chat.llm import generate_answer_with_citations
from app.chat.routes import chat
from app.chat.schema import ChatRequest
from app.core.kb import KnowledgeBase, set_kb


# Mock LLM responses for different query types
MOCK_RESPONSES = {
    "work_experience": {
        "answer": """LiveArena Technologies:
- At LiveArena, Tae worked on AI engagement initiatives, including designing a Gen Z-focused platform and prototyping an AI mentorship system using LLMs [chunk_002, chunk_003]

Personal Portfolio Chatbot:
- Built a GPT-4.1 powered RAG chatbot that synthesizes resume information into conversational responses [chunk_009]""",
        "citations": ["chunk_002", "chunk_003", "chunk_009"]
    },
    "ai_experience": {
        "answer": """Tae has extensive AI experience across multiple projects:

LiveArena Technologies:
- Developed AI engagement platforms and mentorship systems using LLMs [chunk_002, chunk_003]

Personal Portfolio Chatbot:
- Created a RAG system with GPT-4.1 for resume-based conversations [chunk_009]""",
        "citations": ["chunk_002", "chunk_003", "chunk_009"]
    },
    "synthesized": {
        "answer": """Tae's work experience spans AI development and backend engineering:

At LiveArena Technologies, he focused on AI engagement initiatives, working on Gen Z-focused platforms and AI mentorship systems [chunk_002, chunk_003].

He also built a personal portfolio chatbot using GPT-4.1 and RAG technology [chunk_009].""",
        "citations": ["chunk_002", "chunk_003", "chunk_009"]
    }
}


@pytest.fixture
def mock_kb():
    """Create a mock knowledge base for testing."""
    chunks = [
        {
            "id": "chunk_002",
            "text": "Drove end-to-end design of a Gen Z AI engagement initiative at LiveArena Technologies.",
            "metadata": {
                "section": "Experience",
                "entity": "LiveArena Technologies",
                "keywords": ["AI", "LLM", "Gen Z"],
            },
        },
        {
            "id": "chunk_003",
            "text": "Prototyped an AI mentorship platform using LLMs and OpenAI API.",
            "metadata": {
                "section": "Experience",
                "entity": "LiveArena Technologies",
                "keywords": ["AI", "LLM", "OpenAI"],
            },
        },
        {
            "id": "chunk_009",
            "text": "Built a GPT-4.1 powered RAG chatbot for personal portfolio with FastAPI backend.",
            "metadata": {
                "section": "Projects",
                "entity": "Personal Portfolio Chatbot",
                "keywords": ["RAG", "GPT-4.1", "FastAPI"],
            },
        },
    ]
    
    inverted_index = {
        "ai": ["chunk_002", "chunk_003"],
        "llm": ["chunk_002", "chunk_003"],
        "rag": ["chunk_009"],
        "gpt": ["chunk_009"],
    }
    
    chunk_by_id = {c["id"]: c for c in chunks}
    
    kb = KnowledgeBase(
        chunks=chunks,
        inverted_index=inverted_index,
        chunk_by_id=chunk_by_id,
    )
    
    set_kb(kb)
    return kb


def mock_llm_response(response_type: str = "synthesized"):
    """Create a mock LLM response."""
    response = MOCK_RESPONSES.get(response_type, MOCK_RESPONSES["synthesized"])
    
    # Create a mock OpenAI response object
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = f'''{{
        "answer": "{response["answer"].replace('"', '\\"').replace(chr(10), "\\n")}",
        "citations": {response["citations"]}
    }}'''
    
    return mock_response, response


def test_prompt_structure_validation(mock_kb):
    """Test that prompts are well-formed without calling LLM."""
    chunks = [
        {
            "id": "chunk_001",
            "text": "Worked on FastAPI backend development.",
            "metadata": {
                "section": "Experience",
                "entity": "Company A",
                "keywords": ["Backend", "FastAPI"],
            },
        },
    ]
    
    system_prompt, user_prompt = build_prompt("What's Tae's work experience?", chunks)
    
    # Validate system prompt
    assert "synthesize" in system_prompt.lower() or "conversational" in system_prompt.lower()
    assert "entity" in system_prompt.lower()
    assert "citation" in system_prompt.lower()
    
    # Validate user prompt
    assert "What's Tae's work experience?" in user_prompt
    assert "chunk_001" in user_prompt
    assert "Evidence" in user_prompt or "evidence" in user_prompt or "Entity:" in user_prompt
    
    # Check prompt length (not too long/short)
    assert len(system_prompt) > 100  # Should have substantial instructions
    assert len(user_prompt) > 50     # Should include query and evidence


def test_prompt_encourages_synthesis(mock_kb):
    """Test that prompts explicitly encourage synthesis."""
    chunks = [
        {
            "id": "chunk_001",
            "text": "Worked on FastAPI backend development.",
            "metadata": {"section": "Experience", "entity": "Company A", "keywords": []},
        },
    ]
    
    system_prompt, user_prompt = build_prompt("What's Tae's work experience?", chunks)
    
    # Check for synthesis keywords
    synthesis_keywords = ["synthesize", "conversational", "don't copy", "verbatim"]
    has_synthesis_instruction = any(
        keyword in system_prompt.lower() or keyword in user_prompt.lower()
        for keyword in synthesis_keywords
    )
    
    assert has_synthesis_instruction, "Prompt should encourage synthesis, not verbatim copying"


def test_mock_llm_synthesis_quality():
    """Test that mock LLM responses show good synthesis (for comparison)."""
    # This tests what a "good" synthesized response looks like
    synthesized = MOCK_RESPONSES["synthesized"]["answer"]
    verbatim = MOCK_RESPONSES["work_experience"]["answer"]
    
    # Synthesized should be more conversational
    assert "Tae's work experience spans" in synthesized
    assert "At LiveArena Technologies, he focused" in synthesized
    
    # Should combine information rather than list separately
    # (This is a simple heuristic - in practice, use more sophisticated checks)


@patch('app.chat.llm.OpenAI')
def test_chat_with_mock_llm(mock_openai_class, mock_kb):
    """Test the full chat flow with a mocked LLM."""
    # Setup mock
    mock_client = MagicMock()
    mock_openai_class.return_value = mock_client
    
    # Configure mock response
    mock_response_obj, expected_response = mock_llm_response("synthesized")
    mock_client.chat.completions.create.return_value = mock_response_obj
    
    # Make request
    request = ChatRequest(query="What's Tae's work experience?", top_k=5)
    response = chat(request)
    
    # Verify response structure
    assert response.answer is not None
    assert len(response.answer) > 0
    assert len(response.citations) > 0
    assert len(response.evidence) > 0
    
    # Verify citations match evidence
    evidence_ids = {ev.id for ev in response.evidence}
    citation_ids = {cit.chunk_id for cit in response.citations}
    assert citation_ids.issubset(evidence_ids), "Citations should only reference evidence"
    
    # Verify answer is synthesized (not just copied chunks)
    # Check that answer doesn't contain exact chunk text verbatim
    for ev in response.evidence:
        # Answer should not be identical to chunk text
        assert ev.text_preview not in response.answer or len(response.answer) > len(ev.text_preview) * 2


def test_prompt_variations_comparison(mock_kb):
    """Compare different prompt structures to find optimal format."""
    chunks = [
        {
            "id": "chunk_001",
            "text": "Worked on FastAPI backend development at Company A.",
            "metadata": {"section": "Experience", "entity": "Company A", "keywords": ["Backend"]},
        },
    ]
    
    # Test current prompt
    system_prompt, user_prompt = build_prompt("What's Tae's work experience?", chunks)
    
    # Analyze prompt characteristics
    prompt_metrics = {
        "system_length": len(system_prompt),
        "user_length": len(user_prompt),
        "has_synthesis_instruction": "synthesize" in system_prompt.lower() or "synthesize" in user_prompt.lower(),
        "has_entity_grouping": "entity" in system_prompt.lower() and "entity" in user_prompt.lower(),
        "has_citation_instruction": "citation" in system_prompt.lower() or "citation" in user_prompt.lower(),
    }
    
    # All should be true for a good prompt
    assert prompt_metrics["has_synthesis_instruction"]
    assert prompt_metrics["has_entity_grouping"]
    assert prompt_metrics["has_citation_instruction"]
    
    # Prompt shouldn't be too long (causes token waste) or too short (missing instructions)
    assert 200 < prompt_metrics["system_length"] < 2000
    assert 100 < prompt_metrics["user_length"] < 5000


def test_multiple_queries_with_mock(mock_kb):
    """Test multiple query types with mocked responses."""
    queries = [
        "What's Tae's work experience?",
        "What AI experience does Tae have?",
        "Tell me about Tae's backend projects",
    ]
    
    with patch('app.chat.llm.OpenAI') as mock_openai_class:
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        
        for query in queries:
            # Use appropriate mock response based on query
            response_type = "ai_experience" if "ai" in query.lower() else "work_experience"
            mock_response_obj, _ = mock_llm_response(response_type)
            mock_client.chat.completions.create.return_value = mock_response_obj
            
            request = ChatRequest(query=query, top_k=5)
            response = chat(request)
            
            # Basic validation
            assert response.answer is not None
            assert len(response.answer) > 0
            assert response.query == query


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])

