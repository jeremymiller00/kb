import pytest
from unittest.mock import Mock, patch
from knowledge_base.extractors.html_extractor import HTMLExtractor

@pytest.fixture
def mock_logger():
    return Mock()

@pytest.fixture
def extractor(mock_logger):
    extractor = HTMLExtractor()
    extractor.logger = mock_logger
    return extractor

@pytest.fixture
def valid_urls():
    return [
        'https://example.com',
        'http://test.org/article',
        'https://blog.site.com/post/123',
        'https://sub.domain.net/path?param=value'
    ]

@pytest.fixture
def invalid_urls():
    return [
        '',
        'not-a-url',
        'ftp://example.com',
        'file:///path/to/file'
    ]

@pytest.fixture
def mock_html_content():
    return """
    <html>
        <head><title>Test Page</title></head>
        <body>
            <article>
                <h1>Test Article</h1>
                <p>Test content paragraph</p>
            </article>
        </body>
    </html>
    """

def test_can_handle_valid_urls(extractor, valid_urls):
    for url in valid_urls:
        assert extractor.can_handle(url) is True

def test_can_handle_invalid_urls(extractor, invalid_urls):
    for url in invalid_urls:
        assert extractor.can_handle(url) is False

@patch('requests.get')
def test_extract_content_success(mock_get, extractor, mock_html_content):
    mock_response = Mock()
    mock_response.text = mock_html_content
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    content = extractor.extract('https://example.com')
    assert content is not None
    assert 'Test Article' in content
    assert 'Test content paragraph' in content
    extractor.logger.debug.assert_called()  # Verify logger was called

@patch('requests.get')
def test_extract_content_failure(mock_get, extractor):
    mock_response = Mock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    with pytest.raises(Exception):
        extractor.extract('https://example.com/not-found')

def test_extract_content_invalid_url(extractor):
    with pytest.raises(Exception):
        extractor.extract('not-a-valid-url')