# src/knowledge_base/routes/ui.py
# Main FastHTML route handlers for the Knowledge Base UI (retro terminal)

from fasthtml.common import fast_app, serve, Style, Div, Html, Head, Title, Link, Body
import requests
import os
import logging
from datetime import datetime
from src.knowledge_base.ui.components import (
    MainLayout,
    TerminalContainer,
    TerminalSearchBar,
    TerminalResultsList,
    TerminalArticleView,
    TerminalNavControls,
    TerminalSuggestionBox,
    TerminalFilterControls,
    HomeButton,
)
from src.knowledge_base.core.content_manager import ContentManager

app, rt = fast_app()

# Initialize logger and ContentManager
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Initialize ContentManager with database connection
db_connection_string = os.getenv('DB_CONN_STRING')
content_manager = ContentManager(logger, db_connection_string) if db_connection_string else None

# Demo data for articles (fallback)
ARTICLES = [
    {
        "id": 1,
        "title": "How to Use the Knowledge Base",
        "author": "Jane Doe",
        "date": "2025-06-10",
        "tags": ["guide", "intro"],
        "content": (
            "Welcome to the retro Knowledge Base! Use the search bar above to "
            "find articles."
        ),
    },
    {
        "id": 2,
        "title": "80s Terminal UI Design",
        "author": "John Smith",
        "date": "2025-06-09",
        "tags": ["design", "retro"],
        "content": (
            "This article explains how to create a retro terminal UI using "
            "FastHTML."
        ),
    },
]


@rt
def index():
    search_bar = TerminalSearchBar(placeholder="Search articles...")
    
    # Try to get recent articles using ContentManager
    if content_manager:
        try:
            recent_results = content_manager.get_recent_content(limit=5)
            articles_data = [
                {
                    "id": result["id"],
                    "title": result.get("url", "Untitled"),
                    "snippet": result.get("summary", result.get("content", ""))[:60]
                }
                for result in recent_results
            ]
        except Exception as e:
            logger.error(f"Error getting recent content with ContentManager: {e}")
            # Fallback to API
            try:
                api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
                search_url = f"{api_base_url}/content/search/"
                response = requests.get(search_url, params={"query": "", "limit": 5})
                
                if response.status_code == 200:
                    search_results = response.json()
                    articles_data = [
                        {
                            "id": result["id"],
                            "title": result.get("url", "Untitled"),
                            "snippet": result.get("summary", result.get("content", ""))[:60]
                        }
                        for result in search_results
                    ]
                else:
                    articles_data = [
                        {
                            "id": a["id"],
                            "title": a["title"],
                            "snippet": a["content"][:60]
                        }
                        for a in ARTICLES

                    ]
            except Exception:
                # Final fallback to demo data
                articles_data = [
                    {
                        "id": a["id"],
                        "title": a["title"],
                        "snippet": a["content"][:60]
                    }
                    for a in ARTICLES
                ]
    else:
        # No ContentManager, try API directly
        try:
            api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
            search_url = f"{api_base_url}/content/search/"
            response = requests.get(search_url, params={"query": "", "limit": 5})
            
            if response.status_code == 200:
                search_results = response.json()
                articles_data = [
                    {
                        "id": result["id"],
                        "title": result.get("url", "Untitled"),
                        "snippet": result.get("summary", result.get("content", ""))[:60]
                    }
                    for result in search_results
                ]
            else:
                articles_data = [
                    {
                        "id": a["id"],
                        "title": a["title"],
                        "snippet": a["content"][:60]
                    }
                    for a in ARTICLES
                ]
        except Exception:
            # Fallback to demo data
            articles_data = [
                {
                    "id": a["id"],
                    "title": a["title"],
                    "snippet": a["content"][:60]
                }
                for a in ARTICLES
            ]
    
    results = TerminalResultsList(articles_data)
    layout = MainLayout(
        "KNOWLEDGE BASE",
        search_bar,
        results,
        TerminalSuggestionBox(["Try searching for 'retro' or 'guide'."]),
    )
    return Html(
        Head(
            Title("Knowledge Base - Retro Terminal UI"),
            Link(rel="stylesheet", href="/static/styles/retro_terminal.css"),
        ),
        Body(
            layout,
            cls="retro-bg"
        )
    )


