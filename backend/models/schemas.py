from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class DocumentElement(BaseModel):
    id: str
    type: str
    label: str
    text: str = ""
    html: str | None = None
    image_url: str | None = None
    page: int | None = None
    level: int | None = None
    ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    chunk_id: str
    chunk_number: int
    text: str
    section_title: str | None = None
    page_number: int | None = None
    element_types: list[str] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    document_id: str
    filename: str
    status: str
    page_count: int = 0
    elements: list[DocumentElement] = Field(default_factory=list)
    markdown: str = ""
    json_export: dict[str, Any] = Field(default_factory=dict)
    chunks: list[DocumentChunk] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class JobStatus(BaseModel):
    job_id: str
    document_id: str
    filename: str
    stage: str
    progress: int
    message: str
    status: Literal["pending", "running", "complete", "error"]
    error: str | None = None
    parsed: ParsedDocument | None = None


class SearchRequest(BaseModel):
    query: str
    mode: Literal["keyword", "semantic", "hybrid"] = "hybrid"
    size: int = 8


class SearchHit(BaseModel):
    chunk_id: str
    document_title: str
    source_file: str
    section_title: str | None = None
    page_number: int | None = None
    chunk_text: str
    score: float
    match_type: str
    keyword_score: float | None = None
    vector_score: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    highlights: list[str] = Field(default_factory=list)


class SearchQueryDebug(BaseModel):
    documentation_url: str
    index: str
    search_pipeline: str | None = None
    fusion_weights: dict[str, float] = Field(default_factory=dict)
    steps: list[str] = Field(default_factory=list)
    create_search_pipeline: dict[str, Any] | None = None
    search_request: dict[str, Any] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    mode: str
    total: int
    hits: list[SearchHit] = Field(default_factory=list)
    explanation: str = ""
    query_debug: SearchQueryDebug | None = None
