# backend/rag/chunking.py
from __future__ import annotations

import re
from collections import Counter
from statistics import median
from typing import Dict, List, Optional


# =============================================================================
# Chunking configuration
# =============================================================================

DEFAULT_SOURCE = "KimTae-SWE-Resume.pdf"

# Target size and overlap for retrieval-friendly chunks.
# - ~500 chars is small enough for precise retrieval
# - overlap keeps continuity so facts aren't lost at boundaries
TARGET_CHUNK_SIZE = 500
OVERLAP_RATIO = 0.10


# =============================================================================
# Section header detection
# =============================================================================
# We treat these headers as "hard boundaries" when splitting the resume.
# PDF-to-text extraction often changes spacing/punctuation, so we include common
# variants to avoid silent mis-parsing (e.g., everything falling into UNKNOWN).
SECTION_HEADERS = {
    "EDUCATION",
    "PROFESSIONAL EXPERIENCE",
    "PROFESSIONAL EXPERIENCE / LEADERSHIP",
    "PROFESSIONAL EXPERIENCE/LEADERSHIP",
    "PROJECTS",
    "TECHNICAL / SOFT SKILLS",
    "TECHNICAL/SOFT SKILLS",
    "SKILLS",
    "SOCIALS",
    "CONTACT",
    "CONTACT INFO",
}


def canonicalize_header(line: str) -> str:
    """
    Normalize a line for header matching.

    Why:
      Header matching is usually string equality. PDF extraction can add/remove
      spaces around slashes or collapse spacing, which can break equality.

    Used later:
      Stable section labels become metadata for retrieval and answer framing
      (e.g., "in PROJECTS" vs "in PROFESSIONAL EXPERIENCE").
    """
    l = line.strip()
    l = re.sub(r"\s*/\s*", " / ", l)
    l = re.sub(r"[ \t]+", " ", l)
    return l


# Contact information detection patterns
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
LINKEDIN_RE = re.compile(r"\blinkedin\.com/in/[\w-]+", re.I)
GITHUB_RE = re.compile(r"\bgithub\.com/[\w-]+", re.I)


def is_contact_info_line(line: str) -> bool:
    """
    Detect if a line contains contact information (email, LinkedIn, GitHub).

    Why:
      Contact info is frequently at the top of the resume before the first header.
      We pull it into a SOCIALS section so it's easy to retrieve later when users
      ask "what is Tae's email" / "LinkedIn" / "GitHub".

    Used later:
      metadata.section="SOCIALS" allows a simple filter or strong retrieval hit.
    """
    line_lower = line.lower()
    return bool(
        EMAIL_RE.search(line)
        or LINKEDIN_RE.search(line)
        or GITHUB_RE.search(line)
        or "linkedin.com" in line_lower
        or "github.com" in line_lower
    )


def split_by_sections(lines: List[str]) -> Dict[str, List[str]]:
    """
    Split the resume into sections using known headers.

    Why:
      Sections are the top-level semantic grouping. They become metadata, help
      debugging, and help answer formatting ("Projects:" vs "Experience:").

    Output:
      { "PROJECTS": [...], "PROFESSIONAL EXPERIENCE / LEADERSHIP": [...], "SOCIALS": [...], ... }
    """
    sections: Dict[str, List[str]] = {"UNKNOWN": []}
    current = "UNKNOWN"
    first_section_name = None

    for raw in lines:
        maybe_header = canonicalize_header(raw)
        if maybe_header in SECTION_HEADERS:
            # If this is the first known section and we have UNKNOWN content,
            # check if it contains contact info and create SOCIALS section.
            if first_section_name is None:
                first_section_name = maybe_header
                if sections["UNKNOWN"]:
                    contact_lines = [line for line in sections["UNKNOWN"] if is_contact_info_line(line)]
                    other_lines = [line for line in sections["UNKNOWN"] if not is_contact_info_line(line)]

                    if contact_lines:
                        # Include name (usually first line) plus contact items in SOCIALS.
                        socials_content = []
                        if other_lines:
                            socials_content.extend(other_lines[:1])
                            if len(other_lines) > 1:
                                sections[maybe_header] = other_lines[1:]
                            else:
                                sections[maybe_header] = []
                        else:
                            sections[maybe_header] = []
                        socials_content.extend(contact_lines)
                        sections["SOCIALS"] = socials_content
                    else:
                        # No contact info → merge UNKNOWN into the first real section.
                        sections[maybe_header] = sections["UNKNOWN"].copy()
                    sections["UNKNOWN"] = []
                else:
                    sections[maybe_header] = []

            current = maybe_header
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(raw)

    if not sections["UNKNOWN"]:
        sections.pop("UNKNOWN", None)

    return sections


