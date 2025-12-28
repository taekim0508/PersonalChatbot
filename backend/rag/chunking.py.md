# Chunking.py Documentation

## Overview

This module processes PDF resume text and breaks it down into structured, searchable chunks with metadata. It's designed to handle resume-specific formatting quirks and extract meaningful sections, entities, and keywords for RAG (Retrieval Augmented Generation) systems.

---

## Table of Contents

1. [Constants & Configuration](#constants--configuration)
2. [Normalization Functions](#normalization-functions)
3. [Text Analysis Functions](#text-analysis-functions)
4. [Section Splitting Functions](#section-splitting-functions)
5. [Entity Detection & Grouping Functions](#entity-detection--grouping-functions)
6. [Chunking Functions](#chunking-functions)
7. [Keyword Extraction Functions](#keyword-extraction-functions)
8. [Summary & Context Functions](#summary--context-functions)
9. [Main Public API](#main-public-api)

---

## Constants & Configuration

### `SOURCE_NAME`

- **Type**: `str`
- **Value**: `"KimTae-SWE-Resume.pdf"`
- **Purpose**: Default source document name used in chunk metadata

### `TARGET_CHUNK_SIZE`

- **Type**: `int`
- **Value**: `500`
- **Purpose**: Target size (in characters) for each text chunk

### `OVERLAP_RATIO`

- **Type**: `float`
- **Value**: `0.2` (20%)
- **Purpose**: Percentage of overlap between consecutive chunks to maintain context

### `OVERLAP_CHARS`

- **Type**: `int`
- **Calculation**: `max(1, int(TARGET_CHUNK_SIZE * OVERLAP_RATIO))`
- **Purpose**: Actual number of characters to overlap between chunks (minimum 1)

### `SECTION_HEADERS`

- **What**: These are the resume headers that are used extract the sections of my resume. Also is metadata for every chunk. 
- **Why**: RAG may have a hard time identifying the different section headers of my resume so we add in common header variants to prevent failure. For queries where the question is abstract like "What experience does Tae have with AI?" you need to sift through multiple sections. You don't use these sections to directly match the context to the question but to:
    - let retrieval and the LLM know what kind of evidence a chunk is (experience vs. project vs. skill)
    - help LLM phrase answers

### `TECH_KEYWORDS`

- **Purpose**: Maps canonical technology names to their common variations (for keyword matching)
- **Example**: `"AI"` maps to `[" ai ", "artificial intelligence"]`
- **How it works**: When extracting keywords, the code searches for these variations in lowercase text and returns the canonical name
- **Why**: This is just a rough list of the possible keywords, but these are meant to help the retrieval and LLM by categorizing chunks based on the keywords that best fit the context. Additionally, this is is used as metadata. 

### `BULLET_REGEX`

- **Type**: `re.Pattern`
- **Purpose**: Regular expression to detect bullet points in text. 
- **Why**: Can have multiple bullet point types which may create detection difficulties if a single bullet expression is looked for in the resume when there may be multiple types or a different type to begin with. 

### `ENTITY_SEP_REGEX`


- **Example**: Matches `"Company | Role | Dates"` or `"Company — Role"`
- **What**: ENTITY_SEP_REGEX captures common separators used in resume entity headers, such as:
    - "Company | Role | Dates"
    - "Project Name — Tech Stack"
    - "Organization – Position"

- During ingestion, the text to the LEFT of the first separator is treated as the canonical entity name (company or project). All subsequent bullet points are grouped under this entity.

- **Why**: Accurate entity extraction is essential for:
  - answering "Where did Tae do X?"
  - preserving ownership of actions across chunks
  - enabling cross-section synthesis (Experience + Projects)

### `Chunk` (dataclass)

- **Type**: `dataclass`
- **Fields**:
  - `id: str` - Unique identifier for the chunk
  - `text: str` - The chunk's text content
  - `metadata: Dict` - Additional metadata about the chunk
- **Purpose**: Data structure representing a single chunk (note: currently not used in the main function, which returns dicts instead)

---

## Normalization Functions

### `normalize_text(pdf_text: str) -> str`
**Purpose**: Cleans up PDF-extracted text to handle common extraction quirks and inconsistencies.

### `to_lines(pdf_text: str) -> List[str]`
**Purpose**: Converts normalized PDF text into a list of non-empty lines.

**Why**: We need to convert the pdf text into a chunkable and consistent text. Section splitting may be inconsistent or incorrect if the line in the pdf ends different or is formatted differently than others. It also helps with identifying keywords and grouping entities. 
---

### `leading_spaces(line: str) -> int`

**Category**: Text Analysis Helper

**Purpose**: Counts the number of leading spaces in a line (used for indentation detection).

**What it does**:

- Calculates the difference between total line length and length after stripping leading spaces

**Input**: A single line of text
**Output**: Number of leading spaces

**Example**:

```python
leading_spaces("    Indented line")
# Returns: 4
```

---

## Text Analysis Functions

### `is_bullet(line: str, *, indent_threshold: int = 2) -> bool`

**Category**: Bullet Detection

**Purpose**: Determines if a line is a bullet point, handling various bullet formats and edge cases.

**What it does**:

1. First checks if the line matches `BULLET_REGEX` (explicit bullet symbols, numbers, letters)
2. If no explicit bullet found, falls back to indentation detection:
   - If line has `indent_threshold` (default: 2) or more leading spaces, treats it as a bullet
   - This handles cases where PDF extraction loses bullet symbols but preserves indentation

**Parameters**:

- `line`: The text line to check
- `indent_threshold`: Minimum number of leading spaces to consider as a bullet (default: 2)

**Returns**: `True` if the line appears to be a bullet point, `False` otherwise

**Example**:

```python
is_bullet("• First bullet")      # Returns: True
is_bullet("1. Numbered item")    # Returns: True
is_bullet("    Indented line")   # Returns: True (indentation fallback)
is_bullet("Regular text")        # Returns: False
```

**Note**: The indentation fallback can produce false positives, so it's used in combination with other logic in entity grouping.

---

### `canonicalize_header(line: str) -> str`

**Category**: Section Header Normalization

**Purpose**: Normalizes section header text for consistent matching against `SECTION_HEADERS`.

**What it does**:

1. Normalizes spaces around slashes (e.g., `"A / B"` → `"A / B"`)
2. Collapses multiple spaces/tabs into single spaces
3. Strips leading/trailing whitespace

**Input**: Raw header line from PDF
**Output**: Normalized header string ready for comparison

**Example**:

```python
canonicalize_header("PROFESSIONAL  EXPERIENCE  /  LEADERSHIP")
# Returns: "PROFESSIONAL EXPERIENCE / LEADERSHIP"
```

---

### `looks_like_allcaps(line: str) -> bool`

**Category**: Text Pattern Detection

**Purpose**: Checks if a line appears to be all uppercase (used to identify section headers).

**What it does**:

1. Removes all non-alphabetic characters
2. Checks if remaining alphabetic characters are all uppercase
3. Returns `False` if no alphabetic characters found

**Input**: A text line
**Output**: `True` if line is all caps, `False` otherwise

**Example**:

```python
looks_like_allcaps("EDUCATION")        # Returns: True
looks_like_allcaps("Education")        # Returns: False
looks_like_allcaps("123 EDUCATION")    # Returns: True (ignores numbers)
```

---

### `has_date_like_token(line: str) -> bool`

**Category**: Date Detection

**Purpose**: Detects if a line contains date-like patterns (common in experience/education sections).

**What it does**:

1. Searches for 4-digit years: `20XX` or `19XX` (e.g., "2024", "1999")
2. Searches for month abbreviations: Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec (case-insensitive)

**Input**: A text line
**Output**: `True` if date patterns found, `False` otherwise

**Example**:

```python
has_date_like_token("May 2024 – Aug 2024")  # Returns: True
has_date_like_token("Started in 2020")       # Returns: True
has_date_like_token("No dates here")        # Returns: False
```

---

### `titlecase_score(line: str) -> float`

**Category**: Text Pattern Scoring

**Purpose**: Calculates a heuristic score indicating how "title-case-like" a line is (used for entity detection).

**What it does**:

1. Extracts all words (sequences of letters, allowing `&`, `.`, `-` within words)
2. Counts words that start with uppercase letters
3. Returns the fraction: `uppercase_words / total_words`

**Input**: A text line
**Output**: Float between 0.0 and 1.0 (higher = more title-case-like)

**Example**:

```python
titlecase_score("LiveArena Technologies")     # Returns: 1.0 (2/2 words)
titlecase_score("Software Engineering Intern") # Returns: 1.0 (3/3 words)
titlecase_score("worked on backend systems")  # Returns: 0.0 (0/4 words)
titlecase_score("Python and React")           # Returns: 1.0 (2/2 words)
```

**Use case**: Helps identify entity header lines (company names, project names) which are typically title-case.

---

## Section Splitting Functions

### `split_by_sections(lines: List[str]) -> Dict[str, List[str]]`

**Category**: Section Splitting

**Purpose**: Divides resume lines into sections based on known section headers.

**What it does**:

1. Iterates through all lines
2. For each line, canonicalizes it and checks if it matches any `SECTION_HEADERS`
3. When a section header is found, starts a new section
4. Lines before the first header go into `"UNKNOWN"` section
5. Removes `"UNKNOWN"` section if it's empty

**Input**: List of normalized text lines
**Output**: Dictionary mapping section names to their lines

- Keys: Section names (from `SECTION_HEADERS` or `"UNKNOWN"`)
- Values: List of lines belonging to that section

**Example**:

```python
lines = [
    "EDUCATIONS",
    "University Name",
    "PROFESSIONAL EXPERIENCE",
    "Company Name | Role"
]
split_by_sections(lines)
# Returns: {
#   "EDUCATIONS": ["University Name"],
#   "PROFESSIONAL EXPERIENCE": ["Company Name | Role"]
# }
```

---

## Entity Detection & Grouping Functions

### `is_probable_entity_line(line: str) -> bool`

**Category**: Entity Detection

**Purpose**: Determines if a line likely starts a new entity block (e.g., a new job, project, or education entry).

**What it does**:

1. **Filters out false positives**:

   - Empty lines → `False`
   - Section headers (all caps and in `SECTION_HEADERS`) → `False`
   - Bullet points → `False`

2. **Checks for entity indicators** (returns `True` if any match):
   - **Separator detection**: Line contains `|`, `—`, or `–` (common format: "Company | Role | Dates")
   - **Date + title-case**: Line has date-like tokens AND `titlecase_score >= 0.55` (likely role header)
   - **Short title-case**: Line length ≤ 90 characters AND `titlecase_score >= 0.70` (likely project/company name)

**Input**: A single text line
**Output**: `True` if line likely starts an entity, `False` otherwise

**Example**:

```python
is_probable_entity_line("LiveArena Technologies | Software Engineering Intern | May 2024")
# Returns: True (has separator)

is_probable_entity_line("Personal Portfolio Chatbot")
# Returns: True (short, high title-case score)

is_probable_entity_line("• Implemented feature")
# Returns: False (is a bullet)

is_probable_entity_line("EDUCATIONS")
# Returns: False (is a section header)
```

---

### `extract_entity_from_line(line: str) -> str`

**Category**: Entity Extraction

**Purpose**: Extracts the entity name (company/project name) from an entity header line.

**What it does**:

1. Strips whitespace from the line
2. Checks for separators (`|`, `—`, `–`) in order
3. If separator found, returns the left portion (before the separator)
4. If no separator, returns the entire line

**Input**: An entity header line (e.g., "Company | Role | Dates")
**Output**: Entity name string

**Example**:

```python
extract_entity_from_line("LiveArena Technologies | Software Engineering Intern | May 2024")
# Returns: "LiveArena Technologies"

extract_entity_from_line("Personal Portfolio Chatbot")
# Returns: "Personal Portfolio Chatbot"
```

---

### `group_by_entity(section_lines: List[str]) -> List[Dict[str, str]]`

**Category**: Entity Grouping

**Purpose**: Groups lines within a section into entity blocks (each representing one job, project, or education entry).

**What it does**:

1. Iterates through section lines
2. When `is_probable_entity_line()` detects an entity header:
   - Flushes previous entity block (if exists) to the results
   - Starts a new entity block with extracted entity name
3. Non-entity lines are added to the current entity's content buffer
4. If no entity headers detected, creates a single `"General"` entity block
5. Flushes the final entity block

**Input**: List of lines from a section
**Output**: List of dictionaries, each containing:

- `"entity"`: Entity name (company/project name or `"General"`)
- `"content"`: All lines belonging to that entity, joined by newlines

**Example**:

```python
section_lines = [
    "Company A | Role A | Dates",
    "• Bullet 1",
    "• Bullet 2",
    "Company B | Role B | Dates",
    "• Bullet 3"
]
group_by_entity(section_lines)
# Returns: [
#   {
#     "entity": "Company A",
#     "content": "Company A | Role A | Dates\n• Bullet 1\n• Bullet 2"
#   },
#   {
#     "entity": "Company B",
#     "content": "Company B | Role B | Dates\n• Bullet 3"
#   }
# ]
```

---

## Chunking Functions

### `sliding_window_chunks(text: str, *, size: int = TARGET_CHUNK_SIZE, overlap: int = OVERLAP_CHARS) -> List[str]`

**Category**: Text Chunking

**Purpose**: Splits text into overlapping chunks of approximately `size` characters.

**What it does**:

1. Calculates step size: `size - overlap` (how far to move forward between chunks)
2. Uses a sliding window approach:
   - Starts at position `i = 0`
   - Extracts chunk from `i` to `i + size`
   - Moves forward by `step` characters
   - Repeats until end of text
3. **Boundary adjustment**: If chunk ends mid-word, extends to the next whitespace to avoid cutting words
4. Strips whitespace from each chunk
5. Skips empty chunks

**Parameters**:

- `text`: The text to chunk
- `size`: Target chunk size in characters (default: `TARGET_CHUNK_SIZE` = 500)
- `overlap`: Number of characters to overlap between chunks (default: `OVERLAP_CHARS`)

**Input**: Text string
**Output**: List of text chunks

**Example**:

```python
text = "This is a long text that needs to be chunked..."
sliding_window_chunks(text, size=20, overlap=5)
# Returns: [
#   "This is a long text",           # chars 0-20
#   "text that needs to be",         # chars 15-35 (overlaps by 5)
#   "to be chunked..."               # chars 30-50 (overlaps by 5)
# ]
```

**Why overlap?**: Overlapping chunks ensure that information spanning chunk boundaries isn't lost, improving retrieval quality in RAG systems.

---

## Keyword Extraction Functions

### `extract_keywords(text: str, *, max_keywords: int = 14) -> List[str]`

**Category**: Keyword Matching

**Purpose**: Extracts canonical technology/skill keywords from text by matching against `TECH_KEYWORDS` dictionary.

**What it does**:

1. Converts text to lowercase and pads with spaces (for substring matching like `" ai "`)
2. Iterates through `TECH_KEYWORDS`:
   - For each canonical keyword, checks if any of its variants appear in the text
   - If found, adds the canonical keyword to results
3. Adds "soft" high-level terms if patterns detected:
   - **Mentorship**: Matches "mentor", "mentored", "mentorship"
   - **Leadership**: Matches "lead", "leading", "leadership"
   - **Backend**: Matches "backend", "api", "rest"
   - **Real-time**: Matches "real-time", "real time", "socket", "websocket"
4. Deduplicates while preserving order
5. Returns up to `max_keywords` keywords

**Parameters**:

- `text`: Text to extract keywords from
- `max_keywords`: Maximum number of keywords to return (default: 14)

**Input**: Text string
**Output**: List of canonical keyword strings

**Example**:

```python
text = "Built a RAG system using Python and FastAPI. Used OpenAI API for LLM integration."
extract_keywords(text)
# Returns: ["RAG", "Python", "FastAPI", "OpenAI API", "LLM"]
```

**Note**: The function uses substring matching, so `" ai "` (with spaces) matches "artificial intelligence" but avoids false positives like "said" containing "ai".

---

## Summary & Context Functions

### `summarize_entity_block(section: str, entity: str, content: str) -> str`

**Category**: Context Generation

**Purpose**: Creates a human-readable summary describing what an entity block is about.

**What it does**:

1. Extracts keywords from the content (up to 6 keywords)
2. Builds a base description:
   - If entity is `"General"`: `"Tae's {section.lower()} details"`
   - Otherwise: `"Tae's work related to {entity}"`
3. If keywords found, appends: `" focused on {keyword1}, {keyword2}, ..."`
4. Returns the summary string

**Parameters**:

- `section`: Section name (e.g., "PROFESSIONAL EXPERIENCE")
- `entity`: Entity name (e.g., "LiveArena Technologies")
- `content`: Full content of the entity block

**Input**: Section name, entity name, content text
**Output**: Summary string

**Example**:

```python
summarize_entity_block(
    "PROFESSIONAL EXPERIENCE",
    "LiveArena Technologies",
    "Built RAG system using Python, FastAPI, and OpenAI API..."
)
# Returns: "Tae's work related to LiveArena Technologies focused on RAG, Python, FastAPI, OpenAI API."
```

**Use case**: This summary is stored in chunk metadata and inherited by all sub-chunks within an entity block, providing context for retrieval.

---

## Main Public API

### `create_contextual_chunks(pdf_text: str, *, source: str = DEFAULT_SOURCE, chunk_size: int = TARGET_CHUNK_SIZE, overlap_ratio: float = OVERLAP_RATIO) -> List[Dict]`

**Category**: Main Entry Point

**Purpose**: Main function that orchestrates the entire chunking pipeline. This is the function you call to process a resume PDF.

**What it does** (step by step):

1. **Normalize and split into lines**: Calls `to_lines()` to get clean line list

2. **Split into sections**: Calls `split_by_sections()` to organize lines by resume section

3. **For each section**:
   - **Group by entity**: Calls `group_by_entity()` to create entity blocks
   - **For each entity block**:
     - **Generate summary context**: Calls `summarize_entity_block()` for the block
     - **Chunk the content**: Calls `sliding_window_chunks()` to split entity content into ~500 char chunks
     - **For each sub-chunk**:
       - **Create contextual text**: Prefixes chunk with `"Section: {section} | Entity: {entity} - "`
       - **Extract keywords**: Calls `extract_keywords()` on the contextual text
       - **Build chunk dictionary**:
         ```python
         {
           "id": "chunk_000",  # Sequential ID
           "text": "Section: ... | Entity: ... - {chunk_text}",
           "metadata": {
             "source": source,              # PDF filename
             "section": section,            # Section name
             "entity": entity,              # Entity name
             "keywords": [...],              # Extracted keywords
             "summary_context": "..."       # Entity block summary
           }
         }
         ```

**Parameters**:

- `pdf_text`: Raw text extracted from PDF
- `source`: Source document name (default: `DEFAULT_SOURCE` - note: this constant appears to be missing in the code)
- `chunk_size`: Target chunk size in characters (default: 500)
- `overlap_ratio`: Overlap ratio between chunks (default: 0.2)

**Input**: PDF text string
**Output**: List of chunk dictionaries ready for indexing/storage

**Example Output**:

```python
[
  {
    "id": "chunk_000",
    "text": "Section: PROFESSIONAL EXPERIENCE | Entity: LiveArena Technologies - Built a RAG system...",
    "metadata": {
      "source": "KimTae-SWE-Resume.pdf",
      "section": "PROFESSIONAL EXPERIENCE",
      "entity": "LiveArena Technologies",
      "keywords": ["RAG", "Python", "FastAPI"],
      "summary_context": "Tae's work related to LiveArena Technologies focused on RAG, Python, FastAPI."
    }
  },
  # ... more chunks
]
```

**Pipeline Flow**:

```
PDF Text
  ↓
Normalize & Split Lines
  ↓
Split by Sections
  ↓
Group by Entity (within each section)
  ↓
Chunk Each Entity Block (with overlap)
  ↓
Add Context Prefix & Extract Keywords
  ↓
Return List of Chunk Dicts
```

---

## Common Use Cases

### 1. Processing a Resume PDF

```python
from rag.chunking import create_contextual_chunks

# After extracting text from PDF
pdf_text = extract_pdf_text("resume.pdf")
chunks = create_contextual_chunks(pdf_text, source="resume.pdf")

# chunks is now ready to be indexed in a vector database
```

### 2. Custom Chunk Size

```python
# For smaller chunks (e.g., 300 chars)
chunks = create_contextual_chunks(pdf_text, chunk_size=300)
```

### 3. Extracting Keywords from Text

```python
from rag.chunking import extract_keywords

keywords = extract_keywords("Built with Python, React, and Docker")
# Returns: ["Python", "React", "Docker"]
```

---

## Design Decisions & Notes

### Why Contextual Prefixes?

Each chunk is prefixed with `"Section: {section} | Entity: {entity} - "` to provide context during retrieval. This helps the RAG system understand where information came from.

### Why Overlap?

Overlapping chunks (20% by default) ensure that information spanning chunk boundaries isn't lost. This is crucial for maintaining context in RAG systems.

### Why Entity Grouping?

Grouping by entity (company/project) allows all chunks from the same entity to share the same `summary_context`, providing better semantic understanding.

### Handling Edge Cases

- **Missing section headers**: Lines before first header go into `"UNKNOWN"` section
- **No entity headers**: Falls back to `"General"` entity
- **Lost bullet symbols**: Uses indentation fallback in `is_bullet()`
- **Mid-word chunk boundaries**: Extends chunks to next whitespace

---

## Potential Issues & Improvements

### Missing Imports

The code references `DEFAULT_SOURCE` and uses `@dataclass` but doesn't import them:

- `from dataclasses import dataclass` is missing
- `DEFAULT_SOURCE` constant is not defined (line 360)

### Chunk Class Not Used

The `Chunk` dataclass is defined but not used in `create_contextual_chunks()` (which returns plain dicts).

---

## Summary

This module transforms unstructured PDF resume text into structured, searchable chunks with rich metadata. It handles resume-specific formatting, extracts meaningful entities and keywords, and creates overlapping chunks suitable for RAG systems. The main entry point is `create_contextual_chunks()`, which orchestrates normalization → section splitting → entity grouping → chunking → keyword extraction.
