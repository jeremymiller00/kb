import re
import arxiv
from .base import ContentExtractor
from ..utils.logger import logger


class ArxivExtractor(ContentExtractor):
    def __init__(self):
        self.logger = logger

    def can_handle(self, url: str) -> bool:
        if not url:
            return False
        arxiv_pattern = r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)'
        return bool(re.search(arxiv_pattern, url.lower()))

    def extract(self, url: str, work=None) -> str:
        try:
            paper_id = self.extract_arxiv_id(url)
            if not paper_id:
                raise ValueError(f"Invalid arXiv URL: {url}")

            client = arxiv.Client()
            search = arxiv.Search(id_list=[paper_id])
            results = list(client.results(search))

            if not results:
                raise ValueError(f"No paper found for ID: {paper_id}")

            paper = results[0]
            return self.format_paper(paper)
        except Exception as e:
            self.logger.error(f"Error extracting arXiv content: {str(e)}")
            raise

    def extract_arxiv_id(self, url: str) -> str:
        match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', url.lower())
        return match.group(1) if match else None

    def format_paper(self, paper) -> str:
        return f"""Title:{paper.title}
Abstract:{paper.summary}
Authors:{', '.join(str(author) for author in paper.authors)}
Published:{paper.published}
URL:{paper.entry_id}
"""