# =============================================================================
# Normalization (critical for stable parsing)
# =============================================================================

def normalize_text(pdf_text: str) -> str:
    """
    Normalize raw PDF-extracted text into a stable format for parsing.

    Why this exists:
      PDF extraction is noisy. We normalize newlines and collapse whitespace so
      section/entity/bullet rules behave consistently.

    Used later:
      All parsing functions assume normalized input. This reduces "random" bugs
      when you re-export the PDF or tweak formatting.
    """
    txt = pdf_text.replace("\r", "\n")
    txt = re.sub(r"[ \t]+", " ", txt)
    return txt.strip()


def to_lines(pdf_text: str) -> List[str]:
    """
    Convert normalized text into a list of non-empty lines.

    Why:
      Resume structure is mostly encoded as line breaks (headers, entities, bullets).
      The rest of the pipeline is line-based.

    Used later:
      split_by_sections() and group_by_entity() operate on clean lines.
    """
    txt = normalize_text(pdf_text)
    lines = [ln.rstrip() for ln in txt.split("\n")]
    return [ln for ln in lines if ln.strip()]


# =============================================================================
# Bullet detection (robust to Word/PDF variations)
# =============================================================================

BULLET_REGEX = re.compile(
    r"""
    ^\s*(
        [•·●▪◦‣⁃–—\-*o]      |   # common bullet symbols / dashes / hyphen / asterisk / 'o'
        \d{1,2}[.)]          |   # numbered lists: 1. 2) 10.
        [a-zA-Z][.)]             # lettered lists: a) b.
    )
    \s+
    """,
    re.VERBOSE,
)


def leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def is_bullet(line: str, *, indent_threshold: int = 2) -> bool:
    """
    Identify bullet-like lines.

    Why:
      PDF extraction may drop bullet symbols entirely but keep indentation.
      This function treats indentation as a fallback bullet signal.

    Used later:
      group_by_entity() uses bullet detection to prevent bullet content from being
      misclassified as entity headers.
    """
    if BULLET_REGEX.match(line):
        return True
    return leading_spaces(line) >= indent_threshold


# =============================================================================
# Entity detection (company/project grouping)
# =============================================================================

ENTITY_SEP_CHARS = ["|", "—", "–"]

MONTH_RE = re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b", re.I)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
DATE_RANGE_RE = re.compile(
    r"(\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b\.?\s+\d{4})"
    r"(\s*[–—-]\s*)"
    r"(\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b\.?\s+\d{4}|\bPresent\b)",
    re.I,
)

ORG_SUFFIX_RE = re.compile(
    r"\b(Inc|LLC|Ltd|Technologies|Technology|University|College|Labs|Laboratory|Corp|Corporation|Company)\b",
    re.I,
)

ROLE_HINT_RE = re.compile(
    r"\b(Intern|Engineer|Developer|Manager|Analyst|Assistant|Research|Fellow|Lead|Coordinator|Consultant|Editor)\b",
    re.I,
)

# Many resumes put "City, ST" on the same line as the company name (no pipe).
# This helps us detect company headers like "LiveArena Technologies Bellevue, WA".
LOCATION_TAIL_RE = re.compile(r"\b[A-Za-z][A-Za-z .'-]+,\s*[A-Z]{2}\b")


def _split_on_entity_sep(line: str) -> List[str]:
    for sep in ENTITY_SEP_CHARS:
        if sep in line:
            left, right = line.split(sep, 1)
            return [left.strip(), right.strip()]
    return [line.strip()]


def _has_date_signal(s: str) -> bool:
    return bool(DATE_RANGE_RE.search(s) or (MONTH_RE.search(s) and YEAR_RE.search(s)) or YEAR_RE.search(s))


def _titlecase_score(s: str) -> float:
    words = re.findall(r"[A-Za-z][A-Za-z&\.\-']+", s)
    if not words:
        return 0.0
    return sum(1 for w in words if w[0].isupper()) / len(words)


def _looks_like_org_name(s: str) -> bool:
    """
    Heuristic: identify organization/company-like strings.

    Why:
      Entity is used later to group evidence and generate readable answers.
      If the entity is a role/date line or a bullet continuation fragment,
      the chatbot will produce confusing "At stakeholders..." style outputs.
    """
    if ORG_SUFFIX_RE.search(s):
        return True
    tc = _titlecase_score(s)
    if tc >= 0.7 and not ROLE_HINT_RE.search(s):
        return True
    return False


