from __future__ import annotations 

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

SOURCE_NAME = "KimTae-SWE-Resume.pdf"
TARGET_CHUNK_SIZE = 500
OVERLAP_RATIO = 0.2

# number of characters to overlap
OVERLAP_CHARS = max(1, int(TARGET_CHUNK_SIZE * OVERLAP_RATIO))

SECTION_HEADERS = {
    "EDUCATIONS",
    "PROFESSIONAL EXPERIENCE",
    "PROFESSIONAL EXPERIENCE / LEADERSHIP",
    "PROJECTS",
    "TECHNICAL / SOFT SKILLS",
    "SKILLS",
}

# Canonical tech keywords → simple substring variants (lowercased matching)
TECH_KEYWORDS: Dict[str, List[str]] = {
    "AI": [" ai ", "artificial intelligence"],
    "LLM": [" llm", "large language model", "gpt"],
    "RAG": [" rag", "retrieval augmented"],
    "FastAPI": ["fastapi"],
    "OpenAI API": ["openai"],
    "Socket.IO": ["socket.io", "socketio"],
    "WebSockets": ["websocket"],
    "Python": ["python"],
    "TypeScript": ["typescript"],
    "React": ["react"],
    "PostgreSQL": ["postgres"],
    "MongoDB": ["mongodb"],
    "SQLModel": ["sqlmodel"],
    "ChromaDB": ["chromadb", "chroma"],
    "Docker": ["docker"],
    "AWS": ["aws", "amazon web services"],
    "Supabase": ["supabase"],
    "Vercel": ["vercel"],
    "Railway": ["railway"],
    "Tailwind": ["tailwind"],
    "Node.js": ["node.js", "nodejs"],
    "REST": ["rest", "restful"],
}

# Bullet detection: unicode bullets, dashes, asterisks, numbered/lettered bullets.
# re.compile() compiles a regular expression into a regular expression object, which can be used to match against a string.
# re.VERBOSE allows for verbose regular expressions, which means that you can add whitespace and comments to the regular expression.

BULLET_REGEX = re.compile(
    r"""
    ^\s*(
        [•·●▪◦•*o]      |   # common bullet symbols
    )
    \s+
    """,
    re.VERBOSE,
)


# Entity extraction heuristics:
# - Many resumes format: "Company | Role | Dates" or "Project Name | Tech | ..."
# - Sometimes: "Company — Role" or "Company – Role"
ENTITY_SEP_REGEX = re.compile(r"\s*(\||—|–)\s*")

@dataclass(frozen=True)
class Chunk:
    """
    Canonical in-memory representation of a single retrievable knowledge unit
    produced during resume ingestion.

    Each Chunk is designed to be:
      - self-contained (text includes inherited section/entity context)
      - stable (schema should not change at runtime)
      - JSON-serializable (for storage in index/chunks.json)
      - retriever-friendly (metadata supports filtering, boosting, and synthesis)

    This dataclass serves as the contract between:
      - ingestion (PDF parsing + chunking)
      - retrieval (keyword/vector search)
      - prompt construction (LLM context assembly)

    Keeping this schema explicit helps prevent silent regressions and makes
    the RAG pipeline easier to reason about and test.
    """
    id: str
    text: str
    metadata: Dict

# =========================
# Normalization functions
# =========================

def normalize_text(pdf_text: str) -> str:
    """
    Normalize to improve stability across PDF extraction quirks.
    - standardize newlines
    - collapse repeated spaces
    """
    txt = pdf_text.replace("\r", "\n")
    txt = re.sub(r"[ \t]+", " ", txt)
    # Keep newlines: they're useful for section/entity heuristics.
    return txt.strip()


def to_lines(pdf_text: str) -> List[str]:
    txt = normalize_text(pdf_text)
    lines = [ln.rstrip() for ln in txt.split("\n")]
    # Keep leading spaces for indentation heuristics, but drop empty lines.
    return [ln for ln in (ln.strip("\ufeff") for ln in lines) if ln.strip()]

def leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def is_bullet(line: str, *, indent_threshold: int = 2) -> bool:
    """
    Robust bullet detection. Works when:
    - bullets are unicode (•, ·, etc.)
    - bullets are hyphens/dashes
    - bullets are numbered lists (1., 2))
    - bullets disappear but indentation remains
    """
    if BULLET_REGEX.match(line):
        return True

    # Indent-only fallback: lots of PDFs keep indentation even when bullets drop.
    # Caution: this can over-match; we keep threshold modest and combine with other logic in grouping.
    return leading_spaces(line) >= indent_threshold

