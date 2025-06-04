# FastHTML UI components for 80s retro terminal look
# src/knowledge_base/ui/components.py

from fasthtml.common import *

# Container for the main terminal UI
class TerminalContainer:
    def __ft__(self, *c, **kwargs):
        return Div(*c, cls='terminal-container scanlines', **kwargs)

# Retro-styled button
class TerminalButton:
    def __ft__(self, label, primary=False, **kwargs):
        btn_cls = 'button-primary' if primary else ''
        return Button(label, cls=btn_cls, **kwargs)

# Search bar (input + button)
def TerminalSearchBar(placeholder='Search articles...', **kwargs):
    return Form(
        Input(type='text', name='q', placeholder=placeholder, autofocus=True, **kwargs),
        TerminalButton('Search', primary=True, type='submit'),
        role='search',
        style='display:flex;gap:1em;align-items:center;'
    )

# Results list
class TerminalResultsList:
    def __ft__(self, results, on_click=None):
        # results: list of dicts with 'title', 'snippet', 'id'
        return Div(
            *[Div(
                A(r['title'], href=f"/article/{r['id']}", cls='link', onclick=on_click),
                Div(r.get('snippet', ''), cls='highlight'),
                cls='result-item',
                style='margin-bottom:1.5em;'
            ) for r in results],
            cls='results-list'
        )

# Article view (metadata + content)
def TerminalArticleView(title, meta, content, back_url=None):
    return Article(
        ArticleTitle(title),
        ArticleMeta(meta),
        Div(content, style='margin-top:1.5em;'),
        TerminalButton('Back', onclick=f"window.location='{back_url or '/'}'", primary=False) if back_url else None,
        cls='article-view'
    )

# Navigation controls (back, next, etc.)
def TerminalNavControls(back_url=None, next_url=None):
    return Div(
        TerminalButton('Back', onclick=f"window.location='{back_url}'") if back_url else None,
        TerminalButton('Next', onclick=f"window.location='{next_url}'") if next_url else None,
        cls='nav-controls',
        style='display:flex;gap:1em;'
    )

# Suggestion box for AI-driven ideas/questions
def TerminalSuggestionBox(suggestions):
    return Div(
        H3('Suggestions'),
        *[Div(s, cls='highlight', style='margin-bottom:0.5em;') for s in suggestions],
        cls='suggestion-box',
        style='margin-top:2em;'
    )
