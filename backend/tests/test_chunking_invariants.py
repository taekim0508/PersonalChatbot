"""
Test chunking invariants to ensure quality.
"""
from pathlib import Path

from rag.pdf_extract import extract_text_from_pdf
from rag.chunking import create_contextual_chunks, debug_chunking_report


def test_chunking_invariants():
    """
    Test that chunking invariants are met:
    - UNKNOWN section should not have > 5% of chunks
    - PROFESSIONAL EXPERIENCE chunks should not have > 30% with suspicious entities
    - prefix_check should be >= 95%
    - chunk max length should not exceed 900 characters
    """
    pdf_path = Path("data/KimTae-SWE-Resume.pdf")
    pdf_text = extract_text_from_pdf(str(pdf_path))
    chunks = create_contextual_chunks(pdf_text)
    report = debug_chunking_report(pdf_text)
    
    total_chunks = len(chunks)
    assert total_chunks > 0, "No chunks were created"
    
    # Test 1: UNKNOWN section should not have > 5% of chunks
    unknown_count = report["section_counts"].get("UNKNOWN", 0)
    unknown_percentage = (unknown_count / total_chunks) * 100.0 if total_chunks > 0 else 0.0
    assert unknown_percentage <= 5.0, (
        f"UNKNOWN section has {unknown_percentage:.1f}% of chunks ({unknown_count}/{total_chunks}), "
        f"which exceeds the 5% threshold"
    )
    
    # Test 2: PROFESSIONAL EXPERIENCE chunks should not have > 30% with suspicious entities
    # Find the actual section name that starts with "PROFESSIONAL EXPERIENCE"
    prof_exp_section = None
    for section in report["section_counts"].keys():
        if section.startswith("PROFESSIONAL EXPERIENCE"):
            prof_exp_section = section
            break
    
    prof_exp_chunks = [c for c in chunks if c["metadata"]["section"] == prof_exp_section] if prof_exp_section else []
    if prof_exp_chunks:
        prof_exp_entities = [c["metadata"]["entity"] for c in prof_exp_chunks]
        # Check which entities are suspicious (contain month names or years)
        from rag.chunking import MONTH_RE, YEAR_RE
        suspicious_count = sum(
            1 for entity in prof_exp_entities
            if MONTH_RE.search(entity) or YEAR_RE.search(entity)
        )
        suspicious_percentage = (suspicious_count / len(prof_exp_chunks)) * 100.0
        assert suspicious_percentage <= 30.0, (
            f"PROFESSIONAL EXPERIENCE section has {suspicious_percentage:.1f}% chunks with suspicious entities "
            f"({suspicious_count}/{len(prof_exp_chunks)}), which exceeds the 30% threshold"
        )
    
    # Test 3: prefix_check should be >= 95%
    prefix_check = report["prefix_check"]
    assert prefix_check >= 95.0, (
        f"Only {prefix_check:.1f}% of chunks have the correct prefix format (Section: ... | Entity: ...), "
        f"which is below the 95% threshold"
    )
    
    # Test 4: chunk max length should not exceed 900 characters
    max_length = report["chunk_length_stats"]["max"]
    assert max_length <= 900, (
        f"Chunk max length is {max_length} characters, which exceeds the 900 character limit"
    )

