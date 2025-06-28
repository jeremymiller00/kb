# src/knowledge_base/routes/ui.py
# Main FastHTML route handlers for the Knowledge Base UI (retro terminal)

from fasthtml.common import fast_app, serve, Style, Div, Html, Head, Title, Link, Body, Form, RedirectResponse, H3, P, A, Script
import requests
import os
import logging
from datetime import datetime
import asyncio
from typing import Optional
from ..ui.components import (
    MainLayout,
    TerminalContainer,
    TerminalSearchBar,
    TerminalResultsList,
    TerminalArticleView,
    TerminalNavControls,
    TerminalSuggestionBox,
    TerminalFilterControls,
    TerminalUrlProcessor,
    TerminalPaginationControls,
    HomeButton,
)
from ..core.content_manager import ContentManager
from ..extractors.extractor_factory import ExtractorFactory
from ..ai.llm_factory import LLMFactory
from ..storage.database import Database

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
    url_processor = TerminalUrlProcessor()
    
    # Try to get recent articles using ContentManager
    if content_manager:
        try:
            recent_results = content_manager.get_recent_content(limit=5)
            articles_data = [
                {
                    "id": result["id"],
                    "title": result.get("url", "Untitled"),
                    "snippet": result.get("summary", result.get("content", ""))[:100] + ("..." if len(result.get("summary", result.get("content", ""))) > 100 else ""),
                    "type": result.get("type", "unknown")
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
                            "snippet": result.get("summary", result.get("content", ""))[:100] + ("..." if len(result.get("summary", result.get("content", ""))) > 100 else ""),
                            "type": result.get("type", "unknown")
                        }
                        for result in search_results
                    ]
                else:
                    articles_data = [
                        {
                            "id": a["id"],
                            "title": a["title"],
                            "snippet": a["content"][:100] + ("..." if len(a["content"]) > 100 else ""),
                            "type": a.get("type", "demo")
                        }
                        for a in ARTICLES
                    ]
            except Exception:
                # Final fallback to demo data
                articles_data = [
                    {
                        "id": a["id"],
                        "title": a["title"],
                        "snippet": a["content"][:100] + ("..." if len(a["content"]) > 100 else ""),
                        "type": a.get("type", "demo")
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
                        "snippet": result.get("summary", result.get("content", ""))[:100] + ("..." if len(result.get("summary", result.get("content", ""))) > 100 else ""),
                        "type": result.get("type", "unknown")
                    }
                    for result in search_results
                ]
            else:
                articles_data = [
                    {
                        "id": a["id"],
                        "title": a["title"],
                        "snippet": a["content"][:100] + ("..." if len(a["content"]) > 100 else ""),
                        "type": a.get("type", "demo")
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
        url_processor,
        results,
        TerminalSuggestionBox(["Try searching for 'retro' or 'guide', or process a URL above."]),
    )
    return Html(
        Head(
            Title("Knowledge Base - Retro Terminal UI"),
            Link(id="theme-stylesheet", rel="stylesheet", href="/static/styles/retro_terminal.css"),
            Script(src="/static/js/style-toggle.js"),
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
            Link(id="theme-stylesheet", rel="stylesheet", href="/static/styles/retro_terminal.css"),
            Script(src="/static/js/style-toggle.js"),
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
    date_to: str = "",
    page: int = 1
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
    
    # Pagination settings
    page_size = 10
    page = max(1, page)  # Ensure page is at least 1
    offset = (page - 1) * page_size
    total_results = 0
    total_pages = 0
    
    # Use ContentManager for search if available
    if content_manager:
        try:
            # Build search parameters - get more results to handle pagination and count total
            search_kwargs = {"limit": 1000}  # Get many results to count total and paginate
            if query:
                search_kwargs["text_query"] = query
            if keyword_list:
                search_kwargs["keywords"] = keyword_list
            if content_type:
                search_kwargs["content_type"] = content_type
            
            # Use ContentManager to search content with filters
            all_search_results = content_manager.search_content(**search_kwargs)
            
            # Filter by date range if specified (post-filter since ContentManager doesn't support date filtering)
            if timestamp_from or timestamp_to:
                filtered_results = []
                for result in all_search_results:
                    result_timestamp = result.get("timestamp", 0)
                    if timestamp_from and result_timestamp < timestamp_from:
                        continue
                    if timestamp_to and result_timestamp > timestamp_to:
                        continue
                    filtered_results.append(result)
                all_search_results = filtered_results
            
            # Calculate pagination
            total_results = len(all_search_results)
            total_pages = (total_results + page_size - 1) // page_size  # Ceiling division
            
            # Get results for current page
            paginated_results = all_search_results[offset:offset + page_size]
            
            filtered_articles = [
                {
                    "id": result["id"],
                    "title": result.get("url", "Untitled"),  # Use URL as title if no title field
                    "content": result.get("summary", result.get("content", ""))[:200],
                    "type": result.get("type", "unknown"),
                    "snippet": result.get("summary", result.get("content", ""))[:150] + ("..." if len(result.get("summary", result.get("content", ""))) > 150 else "")
                }
                for result in paginated_results
            ]
        except Exception as e:
            logger.error(f"Error using ContentManager for search: {e}")
            # Fallback to API call
            try:
                api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
                search_url = f"{api_base_url}/content/search/"
                params = {"limit": 1000}  # Get many results for pagination
                if query:
                    params["query"] = query
                response = requests.get(search_url, params=params)
                
                if response.status_code == 200:
                    all_results = response.json()
                    
                    # Apply client-side filtering for API results
                    filtered_results = all_results
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
                    
                    # Calculate pagination
                    total_results = len(filtered_results)
                    total_pages = (total_results + page_size - 1) // page_size
                    
                    # Get results for current page
                    paginated_results = filtered_results[offset:offset + page_size]
                    
                    filtered_articles = [
                        {
                            "id": result["id"],
                            "title": result.get("url", "Untitled"),
                            "content": result.get("summary", result.get("content", ""))[:200],
                            "type": result.get("type", "unknown"),
                            "snippet": result.get("summary", result.get("content", ""))[:150] + ("..." if len(result.get("summary", result.get("content", ""))) > 150 else "")
                        }
                        for result in paginated_results
                    ]
                else:
                    filtered_articles = []
                    total_results = 0
                    total_pages = 0
            except Exception as api_e:
                logger.error(f"API fallback also failed: {api_e}")
                # Final fallback to demo data with filtering
                all_articles = ARTICLES
                if query:
                    all_articles = [
                        a for a in all_articles 
                        if query.lower() in a["title"].lower() 
                        or query.lower() in a["content"].lower()
                        or any(query.lower() in tag.lower() for tag in a["tags"])
                    ]
                if content_type:
                    all_articles = [a for a in all_articles if a.get("type") == content_type]
                if keyword_list:
                    all_articles = [
                        a for a in all_articles 
                        if any(keyword.lower() == t.lower() for t in a.get("tags", []) for keyword in keyword_list)
                    ]
                
                # Calculate pagination for demo data
                total_results = len(all_articles)
                total_pages = (total_results + page_size - 1) // page_size
                
                # Get results for current page
                paginated_articles = all_articles[offset:offset + page_size]
                filtered_articles = paginated_articles
    else:
        # No ContentManager available, try API directly
        try:
            api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
            search_url = f"{api_base_url}/content/search/"
            params = {"limit": 1000}  # Get many results for pagination
            if query:
                params["query"] = query
            response = requests.get(search_url, params=params)
            
            if response.status_code == 200:
                all_results = response.json()
                
                # Apply client-side filtering for API results
                filtered_results = all_results
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
                
                # Calculate pagination
                total_results = len(filtered_results)
                total_pages = (total_results + page_size - 1) // page_size
                
                # Get results for current page
                paginated_results = filtered_results[offset:offset + page_size]
                
                filtered_articles = [
                    {
                        "id": result["id"],
                        "title": result.get("url", "Untitled"),
                        "content": result.get("summary", result.get("content", ""))[:200],
                        "type": result.get("type", "unknown"),
                        "snippet": result.get("summary", result.get("content", ""))[:150] + ("..." if len(result.get("summary", result.get("content", ""))) > 150 else "")
                    }
                    for result in paginated_results
                ]
            else:
                filtered_articles = []
                total_results = 0
                total_pages = 0
        except Exception as e:
            logger.error(f"API search failed: {e}")
            # Fallback to demo data with filtering
            all_articles = ARTICLES
            if query:
                all_articles = [
                    a for a in all_articles 
                    if query.lower() in a["title"].lower() 
                    or query.lower() in a["content"].lower()
                    or any(query.lower() in tag.lower() for tag in a["tags"])
                ]
            if content_type:
                all_articles = [a for a in all_articles if a.get("type") == content_type]
            if keyword_list:
                all_articles = [
                    a for a in all_articles 
                    if any(keyword.lower() == t.lower() for t in a.get("tags", []) for keyword in keyword_list)
                ]
            
            # Calculate pagination for demo data
            total_results = len(all_articles)
            total_pages = (total_results + page_size - 1) // page_size
            
            # Get results for current page
            paginated_articles = all_articles[offset:offset + page_size]
            filtered_articles = paginated_articles
    
    results = TerminalResultsList([
        {
            "id": a["id"],
            "title": a["title"],
            "snippet": a.get("snippet", a["content"][:60] + "..." if len(a["content"]) > 60 else a["content"]),
            "type": a.get("type", "unknown")
        }
        for a in filtered_articles
    ], page=page, total_results=total_results, page_size=page_size)
    
    # Create pagination controls
    query_params = {}
    if query:
        query_params['query'] = query
    if content_type:
        query_params['content_type'] = content_type
    if keywords:
        query_params['keywords'] = keywords
    if date_from:
        query_params['date_from'] = date_from
    if date_to:
        query_params['date_to'] = date_to
    
    pagination_controls = TerminalPaginationControls(
        current_page=page,
        total_pages=total_pages,
        base_url="/search",
        query_params=query_params
    ) if total_pages > 1 else None
    
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
    
    layout_elements = [
        search_bar,
        filter_controls,
        results
    ]
    
    # Add pagination controls if they exist
    if pagination_controls:
        layout_elements.append(pagination_controls)
    
    # Add suggestions at the end
    layout_elements.append(TerminalSuggestionBox(suggestions))
    
    layout = MainLayout(
        "SEARCH RESULTS",
        *layout_elements
    )
    
    return Html(
        Head(
            Title("Search - Knowledge Base"),
            Link(id="theme-stylesheet", rel="stylesheet", href="/static/styles/retro_terminal.css"),
            Script(src="/static/js/style-toggle.js"),
        ),
        Body(
            layout,
            cls="retro-bg"
        )
    )


@rt('/ui')
def ui_index():
    return index()


@rt('/process', methods=['POST'])
def process_url_endpoint(
    url: str,
    debug: Optional[str] = None,
    jina: Optional[str] = None
):
    """Process URL endpoint that replicates CLI functionality"""
    try:
        # Convert form values to booleans
        debug_mode = debug == 'true'
        use_jina = jina == 'true'
        
        # Initialize components (same as CLI)
        if not content_manager:
            return Html(
                Head(Title("Error")),
                Body(MainLayout("ERROR", Div("ContentManager not initialized. Check database connection.")))
            )
        
        # Clean and prepare URL
        clean_url = content_manager.clean_url(url)
        if use_jina or clean_url.endswith('.pdf'):
            clean_url = content_manager.jinafy_url(clean_url)
        
        file_type, file_path, time_now, complete_url = content_manager.get_file_path(clean_url)
        logger.info(f"Processing URL: {complete_url}, File type: {file_type}, Debug: {debug_mode}")
        
        # Extract content
        extractor = ExtractorFactory().get_extractor(clean_url)
        extractor.set_logger(logger)
        normalized_url = extractor.normalize_url(clean_url)
        content = extractor.extract(normalized_url, work=False)  # Assuming not work mode for web UI
        
        # Process with LLM
        llm = LLMFactory().create_llm('openai')
        llm.set_logger(logger)
        summary = llm.generate_summary(content, summary_type=file_type)
        keywords = llm.extract_keywords_from_summary(summary)
        embedding = llm.generate_embedding(content)
        obsidian_markdown = llm.summary_to_obsidian_markdown(summary, keywords)
        
        # Save content if not in debug mode
        if not debug_mode:
            # Save to disk
            content_manager.save_content(
                file_type=file_type,
                file_path=file_path,
                content=content,
                summary=summary,
                keywords=keywords,
                embeddings=embedding,
                url=complete_url,
                timestamp=time_now,
                obsidian_markdown=obsidian_markdown
            )
            
            # Save to database
            try:
                conn_string = os.getenv('DB_CONN_STRING')
                if conn_string:
                    db = Database(logger=logger, connection_string=conn_string)
                    db_record_data = {
                        'url': complete_url,
                        'type': file_type,
                        'timestamp': time_now,
                        'content': content,
                        'summary': summary,
                        'embeddings': embedding if isinstance(embedding, list) else [],
                        'obsidian_markdown': obsidian_markdown,
                        'keywords': keywords if isinstance(keywords, list) else []
                    }
                    record_id = db.store_content(db_record_data)
                    db.close()
                    logger.info(f"Record {record_id} saved to database")
            except Exception as db_e:
                logger.error(f"Database save failed: {db_e}")
            
            # Create Obsidian note
            try:
                obsidian_path = os.getenv('DSV_KB_PATH')
                if obsidian_path:
                    content_manager.create_obsidian_note(file_path, f"{obsidian_path}/_new-notes/")
                    logger.info(f"Obsidian note created for {file_path}")
            except Exception as obsidian_e:
                logger.error(f"Obsidian note creation failed: {obsidian_e}")
        
        # Create success page
        success_content = Div(
            H3("✅ URL Processed Successfully!"),
            P(f"URL: {complete_url}"),
            P(f"Type: {file_type}"),
            P(f"Debug mode: {'Yes' if debug_mode else 'No'}"),
            Div(
                H3("Summary:"),
                P(summary[:500] + "..." if len(summary) > 500 else summary),
                style="background:#222a22;padding:1em;border:1px solid #39ff1444;border-radius:4px;margin:1em 0;"
            ),
            Div(
                H3("Keywords:"),
                P(", ".join(keywords[:10]) if keywords else "None"),
                style="background:#222a22;padding:1em;border:1px solid #39ff1444;border-radius:4px;margin:1em 0;"
            ),
            A("🏠 Back to Home", href="/", cls="home-button", style="display:inline-block;padding:0.5em 1em;background:#39ff14;color:#000;text-decoration:none;border-radius:4px;font-weight:bold;margin-top:1em;font-family:monospace;")
        )
        
        layout = MainLayout("PROCESSING COMPLETE", success_content)
        return Html(
            Head(
                Title("Processing Complete - Knowledge Base"),
                Link(id="theme-stylesheet", rel="stylesheet", href="/static/styles/retro_terminal.css"),
                Script(src="/static/js/style-toggle.js"),
            ),
            Body(layout, cls="retro-bg")
        )
        
    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}")
        error_content = Div(
            H3("❌ Processing Failed"),
            P(f"Error: {str(e)}"),
            P(f"URL: {url}"),
            A("🏠 Back to Home", href="/", cls="home-button", style="display:inline-block;padding:0.5em 1em;background:#39ff14;color:#000;text-decoration:none;border-radius:4px;font-weight:bold;margin-top:1em;font-family:monospace;")
        )
        layout = MainLayout("PROCESSING ERROR", error_content)
        return Html(
            Head(
                Title("Processing Error - Knowledge Base"),
                Link(id="theme-stylesheet", rel="stylesheet", href="/static/styles/retro_terminal.css"),
                Script(src="/static/js/style-toggle.js"),
            ),
            Body(layout, cls="retro-bg")
        )


router = app

if __name__ == "__main__":
    serve()
