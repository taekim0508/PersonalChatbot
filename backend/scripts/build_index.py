import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from rag.pdf_extract import extract_text_from_pdf
from rag.chunking import create_contextual_chunks 

# Paths relative to backend directory
RESUME_PATH = backend_dir / "data" / "KimTae-SWE-Resume.pdf"
CHUNKS_PATH = backend_dir / "index" / "chunks.json"
INVERTED_INDEX_PATH = backend_dir / "index" / "inverted_index.json"

TOKEN_RE = re.compile(r"[A-Za-z0-9\.\+#]+")

def tokenize(text: str) -> List[str]:
    tokens = [t.lower() for t in TOKEN_RE.findall(text)]
    return [t for t in tokens if len(t) >= 2]

def build_inverted_index(chunks: List[Dict]) -> Dict[str, List[str]]:
    inv = defaultdict(set)

    for chunk in chunks:
        cid = chunk["id"]
        text_tokens = tokenize(chunk["text"])
        for tok in text_tokens:
            inv[tok].add(cid)
        
        for kw in chunk.get("metadata", {}).get("keywords", []):
            for tok in tokenize(kw):
                inv[tok].add(cid)
    
    return {k: sorted(list(v)) for k, v in inv.items()}


def main():
    text = extract_text_from_pdf(str(RESUME_PATH))
    chunks = create_contextual_chunks(text, source="KimTae-SWE-Resume.pdf")

    CHUNKS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CHUNKS_PATH.write_text(json.dumps(chunks, indent=2), encoding="utf-8")

    inv = build_inverted_index(chunks)
    INVERTED_INDEX_PATH.write_text(json.dumps(inv, indent=2), encoding="utf-8")

    print(f"Wrote {len(chunks)} chunks -> {CHUNKS_PATH}")
    print(f"Wrote inverted index with {len(inv)} tokens -> {INVERTED_INDEX_PATH}")
    print("Sample chunk:", chunks[0]["id"], chunks[0]["metadata"]["section"], chunks[0]["metadata"]["entity"])

if __name__ == "__main__":
    main()