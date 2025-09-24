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
    TerminalRelatedArticlesList,
    HomeButton,
)
from ..core.content_manager import ContentManager
from ..extractors.extractor_factory import ExtractorFactory
from ..ai.llm_factory import LLMFactory
from ..ai.suggestion_engine import SuggestionEngine
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

# Initialize SuggestionEngine
suggestion_engine = SuggestionEngine(LLMFactory(), content_manager)
suggestion_engine.set_logger(logger)

# Demo data for articles (fallback)
ARTICLES = [
    {
        "id": 1,
        "title": "How to Use the Knowledge Base",
        "author": "Jane Doe",
        "date": "2025-06-10",
        "tags": ["guide", "intro"],
        "summary": "A brief guide on how to navigate and use the Knowledge Base effectively.",
        "content": (
            "Welcome to the retro Knowledge Base! Use the search bar above to "
            "find articles. You can filter by content type, keywords, and date ranges. "
            "Click on any article title to view the full content. The interface is "
            "designed with an 80s terminal aesthetic for a unique user experience."
        ),
    },
    {
        "id": 2,
        "title": "80s Terminal UI Design",
        "author": "John Smith",
        "date": "2025-06-09",
        "tags": ["design", "retro"],
        "summary": "Learn the principles and techniques for creating retro terminal-style user interfaces.",
        "content": (
            "This article explains how to create a retro terminal UI using "
            "FastHTML. Key elements include monospace fonts, green/amber color schemes, "
            "scanline effects, and blinking cursors. The design should evoke the feel "
            "of 1980s computer terminals while maintaining modern usability standards. "
            "FastHTML provides excellent support for custom CSS and interactive components "
            "that make this aesthetic achievable with clean, semantic code."
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
    
    # Generate AI-driven suggestions for home page
    try:
        home_context = {
            'recent_articles': articles_data[:5] if articles_data else [],
            'total_articles': len(articles_data) if articles_data else 0
        }
        
        ai_suggestions = suggestion_engine.generate_suggestions('home', home_context, limit=3)
        
        # Use full AI suggestion objects
        home_suggestions = ai_suggestions
        
    except Exception as e:
        logger.error(f"Error generating AI suggestions for home page: {e}")
        # Fallback to basic suggestions (simple text format)
        home_suggestions = ["Try searching for 'retro' or 'guide', or process a URL above."]
    
    layout = MainLayout(
        "KNOWLEDGE BASE",
        search_bar,
        url_processor,
        results,
        TerminalSuggestionBox(home_suggestions),
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
def article_view(article_id: int, back_url: str = "/", use_keywords: bool = False):
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
                    "summary": article_data.get("summary", "No summary available"),
                    "content": article_data.get("content", "No content available")
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
                    "summary": article_data.get("summary", "No summary available"),
                    "content": article_data.get("content", "No content available")
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
    
    # Get related articles using similarity-based algorithm by default
    related_articles = []
    algorithm_used = "similarity"
    
    if use_keywords:
        # Use keyword-based algorithm when requested
        if content_manager:
            try:
                related_articles = content_manager.find_related_articles(article_id, limit=5)
                algorithm_used = "keywords"
                logger.info(f"Found {len(related_articles)} related articles for article {article_id} using keyword algorithm")
            except Exception as e:
                logger.error(f"Error getting related articles with keyword algorithm: {e}")
    else:
        # Use similarity-based algorithm by default
        try:
            api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
            similar_url = f"{api_base_url}/content/{article_id}/similar?n=5"
            
            response = requests.get(similar_url)
            
            if response.status_code == 200:
                similar_articles = response.json()
                # Convert similarity results to match the expected format
                related_articles = []
                for similar_article in similar_articles:
                    similarity_score = similar_article.get("similarity_score", 0.0)
                    
                    # Skip articles with zero similarity score (no relevance)
                    if similarity_score <= 0:
                        continue
                        
                    article_data = {
                        "id": similar_article["id"],
                        "url": similar_article.get("url", "Untitled"),
                        "type": similar_article.get("type", "unknown"),
                        "summary": similar_article.get("summary", ""),
                        "content": similar_article.get("content", ""),
                        "keywords": similar_article.get("keywords", []),
                        # Convert similarity_score to match_score for consistency with UI component
                        "match_score": similarity_score
                    }
                    related_articles.append(article_data)
                
                # Sort by similarity score/match_score in descending order (highest relevance first)
                related_articles.sort(key=lambda x: x.get("match_score", 0.0), reverse=True)
                
                algorithm_used = "similarity"
                logger.info(f"Found {len(related_articles)} related articles for article {article_id} using similarity algorithm")
            else:
                logger.warning(f"Similarity API returned status {response.status_code}, falling back to keyword algorithm")
                # Fallback to keyword algorithm if similarity fails
                if content_manager:
                    try:
                        related_articles = content_manager.find_related_articles(article_id, limit=5)
                        algorithm_used = "keywords (fallback)"
                        logger.info(f"Found {len(related_articles)} related articles for article {article_id} using keyword fallback")
                    except Exception as e:
                        logger.error(f"Error getting related articles with keyword fallback: {e}")
        except Exception as e:
            logger.error(f"Error getting related articles with similarity algorithm: {e}")
            # Fallback to keyword algorithm if similarity fails
            if content_manager:
                try:
                    related_articles = content_manager.find_related_articles(article_id, limit=5)
                    algorithm_used = "keywords (fallback)"
                    logger.info(f"Found {len(related_articles)} related articles for article {article_id} using keyword fallback")
                except Exception as e:
                    logger.error(f"Error getting related articles with keyword fallback: {e}")
    
    article_content = TerminalArticleView(
        title=article["title"],
        meta={
            "id": article["id"],
            "author": article["author"],
            "date": article["date"],
            "tags": article["tags"],
            "source_url": article.get("source_url", article["title"]) if article["title"].startswith('http') else None
        },
        summary=article["summary"],
        content=article["content"],
        back_url=back_url
    )
    
    # Create related articles component with algorithm toggle
    related_articles_component = TerminalRelatedArticlesList(
        related_articles, 
        current_article_id=article_id,
        algorithm_used=algorithm_used,
        use_keywords=use_keywords
    )
    
    # Generate AI-driven suggestions based on article context
    try:
        article_context = {
            'title': article['title'],
            'summary': article['summary'],
            'content': article['content'],
            'keywords': article['tags'],
            'article_id': article['id']
        }
        
        ai_suggestions = suggestion_engine.generate_suggestions('article', article_context, limit=3)
        
        # Pass full suggestion objects to the component
        suggestions_for_display = ai_suggestions
        
    except Exception as e:
        logger.error(f"Error generating AI suggestions for article {article_id}: {e}")
        # Fallback to basic suggestions (simple text format)
        suggestions_for_display = [
            f"Article ID: {article['id']}", 
            f"Keywords: {', '.join(article['tags'][:3])}" if article['tags'] else "No keywords found",
            "Explore related topics and ideas"
        ]
    
    layout = MainLayout(
        "ARTICLE VIEW",
        article_content,
        related_articles_component,
        TerminalSuggestionBox(suggestions_for_display),
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
    
    # Build search parameters for back navigation
    search_params = {
        'query': query,
        'content_type': content_type,
        'keywords': keywords,
        'date_from': date_from,
        'date_to': date_to,
        'page': page
    }
    
    results = TerminalResultsList([
        {
            "id": a["id"],
            "title": a["title"],
            "snippet": a.get("snippet", a["content"][:60] + "..." if len(a["content"]) > 60 else a["content"]),
            "type": a.get("type", "unknown")
        }
        for a in filtered_articles
    ], page=page, total_results=total_results, page_size=page_size, search_params=search_params)
    
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
    
    # Generate AI-driven suggestions based on search context
    try:
        search_context = {
            'query': query,
            'result_count': total_results,
            'content_types': [content_type] if content_type else [],
            'keywords': keyword_list,
            'filters_applied': bool(query or content_type or keyword_list or date_from or date_to)
        }
        
        ai_suggestions = suggestion_engine.generate_suggestions('search', search_context, limit=3)
        
        # Use full AI suggestion objects
        suggestions = ai_suggestions.copy()
        
        # Add result summary as first suggestion if we have results
        if total_results > 0:
            filter_applied = bool(query or content_type or keyword_list or date_from or date_to)
            if filter_applied:
                filter_parts = []
                if query:
                    filter_parts.append(f"'{query}'")
                if content_type:
                    filter_parts.append(f"{content_type}")
                if keyword_list:
                    filter_parts.append(f"{', '.join(keyword_list)}")
                
                result_summary = f"Found {total_results} result(s)" + (f" for {'; '.join(filter_parts)}" if filter_parts else "")
                # Insert summary as simple text (backward compatibility)
                suggestions.insert(0, result_summary)
        
    except Exception as e:
        logger.error(f"Error generating AI suggestions for search: {e}")
        # Fallback to basic suggestions
        suggestions = []
        filter_applied = bool(query or content_type or keyword_list or date_from or date_to)
        if filter_applied:
            suggestions.append(f"Found {total_results} result(s) with your current filters")
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


@rt('/api/related/{article_id:int}')
def get_related_articles_api(article_id: int, limit: int = 5):
    """API endpoint to get related articles for a given article ID"""
    if not content_manager:
        return {"error": "ContentManager not available", "related_articles": []}
    
    try:
        related_articles = content_manager.find_related_articles(article_id, limit=limit)
        
        # Format for API response
        formatted_articles = []
        for article in related_articles:
            formatted_articles.append({
                "id": article["id"],
                "title": article.get("url", "Untitled"),
                "summary": article.get("summary", "")[:120] + ("..." if len(article.get("summary", "")) > 120 else ""),
                "type": article.get("type", "unknown"),
                "match_score": article.get("match_score", 0.0),
                "keywords": article.get("keywords", [])
            })
        
        return {
            "article_id": article_id,
            "related_articles": formatted_articles,
            "total_found": len(formatted_articles)
        }
        
    except Exception as e:
        logger.error(f"Error in related articles API: {e}")
        return {"error": str(e), "related_articles": []}


@rt('/process-text', methods=['POST'])
def process_text_endpoint(
    content: str,
    title: Optional[str] = None,
    url: Optional[str] = None,
    debug: Optional[str] = None
):
    """Process direct text content endpoint"""
    try:
        # Convert form values to booleans
        debug_mode = debug == 'true'
        
        # Initialize components
        if not content_manager:
            return Html(
                Head(Title("Error")),
                Body(MainLayout("ERROR", Div("ContentManager not initialized. Check database connection.")))
            )
        
        # Generate a unique identifier for this text content
        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        
        # Use provided URL or create a synthetic one
        if url and url.strip():
            stored_url = url.strip()
        else:
            # Create a synthetic URL for the text content
            stored_url = f"text://direct-input/{content_hash}"
            if title:
                stored_url = f"text://direct-input/{title.replace(' ', '-')}-{content_hash}"
        
        # Get current timestamp
        import time
        time_now = int(time.time())
        
        # Generate file path for saving using ContentManager's proper method
        file_type, file_path, time_now, complete_url = content_manager.get_file_path(stored_url)
        
        logger.info(f"Processing direct text content: {len(content)} characters, Debug: {debug_mode}")
        
        # Process with LLM (skip extraction since we have the content directly)
        llm = LLMFactory().create_llm('openai')
        llm.set_logger(logger)
        summary = llm.generate_summary(content, summary_type=file_type)
        keywords = llm.extract_keywords_from_summary(summary)
        embedding = llm.generate_embedding(content)
        obsidian_markdown = llm.summary_to_obsidian_markdown(summary, keywords)
        
        # If user provided a title, prepend it as H1 header to obsidian_markdown
        # This ensures the create_obsidian_note method uses the user's title
        if title and title.strip():
            obsidian_markdown = f"# {title.strip()}\n\n{obsidian_markdown}"
        
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
                url=stored_url,
                timestamp=time_now,
                obsidian_markdown=obsidian_markdown
            )
            
            # Save to database
            try:
                conn_string = os.getenv('DB_CONN_STRING')
                if conn_string:
                    db = Database(logger=logger, connection_string=conn_string)
                    db_record_data = {
                        'url': stored_url,
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
        display_title = title if title else f"Text Content ({content_hash})"
        success_content = Div(
            H3("✅ Text Content Processed Successfully!"),
            P(f"Title: {display_title}"),
            P(f"URL: {stored_url}"),
            P(f"Content length: {len(content)} characters"),
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
        logger.error(f"Error processing text content: {str(e)}")
        error_content = Div(
            H3("❌ Processing Failed"),
            P(f"Error: {str(e)}"),
            P(f"URL: {url if url else 'None provided'}"),
            P(f"Content length: {len(content)} characters"),
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
        original_url = clean_url
        if use_jina or clean_url.endswith('.pdf'):
            original_url, clean_url = content_manager.jinafy_url(clean_url)
        
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
                url=original_url,
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