@rt('/article/{article_id:int}')
def article_view(article_id: int):
    # Try to fetch article using ContentManager first
    article = None
    if content_manager:
        try:
            # Search for the specific article by ID
            # Since we don't have a direct get_by_id method, we can search and filter
            all_results = content_manager.db.search_content({}, limit=1000)  # Get all to find by ID
            article_data = next((result for result in all_results if result["id"] == article_id), None)
            
            if article_data:
                article = {
                    "id": article_data["id"],
                    "title": article_data.get("url", "Untitled"),
                    "author": "System",  
                    "date": datetime.fromtimestamp(article_data.get("timestamp", 0)).strftime('%Y-%m-%d') if article_data.get("timestamp") else "Unknown",
                    "tags": article_data.get("keywords", []),
                    "content": article_data.get("summary", article_data.get("content", ""))
                }
        except Exception as e:
            logger.error(f"Error getting article with ContentManager: {e}")
    
    # Fallback to API if ContentManager failed or not available
    if not article:
        try:
            api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
            article_url = f"{api_base_url}/content/{article_id}"
            
            response = requests.get(article_url)
            
            if response.status_code == 200:
                article_data = response.json()
                # Convert database article to display format
                article = {
                    "id": article_data["id"],
                    "title": article_data.get("url", "Untitled"),
                    "author": "System",  
                    "date": datetime.fromtimestamp(article_data.get("timestamp", 0)).strftime('%Y-%m-%d') if article_data.get("timestamp") else "Unknown",
                    "tags": article_data.get("keywords", []),
                    "content": article_data.get("summary", article_data.get("content", ""))
                }
            else:
                article = None
        except Exception as e:
            logger.error(f"Error getting article via API: {e}")
            article = None
    
    if not article:
        return Html(
            Head(Title("Not found")),
            Body(MainLayout("ERROR", Div("Article not found")))
        )
    article_content = TerminalArticleView(
        title=article["title"],
        meta={
            "author": article["author"],
            "date": article["date"],
            "tags": article["tags"]
        },
        content=article["content"],
        back_url="/"
    )
    layout = MainLayout(
        "ARTICLE VIEW",
        article_content,
        TerminalSuggestionBox(["Related: 80s Terminal UI Design"]),
    )
    return Html(
        Head(
            Title(article["title"]),
            Link(rel="stylesheet", href="/static/styles/retro_terminal.css"),
        ),
        Body(
            layout,
            cls="retro-bg"
        )
    )


