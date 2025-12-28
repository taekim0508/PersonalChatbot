# backend/scripts/query_index.py
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from rag.retrieval import load_chunks_and_index, retrieve

def main():
    # Use paths relative to backend directory
    chunks_path = backend_dir / "index" / "chunks.json"
    inverted_index_path = backend_dir / "index" / "inverted_index.json"
    _, inv, by_id = load_chunks_and_index(
        chunks_path=str(chunks_path),
        inverted_index_path=str(inverted_index_path)
    )

    while True:
        q = input("\nQuery (or 'exit'): ").strip()
        if q.lower() in {"exit", "quit"}:
            break

        results = retrieve(q, inv=inv, chunk_by_id=by_id, top_k=6)
        for r in results:
            c = r.chunk
            m = c["metadata"]
            print("\n---")
            print(c["id"], "|", m["section"], "|", m["entity"], "| score:", r.score, "|", ",".join(r.reasons))
            print("keywords:", m.get("keywords", []))
            print(c["text"][:350])

if __name__ == "__main__":
    main()
