import requests
from bs4 import BeautifulSoup

from .base import ContentExtractor


class HuggingFaceExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return 'huggingface.co' in url
    
    def extract(self, url: str, work=None) -> str:
        return self.get_huggingface_content(url, work=work)

    def get_huggingface_content(self, url, work=False):
        model_html_content = self.fetch_huggingface_model_page(url, work=work)
        if model_html_content:
            model_sections = self.parse_huggingface_html(model_html_content)
            content = '\n\n'.join([f'**{section_name}**\n{section_content}' for section_name, section_content in model_sections.items()])
            return content
        else:
            return "Hugging Face model page not found."

    def fetch_huggingface_model_page(self, url, work=False):
        if work:
            response = requests.get(url, verify="/Users/jeremymiller/Desktop/Zscaler Root CA.pem")
        else:
            response = requests.get(url)
        if response.status_code == 200:
            return response.text
        else:
            return None

    def parse_huggingface_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        sections = {}

        for heading in soup.find_all('h2'):
            heading_text = heading.get_text(strip=True)
            content = []

            for sibling in heading.find_next_siblings():
                if sibling.name == 'h2':
                    break
                content.append(sibling.get_text(strip=True))

            sections[heading_text] = ' '.join(content)

        return sections