# =========================
# Section splitting
# =========================

def canonicalize_header(line: str) -> str:
    """
    Normalize a single line for the purpose of matching section headers.

    Why this exists:
      PDF extraction may introduce minor formatting differences that break exact matches:
        - inconsistent spacing around slashes: 'A/B' vs 'A / B'
        - multiple spaces: 'PROFESSIONAL  EXPERIENCE'
        - stray whitespace

    This function applies lightweight normalization so that: text with different spacing 
    can be treated as equivalent for section detection.

    Used by:
      - split_by_sections(): to robustly detect header boundaries and assign metadata["section"]
    """
    l = re.sub(r"\s*/\s*", " / ", line.strip())
    l = re.sub(r"[ \t]+", " ", l)
    return l


def split_by_sections(lines: List[str]) -> Dict[str, List[str]]:
    """
    Returns dict: section_name -> lines
    Unknown lines before first header go into "UNKNOWN".
    """
    sections: Dict[str, List[str]] = {"UNKNOWN": []}
    current = "UNKNOWN"

    for raw in lines:
        ln = canonicalize_header(raw)
        if ln in SECTION_HEADERS:
            current = ln
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(raw)

    # Drop UNKNOWN if empty
    if not sections["UNKNOWN"]:
        sections.pop("UNKNOWN", None)
    return sections


# =========================
# Entity detection (hardened)
# =========================

def looks_like_allcaps(line: str) -> bool:
    # e.g., "EDUCATION"
    alpha = re.sub(r"[^A-Za-z]", "", line)
    return bool(alpha) and alpha.isupper()


def has_date_like_token(line: str) -> bool:
    # common in experience lines
    return bool(re.search(r"\b(20\d{2}|19\d{2})\b", line)) or bool(
        re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b", line, re.I)
    )


def titlecase_score(line: str) -> float:
    """
    Heuristic score: fraction of words that are TitleCase-ish.
    """
    words = re.findall(r"[A-Za-z][A-Za-z&\.\-]+", line)
    if not words:
        return 0.0
    tc = sum(1 for w in words if w[0].isupper())
    return tc / len(words)


def is_probable_entity_line(line: str) -> bool:
    """
    A strong guess that this line begins a new entity block.
    We avoid false positives like: section headers, bullets, and pure tech lists.
    """
    s = line.strip()
    if not s:
        return False
    if looks_like_allcaps(s) and s in SECTION_HEADERS:
        return False
    if is_bullet(s):
        return False

    # Common resume entity formatting: includes separators like "|" or em/en dash.
    if ENTITY_SEP_REGEX.search(s):
        # e.g., "LiveArena Technologies | Software Engineering Intern | May 2024 – Aug 2024"
        return True

    # If it contains a date-like token and is title-case heavy, it’s likely the role header line.
    if has_date_like_token(s) and titlecase_score(s) >= 0.55:
        return True

    # If it’s short-ish and title-case heavy, likely a project/company line.
    # This catches "Personal Portfolio Chatbot" etc.
    if len(s) <= 90 and titlecase_score(s) >= 0.70:
        return True

    return False


def extract_entity_from_line(line: str) -> str:
    """
    Extract the entity name from an entity header line.
    - If separators exist, use the left segment.
    - Otherwise use the full line.
    """
    s = line.strip()
    parts = ENTITY_SEP_REGEX.split(s)
    # re.split with capturing groups returns separators too; easiest is manual:
    # We'll just split by the first detected separator among | — –.
    for sep in ["|", "—", "–"]:
        if sep in s:
            left = s.split(sep, 1)[0].strip()
            return left or s
    return s


def group_by_entity(section_lines: List[str]) -> List[Dict[str, str]]:
    """
    Groups a section into entity blocks:
    [
      {"entity": "LiveArena Technologies", "content": "LiveArena ...\n• ...\n• ..."},
      ...
    ]

    If we never detect an entity header, we fall back to one "General" block.
    """
    blocks: List[Dict[str, str]] = []
    current_entity: Optional[str] = None
    buf: List[str] = []

    def flush():
        nonlocal current_entity, buf
        if current_entity and buf:
            blocks.append({"entity": current_entity, "content": "\n".join(buf).strip()})
        current_entity, buf = None, []

    for ln in section_lines:
        if is_probable_entity_line(ln):
            if current_entity is not None:
                flush()
            current_entity = extract_entity_from_line(ln)
            buf.append(ln.strip())
        else:
            if current_entity is None:
                current_entity = "General"
            buf.append(ln.strip())

    flush()

    if not blocks and section_lines:
        blocks.append({"entity": "General", "content": "\n".join(x.strip() for x in section_lines).strip()})
    return blocks


