"""Content management module for handling file operations in knowledge base.

NOTE: Manages acquiring content from web sources, creating raw JSON data,
 and Obsidian notes, NOT database operations.

It includes features for:
- Generating file paths based on URLs and content types
- Saving content with metadata to JSON files
- Creating Obsidian-compatible markdown notes
- Managing file organization and indexing
The ContentManager class handles:
- File path generation with timestamps
- Content type detection (GitHub, arXiv, YouTube, etc.)
- JSON content storage with metadata
- Index file management
- Obsidian note creation from JSON data
Dependencies:
    os: File and directory operations
    sys: System-specific parameters and functions
    time: Time-related functions
    json: JSON data encoding/decoding
    re: Regular expression operations
    urllib.parse: URL parsing utilities
"""

import os
import sys
import time
import json
import re
from urllib.parse import urlparse


class ContentManager():
    def __init__(self, logger):
        self.logger = logger

    def get_file_path(self, url):
        self.logger.debug(f"Creating file path for URL: {url}")
        time_now = time.time()
        date_time = time.localtime(time_now)
        year, month, day = (
            str(date_time.tm_year),
            str(date_time.tm_mon).zfill(2),
            str(date_time.tm_mday).zfill(2)
        )
        path = f"{os.getenv('DSV_KB_PATH')}/{year}-{month}-{day}"
        self.logger.debug(f"Checking if directory exists: {path}")

        try:
            os.makedirs(path, exist_ok=True)

        except Exception as e:
            self.logger.error(f"An exception occurred while create a required directory: {e}")
            self.logger.error("Please create this directory manually before running the script.")
            self.logger.error("You can do this by running this command in Terminal:")
            self.logger.error(f"mkdir -p {path}")
            sys.exit(1)

        prefix = ''
        youtube_regex = (
            r'(https?://)?(www\.)?'
            '(youtube|youtu|youtube-nocookie)\.(com|be)/'
            '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
        huggingface_regex = (r'https?:\/\/huggingface\.co\/([^\/]+\/[^\/]+)')
        self.logger.debug(f"Checking URL for prefix: {url}")

        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url

        if 'github.com' in url and 'ipynb' not in url:
            prefix = 'github'
            parts = url.split('/')
            username = parts[3]
            repo_name = parts[4]
            file_name = f'{prefix}_{username}_{repo_name}'

        elif 'github.com' in url and 'ipynb' in url:
            prefix = 'github_ipynb'
            parts = url.split('/')
            username = parts[3]
            repo_name = parts[4]
            ipynb_file_name = parts[-1].replace('.ipynb', '')
            file_name = f'{prefix}_{username}_{repo_name}_{ipynb_file_name}_ipynb'

        elif 'arxiv.org' in url:
            prefix = 'arxiv'
            parts = url.split('/')
            arxiv_id = parts[-1]
            file_name = f'{prefix}_{arxiv_id}'

        elif 'mp.weixin.qq.com' in url:
            prefix = re.findall('/s/([^/]+)', url)[0]
            file_name = f'{prefix}'

        elif re.match(youtube_regex, url):
            prefix = 'youtube'
            youtube_id = re.match(youtube_regex, url).group(6)
            file_name = f'{prefix}_{youtube_id}'

        elif re.match(huggingface_regex, url):
            prefix = 'huggingface'
            huggingface_id = re.match(
                huggingface_regex, url
                ).group(1).replace('/', '_')
            file_name = f'{prefix}_{huggingface_id}'

        else:
            file_name = re.sub('[^0-9a-zA-Z]+', '', url)
            if len(file_name) > 100:
                file_name = file_name[:100]
        file_name += '_' + str(int(time_now)) + '.json'

        self.logger.debug(f"File path created: {path}/{file_name}")

        file_type = prefix
        if file_type not in ('github', 'arxiv', 'youtube',
                             'huggingface', 'github_ipynb'):
            file_type = 'general'

        self.logger.debug(f"File type detected: {file_type}")
        return (file_type, f'{path}/{file_name}', str(int(time_now)), url)

    def save_content(self, file_type, file_path, timestamp, content, url, summary,
                     keywords, embeddings, obsidian_markdown):
        
        self.logger.debug(f"Saving content to file: {file_path}")
        content_dict = {
            'url': url,
            'type': file_type,  # 'github', 'arxiv', 'general
            'timestamp': timestamp,
            'content': content,
            'summary': summary,
            'keywords': keywords,
            'embeddings': embeddings,
            'obsidian_markdown': obsidian_markdown,
        }
        self.logger.debug(f"Content dictionary created: {content_dict}")
        with open(file_path, 'w') as file:
            json.dump(content_dict, file, indent=4)
        self.logger.debug(f"Content saved to file: {file_path}")

        with open(f"{os.getenv('DSV_KB_PATH')}/index.csv", 'a') as index_file:
            index_file.write(f'{file_type},{timestamp},{file_path}\n')
        self.logger.debug(f"File path added to index: {file_path}")

        return

    def create_obsidian_note(self, json_file_path, output_directory):
        self.logger.debug(f"Creating Obsidian note from JSON file: {json_file_path}")
        with open(json_file_path, 'r') as file:
            doc_data = json.load(file)
        self.logger.debug(f"Loaded JSON data: {doc_data}")

        url = doc_data.get('url', '')
        filename = urlparse(url).path.split('/')[-1]
        if not filename:
            filename = url.replace('://', '_').replace('/', '_')
        filename = filename.strip() + '.md'
        self.logger.debug(f"Filename created: {filename}")

        content = "---\n"
        content += f"url: {url}\n"
        content += f"type: {doc_data.get('type', '')}\n"
        content += "tags:\n"
        content += " - literature-note\n"
        for keyword in doc_data.get('keywords', []):
            content += f" - {keyword}\n"
        content += "---\n\n"
        content += doc_data.get('obsidian_markdown', '')
        self.logger.debug(f"Obsidian note content created: {content}")

        os.makedirs(output_directory, exist_ok=True)
        self.logger.debug(f"Output directory created: {output_directory}")

        output_path = os.path.join(output_directory, filename)
        with open(output_path, 'w') as file:
            file.write(content)
        self.logger.debug(f"Obsidian note saved: {output_path}")

        self.logger.info(f"Obsidian note created: {output_path}")
        return
    
    def clean_url(self, url: str) -> str:
        if url.startswith('!wget'):
            return url.split(' ', 1)[1].strip()
        return url.split(' ', 1)[0].strip()

    def jinafy_url(self, url: str) -> str:
        """Use Jina to process URL if cannot process; useful for pdfs"""
        return f"https://r.jina.ai/{url}"
