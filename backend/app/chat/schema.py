from pydantic import BaseModel, Field
from typing import List


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(6, ge=1, le=12)


class RetrievedEvidence(BaseModel):
    id: str
    score: float
    section: str
    entity: str
    keywords: List[str]
    text_preview: str


class Citation(BaseModel):
    chunk_id: str
    section: str
    entity: str


class ChatResponse(BaseModel):
    query: str
    top_k: int
    answer: str
    citations: List[Citation]
    evidence: List[RetrievedEvidence]