def _is_sentence_like_continuation(line: str) -> bool:
    """
    Detect bullet-wrapped continuation lines like:
      'stakeholders, and developing a university-based pilot...'

    Why:
      Bullet items frequently wrap across lines in PDF extraction.
      These continuation lines must NOT become new entity headers.

    Used later:
      Prevents group_by_entity() from splitting an entity block mid-bullet,
      which would corrupt metadata.entity and degrade retrieval grouping.
    """
    s = line.strip()
    if not s:
        return False

    # Lowercase start is a strong continuation signal in resumes.
    if s[0].islower():
        return True

    # Very long lines with commas are usually prose, not headers.
    if len(s) > 90 and "," in s:
        return True

    return False


def is_probable_company_header(line: str) -> bool:
    """
    Detect company/org header lines in experience sections.
    
    Hardened rules:
      - Must be non-bullet
      - Must start with uppercase letter
      - Length <= 80 chars
      - Must NOT contain month/year date signals
      - Must NOT be a sentence-like continuation (lowercase start, etc.)

    Accepts two common formats:
      1) 'Company | Location'
      2) 'Company City, ST'  (no pipe separator)

    We intentionally pick the company name as the entity so later answers can say:
      "At LiveArena Technologies, Tae ..."
    """
    s = line.strip()
    if not s:
        return False
    
    # Must be non-bullet
    if is_bullet(s):
        return False
    
    # Must start with uppercase letter
    if not s or not s[0].isupper():
        return False
    
    # Length must be <= 80 chars
    if len(s) > 80:
        return False
    
    # Must NOT contain month/year date signals
    if _has_date_signal(s):
        return False
    
    # Must NOT be a sentence-like continuation
    if _is_sentence_like_continuation(s):
        return False

    parts = _split_on_entity_sep(s)
    left = parts[0]

    if _looks_like_org_name(left):
        return True

    # Handle "Company Bellevue, WA" style lines
    if LOCATION_TAIL_RE.search(s) and _titlecase_score(s) >= 0.6 and not ROLE_HINT_RE.search(s):
        return True

    return False


def is_probable_role_header(line: str) -> bool:
    """
    Detect role/title lines (often contain dates).

    Why:
      In experience sections, role lines should remain under the most recent company
      entity. They should not become the entity name.
    """
    s = line.strip()
    if not s or is_bullet(s):
        return False
    if _is_sentence_like_continuation(s):
        return False
    return bool(_has_date_signal(s) and ROLE_HINT_RE.search(s))


def is_probable_project_header(line: str) -> bool:
    """
    Detect project header lines in PROJECTS.
    
    Hardened rule: Any line containing | is treated as a project header.
    Even if the line contains dates, we extract the project name from left-of-|.

    Updated for your resume style:
      'Personal Portfolio Chatbot | GPT-4.1 Nano, Chroma, FastAPI Jul. 2025 – Sep. 2025'
    These often include dates, so we allow date signals here and simply extract
    the project name from the left side of '|'.

    Used later:
      metadata.entity becomes the project name so retrieval and answer synthesis
      can group by project cleanly.
    """
    s = line.strip()
    if not s or is_bullet(s):
        return False
    
    # Any line containing | is a project header (even with dates)
    if "|" in s:
        left = s.split("|", 1)[0].strip()
        return bool(left)  # Just needs to have content left of |
    
    # Fallback for project headers without a pipe
    if len(s) > 90:
        return False
    return _titlecase_score(s) >= 0.70


def _extract_project_entity(line: str) -> str:
    """
    Extract the project name from a project header line.
    Prefer left-of-pipe when available.
    """
    s = line.strip()
    if "|" in s:
        return s.split("|", 1)[0].strip()
    return s


