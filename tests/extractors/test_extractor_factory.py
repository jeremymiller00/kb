""" 
pytest tests/extractors/test_extractor_factory.py -v
"""

import pytest
from knowledge_base.extractors.extractor_factory import ExtractorFactory
from knowledge_base.extractors.arxiv_extractor import ArxivExtractor
from knowledge_base.extractors.github_repo_extractor import GitHubRepoExtractor
from knowledge_base.extractors.github_notebook_extractor import GitHubNotebookExtractor
from knowledge_base.extractors.youtube_extractor import YouTubeExtractor
from knowledge_base.extractors.huggingface_extractor import HuggingFaceExtractor
from knowledge_base.extractors.html_extractor import HTMLExtractor

@pytest.fixture
def factory():
    return ExtractorFactory()

@pytest.fixture
def test_urls():
    return {
        'arxiv': 'https://arxiv.org/abs/2303.08774',
        'github_repo': 'https://github.com/user/repo',
        'github_notebook': 'https://github.com/user/repo/blob/main/notebook.ipynb',
        'github_pdf': 'https://github.com/user/repo/blob/main/document.pdf',
        'youtube': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'huggingface': 'https://huggingface.co/models',
        'html': 'https://example.com',
    }

def test_factory_initialization(factory):
    assert len(factory.extractors) == 6
    assert isinstance(factory.extractors[0], ArxivExtractor)
    assert isinstance(factory.extractors[-1], HTMLExtractor)

def test_arxiv_extractor_selection(factory, test_urls):
    extractor = factory.get_extractor(test_urls['arxiv'])
    assert isinstance(extractor, ArxivExtractor)

def test_github_repo_extractor_selection(factory, test_urls):
    extractor = factory.get_extractor(test_urls['github_repo'])
    assert isinstance(extractor, GitHubRepoExtractor)

def test_github_notebook_extractor_selection(factory, test_urls):
    extractor = factory.get_extractor(test_urls['github_notebook'])
    assert isinstance(extractor, GitHubNotebookExtractor)

def test_github_pdf_extractor_selection(factory, test_urls):
    extractor = factory.get_extractor(test_urls['github_pdf'])
    assert isinstance(extractor, HTMLExtractor)

def test_youtube_extractor_selection(factory, test_urls):
    extractor = factory.get_extractor(test_urls['youtube'])
    print(f"extractor: {extractor}")
    assert isinstance(extractor, YouTubeExtractor)

def test_huggingface_extractor_selection(factory, test_urls):
    extractor = factory.get_extractor(test_urls['huggingface'])
    assert isinstance(extractor, HuggingFaceExtractor)

def test_html_extractor_fallback(factory, test_urls):
    extractor = factory.get_extractor(test_urls['html'])
    assert isinstance(extractor, HTMLExtractor)

def test_invalid_url_fallback(factory):
    extractor = factory.get_extractor("invalid_url")
    assert isinstance(extractor, HTMLExtractor)