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
