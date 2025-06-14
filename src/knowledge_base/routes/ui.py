# src/knowledge_base/routes/ui.py
# Main FastHTML route handlers for the Knowledge Base UI (retro terminal)

from fasthtml.common import fast_app, serve, Style, Div, Html, Head, Title, Link, Body
import requests
import os
from datetime import datetime
from src.knowledge_base.ui.components import (
    MainLayout,
    TerminalContainer,
    TerminalSearchBar,
    TerminalResultsList,
    TerminalArticleView,
    TerminalNavControls,
    TerminalSuggestionBox,
)

app, rt = fast_app()

# Demo data for articles
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
    
    # Try to get recent articles from FastAPI endpoint
    try:
        api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
        search_url = f"{api_base_url}/content/search/"
        
        # Get recent articles (empty query returns all with limit)
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
            Style("""
                body { background: #101510; color: #39ff14; font-family: 'Fira Mono', 'Consolas', 'Menlo', 'Monaco', monospace; margin: 0; padding: 0; }
                .terminal-container { background: #181c18; border: 2px solid #39ff14; border-radius: 4px; padding: 2rem; margin: 2rem auto; max-width: 900px; box-shadow: 0 0 24px #39ff1433; }
                .terminal-title { font-size: 1.8rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1.5rem; text-align: center; border-bottom: 2px solid #39ff14; padding-bottom: 0.5rem; }
                .blink { animation: blink-cursor 1.1s steps(1) infinite; }
                @keyframes blink-cursor { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
                a, .link { color: #ffe066; text-decoration: underline; cursor: pointer; }
                a:hover, .link:hover { color: #fff700; }
                input, button { background: #101510; color: #39ff14; border: 1.5px solid #39ff14; font-family: inherit; padding: 0.4em 0.7em; border-radius: 2px; margin-bottom: 1em; }
                .button-primary { background: #39ff14; color: #101510; font-weight: bold; text-transform: uppercase; }
                .highlight { color: #ffe066; background: #222a22; padding: 0.1em 0.3em; border-radius: 2px; }
                .result-item { border-left: 3px solid #39ff1444; padding-left: 1rem; margin-bottom: 1.5rem; }
            """),
        ),
        Body(
            layout,
            cls="retro-bg"
        )
    )


@rt('/article/{article_id:int}')
def article_view(article_id: int):
    # Fetch article from database via API
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
            Style("""
                body { background: #101510; color: #39ff14; font-family: 'Fira Mono', 'Consolas', 'Menlo', 'Monaco', monospace; margin: 0; padding: 0; }
                .terminal-container { background: #181c18; border: 2px solid #39ff14; border-radius: 4px; padding: 2rem; margin: 2rem auto; max-width: 900px; box-shadow: 0 0 24px #39ff1433; }
                .terminal-title { font-size: 1.8rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1.5rem; text-align: center; border-bottom: 2px solid #39ff14; padding-bottom: 0.5rem; }
                .blink { animation: blink-cursor 1.1s steps(1) infinite; }
                @keyframes blink-cursor { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
                a, .link { color: #ffe066; text-decoration: underline; cursor: pointer; }
                a:hover, .link:hover { color: #fff700; }
                input, button { background: #101510; color: #39ff14; border: 1.5px solid #39ff14; font-family: inherit; padding: 0.4em 0.7em; border-radius: 2px; margin-bottom: 1em; }
                .button-primary { background: #39ff14; color: #101510; font-weight: bold; text-transform: uppercase; }
                .highlight { color: #ffe066; background: #222a22; padding: 0.1em 0.3em; border-radius: 2px; }
                .result-item { border-left: 3px solid #39ff1444; padding-left: 1rem; margin-bottom: 1.5rem; }
            """),
        ),
        Body(
            layout,
            cls="retro-bg"
        )
    )


@rt('/search')
def search_page(query: str = ""):
    search_bar = TerminalSearchBar(placeholder="Search articles...", value=query)
    
    # Use FastAPI search endpoint instead of demo data
    if query:
        try:
            # Get the FastAPI base URL from environment or default to localhost
            api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
            search_url = f"{api_base_url}/content/search/"
            
            # Make request to FastAPI search endpoint
            response = requests.get(search_url, params={"query": query, "limit": 20})
            
            if response.status_code == 200:
                search_results = response.json()
                filtered_articles = [
                    {
                        "id": result["id"],
                        "title": result.get("url", "Untitled"),  # Use URL as title if no title field
                        "content": result.get("summary", result.get("content", ""))[:200]
                    }
                    for result in search_results
                ]
            else:
                filtered_articles = []
        except Exception as e:
            # Fallback to demo data if API call fails
            filtered_articles = [
                a for a in ARTICLES 
                if query.lower() in a["title"].lower() 
                or query.lower() in a["content"].lower()
                or any(query.lower() in tag.lower() for tag in a["tags"])
            ]
    else:
        # Show demo data when no query
        filtered_articles = ARTICLES
    
    results = TerminalResultsList([
        {
            "id": a["id"],
            "title": a["title"],
            "snippet": a["content"][:60] + "..." if len(a["content"]) > 60 else a["content"]
        }
        for a in filtered_articles
    ])
    
    suggestions = []
    if query:
        suggestions.append(f"Found {len(filtered_articles)} result(s) for '{query}'")
    else:
        suggestions.append("Try searching for 'retro' or 'guide'.")
    
    layout = MainLayout(
        "SEARCH RESULTS",
        search_bar,
        results,
        TerminalSuggestionBox(suggestions),
    )
    
    return Html(
        Head(
            Title("Search - Knowledge Base"),
            Style("""
                body { background: #101510; color: #39ff14; font-family: 'Fira Mono', 'Consolas', 'Menlo', 'Monaco', monospace; margin: 0; padding: 0; }
                .terminal-container { background: #181c18; border: 2px solid #39ff14; border-radius: 4px; padding: 2rem; margin: 2rem auto; max-width: 900px; box-shadow: 0 0 24px #39ff1433; }
                .terminal-title { font-size: 1.8rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1.5rem; text-align: center; border-bottom: 2px solid #39ff14; padding-bottom: 0.5rem; }
                .blink { animation: blink-cursor 1.1s steps(1) infinite; }
                @keyframes blink-cursor { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }
                a, .link { color: #ffe066; text-decoration: underline; cursor: pointer; }
                a:hover, .link:hover { color: #fff700; }
                input, button { background: #101510; color: #39ff14; border: 1.5px solid #39ff14; font-family: inherit; padding: 0.4em 0.7em; border-radius: 2px; margin-bottom: 1em; }
                .button-primary { background: #39ff14; color: #101510; font-weight: bold; text-transform: uppercase; }
                .highlight { color: #ffe066; background: #222a22; padding: 0.1em 0.3em; border-radius: 2px; }
                .result-item { border-left: 3px solid #39ff1444; padding-left: 1rem; margin-bottom: 1.5rem; }
            """),
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
