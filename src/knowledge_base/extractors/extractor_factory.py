from typing import List
from .base import ContentExtractor
from .arxiv_extractor import ArxivExtractor
from .github_repo_extractor import GitHubRepoExtractor
from .github_notebook_extractor import GitHubNotebookExtractor
from .youtube_extractor import YouTubeExtractor
from .huggingface_extractor import HuggingFaceExtractor
from .html_extractor import HTMLExtractor


class ExtractorFactory:
    def __init__(self):
        self.extractors: List[ContentExtractor] = [
            ArxivExtractor(),
            GitHubRepoExtractor(),
            GitHubNotebookExtractor(),
            YouTubeExtractor(),
            HuggingFaceExtractor(),
            HTMLExtractor()
        ]
    
    def get_extractor(self, url: str) -> ContentExtractor:
        for extractor in self.extractors:
            if extractor.can_handle(url):
                return extractor
        return HTMLExtractor()  # Default fallback