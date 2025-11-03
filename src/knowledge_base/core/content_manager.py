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
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Dict, List, Any, Optional
from ..storage.database import Database


class ContentManager():
    def __init__(self, logger, db_connection_string=None):
        self.logger = logger
        self.db = Database(connection_string=db_connection_string, logger=logger) if db_connection_string else None

    def get_file_path(self, url, force_general=False):
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

        if not force_general:
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

        # if none of the above prefixes are detected, use general prefix
        if force_general or prefix == '':
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

    # def create_obsidian_note(self, json_file_path, output_directory):
    #     self.logger.debug(f"Creating Obsidian note from JSON file: {json_file_path}")
    #     with open(json_file_path, 'r') as file:
    #         doc_data = json.load(file)
    #     self.logger.debug(f"Loaded JSON data: {doc_data}")

    #     url = doc_data.get('url', '')
    #     filename = urlparse(url).path.split('/')[-1]
    #     if not filename:
    #         filename = url.replace('://', '_').replace('/', '_')
    #     filename = filename.strip() + '.md'
    #     self.logger.debug(f"Filename created: {filename}")

    #     content = "---\n"
    #     content += f"url: {url}\n"
    #     content += f"type: {doc_data.get('type', '')}\n"
    #     content += "tags:\n"
    #     content += " - literature-note\n"
    #     for keyword in doc_data.get('keywords', []):
    #         content += f" - {keyword}\n"
    #     content += "---\n\n"
    #     content += doc_data.get('obsidian_markdown', '')
    #     self.logger.debug(f"Obsidian note content created: {content}")

    #     os.makedirs(output_directory, exist_ok=True)
    #     self.logger.debug(f"Output directory created: {output_directory}")

    #     output_path = os.path.join(output_directory, filename)
    #     with open(output_path, 'w') as file:
    #         file.write(content)
    #     self.logger.debug(f"Obsidian note saved: {output_path}")

    #     self.logger.info(f"Obsidian note created: {output_path}")
    #     return

    def _standardize_title_for_obsidian(self, title: str, max_length: int = 80) -> str:
        """
        Standardizes a title for Obsidian note filenames and H1 headers.
        - Replaces dashes and underscores with spaces.
        - Removes most non-alphanumeric characters (keeps spaces).
        - Collapses multiple spaces to one.
        - Strips leading/trailing spaces.
        - Limits length.
        """
        if not title:
            return "Untitled Note"

        # Replace dashes and underscores with spaces
        title = title.replace('-', ' ').replace('_', ' ')
        
        # Keep alphanumeric characters and spaces, remove others
        # This also handles many common URL-encoded chars like %20 (becomes space then cleaned)
        title = re.sub(r'[^\w\s]', '', title)
        
        # Collapse multiple spaces to a single space
        title = re.sub(r'\s+', ' ', title).strip()
        
        # Limit length
        if len(title) > max_length:
            title = title[:max_length].strip()
            # Try to cut at a word boundary if possible
            if ' ' in title and len(title) == max_length: # Check if it was exactly max_length before potential rfind
                last_space = title.rfind(' ')
                if last_space > max_length / 2: # Only cut if it doesn't make the title too short
                    title = title[:last_space]

        if not title: # If all characters were removed or title became empty after truncation
            return "Untitled Note"
            
        return title.strip()

    def create_obsidian_note(self, json_file_path, output_directory):
        self.logger.debug(f"Creating Obsidian note from JSON file: {json_file_path}")

        # Check if the file exists before trying to open it
        if not os.path.exists(json_file_path):
            self.logger.error(f"JSON file does not exist: {json_file_path}")
            raise FileNotFoundError(f"JSON file not found: {json_file_path}")

        with open(json_file_path, 'r') as file:
            doc_data = json.load(file)
        self.logger.debug(f"Loaded JSON data: {doc_data}")

        url = doc_data.get('url', '')
        obsidian_markdown_content = doc_data.get('obsidian_markdown', '')
        
        # Attempt to extract title from H1 in markdown content
        h1_title = None
        if obsidian_markdown_content:
            lines = obsidian_markdown_content.split('\n', 1)
            if lines and lines[0].startswith('# '):
                h1_title = lines[0][2:].strip() # Get text after '# '
        
        base_title_for_filename = "Untitled" # Default
        if h1_title:
            base_title_for_filename = h1_title
            self.logger.debug(f"Using H1 title from markdown content: '{h1_title}'")
        elif url:
            # Fallback to URL parsing if no H1 title
            # Try to get a meaningful part from the URL path
            parsed_url = urlparse(url)
            path_parts = [part for part in parsed_url.path.split('/') if part]
            if path_parts:
                # Use the last non-numeric part of the path, or the last part if all are numeric/single
                # This is a heuristic to get a more meaningful title than just an ID
                name_part = path_parts[-1]
                # If it looks like a common file extension (e.g., .html, .pdf), remove it
                name_part, _ = os.path.splitext(name_part)
                if len(path_parts) > 1 and name_part.isdigit(): # If last part is just an ID, try parent
                    parent_part = path_parts[-2]
                    parent_part, _ = os.path.splitext(parent_part)
                    if not parent_part.isdigit():  # Don't use if parent is also just an ID
                        base_title_for_filename = parent_part
                    else:
                        base_title_for_filename = name_part  # Fallback to the ID-like part
                else:
                    base_title_for_filename = name_part
            elif parsed_url.netloc: # If no path, use domain (sanitized)
                base_title_for_filename = parsed_url.netloc.replace('www.', '')
            self.logger.debug(f"Using URL-derived base title: '{base_title_for_filename}'")
        
        standardized_title = self._standardize_title_for_obsidian(base_title_for_filename)
        filename = standardized_title + '.md'
        self.logger.debug(f"Standardized filename created: {filename}")

        # Prepare note content with standardized H1 title
        # If H1 was extracted, the obsidian_markdown_content already has it.
        # If not, we prepend the new standardized_title as H1.
        final_obsidian_content = obsidian_markdown_content
        if not h1_title: # Only add H1 if it wasn't already there
            final_obsidian_content = f"# {standardized_title}\n\n{obsidian_markdown_content}"
        elif h1_title != standardized_title: # If H1 existed but was different after standardization
            # Replace original H1 with standardized one
            lines = obsidian_markdown_content.split('\n', 1)
            if len(lines) > 1:
                final_obsidian_content = f"# {standardized_title}\n{lines[1]}"
            else: # Only H1 line existed
                final_obsidian_content = f"# {standardized_title}"

        content_header = "---\n"
        content_header += f"url: {url}\n"
        content_header += f"type: {doc_data.get('type', '')}\n"
        content_header += "tags:\n"
        content_header += " - literature-note\n" # Default tag
        # Add standardized title as a tag/alias for easier linking if needed
        content_header += f" - {standardized_title.replace(' ', '-')}\n" 
        for keyword in doc_data.get('keywords', []):
            # Sanitize keywords for tags (Obsidian tags don't like spaces)
            tag_keyword = keyword.replace(' ', '-').replace('_', '-')
            content_header += f" - {tag_keyword}\n"
        content_header += "---\n\n"
        
        final_content_for_file = content_header + final_obsidian_content
        self.logger.debug(f"Final Obsidian note content prepared.")

        os.makedirs(output_directory, exist_ok=True)
        self.logger.debug(f"Output directory verified/created: {output_directory}")

        output_path = os.path.join(output_directory, filename)
        with open(output_path, 'w') as file:
            file.write(final_content_for_file)
        self.logger.debug(f"Obsidian note saved: {output_path}")

        self.logger.info(f"Obsidian note created: {output_path} with title '{standardized_title}'")
        return

    def clean_url(self, url: str) -> str:
        if url.startswith('!wget'):
            url = url.split(' ', 1)[1].strip()
        else:
            url = url.split(' ', 1)[0].strip()
        
        # Strip UTM parameters and other tracking parameters
        parsed = urlparse(url)
        if parsed.query:
            # Remove tracking parameters
            tracking_params = {
                'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                'fbclid', 'gclid', 'msclkid', 'twclid', 'igshid', 'ref', 'referrer'
            }
            
            query_params = parse_qs(parsed.query, keep_blank_values=True)
            cleaned_params = {k: v for k, v in query_params.items() 
                            if k.lower() not in tracking_params}
            
            # Reconstruct URL without tracking parameters
            cleaned_query = urlencode(cleaned_params, doseq=True) if cleaned_params else ''
            url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, 
                            parsed.params, cleaned_query, parsed.fragment))
        
        return url

    def jinafy_url(self, url: str) -> tuple[str, str]:
        """Use Jina to process URL if cannot process; useful for pdfs
        
        Returns:
            tuple: (original_url, jina_processed_url)
        """
        jina_url = f"https://r.jina.ai/{url}"
        return (url, jina_url)

    def search_content(
        self, 
        text_query: str = "",
        keywords: List[str] = None,
        content_type: str = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for content using full-text search and keyword matching.
        
        Args:
            text_query: Text to search for in content and summaries
            keywords: List of keywords to match
            content_type: Filter by content type (github, arxiv, etc.)
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        if not self.db:
            self.logger.error("Database not initialized. Cannot perform search.")
            return []
        
        try:
            # Build search query parameters
            query_params = {}
            
            # Add full-text search if query provided
            if text_query and text_query.strip():
                # Convert text query to PostgreSQL tsquery format
                # Remove special characters and join with &
                clean_query = re.sub(r'[^\w\s]', ' ', text_query.strip())
                query_terms = [term for term in clean_query.split() if term]
                if query_terms:
                    query_params['text_search'] = ' & '.join(query_terms)
            
            # Add keyword search if keywords provided
            if keywords:
                query_params['keywords'] = keywords
            
            # Add content type filter
            if content_type:
                query_params['type'] = content_type
            
            self.logger.debug(f"Searching with parameters: {query_params}")
            results = self.db.search_content(query_params, limit=limit)
            
            self.logger.info(f"Found {len(results)} results for search")
            return results
            
        except Exception as e:
            self.logger.error(f"Error during content search: {e}")
            return []

    def search_by_keywords(self, keywords: List[str], limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for content by keywords only.
        
        Args:
            keywords: List of keywords to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        return self.search_content(keywords=keywords, limit=limit)

    def search_by_text(self, text_query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for content by full-text search only.
        
        Args:
            text_query: Text to search for
            limit: Maximum number of results to return
            
        Returns:
            List of matching documents
        """
        return self.search_content(text_query=text_query, limit=limit)

    def get_recent_content(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recently added content.
        
        Args:
            limit: Maximum number of results to return
            
        Returns:
            List of recent documents
        """
        if not self.db:
            self.logger.error("Database not initialized. Cannot get recent content.")
            return []
        
        try:
            # Search with empty criteria to get all content, ordered by timestamp
            results = self.db.search_content({}, limit=limit)
            # Sort by timestamp descending to get most recent first
            results.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            return results
        except Exception as e:
            self.logger.error(f"Error getting recent content: {e}")
            return []

    def find_related_articles(self, article_id: int, keywords: List[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find articles related to a given article, sorted by match strength.
        
        Args:
            article_id: ID of the current article to find relations for
            keywords: Optional list of keywords to search for. If not provided, will use the article's keywords
            limit: Maximum number of related articles to return
            
        Returns:
            List of related articles with match strength scores
        """
        if not self.db:
            self.logger.error("Database not initialized. Cannot find related articles.")
            return []
        
        try:
            # First, get the current article to extract its keywords if none provided
            if not keywords:
                all_results = self.db.search_content({}, limit=1000)
                current_article = next((result for result in all_results if result["id"] == article_id), None)
                if not current_article:
                    self.logger.error(f"Article with ID {article_id} not found")
                    return []
                keywords = current_article.get("keywords", [])
            
            if not keywords:
                self.logger.warning(f"No keywords found for article {article_id}")
                return []
            
            # Search for articles containing these keywords
            related_results = self.search_content(keywords=keywords, limit=limit * 3)  # Get more to score and filter
            
            # Filter out the current article
            related_results = [article for article in related_results if article["id"] != article_id]
            
            # Calculate match strength for each related article
            scored_articles = []
            for article in related_results:
                article_keywords = article.get("keywords", [])
                match_score = self._calculate_match_strength(keywords, article_keywords)
                
                # Add the match score to the article data
                article_with_score = article.copy()
                article_with_score["match_score"] = match_score
                scored_articles.append(article_with_score)
            
            # Sort by match strength (highest first) and limit results
            scored_articles.sort(key=lambda x: x["match_score"], reverse=True)
            
            self.logger.info(f"Found {len(scored_articles[:limit])} related articles for article {article_id}")
            return scored_articles[:limit]
            
        except Exception as e:
            self.logger.error(f"Error finding related articles: {e}")
            return []

    def _calculate_match_strength(self, source_keywords: List[str], target_keywords: List[str]) -> float:
        """
        Calculate match strength between two sets of keywords.
        
        Args:
            source_keywords: Keywords from the source article
            target_keywords: Keywords from the target article
            
        Returns:
            Match strength score (0.0 to 1.0)
        """
        if not source_keywords or not target_keywords:
            return 0.0
        
        # Convert to lowercase for case-insensitive comparison
        source_set = set(keyword.lower().strip() for keyword in source_keywords)
        target_set = set(keyword.lower().strip() for keyword in target_keywords)
        
        # Calculate Jaccard similarity (intersection over union)
        intersection = len(source_set.intersection(target_set))
        union = len(source_set.union(target_set))
        
        if union == 0:
            return 0.0
        
        jaccard_similarity = intersection / union
        
        # Boost score based on number of exact matches
        exact_matches = intersection
        match_boost = min(exact_matches * 0.1, 0.5)  # Up to 0.5 boost for many matches
        
        # Final score combining similarity and match boost
        final_score = min(jaccard_similarity + match_boost, 1.0)
        
        return final_score
