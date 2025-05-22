""" 
pytest tests/extractors/test_youtube_extractor.py -v
"""

import pytest
from knowledge_base.extractors.youtube_extractor import YouTubeExtractor

@pytest.fixture
def extractor():
    return YouTubeExtractor()

@pytest.fixture
def valid_urls():
    return [
        'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'https://youtu.be/dQw4w9WgXcQ',
        'https://youtube.com/embed/dQw4w9WgXcQ',
        'https://youtube.com/v/dQw4w9WgXcQ',
        'https://youtube.com/shorts/dQw4w9WgXcQ',
    ]

@pytest.fixture
def invalid_urls():
    return [
        'https://youtube.com',
        'https://youtu.be/',
        'https://youtube.com/watch',
        'https://notyoutube.com/watch?v=dQw4w9WgXcQ',
        'https://youtube.com/watch?v=short'  # Less than 11 chars
    ]

def test_valid_youtube_urls(extractor, valid_urls):
    for url in valid_urls:
        assert extractor.can_handle(url) is True

def test_invalid_youtube_urls(extractor, invalid_urls):
    for url in invalid_urls:
        assert extractor.can_handle(url) is False

def test_extract_video_id(extractor):
    url = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
    assert extractor.extract_video_id(url) == 'dQw4w9WgXcQ'