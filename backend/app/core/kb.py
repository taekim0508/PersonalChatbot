# backend/app/core/kb.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
from typing import Dict, List, Optional


@dataclass
class KnowledgeBase:
    chunks: List[dict]
    inverted_index: Dict[str, List[str]]
    chunk_by_id: Dict[str, dict]


_KB: Optional[KnowledgeBase] = None


def load_kb(
    *,
    chunks_path: str = "index/chunks.json",
    inverted_index_path: str = "index/inverted_index.json",
) -> KnowledgeBase:
    """Load KB from disk (persistent index artifacts)."""
    chunks = json.loads(Path(chunks_path).read_text(encoding="utf-8"))
    inv = json.loads(Path(inverted_index_path).read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in chunks}
    return KnowledgeBase(chunks=chunks, inverted_index=inv, chunk_by_id=by_id)


def get_kb() -> KnowledgeBase:
    """
    Accessor for a singleton KB instance loaded at app startup.
    Raises a clear error if the KB was not initialized.
    """
    if _KB is None:
        raise RuntimeError(
            "KnowledgeBase is not loaded. Run scripts/build_index.py and start the API, "
            "or ensure startup initializes the KB."
        )
    return _KB


def set_kb(kb: KnowledgeBase) -> None:
    global _KB
    _KB = kb
