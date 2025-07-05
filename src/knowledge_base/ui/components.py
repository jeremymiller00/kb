# FastHTML UI components for 80s retro terminal look
# src/knowledge_base/ui/components.py

from fasthtml.common import Div, Button, Form, Input, A, Article, H1, H2, H3, P, Span, Select, Option, Label, Textarea, Script

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
def TerminalResultsList(results, on_click=None, page=1, total_results=None, page_size=10):
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
    
    # Calculate result numbering offset for pagination
    start_num = (page - 1) * page_size + 1
    
    # Show total results count if available
    results_count_text = f"Found {len(results)} result{'s' if len(results) != 1 else ''}"
    if total_results and total_results > len(results):
        results_count_text = f"Showing {len(results)} of {total_results} result{'s' if total_results != 1 else ''}"
    
    return Div(
        Div(
            H3(results_count_text, 
               style="color: #ffe066; margin-bottom: 1.5em; font-size: 1.2em;"),
            cls="results-header"
        ),
        *[
            Div(
                # Result number and title
                Div(
                    Span(f"[{start_num + i:02d}]", cls="result-number"),
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


# Pagination controls for search results
def TerminalPaginationControls(
    current_page=1, 
    total_pages=1, 
    base_url="/search", 
    query_params=None
):
    """Pagination controls for navigating between result pages"""
    if total_pages <= 1:
        return None  # No pagination needed
    
    query_params = query_params or {}
    
    def build_url(page_num):
        """Build URL with query parameters and page number"""
        params = {**query_params, 'page': page_num}
        param_string = '&'.join([f"{k}={v}" for k, v in params.items() if v])
        return f"{base_url}?{param_string}" if param_string else base_url
    
    controls = []
    
    # Previous page button
    if current_page > 1:
        controls.append(
            A(
                "◀ Previous",
                href=build_url(current_page - 1),
                cls="pagination-btn",
                style="padding: 0.5em 1em; background: #39ff14; color: #000; text-decoration: none; border-radius: 4px; font-family: monospace; font-weight: bold; margin-right: 0.5em;"
            )
        )
    
    # Current page indicator and nearby pages
    start_page = max(1, current_page - 2)
    end_page = min(total_pages, current_page + 2)
    
    # Show first page if not in range
    if start_page > 1:
        controls.append(
            A(
                "1", 
                href=build_url(1),
                cls="pagination-btn",
                style="padding: 0.5em 0.8em; background: #222; color: #39ff14; text-decoration: none; border: 1px solid #39ff14; border-radius: 4px; font-family: monospace; margin: 0 0.2em;"
            )
        )
        if start_page > 2:
            controls.append(Span("...", style="color: #39ff14; margin: 0 0.5em;"))
    
    # Page number buttons
    for page_num in range(start_page, end_page + 1):
        if page_num == current_page:
            controls.append(
                Span(
                    str(page_num),
                    cls="pagination-current",
                    style="padding: 0.5em 0.8em; background: #39ff14; color: #000; border-radius: 4px; font-family: monospace; font-weight: bold; margin: 0 0.2em;"
                )
            )
        else:
            controls.append(
                A(
                    str(page_num),
                    href=build_url(page_num),
                    cls="pagination-btn",
                    style="padding: 0.5em 0.8em; background: #222; color: #39ff14; text-decoration: none; border: 1px solid #39ff14; border-radius: 4px; font-family: monospace; margin: 0 0.2em;"
                )
            )
    
    # Show last page if not in range
    if end_page < total_pages:
        if end_page < total_pages - 1:
            controls.append(Span("...", style="color: #39ff14; margin: 0 0.5em;"))
        controls.append(
            A(
                str(total_pages),
                href=build_url(total_pages),
                cls="pagination-btn", 
                style="padding: 0.5em 0.8em; background: #222; color: #39ff14; text-decoration: none; border: 1px solid #39ff14; border-radius: 4px; font-family: monospace; margin: 0 0.2em;"
            )
        )
    
    # Next page button
    if current_page < total_pages:
        controls.append(
            A(
                "Next ▶",
                href=build_url(current_page + 1),
                cls="pagination-btn",
                style="padding: 0.5em 1em; background: #39ff14; color: #000; text-decoration: none; border-radius: 4px; font-family: monospace; font-weight: bold; margin-left: 0.5em;"
            )
        )
    
    return Div(
        Div(
            f"Page {current_page} of {total_pages}",
            style="color: #ffe066; margin-bottom: 1em; text-align: center; font-family: monospace;"
        ),
        Div(
            *controls,
            style="display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 0.2em;"
        ),
        cls="pagination-controls",
        style="margin: 2em 0; padding: 1em; background: #1a1f1a; border: 1px solid #39ff1444; border-radius: 4px; text-align: center;"
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
    """URL processing form for the home page with options for URL or direct text"""
    return Div(
        H3('Process Content'),
        P('Choose how you want to process content: enter a URL to extract content from the web, or paste text directly.'),
        
        # Processing mode selector
        Div(
            Label(
                Input(
                    type='radio',
                    name='processing_mode',
                    value='url',
                    checked=True,
                    onchange='toggleProcessingMode()'
                ),
                ' Process URL',
                style='margin-right:2em;display:flex;align-items:center;gap:0.5em;'
            ),
            Label(
                Input(
                    type='radio',
                    name='processing_mode',
                    value='text',
                    onchange='toggleProcessingMode()'
                ),
                ' Process Direct Text',
                style='display:flex;align-items:center;gap:0.5em;'
            ),
            style='margin-bottom:1em;display:flex;align-items:center;'
        ),
        
        # URL processing form
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
                    Input(type='checkbox', name='jina', value='true', checked=True),
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
            style='background:#222a22;padding:1.5em;border:1px solid #39ff1444;border-radius:4px;',
            id='url-form'
        ),
        
        # Direct text processing form
        Form(
            Input(
                type='text',
                name='title',
                placeholder='Enter title for this content (optional)',
                style='flex:1;margin-bottom:1em;'
            ),
            Input(
                type='url',
                name='url',
                placeholder='Enter source URL for this content (optional)',
                style='flex:1;margin-bottom:1em;'
            ),
            Div(
                Label('Content Text:', style='display:block;margin-bottom:0.5em;font-weight:bold;'),
                Textarea(
                    name='content',
                    placeholder='Paste your text content here...',
                    required=True,
                    style='width:100%;height:150px;resize:vertical;font-family:monospace;'
                ),
                style='margin-bottom:1em;'
            ),
            Div(
                Label(
                    Input(type='checkbox', name='debug', value='true'),
                    ' Debug mode (don\'t save to disk)',
                    style='margin-bottom:1em;display:flex;align-items:center;gap:0.5em;'
                ),
                style='margin-bottom:1em;'
            ),
            Button(
                'Process Text',
                type='submit',
                cls='button-primary',
                style='width:100%;'
            ),
            action='/process-text',
            method='post',
            style='background:#222a22;padding:1.5em;border:1px solid #39ff1444;border-radius:4px;display:none;',
            id='text-form'
        ),
        
        # JavaScript to toggle between forms
        Script("""
        function toggleProcessingMode() {
            const urlMode = document.querySelector('input[name="processing_mode"][value="url"]').checked;
            const urlForm = document.getElementById('url-form');
            const textForm = document.getElementById('text-form');
            
            if (urlMode) {
                urlForm.style.display = 'block';
                textForm.style.display = 'none';
            } else {
                urlForm.style.display = 'none';
                textForm.style.display = 'block';
            }
        }
        """, type='text/javascript'),
        
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
