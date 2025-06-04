# src/knowledge_base/routes/ui.py
# Main FastHTML route handlers for the Knowledge Base UI (retro terminal)

from fasthtml.common import *
from src.knowledge_base.ui.components import (
    TerminalContainer, TerminalSearchBar, TerminalResultsList,
    TerminalArticleView, TerminalNavControls, TerminalSuggestionBox
)

# Demo data for now
ARTICLES = [
    {'id': 1, 'title': 'Welcome to the Knowledge Base', 'snippet': 'Start your journey here.'},
    {'id': 2, 'title': 'Retro Terminal UI Design', 'snippet': 'How to build an 80s terminal interface.'},
]

@route('/kb')
def kb_home():
    return Titled(
        'Knowledge Base',
        TerminalContainer(
            TerminalSearchBar(),
            TerminalResultsList(ARTICLES),
        )
    )

@route('/article/{article_id:int}')
def kb_article(article_id: int):
    # In real app, fetch article by id
    article = next((a for a in ARTICLES if a['id'] == article_id), None)
    if not article:
        return Titled('Not Found', TerminalContainer('Article not found.'))
    meta = {'author': 'System', 'date': '2025-06-03', 'tags': ['demo', 'retro']}
    content = f"This is the content for '{article['title']}'."
    return Titled(
        article['title'],
        TerminalContainer(
            TerminalArticleView(article['title'], meta, content, back_url='/kb'),
            TerminalSuggestionBox(['Try searching for "terminal"', 'Explore related articles!'])
        )
    )

# Add more routes as needed for integration
