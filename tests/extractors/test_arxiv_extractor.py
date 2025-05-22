import pytest
from unittest.mock import Mock, patch
from knowledge_base.extractors.arxiv_extractor import ArxivExtractor

@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def extractor(mock_logger):
    extractor = ArxivExtractor()
    extractor.logger = mock_logger
    return extractor

@pytest.fixture
def valid_urls():
    return [
        'https://arxiv.org/abs/2301.12345',
        'https://arxiv.org/pdf/2301.12345.pdf',
        'https://arxiv.org/abs/2301.12345v1',
        'http://arxiv.org/abs/2301.12345'
    ]

@pytest.fixture
def invalid_urls():
    return [
        'https://example.com',
        'https://arxiv.org/not-an-id',
        'https://arxiv.org/abs/',
        'https://arxiv.org/abs/invalid'
    ]

@pytest.fixture
def mock_arxiv_paper():
    return {
        'title': 'Test Paper',
        'abstract': 'Test abstract',
        'authors': ['Author One', 'Author Two'],
        'doi': '10.1234/5678',
        'published': '2023-01-01',
        'pdf_url': 'https://arxiv.org/pdf/2301.12345.pdf'
    }

@pytest.fixture
def mock_paper():
    paper = Mock()
    paper.title = "Test Paper Title"
    paper.summary = "Test paper summary"
    paper.authors = ["Author One", "Author Two"]
    paper.published = "2024-02-15"
    paper.entry_id = "https://arxiv.org/abs/2301.12345"
    return paper

def test_can_handle_valid_urls(extractor, valid_urls):
    for url in valid_urls:
        assert extractor.can_handle(url) is True

def test_can_handle_invalid_urls(extractor, invalid_urls):
    for url in invalid_urls:
        assert extractor.can_handle(url) is False

def test_extract_arxiv_id(extractor):
    url = 'https://arxiv.org/abs/2301.12345v1'
    assert extractor.extract_arxiv_id(url) == '2301.12345'

@patch('arxiv.Client')
def test_extract_content_success(mock_client, extractor, mock_paper):
    mock_client_instance = Mock()
    mock_client_instance.results.return_value = [mock_paper]
    mock_client.return_value = mock_client_instance
    
    content = extractor.extract('https://arxiv.org/abs/2301.12345')
    assert "Test Paper Title" in content
    assert "Test paper summary" in content

@patch('arxiv.Client')
def test_extract_content_no_results(mock_client, extractor):
    mock_client_instance = Mock()
    mock_client_instance.results.return_value = []
    mock_client.return_value = mock_client_instance
    
    with pytest.raises(ValueError, match="No paper found"):
        extractor.extract('https://arxiv.org/abs/2301.12345')

def test_extract_content_invalid_url(extractor):
    with pytest.raises(ValueError, match="Invalid arXiv URL"):
        extractor.extract('not-a-valid-url')