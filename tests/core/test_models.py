import pytest
from datetime import datetime
from pydantic import ValidationError
from src.knowledge_base.core.models import (
    ProcessOptions,
    URLRequest,
    ProcessResponse,
    DocumentResponse,
    DocumentCreate
)

@pytest.fixture
def sample_process_options():
    return {
        "debug": True,
        "work": False,
        "jina": True
    }

@pytest.fixture
def sample_document_data():
    return {
        "id": 1,
        "url": "https://example.com",
        "type": "web",
        "timestamp": int(datetime.now().timestamp()),
        "content": "Test content",
        "summary": "Test summary",
        "keywords": ["test", "example"],
        "embeddings": [0.1, 0.2, 0.3]
    }

def test_process_options_creation(sample_process_options):
    options = ProcessOptions(**sample_process_options)
    assert options.debug == True
    assert options.work == False
    assert options.jina == True

def test_process_options_defaults():
    options = ProcessOptions()
    assert options.debug == False
    assert options.work == False
    assert options.jina == False

def test_url_request_validation():
    # Valid URL
    request = URLRequest(url="https://example.com")
    assert str(request.url) == "https://example.com/"  # Note the trailing slash
    
    # Invalid URL should raise ValidationError
    with pytest.raises(ValidationError):
        URLRequest(url="not-a-url")

def test_document_response_creation(sample_document_data):
    doc = DocumentResponse(**sample_document_data)
    assert doc.id == 1
    assert doc.url == "https://example.com"
    assert isinstance(doc.keywords, list)
    assert isinstance(doc.embeddings, list)

def test_document_response_embeddings_parsing():
    # Test JSON string parsing
    data = {
        "id": 1,
        "url": "https://example.com",
        "type": "web",
        "timestamp": 1234567890,
        "content": "content",
        "embeddings": "[0.1, 0.2, 0.3]"
    }
    doc = DocumentResponse(**data)
    assert doc.embeddings == [0.1, 0.2, 0.3]

def test_document_create_validation():
    # Test required fields
    with pytest.raises(ValidationError):
        DocumentCreate()
    
    # Test valid creation
    doc = DocumentCreate(
        url="https://example.com",
        type="web",
        content="Test content"
    )
    assert doc.url == "https://example.com"
    assert doc.type == "web"
    assert doc.content == "Test content"