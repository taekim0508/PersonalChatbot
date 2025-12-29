from pathlib import Path

from rag.pdf_extract import extract_text_from_pdf
from rag.chunking import create_contextual_chunks, SECTION_HEADERS


def test_pdf_extract_has_content():
    pdf_path = Path("data/KimTae-SWE-Resume.pdf")
    text = extract_text_from_pdf(str(pdf_path))
    assert len(text) > 300, "Extracted text seems too short; PDF extraction may have failed."


def test_section_headers_detected():
    pdf_path = Path("data/KimTae-SWE-Resume.pdf")
    text = extract_text_from_pdf(str(pdf_path))
    chunks = create_contextual_chunks(text)

    sections = {c["metadata"]["section"] for c in chunks}
    # We expect at least one known header to appear in metadata
    assert any(s in SECTION_HEADERS for s in sections), f"No known sections detected. Got: {sections}"


def test_chunks_have_context_prefix():
    pdf_path = Path("data/KimTae-SWE-Resume.pdf")
    text = extract_text_from_pdf(str(pdf_path))
    chunks = create_contextual_chunks(text)

    sample = chunks[:5]
    for c in sample:
        assert c["text"].startswith("Section:"), "Chunks should prepend context for standalone retrieval."


def test_chunk_size_reasonable():
    pdf_path = Path("data/KimTae-SWE-Resume.pdf")
    text = extract_text_from_pdf(str(pdf_path))
    chunks = create_contextual_chunks(text, chunk_size=500, overlap_ratio=0.10)

    # Not strict equality because we expand to word boundary sometimes.
    for c in chunks:
        assert len(c["text"]) < 900, "Chunk seems too large; check chunking logic."


def test_keywords_populated_sometimes():
    pdf_path = Path("data/KimTae-SWE-Resume.pdf")
    text = extract_text_from_pdf(str(pdf_path))
    chunks = create_contextual_chunks(text)

    # At least some chunks should have tech keywords, otherwise keyword extraction is broken.
    count_with_keywords = sum(1 for c in chunks if c["metadata"]["keywords"])
    assert count_with_keywords >= 2, "Expected some chunks to contain extracted keywords."


def test_entities_not_all_general():
    pdf_path = Path("data/KimTae-SWE-Resume.pdf")
    text = extract_text_from_pdf(str(pdf_path))
    chunks = create_contextual_chunks(text)

    entities = [c["metadata"]["entity"] for c in chunks]
    assert len(entities) > 0
    assert any(e != "General" for e in entities), "All entities are 'General'—entity detection likely failed."


def test_experience_entities_no_lowercase_commas():
    """
    Test that PROFESSIONAL EXPERIENCE entities don't contain wrapped bullet continuations.
    No entity should start with lowercase and contain commas (e.g., "stakeholders, and developing...").
    """
    pdf_path = Path("data/KimTae-SWE-Resume.pdf")
    text = extract_text_from_pdf(str(pdf_path))
    chunks = create_contextual_chunks(text)

    # Get all entities from PROFESSIONAL EXPERIENCE sections
    exp_chunks = [
        c for c in chunks 
        if c["metadata"]["section"].startswith("PROFESSIONAL EXPERIENCE")
    ]
    entities = [c["metadata"]["entity"] for c in exp_chunks]
    
    # Check that no entity starts with lowercase and contains commas
    # This would indicate a wrapped bullet continuation was incorrectly used as entity
    for entity in entities:
        if entity and entity[0].islower() and "," in entity:
            assert False, (
                f"Found experience entity that looks like wrapped bullet continuation: '{entity}'. "
                f"This should not be an entity header."
            )


def test_projects_has_multiple_entities():
    """
    Test that PROJECTS section has at least 2 distinct entities.
    This ensures project headers are being detected correctly.
    """
    pdf_path = Path("data/KimTae-SWE-Resume.pdf")
    text = extract_text_from_pdf(str(pdf_path))
    chunks = create_contextual_chunks(text)

    # Get all entities from PROJECTS section
    project_chunks = [
        c for c in chunks 
        if c["metadata"]["section"] == "PROJECTS"
    ]
    entities = set(c["metadata"]["entity"] for c in project_chunks)
    
    # Should have at least 2 distinct entities (e.g., "Personal Portfolio Chatbot", "Tic Tac Toe")
    assert len(entities) >= 2, (
        f"PROJECTS section should have at least 2 distinct entities, but found: {entities}"
    )
    
    # Entities should not all be "General"
    assert "General" not in entities or len(entities) > 1, (
        f"PROJECTS section entities are all 'General'—project header detection likely failed. "
        f"Found entities: {entities}"
    )
