from typing import List, Optional, Union
# from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, HttpUrl, Field, validator

Base = declarative_base()


# SQLAlchemy Models
class ProcessOptions(BaseModel):
    debug: bool = Field(default=False, description="Run in debug mode")
    work: bool = Field(default=False, description="Work mode for special processing")
    jina: bool = Field(default=False, description="Use Jina for processing")


class URLRequest(BaseModel):
    url: HttpUrl
    debug: bool = False
    work: bool = False
    jina: bool = False


class ProcessResponse(BaseModel):
    file_type: str
    file_path: str
    timestamp: str
    url: str
    content: str
    summary: str
    keywords: list
    obsidian_markdown: str
    embedding: list


class DocumentResponse(BaseModel):
    id: Union[int, str] = Field(..., description="Document unique identifier")
    url: str = Field(..., description="Source URL of the document")
    type: str = Field(..., description="Document type (github, arxiv, etc)")
    timestamp: int = Field(..., description="Unix timestamp of creation")
    content: str = Field(..., description="Raw document content")
    summary: Optional[str] = Field(None, description="AI-generated summary")
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords")
    embeddings: Optional[List[float]] = Field(None, description="Vector embeddings")

    @validator('embeddings', pre=True)
    def parse_embeddings(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return [float(x) for x in v.strip('[]').split(',')]
        return v

    class Config:
        orm_mode = True


class DocumentCreate(BaseModel):
    url: str = Field(..., description="Source URL of the document")
    type: str = Field(..., description="Document type (github, arxiv, etc)")
    content: str = Field(..., description="Raw document content")
    summary: Optional[str] = Field(None, description="AI-generated summary")
    keywords: Optional[List[str]] = Field(None, description="Extracted keywords")
    embeddings: Optional[List[float]] = Field(None, description="Vector embeddings")
    obsidian_markdown: Optional[str] = Field(None, description="Formatted Obsidian markdown")

    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com",
                "type": "web",
                "content": "Example content",
                "summary": "Brief summary",
                "keywords": ["example", "keywords"],
                "embeddings": [0.1, 0.2, 0.3],
                "obsidian_markdown": "# Example\nContent"
            }
        }