@rt('/search')
def search_page(
    query: str = "",
    content_type: str = "",
    keywords: str = "",
    date_from: str = "",
    date_to: str = ""
):
    search_bar = TerminalSearchBar(placeholder="Search articles...", value=query)
    
    # Handle "All Types" selection - convert to empty string for search
    if content_type == "All Types" or content_type == "__all__":
        content_type = ""
    
    # Parse keywords from comma-separated string
    keyword_list = [keyword.strip() for keyword in keywords.split(',') if keyword.strip()] if keywords else []
    
    # Convert date strings to timestamps if provided
    timestamp_from = None
    timestamp_to = None
    if date_from:
        try:
            dt = datetime.strptime(date_from, '%Y-%m-%d')
            timestamp_from = int(dt.timestamp())
        except ValueError:
            logger.warning(f"Invalid date_from format: {date_from}")
    if date_to:
        try:
            dt = datetime.strptime(date_to + ' 23:59:59', '%Y-%m-%d %H:%M:%S')
            timestamp_to = int(dt.timestamp())
        except ValueError:
            logger.warning(f"Invalid date_to format: {date_to}")
    
    # Create filter controls
    filter_controls = TerminalFilterControls(
        query=query,
        selected_tags=keyword_list,
        selected_type=content_type,
        date_from=date_from,
        date_to=date_to
    )
    
    # Use ContentManager for search if available
    if content_manager:
        try:
            # Build search parameters
            search_kwargs = {"limit": 20}
            if query:
                search_kwargs["text_query"] = query
            if keyword_list:
                search_kwargs["keywords"] = keyword_list
            if content_type:
                search_kwargs["content_type"] = content_type
            
            # Use ContentManager to search content with filters
            search_results = content_manager.search_content(**search_kwargs)
            
            # Filter by date range if specified (post-filter since ContentManager doesn't support date filtering)
            if timestamp_from or timestamp_to:
                filtered_results = []
                for result in search_results:
                    result_timestamp = result.get("timestamp", 0)
                    if timestamp_from and result_timestamp < timestamp_from:
                        continue
                    if timestamp_to and result_timestamp > timestamp_to:
                        continue
                    filtered_results.append(result)
                search_results = filtered_results
            
            filtered_articles = [
                {
                    "id": result["id"],
                    "title": result.get("url", "Untitled"),  # Use URL as title if no title field
                    "content": result.get("summary", result.get("content", ""))[:200]
                }
                for result in search_results
            ]
        except Exception as e:
            logger.error(f"Error using ContentManager for search: {e}")
            # Fallback to API call
            try:
                api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
                search_url = f"{api_base_url}/content/search/"
                params = {"limit": 20}
                if query:
                    params["query"] = query
                response = requests.get(search_url, params=params)
                
                if response.status_code == 200:
                    search_results = response.json()
                    
                    # Apply client-side filtering for API results
                    filtered_results = search_results
                    if content_type:
                        filtered_results = [r for r in filtered_results if r.get("type") == content_type]
                    if keyword_list:
                        filtered_results = [
                            r for r in filtered_results 
                            if any(keyword.lower() == k.lower() for k in r.get("keywords", []) for keyword in keyword_list)
                        ]
                    if timestamp_from or timestamp_to:
                        filtered_results = [
                            r for r in filtered_results
                            if (not timestamp_from or r.get("timestamp", 0) >= timestamp_from) and
                               (not timestamp_to or r.get("timestamp", 0) <= timestamp_to)
                        ]
                    
                    filtered_articles = [
                        {
                            "id": result["id"],
                            "title": result.get("url", "Untitled"),
                            "content": result.get("summary", result.get("content", ""))[:200]
                        }
                        for result in filtered_results
                    ]
                else:
                    filtered_articles = []
            except Exception as api_e:
                logger.error(f"API fallback also failed: {api_e}")
                # Final fallback to demo data with filtering
                filtered_articles = ARTICLES
                if query:
                    filtered_articles = [
                        a for a in filtered_articles 
                        if query.lower() in a["title"].lower() 
                        or query.lower() in a["content"].lower()
                        or any(query.lower() in tag.lower() for tag in a["tags"])
                    ]
                if content_type:
                    filtered_articles = [a for a in filtered_articles if a.get("type") == content_type]
                if keyword_list:
                    filtered_articles = [
                        a for a in filtered_articles 
                        if any(keyword.lower() == t.lower() for t in a.get("tags", []) for keyword in keyword_list)
                    ]
    else:
        # No ContentManager available, try API directly
        try:
            api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
            search_url = f"{api_base_url}/content/search/"
            params = {"limit": 20}
            if query:
                params["query"] = query
            response = requests.get(search_url, params=params)
            
            if response.status_code == 200:
                search_results = response.json()
                
                # Apply client-side filtering for API results
                filtered_results = search_results
                if content_type:
                    filtered_results = [r for r in filtered_results if r.get("type") == content_type]
                if keyword_list:
                    filtered_results = [
                        r for r in filtered_results 
                        if any(keyword.lower() == k.lower() for k in r.get("keywords", []) for keyword in keyword_list)
                    ]
                if timestamp_from or timestamp_to:
                    filtered_results = [
                        r for r in filtered_results
                        if (not timestamp_from or r.get("timestamp", 0) >= timestamp_from) and
                           (not timestamp_to or r.get("timestamp", 0) <= timestamp_to)
                    ]
                
                filtered_articles = [
                    {
                        "id": result["id"],
                        "title": result.get("url", "Untitled"),
                        "content": result.get("summary", result.get("content", ""))[:200]
                    }
                    for result in filtered_results
                ]
            else:
                filtered_articles = []
        except Exception as e:
            logger.error(f"API search failed: {e}")
            # Fallback to demo data with filtering
            filtered_articles = ARTICLES
            if query:
                filtered_articles = [
                    a for a in filtered_articles 
                    if query.lower() in a["title"].lower() 
                    or query.lower() in a["content"].lower()
                    or any(query.lower() in tag.lower() for tag in a["tags"])
                ]
            if content_type:
                filtered_articles = [a for a in filtered_articles if a.get("type") == content_type]
            if keyword_list:
                filtered_articles = [
                    a for a in filtered_articles 
                    if any(keyword.lower() == t.lower() for t in a.get("tags", []) for keyword in keyword_list)
                ]
    
    results = TerminalResultsList([
        {
            "id": a["id"],
            "title": a["title"],
            "snippet": a["content"][:60] + "..." if len(a["content"]) > 60 else a["content"]
        }
        for a in filtered_articles
    ])
    
    # Create suggestions based on filters and results
    suggestions = []
    filter_applied = bool(query or content_type or keyword_list or date_from or date_to)
    if filter_applied:
        filter_parts = []
        if query:
            filter_parts.append(f"text: '{query}'")
        if content_type:
            filter_parts.append(f"type: {content_type}")
        if keyword_list:
            filter_parts.append(f"keywords: {', '.join(keyword_list)}")
        if date_from or date_to:
            date_range = f"{date_from or 'any'} to {date_to or 'any'}"
            filter_parts.append(f"dates: {date_range}")
        
        suggestions.append(f"Found {len(filtered_articles)} result(s) with filters: {'; '.join(filter_parts)}")
    else:
        suggestions.append("Use filters below to narrow your search or try searching for 'retro' or 'guide'.")
    
    layout = MainLayout(
        "SEARCH RESULTS",
        search_bar,
        filter_controls,
        results,
        TerminalSuggestionBox(suggestions),
    )
    
    return Html(
        Head(
            Title("Search - Knowledge Base"),
            Link(rel="stylesheet", href="/static/styles/retro_terminal.css"),
        ),
        Body(
            layout,
            cls="retro-bg"
        )
    )


@rt('/ui')
def ui_index():
    return index()


router = app

if __name__ == "__main__":
    serve()
