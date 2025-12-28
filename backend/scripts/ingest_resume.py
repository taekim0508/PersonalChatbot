import json
from pathlib import Path

from rag.pdf_extract import extract_text_from_pdf
from rag.chunking import create_contextual_chunks

RESUME_PATH = Path("data/resume.pdf")
OUT_PATH = Path("index/chunks.json")

text = extract_text_from_pdf(str(RESUME_PATH))
chunks = create_contextual_chunks(text, source="KimTae-SWE-Resume.pdf")

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
OUT_PATH.write_text(json.dumps(chunks, indent=2), encoding="utf-8")

print(f"Wrote {len(chunks)} chunks -> {OUT_PATH}")
print(chunks[0]["metadata"])
print(chunks[0]["text"][:250])
