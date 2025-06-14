# FastHTML UI components for 80s retro terminal look
# src/knowledge_base/ui/components.py

from fasthtml.common import Div, Button, Form, Input, A, Article, H1, H2, H3, P, Span, Select, Option, Label

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


# Search bar (input + button) using FastHTML Form, Input, and Button components
def TerminalSearchBar(placeholder='Search articles...', value='', **kwargs):
    """Search form using FastHTML's Form, Input, and Button components"""
    return Form(
        Input(
            type='text',
            name='query',
            placeholder=placeholder,
            value=value,
            autofocus=True,
            style='flex:1;',
            **kwargs
        ),
        Button(
            'Search',
            type='submit',
            cls='button-primary',
            style='margin-left:1em;'
        ),
        action='/search',
        method='get',
        role='search',
        style='display:flex;gap:1em;align-items:center;margin-bottom:2em;'
    )


# Filter controls for tags, date, and content type
def TerminalFilterControls(
    query='',
    selected_tags=None,
    selected_type='',
    date_from='',
    date_to='',
    available_tags=None,
    available_types=None
):
    """Filtering controls using FastHTML form elements"""
    selected_tags = selected_tags or []
    available_tags = available_tags or []
    available_types = available_types or ['github', 'arxiv', 'youtube', 'huggingface', 'general']
    
    return Div(
        H3('Filters'),
        Form(
            # Hidden field to preserve search query
            Input(type='hidden', name='query', value=query),
            
            # Content Type Filter
            Div(
                Label('Content Type:', _for='type_filter'),
                Select(
                    Option('All Types', value='__all__', selected=(selected_type == '' or selected_type == '__all__')),
                    *[
                        Option(t.title(), value=t, selected=(selected_type == t))
                        for t in available_types
                    ],
                    name='content_type',
                    id='type_filter',
                    style='width:100%;margin-bottom:1em;'
                ),
                style='margin-bottom:1em;'
            ),
            
            # Keywords Filter
            Div(
                Label('Keywords (comma-separated):', _for='keywords_filter'),
                Input(
                    type='text',
                    name='keywords',
                    id='keywords_filter',
                    placeholder='e.g., machine-learning, ai, python',
                    value=','.join(selected_tags) if selected_tags else '',
                    style='width:100%;margin-bottom:1em;'
                ),
                style='margin-bottom:1em;'
            ),
            
            # Date Range Filter
            Div(
                Label('Date Range:', style='display:block;margin-bottom:0.5em;'),
                Div(
                    Input(
                        type='date',
                        name='date_from',
                        value=date_from,
                        placeholder='From date',
                        style='flex:1;margin-right:0.5em;'
                    ),
                    Input(
                        type='date',
                        name='date_to',
                        value=date_to,
                        placeholder='To date',
                        style='flex:1;margin-left:0.5em;'
                    ),
                    style='display:flex;gap:1em;'
                ),
                style='margin-bottom:1em;'
            ),
            
            # Filter and Clear buttons
            Div(
                Button(
                    'Apply Filters',
                    type='submit',
                    cls='button-primary',
                    style='margin-right:1em;'
                ),
                Button(
                    'Clear Filters',
                    type='button',
                    onclick="window.location='/search'",
                    style='background:#666;'
                ),
                style='display:flex;gap:1em;'
            ),
            
            action='/search',
            method='get',
            style='background:#222a22;padding:1.5em;border:1px solid #39ff1444;border-radius:4px;'
        ),
        cls='filter-controls',
        style='margin-bottom:2em;'
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
    # Check if title looks like a URL and make it clickable
    if title and (title.startswith('http://') or title.startswith('https://')):
        return H3(
            A(title, href=title, target='_blank', cls='link'),
            cls='article-title'
        )
    else:
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
