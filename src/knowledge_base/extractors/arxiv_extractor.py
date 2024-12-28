import re
import requests
from bs4 import BeautifulSoup
from .base import ContentExtractor


class ArxivExtractor(ContentExtractor):
    def can_handle(self, url: str) -> bool:
        return 'arxiv.org' in url
    
    def extract(self, url: str, work=None) -> str:
        return self.get_arxiv_content(url, work=work)
    
    def get_arxiv_content(self, url, work=False):
        arxiv_id = self.extract_arxiv_id(url)
        if arxiv_id is None:
            return "Arxiv ID not found."
        arxiv_html_content = self.fetch_arxiv_page(arxiv_id, work=work)
        if arxiv_html_content:
            arxiv_sections = self.parse_html(arxiv_html_content)
            content = '\n\n'.join([f'**{section_name}**\n{section_content}' for section_name, section_content in arxiv_sections.items()])
            return content
        else: # if the html page is not found, we downgrade the old version
            #return "Arxiv page not found."
            print("Arxiv page not found. Downgrading to old version.")
            return self.get_arxiv_content_old_version(url, work=work)

    def extract_arxiv_id(self, url, include_version=False):
        # Patterns for different types of Arxiv URLs
        patterns = [
            r'https://browse\.arxiv\.org/html/(\d{4}\.\d{4,5}v?\d*)',  # HTML version
            r'https://arxiv\.org/abs/(\d{4}\.\d{4,5})',                # Abstract page
            r'https://arxiv\.org/pdf/(\d{4}\.\d{4,5}v?\d*)\.pdf'       # PDF version
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                arxiv_id_full = match.group(1)
                # Extract base Arxiv ID without version if not required
                if not include_version:
                    arxiv_id_base = re.match(r'(\d{4}\.\d{4,5})', arxiv_id_full).group(1)
                    return arxiv_id_base
                return arxiv_id_full
        return None

    def fetch_arxiv_page(self, arxiv_id, work=False):
        # Define a list of URL patterns to try
        url_patterns = [
            f"https://arxiv.org/html/{arxiv_id}v{{version}}"
            f"https://browse.arxiv.org/html/{arxiv_id}v{{version}}",
        ]

        # Try fetching from each URL pattern, iterating through versions if necessary
        for version in range(1, 3):  # Assuming you want to check versions 1 and 2; adjust range as needed
            for pattern in url_patterns:
                url = pattern.format(version=version)
                try:
                    if work:
                        response = requests.get(url, verify="/Users/jeremymiller/Desktop/Zscaler Root CA.pem")
                    else:
                        response = requests.get(url)
                except Exception as e:
                    print(f"Error getting arxiv html: {e}")
                if response and response.status_code == 200:
                    return response.text
        return None  # Return None if none of the URLs work

    def parse_html(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        sections = {}

        # Extract title from <h1>
        title = soup.find('h1')
        if title:
            sections["Title"] = self.clean_text(title.get_text(strip=True))

        # Extract abstract
        abstract_div = soup.find('div', class_='ltx_abstract')
        if abstract_div:
            abstract = abstract_div.find('p')
            if abstract:
                sections["Abstract"] = self.clean_text(abstract.get_text(strip=True))

        # Extract sections from <h2>
        for heading in soup.find_all('h2', class_='ltx_title ltx_title_section'):
            # Removing any <span> elements (like section numbers) from the heading
            for span in heading.find_all('span', class_='ltx_tag ltx_tag_section'):
                span.decompose()
            section_name = self.clean_text(heading.get_text(strip=True))

            # Extracting content under the section
            content = []
            for sibling in heading.find_next_siblings():
                if sibling.name == 'h2':
                    break
                content.append(self.clean_text(sibling.get_text(strip=True)))
            sections[section_name] = ' '.join(content)

        return sections

    def get_arxiv_content_old_version(self, url, work=False):
        if '/pdf/' in url:
            # If the URL is a PDF link, construct the corresponding abstract link
            url = url.replace('/pdf/', '/abs/', 1).replace('.pdf', '', 1)
        if work:
            response = requests.get(url, verify="/Users/jeremymiller/Desktop/Zscaler Root CA.pem")
        else:
            response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h1', class_='title mathjax').text.strip()
        abstract = soup.find('blockquote', class_='abstract mathjax').text.strip()
        content = f'{title}\n\n{abstract}'

        # Remove all empty lines from the content
        content = '\n'.join([line for line in content.split('\n') if line.strip()])

        return content

    # Function to clean text by removing non-tokenizable characters
    def clean_text(self, text):
        # Replace non-tokenizable characters with an empty string
        cleaned_text = re.sub(r'[^\x00-\x7F]+', '', text)
        # Remove LaTeX equations
        cleaned_text = self.remove_latex_equations(cleaned_text)
        # Remove complex LaTeX-like expressions
        cleaned_text = self.remove_complex_latex(cleaned_text)
        return cleaned_text

    def remove_latex_equations(self, text):
        # Pattern to match common LaTeX equation delimiters and commands
        # Adjust the pattern as needed to cover more cases
        pattern = r'\\(?:begin\{[a-z]*\}|end\{[a-z]*\}|[a-zA-Z]+\{.*?\}|[a-zA-Z]+)'
        clean_text = re.sub(pattern, '', text)

        # Additional cleanup for orphaned markers or commands
        clean_text = re.sub(r'\\[a-zA-Z]+', '', clean_text)
        clean_text = re.sub(r'\{|\}', '', clean_text)

        return clean_text

    def remove_complex_latex(self, text):
        # Attempt to catch complex LaTeX-like expressions by looking for extended patterns
        # This pattern is an attempt to match more complex mathematical expressions
        # Adjust and expand upon these patterns based on observed structures in your text
        patterns = [
            r'\([^\)]*\)',  # Attempt to catch expressions enclosed in parentheses
            r'\[[^\]]*\]',  # Attempt to catch expressions enclosed in brackets
            r'\\[a-zA-Z]+\[[^\]]*\]',  # Catch LaTeX commands that might use brackets
            r'\\[a-zA-Z]+',  # Catch standalone LaTeX commands
            r'\{[^\}]*\}',  # Attempt to catch expressions enclosed in curly braces
            r'[a-zA-Z]\[[^\]]*\]',  # Catch expressions like X[...]
            r'\^[^\s]+',  # Catch superscript expressions
            r'_\{[^\}]*\}',  # Catch subscript expressions
            r'bold_[a-zA-Z]',  # Specific patterns observed in your example
            r'italic_[a-zA-Z]',
            r'fraktur_[a-zA-Z]',
            r'over\^[^\s]+',  # Catch over^ expressions
            r'start_[A-Z]+',  # Catch start_ expressions
            r'end_[A-Z]+'  # Catch end_ expressions
        ]

        clean_text = text
        for pattern in patterns:
            clean_text = re.sub(pattern, '', clean_text)

        # Additional cleanup for leftover markers or nonsensical sequences
        clean_text = re.sub(r'[\{\}\[\]\(\)]', '', clean_text)  # Remove leftover braces, brackets, parentheses
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()  # Remove extra spaces

        return clean_text
