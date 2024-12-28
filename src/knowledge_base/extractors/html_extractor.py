import requests
from bs4 import BeautifulSoup

from .base import ContentExtractor
# from src.knowledge_base.utils.config import configure_logging

# self.logger = configure_logging()


class HTMLExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return True  # Default fallback
    
    def extract(self, url: str, work=None) -> str:
        return self.get_html_content(url, work=work)
    
    def get_html_content(self, url, work=False, use_jina=False):
        self.logger.debug(f"Extracting content from HTML: {url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        # use jina.ai
        if use_jina:
            self.logger.debug(f"Using Jina: {use_jina}")
            jina_url = "https://r.jina.ai/"
            if work:
                response = requests.get(jina_url + url, headers=headers, verify="/Users/jeremymiller/Desktop/Zscaler Root CA.pem")
            else:
                response = requests.get(jina_url + url, headers=headers)
            content = str(response.content)

        # using beautiful soup by default
        else:
            self.logger.debug(f"Using Beautiful Soup: {not use_jina}")
            if work:
                response = requests.get(url, headers=headers, verify="/Users/jeremymiller/Desktop/Zscaler Root CA.pem")
            else:
                response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            content = soup.get_text()

        # Remove all empty lines from the content
        self.logger.debug(f"Content extracted: {content}")
        content = '\n'.join([line for line in content.split('\n') if line.strip()])

        return content