def group_by_entity(section: str, section_lines: List[str]) -> List[Dict[str, str]]:
    """
    Group lines within a section into entity blocks:
      [{"entity": "...", "content": "..."}, ...]

    What this does:
      - EXPERIENCE sections: entity = company/org (not role/date, not bullet fragments)
      - PROJECTS section: entity = project name (usually left of '|')

    Why it's written this way:
      Entity is the primary "ownership" key later. Retrieval may fetch multiple chunks,
      and answer generation often groups by entity. If entity is wrong, answers become
      confusing and citations become less meaningful.

    How it's used later:
      create_contextual_chunks() splits each entity block into smaller overlapping chunks.
      Every chunk inherits the entity in metadata and in the text prefix so the model
      can answer high-level questions like "Tae's AI experience" across entities.
    """
    blocks: List[Dict[str, str]] = []
    current_entity: Optional[str] = None
    buf: List[str] = []

    # In experience sections, we keep the most recent "company" entity and attach
    # role lines + bullets beneath it.
    current_company: Optional[str] = None

    def flush():
        nonlocal current_entity, buf, current_company
        if current_entity and buf:
            blocks.append({"entity": current_entity, "content": "\n".join(buf).strip()})
        current_entity, buf, current_company = None, [], current_company

    for ln in section_lines:
        s = ln.strip()
        if not s:
            continue

        # ---- EXPERIENCE grouping (hardened) ----
        if section.startswith("PROFESSIONAL EXPERIENCE"):
            # CRITICAL: Never allow wrapped bullet continuation lines to become new entities
            # Lines starting with lowercase (e.g., "stakeholders, and developing...") 
            # are continuation of previous bullet and must stay under current entity
            if _is_sentence_like_continuation(s):
                if current_entity is None:
                    current_entity = current_company or "General"
                buf.append(s)
                continue

            # Company header starts a new block (only if it passes all hardened checks)
            if is_probable_company_header(s):
                if current_entity is not None:
                    flush()
                # Extract company name (left of separator if present)
                company = _split_on_entity_sep(s)[0].strip()
                current_company = company
                current_entity = company
                buf.append(s)
                continue

            # Role header (contains month+year + role words) stays under current company
            # Must NOT replace the entity, just append to current company's content
            if is_probable_role_header(s):
                if current_entity is None:
                    current_entity = current_company or "General"
                buf.append(s)
                continue

            # Bullet lines and other details belong to current company
            # If we're in a bullet that wraps, all wrapped lines stay under current entity
            if current_entity is None:
                current_entity = current_company or "General"
            buf.append(s)
            continue

        # ---- PROJECTS grouping (hardened) ----
        if section == "PROJECTS":
            # Any line containing | is treated as a project header
            # Extract entity from left-of-|, even if line contains dates
            if "|" in s and not is_bullet(s):
                if current_entity is not None:
                    flush()
                current_entity = _extract_project_entity(s)
                buf.append(s)
                continue
            
            # Fallback: check if it's a project header without |
            if is_probable_project_header(s):
                if current_entity is not None:
                    flush()
                current_entity = _extract_project_entity(s)
                buf.append(s)
                continue

            if current_entity is None:
                current_entity = "General"
            buf.append(s)
            continue

        # ---- Other sections (Education/Skills/Socials) ----
        if current_entity is None:
            current_entity = "General"
        buf.append(s)

    # Flush last block
    if current_entity and buf:
        blocks.append({"entity": current_entity, "content": "\n".join(buf).strip()})

    # If nothing got grouped but we had content, keep it as one General block.
    if not blocks and section_lines:
        blocks.append({"entity": "General", "content": "\n".join(x.strip() for x in section_lines).strip()})

    return blocks


# =============================================================================
# Chunking helpers
# =============================================================================

