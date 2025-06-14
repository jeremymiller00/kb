# FastHTML UI components for 80s retro terminal look
# src/knowledge_base/ui/components.py

from fasthtml.common import Div, Button, Form, Input, A, Article, H1, H2, H3, P, Span

# Main layout wrapper
def MainLayout(title, *content, **kwargs):
    """Main layout wrapper that includes terminal styling and accessibility"""
    return Div(
        H1(title + " ", Span("_", cls="blink"), cls="terminal-title"),
        Div(*content, cls="terminal-content"),
        cls='terminal-container scanlines',
        **kwargs
    )

# Container for the main terminal UI
def TerminalContainer(*c, **kwargs):
    return Div(*c, cls='terminal-container scanlines', **kwargs)


# Retro-styled button
def TerminalButton(label, primary=False, **kwargs):
    btn_cls = 'button-primary' if primary else ''
    return Button(label, cls=btn_cls, **kwargs)


# Search bar (input + button)
def TerminalSearchBar(placeholder='Search articles...', **kwargs):
    return Form(
        Input(
            type='text',
            name='query',
            placeholder=placeholder,
            autofocus=True,
            **kwargs
        ),
        TerminalButton('Search', primary=True, type='submit'),
        action='/search',
        method='get',
        role='search',
        style='display:flex;gap:1em;align-items:center;'
    )


# Results list
def TerminalResultsList(results, on_click=None):
    # results: list of dicts with 'title', 'snippet', 'id'
    return Div(
        *[
            Div(
                A(
                    r['title'],
                    href=f"/article/{r['id']}",
                    cls='link',
                    onclick=on_click
                ),
                Div(r.get('snippet', ''), cls='highlight'),
                cls='result-item',
                style='margin-bottom:1.5em;'
            ) for r in results
        ],
        cls='results-list'
    )


# Article view (metadata + content)
def TerminalArticleView(title, meta, content, back_url=None):
    return Article(
        ArticleTitle(title),
        ArticleMeta(meta),
        Div(content, style='margin-top:1.5em;'),
        TerminalButton(
            'Back',
            onclick=f"window.location='{back_url or '/'}'",
            primary=False
        ) if back_url else None,
        cls='article-view'
    )


# Navigation controls (back, next, etc.)
def TerminalNavControls(back_url=None, next_url=None):
    return Div(
        TerminalButton(
            'Back',
            onclick=f"window.location='{back_url}'"
        ) if back_url else None,
        TerminalButton(
            'Next',
            onclick=f"window.location='{next_url}'"
        ) if next_url else None,
        cls='nav-controls',
        style='display:flex;gap:1em;'
    )


# Suggestion box for AI-driven ideas/questions
def TerminalSuggestionBox(suggestions):
    return Div(
        H3('Suggestions'),
        *[
            Div(s, cls='highlight', style='margin-bottom:0.5em;')
            for s in suggestions
        ],
        cls='suggestion-box',
        style='margin-top:2em;'
    )


# Add stubs for ArticleTitle and ArticleMeta for now (to avoid NameError)
def ArticleTitle(title):
    return H3(title, cls='article-title')


def ArticleMeta(meta):
    # meta: dict with keys like 'author', 'date', 'tags'
    items = []
    if isinstance(meta, dict):
        if 'author' in meta:
            items.append(f"By {meta['author']}")
        if 'date' in meta:
            items.append(meta['date'])
        if 'tags' in meta:
            items.append(', '.join(meta['tags']))
    return Div(' | '.join(items), cls='article-meta')
