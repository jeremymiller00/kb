# FastHTML UI components for 80s retro terminal look
# src/knowledge_base/ui/components.py

from fasthtml.common import Div, Button, Form, Input, A, Article, H1, H2, H3, P, Span, Select, Option, Label

# Main layout wrapper
def MainLayout(title, *content, show_home_button=True, **kwargs):
    """Main layout wrapper that includes terminal styling and accessibility"""
    elements = []
    
    # Add home button if requested and not on home page
    if show_home_button and title != "KNOWLEDGE BASE":
        elements.append(HomeButton())
    
    # Add title
    elements.append(H1(title + " ", Span("_", cls="blink"), cls="terminal-title"))
    
    # Add main content
    elements.append(Div(*content, cls="terminal-content"))
    
    return Div(
        *elements,
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


# Home button component
def HomeButton():
    """Home button that appears at the top of every page"""
    return A(
        "🏠 HOME",
        href="/",
        cls="home-button",
        style="display:inline-block;padding:0.5em 1em;background:#39ff14;color:#000;text-decoration:none;border-radius:4px;font-weight:bold;margin-bottom:1em;font-family:monospace;"
    )


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
    """Enhanced results list with better styling and metadata display"""
    if not results:
        return Div(
            Div(
                H3("No Results Found", style="color: #ffe066; text-align: center;"),
                P("Try adjusting your search terms or filters.", style="color: #39ff14; text-align: center; opacity: 0.7;"),
                cls="no-results",
                style="padding: 2em; text-align: center; border: 1px dashed #39ff1444; border-radius: 4px;"
            ),
            cls='results-list'
        )
    
    return Div(
        Div(
            H3(f"Found {len(results)} result{'s' if len(results) != 1 else ''}", 
               style="color: #ffe066; margin-bottom: 1.5em; font-size: 1.2em;"),
            cls="results-header"
        ),
        *[
            Div(
                # Result number and title
                Div(
                    Span(f"[{i+1:02d}]", cls="result-number"),
                    A(
                        r['title'] if r['title'] else "Untitled",
                        href=f"/article/{r['id']}",
                        cls='result-title',
                        onclick=on_click
                    ),
                    cls="result-header-row",
                    style="display: flex; align-items: center; gap: 0.5em; margin-bottom: 0.5em;"
                ),
                # Snippet/preview
                Div(
                    r.get('snippet', ''),
                    cls='result-snippet',
                    style="color: #cccccc; font-size: 0.9em; line-height: 1.4; margin-left: 2.5em;"
                ),
                # Additional metadata if available
                Div(
                    *[
                        Span(f"ID: {r['id']}", cls="result-meta-item"),
                        Span("•", style="color: #39ff1444; margin: 0 0.5em;"),
                        Span(f"Type: {r.get('type', 'unknown')}", cls="result-meta-item") if r.get('type') else None,
                        Span("•", style="color: #39ff1444; margin: 0 0.5em;") if r.get('type') else None,
                        Span(f"Length: {len(r.get('snippet', ''))} chars", cls="result-meta-item")
                    ],
                    cls="result-metadata",
                    style="margin-left: 2.5em; margin-top: 0.5em; font-size: 0.8em; color: #39ff1466; display: flex; align-items: center;"
                ),
                cls='result-item',
                style='margin-bottom: 2em; padding: 1em; border: 1px solid #39ff1422; border-radius: 4px; transition: all 0.2s ease;',
                onmouseover="this.style.borderColor='#39ff1466'; this.style.backgroundColor='#1a1f1a';",
                onmouseout="this.style.borderColor='#39ff1422'; this.style.backgroundColor='transparent';"
            ) for i, r in enumerate(results)
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


# URL Processing form component
def TerminalUrlProcessor(placeholder='Enter URL to process...', **kwargs):
    """URL processing form for the home page"""
    return Div(
        H3('Process URL'),
        P('Paste a URL below to extract content, generate summary, and save to your knowledge base.'),
        Form(
            Input(
                type='url',
                name='url',
                placeholder=placeholder,
                required=True,
                autofocus=False,
                style='flex:1;margin-bottom:1em;',
                **kwargs
            ),
            Div(
                Label(
                    Input(type='checkbox', name='debug', value='true'),
                    ' Debug mode (don\'t save to disk)',
                    style='margin-bottom:1em;display:flex;align-items:center;gap:0.5em;'
                ),
                Label(
                    Input(type='checkbox', name='jina', value='true'),
                    ' Use Jina for processing (recommended for PDFs)',
                    style='margin-bottom:1em;display:flex;align-items:center;gap:0.5em;'
                ),
                style='margin-bottom:1em;'
            ),
            Button(
                'Process URL',
                type='submit',
                cls='button-primary',
                style='width:100%;'
            ),
            action='/process',
            method='post',
            style='background:#222a22;padding:1.5em;border:1px solid #39ff1444;border-radius:4px;'
        ),
        cls='url-processor',
        style='margin-bottom:2em;'
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
