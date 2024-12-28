import json
import requests
from .base import ContentExtractor


class GitHubNotebookExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return self.is_github_notebook(url)
    
    def extract(self, url: str, work=None) -> str:
        notebook_content = self.get_github_notebook_content(url, work=work)
        notebook_cells = self.parse_notebook(notebook_content)
        return '\n\n'.join([f'**{cell["type"]}**\n{cell["content"]}' for cell in notebook_cells])

    def is_github_notebook(self, url):
        return 'github.com' in url and url.endswith('.ipynb')

    def get_github_notebook_content(self, github_url, work=False):
        github_url = github_url.strip()
        raw_url = github_url.replace('github.com', 'raw.githubusercontent.com').replace('/blob/', '/')
        if work:
            response = requests.get(raw_url, verify="/Users/jeremymiller/Desktop/Zscaler Root CA.pem")
        else:
            response = requests.get(raw_url)
        if response.status_code == 200:
            return response.text
        else:
            return None

    def parse_notebook(self, notebook_content):
        notebook_data = json.loads(notebook_content)
        parsed_content = []

        for cell in notebook_data['cells']:
            cell_type = cell['cell_type']
            cell_content = ''.join(cell['source'])
            parsed_content.append({'type': cell_type, 'content': cell_content})

        return parsed_content