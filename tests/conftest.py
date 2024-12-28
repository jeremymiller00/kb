import pytest
import os
from datetime import datetime

@pytest.fixture
def mock_env_setup(monkeypatch, tmp_path):
    """Setup mock environment variables"""
    kb_path = str(tmp_path / 'test_kb')
    monkeypatch.setenv('DSV_KB_PATH', kb_path)
    os.makedirs(kb_path, exist_ok=True)
    return kb_path

@pytest.fixture
def sample_urls():
    """Provide sample URLs for different types"""
    return {
        'github': 'https://github.com/username/repo',
        'github_ipynb': 'https://github.com/username/repo/blob/main/notebook.ipynb',
        'arxiv': 'https://arxiv.org/abs/1234.5678',
        'youtube': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'huggingface': 'https://huggingface.co/username/model',
        'general': 'https://example.com/article'
    }

@pytest.fixture
def mock_time(monkeypatch):
    """Mock time.time() to return a fixed timestamp"""
    FIXED_TIME = 1640995200  # 2022-01-01 00:00:00
    
    class MockTime:
        @staticmethod
        def time():
            return FIXED_TIME
        
        @staticmethod
        def localtime(timestamp):
            return datetime.fromtimestamp(timestamp).timetuple()
    
    monkeypatch.setattr('time.time', MockTime.time)
    monkeypatch.setattr('time.localtime', MockTime.localtime)
    return FIXED_TIME

@pytest.fixture
def sample_content():
    """Provide sample content for testing"""
    return {
        'content': 'Sample webpage content',
        'summary': 'This is a summary of the content',
        'keywords': ['key1', 'key2', 'key3'],
        'embeddings': [0.1, 0.2, 0.3],
        'obsidian_markdown': '# Title\n\nContent here'
    }

@pytest.fixture
def mock_ai_functions(mocker):
    """Mock AI-related functions"""
    mocker.patch('ai_func.generate_summary', return_value='Mock summary')
    mocker.patch('ai_func.extract_keywords_from_summary', return_value=['key1', 'key2'])
    mocker.patch('ai_func.generate_embedding', return_value=[0.1, 0.2, 0.3])
    mocker.patch('ai_func.summary_to_obsidian_markdown', return_value='# Mock markdown')

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for file operations"""
    return tmp_path