# =========================
# Chunking logic (500 chars, 10% overlap)
# =========================

def sliding_window_chunks(text: str, *, size: int = TARGET_CHUNK_SIZE, overlap: int = OVERLAP_CHARS) -> List[str]:
    """
    Simple and reliable: produces chunks ~size chars with overlap.
    Attempts to avoid starting/ending in the middle of a word by mild boundary adjustment.
    """
    if not text:
        return []

    n = len(text)
    step = max(1, size - overlap)
    chunks: List[str] = []
    i = 0

    while i < n:
        j = min(i + size, n)
        chunk = text[i:j]

        # Mild boundary cleanup: extend end to next whitespace if we're in the middle of a word
        if j < n and j > i and chunk and chunk[-1].isalnum():
            k = j
            while k < n and text[k].isalnum():
                k += 1
            chunk = text[i:k]
            j = k

        chunk = chunk.strip()
        if chunk:
            chunks.append(chunk)

        if j >= n:
            break
        i += step

    return chunks


# =========================
# Keywords + summary_context
# =========================

def extract_keywords(text: str, *, max_keywords: int = 14) -> List[str]:
    """
    Extract canonical tech/skill keywords from text.
    Prioritizes configured TECH_KEYWORDS. Adds a couple of high-level signals.
    """
    lower = f" {text.lower()} "  # pad for " ai " matching
    found: List[str] = []

    for canonical, variants in TECH_KEYWORDS.items():
        for v in variants:
            if v in lower:
                found.append(canonical)
                break

    # Add some “soft” high-level terms if present
    if re.search(r"\bmentor(ed|ship)?\b", text, re.I):
        found.append("Mentorship")
    if re.search(r"\blead(ing|ership|)\b", text, re.I):
        found.append("Leadership")
    if re.search(r"\bbackend\b|\bapi\b|\brest\b", text, re.I):
        found.append("Backend")
    if re.search(r"\breal[- ]time\b|\bsocket\b|\bwebsocket\b", text, re.I):
        found.append("Real-time")

    # Dedup preserve order
    seen = set()
    out: List[str] = []
    for k in found:
        if k not in seen:
            seen.add(k)
            out.append(k)

    return out[:max_keywords]


def summarize_entity_block(section: str, entity: str, content: str) -> str:
    """
    Simple heuristic: build a short 'what is this block about' line.
    Stored per block and inherited by each sub-chunk.
    """
    kws = extract_keywords(content, max_keywords=6)
    if entity == "General":
        base = f"Tae's {section.lower()} details"
    else:
        base = f"Tae's work related to {entity}"

    if kws:
        return f"{base} focused on {', '.join(kws[:4])}."
    return f"{base}."


# =========================
# Public API
# =========================

def create_contextual_chunks(
    pdf_text: str,
    *,
    source: str = SOURCE_NAME,
    chunk_size: int = TARGET_CHUNK_SIZE,
    overlap_ratio: float = OVERLAP_RATIO,
) -> List[Dict]:
    """
    Main entrypoint.

    Produces JSON-compatible chunk dicts:
      {
        "id": "chunk_005",
        "text": "Section: ... | Entity: ... - ...",
        "metadata": {
          "source": "...",
          "section": "...",
          "entity": "...",
          "keywords": [...],
          "summary_context": "..."
        }
      }
    """
    lines = to_lines(pdf_text)
    sections = split_by_sections(lines)

    overlap = max(1, int(chunk_size * overlap_ratio))
    out: List[Dict] = []
    idx = 0

    for section, sec_lines in sections.items():
        blocks = group_by_entity(sec_lines)

        for block in blocks:
            entity = block["entity"]
            content = block["content"]

            summary_context = summarize_entity_block(section, entity, content)

            # Split within entity block
            sub_chunks = sliding_window_chunks(content, size=chunk_size, overlap=overlap)

            for sc in sub_chunks:
                prefix = f"Section: {section} | Entity: {entity} - "
                contextual_text = prefix + sc

                out.append(
                    {
                        "id": f"chunk_{idx:03d}",
                        "text": contextual_text,
                        "metadata": {
                            "source": source,
                            "section": section,
                            "entity": entity,
                            "keywords": extract_keywords(contextual_text),
                            "summary_context": summary_context,
                        },
                    }
                )
                idx += 1

    return out