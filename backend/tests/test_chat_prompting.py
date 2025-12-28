# backend/tests/test_chat_prompting.py
"""
Tests for chat prompting functionality.
"""
from app.chat.prompting import format_context_chunks, build_prompt, SYSTEM_INSTRUCTIONS


def test_format_context_chunks_basic():
    """Test basic formatting of chunks."""
    chunks = [
        {
            "id": "chunk_001",
            "text": "Worked on FastAPI backend",
            "metadata": {
                "section": "Experience",
                "entity": "Company A",
                "summary_context": "Backend development role",
            },
        },
        {
            "id": "chunk_002",
            "text": "Built RAG system",
            "metadata": {
                "section": "Projects",
                "entity": "Project X",
                "summary_context": "AI/ML project",
            },
        },
    ]
    
    result = format_context_chunks(chunks)
    
    assert "chunk_001" in result
    assert "chunk_002" in result
    assert "Section=Experience" in result
    assert "Section=Projects" in result
    assert "Entity=Company A" in result
    assert "Entity=Project X" in result
    assert "Worked on FastAPI backend" in result
    assert "Built RAG system" in result
    assert "SummaryContext: Backend development role" in result
    assert "---" in result  # Separator between chunks


def test_format_context_chunks_missing_metadata():
    """Test formatting with missing metadata fields."""
    chunks = [
        {
            "id": "chunk_003",
            "text": "Some text",
            "metadata": {},  # Empty metadata
        },
    ]
    
    result = format_context_chunks(chunks)
    
    assert "chunk_003" in result
    assert "Section=" in result  # Empty section
    assert "Entity=" in result  # Empty entity
    assert "Some text" in result


def test_format_context_chunks_missing_id():
    """Test formatting when chunk ID is missing."""
    chunks = [
        {
            "text": "Text without ID",
            "metadata": {
                "section": "Test",
                "entity": "Test Entity",
            },
        },
    ]
    
    result = format_context_chunks(chunks)
    
    assert "unknown" in result  # Should default to "unknown"
    assert "Text without ID" in result


def test_build_prompt_returns_tuple():
    """Test that build_prompt returns a tuple of (system, user) prompts."""
    chunks = [
        {
            "id": "chunk_001",
            "text": "Test content",
            "metadata": {
                "section": "Experience",
                "entity": "Company",
            },
        },
    ]
    
    system_prompt, user_prompt = build_prompt("What is the experience?", chunks)
    
    assert isinstance(system_prompt, str)
    assert isinstance(user_prompt, str)
    assert system_prompt == SYSTEM_INSTRUCTIONS
    assert "What is the experience?" in user_prompt
    assert "chunk_001" in user_prompt
    assert "Resume context:" in user_prompt


def test_build_prompt_empty_chunks():
    """Test building prompt with empty chunk list."""
    system_prompt, user_prompt = build_prompt("Test query", [])
    
    assert system_prompt == SYSTEM_INSTRUCTIONS
    assert "Test query" in user_prompt
    assert "Resume context:" in user_prompt
    # Should still be valid even with no chunks


def test_build_prompt_includes_all_instructions():
    """Test that user prompt includes all required instructions."""
    chunks = [{"id": "chunk_001", "text": "Test", "metadata": {}}]
    _, user_prompt = build_prompt("Test query", chunks)
    
    assert "Answer the question using ONLY" in user_prompt
    assert "synthesize across multiple entities" in user_prompt
    assert "bullet points grouped by Entity" in user_prompt
    assert "Citations" in user_prompt


def test_format_context_chunks_preserves_text():
    """Test that full text content is preserved in formatting."""
    long_text = "This is a longer piece of text. " * 10
    chunks = [
        {
            "id": "chunk_001",
            "text": long_text,
            "metadata": {"section": "Test", "entity": "Test"},
        },
    ]
    
    result = format_context_chunks(chunks)
    
    # Should contain the full text, not truncated
    assert long_text in result
    assert len(result) > len(long_text)  # Plus formatting