def sliding_window_chunks(text: str, *, size: int, overlap: int) -> List[str]:
    """
    Create chunks with overlap using a sliding window.

    Why:
      Small chunks retrieve precisely; overlap preserves continuity.
      This is important for answers that span multiple bullets/lines.

    Used later:
      Retrieval returns chunks as evidence; the LLM synthesizes across evidence.
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

        # Avoid cutting in the middle of a word when possible.
        if j < n and chunk and chunk[-1].isalnum():
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


def extract_keywords(text: str, tech_keywords: Dict[str, List[str]]) -> List[str]:
    """
    Extract canonical tech keywords from text via substring matching.

    Why:
      Keywords give retrieval a stable handle for abstract questions like:
      "backend frameworks" or "AI experience" even if the exact phrase isn't present.

    Used later:
      Retrieval scoring can boost chunks based on keywords overlap and capabilities.
    """
    lower = f" {text.lower()} "
    found: List[str] = []

    for canonical, variants in tech_keywords.items():
        for v in variants:
            if v in lower:
                found.append(canonical)
                break

    # Add high-level tags that help answer broad "experience" questions.
    if re.search(r"\bmentor(ed|ship)?\b", text, re.I):
        found.append("Mentorship")
    if re.search(r"\blead(ing|ership|)\b", text, re.I):
        found.append("Leadership")
    if re.search(r"\bbackend\b|\bapi\b|\brest\b", text, re.I):
        found.append("Backend")
    if re.search(r"\breal[- ]time\b|\bsocket\b|\bwebsocket\b", text, re.I):
        found.append("Real-time")

    # Deduplicate while preserving order.
    seen = set()
    out: List[str] = []
    for k in found:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def summarize_entity_block(section: str, entity: str, content: str, tech_keywords: Dict[str, List[str]]) -> str:
    """
    Produce a short summary_context per entity block.

    Why:
      The LLM often benefits from a high-level hint about what an entity block is.
      This helps it synthesize across multiple retrieved chunks without losing the plot.

    Used later:
      - passed alongside chunks (metadata.summary_context)
      - can be used in prompt formatting or future re-ranking
    """
    kws = extract_keywords(content, tech_keywords)[:5]
    base = f"Tae's work related to {entity}" if entity != "General" else f"Tae's {section.lower()} details"
    if kws:
        return f"{base} focused on {', '.join(kws[:4])}."
    return f"{base}."


# =============================================================================
# Public API
# =============================================================================

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


def create_contextual_chunks(
    pdf_text: str,
    *,
    source: str = DEFAULT_SOURCE,
    chunk_size: int = TARGET_CHUNK_SIZE,
    overlap_ratio: float = OVERLAP_RATIO,
) -> List[Dict]:
    """
    Main entrypoint: convert resume text into contextualized chunks.

    Output chunk schema:
      {
        "id": "chunk_005",
        "text": "Section: ... | Entity: ... - ...",
        "metadata": {...}
      }

    Why:
      - Prefixing the text with section/entity makes each chunk self-contained.
      - metadata is used for retrieval boosting, grouping, citations, and debugging.
    """
    lines = to_lines(pdf_text)
    sections = split_by_sections(lines)

    overlap = max(1, int(chunk_size * overlap_ratio))

    out: List[Dict] = []
    idx = 0

    for section, sec_lines in sections.items():
        blocks = group_by_entity(section, sec_lines)

        for block in blocks:
            entity = block["entity"]
            content = block["content"]

            summary_context = summarize_entity_block(section, entity, content, TECH_KEYWORDS)
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
                            "keywords": extract_keywords(contextual_text, TECH_KEYWORDS),
                            "summary_context": summary_context,
                        },
                    }
                )
                idx += 1

    return out


def debug_chunking_report(pdf_text: str) -> dict:
    """
    Generate a structured report verifying chunking invariants.

    Used later:
      This is your guardrail against regressions when you update the resume or
      tweak parsing rules. It makes failures obvious (bad entities, UNKNOWN section,
      missing prefixes, low keyword coverage).
    """
    chunks = create_contextual_chunks(pdf_text)

    if not chunks:
        return {
            "section_counts": {},
            "entity_counts_by_section": {},
            "suspicious_entities": [],
            "chunk_length_stats": {"min": 0, "median": 0, "max": 0},
            "prefix_check": 0.0,
            "keywords_coverage": 0.0,
        }

    section_counts = Counter(c["metadata"]["section"] for c in chunks)

    entity_counts_by_section: Dict[str, List[tuple]] = {}
    for section in section_counts.keys():
        section_chunks = [c for c in chunks if c["metadata"]["section"] == section]
        entity_counter = Counter(c["metadata"]["entity"] for c in section_chunks)
        entity_counts_by_section[section] = entity_counter.most_common(10)

    suspicious_entities = []
    for chunk in chunks:
        entity = chunk["metadata"]["entity"]
        section = chunk["metadata"]["section"]
        if MONTH_RE.search(entity) or YEAR_RE.search(entity) or _is_sentence_like_continuation(entity):
            suspicious_entities.append({"entity": entity, "section": section})

    # Deduplicate
    seen = set()
    unique_suspicious = []
    for item in suspicious_entities:
        key = (item["entity"], item["section"])
        if key not in seen:
            seen.add(key)
            unique_suspicious.append(item)

    chunk_lengths = [len(c["text"]) for c in chunks]
    chunk_length_stats = {
        "min": min(chunk_lengths),
        "median": int(median(chunk_lengths)),
        "max": max(chunk_lengths),
    }

    prefix_matches = sum(
        1 for c in chunks if c["text"].startswith("Section:") and "Entity:" in c["text"]
    )
    prefix_check = (prefix_matches / len(chunks)) * 100.0 if chunks else 0.0

    chunks_with_keywords = sum(
        1 for c in chunks if c["metadata"].get("keywords") and len(c["metadata"]["keywords"]) > 0
    )
    keywords_coverage = (chunks_with_keywords / len(chunks)) * 100.0 if chunks else 0.0

    return {
        "section_counts": dict(section_counts),
        "entity_counts_by_section": entity_counts_by_section,
        "suspicious_entities": unique_suspicious,
        "chunk_length_stats": chunk_length_stats,
        "prefix_check": prefix_check,
        "keywords_coverage": keywords_coverage,
    }
