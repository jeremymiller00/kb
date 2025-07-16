# FastHTML UI components for 80s retro terminal look
# src/knowledge_base/ui/components.py

from fasthtml.common import Div, Button, Form, Input, A, Article, H1, H2, H3, P, Span, Select, Option, Label, Textarea, Script, NotStr

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
def TerminalResultsList(results, on_click=None, page=1, total_results=None, page_size=10, search_params=None):
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
    
    # Build back URL from search parameters
    def build_back_url(search_params):
        if not search_params:
            return "/search"
        
        params = []
        for key, value in search_params.items():
            if value and value != "" and value != "__all__":
                params.append(f"{key}={value}")
        
        return f"/search?{'&'.join(params)}" if params else "/search"
    
    back_url = build_back_url(search_params)
    
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
                        href=f"/article/{r['id']}?back_url={back_url.replace('&', '%26').replace('?', '%3F')}",
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


# Function to parse keywords from content and make them clickable
def parse_keywords_to_links(content_text, keywords_list):
    """
    Parse content text and convert keywords to clickable links.
    Returns content with keywords wrapped in A components.
    """
    if not content_text or not keywords_list:
        return content_text
    
    # Split content into lines to preserve structure
    lines = content_text.split('\n')
    processed_lines = []
    
    for line in lines:
        processed_line = line
        # Sort keywords by length (descending) to avoid partial matches
        sorted_keywords = sorted(keywords_list, key=len, reverse=True)
        
        for keyword in sorted_keywords:
            if keyword and len(keyword.strip()) > 2:  # Only process meaningful keywords
                # Case-insensitive search and replace
                import re
                pattern = re.compile(re.escape(keyword.strip()), re.IGNORECASE)
                
                # Create replacement function to preserve original case
                def replace_with_link(match):
                    original_text = match.group(0)
                    # Create a search URL that searches for this keyword
                    search_url = f"/search?keywords={keyword.strip()}"
                    return f'<a href="{search_url}" class="keyword-link" style="color: #66ff66; text-decoration: underline; font-weight: bold;" title="Search for related articles about: {keyword.strip()}">{original_text}</a>'
                
                processed_line = pattern.sub(replace_with_link, processed_line)
        
        processed_lines.append(processed_line)
    
    return '\n'.join(processed_lines)


# Article view (metadata + content) using FastHTML's Article, ArticleTitle, ArticleMeta
def TerminalArticleView(title, meta, summary, content, back_url=None):
    """
    Enhanced article view component using FastHTML's native Article, ArticleTitle, and ArticleMeta components
    with terminal styling and improved accessibility.
    """
    from fasthtml.common import Article as FastArticle, H1 as ArticleTitle, Div as ArticleMeta, H2
    
    # Create article title - make it clickable if it's a URL
    if title and (title.startswith('http://') or title.startswith('https://')):
        title_element = ArticleTitle(
            A(title, href=title, target='_blank', cls='article-title-link',
              style="color: #39ff14; text-decoration: none; word-break: break-all; transition: color 0.2s ease;",
              onmouseover="this.style.color='#66ff66'",
              onmouseout="this.style.color='#39ff14'"),
            cls='article-title',
            style="color: #ffe066; border-bottom: 2px solid #39ff14; padding-bottom: 0.8em; margin-bottom: 1.5em; font-size: 1.8em; font-weight: bold; line-height: 1.3;"
        )
    else:
        title_element = ArticleTitle(
            title or "Untitled Article",
            cls='article-title',
            style="color: #ffe066; border-bottom: 2px solid #39ff14; padding-bottom: 0.8em; margin-bottom: 1.5em; font-size: 1.8em; font-weight: bold; line-height: 1.3;"
        )
    
    # Create enhanced metadata display with better structure
    meta_element = None
    if isinstance(meta, dict) and any(meta.get(key) for key in ['id', 'author', 'date', 'tags', 'source_url']):
        meta_rows = []
        
        # ID row
        if meta.get('id'):
            meta_rows.append(
                Div(
                    Span("ID:", cls="meta-label", style="color: #39ff14; font-weight: bold; margin-right: 0.5em;"),
                    Span(str(meta['id']), cls="meta-value", style="color: #cccccc; font-family: monospace;"),
                    cls="meta-row",
                    style="margin-bottom: 0.5em;"
                )
            )
        
        # Author row
        if meta.get('author'):
            meta_rows.append(
                Div(
                    Span("Author:", cls="meta-label", style="color: #39ff14; font-weight: bold; margin-right: 0.5em;"),
                    Span(meta['author'], cls="meta-value", style="color: #cccccc;"),
                    cls="meta-row",
                    style="margin-bottom: 0.5em;"
                )
            )
        
        # Date row
        if meta.get('date'):
            meta_rows.append(
                Div(
                    Span("Published:", cls="meta-label", style="color: #39ff14; font-weight: bold; margin-right: 0.5em;"),
                    Span(meta['date'], cls="meta-value", style="color: #cccccc;"),
                    cls="meta-row",
                    style="margin-bottom: 0.5em;"
                )
            )
        
        # Source URL row (if different from title)
        if meta.get('source_url') and meta['source_url'] != title:
            meta_rows.append(
                Div(
                    Span("Source:", cls="meta-label", style="color: #39ff14; font-weight: bold; margin-right: 0.5em;"),
                    A(
                        meta['source_url'] if len(meta['source_url']) <= 60 else meta['source_url'][:57] + "...",
                        href=meta['source_url'],
                        target='_blank',
                        cls="meta-value",
                        style="color: #39ff14; text-decoration: underline; word-break: break-all;"
                    ),
                    cls="meta-row",
                    style="margin-bottom: 0.5em;"
                )
            )
        
        # Tags row
        if meta.get('tags') and isinstance(meta['tags'], list) and meta['tags']:
            tag_elements = []
            for tag in meta['tags']:
                tag_elements.append(
                    A(
                        tag,
                        href=f"/search?keywords={tag.strip()}",
                        cls="tag-item keyword-link",
                        style="background: #39ff1422; color: #39ff14; padding: 0.2em 0.5em; border-radius: 3px; font-size: 0.85em; margin-right: 0.5em; border: 1px solid #39ff1466; text-decoration: none; font-weight: bold; transition: all 0.2s ease;",
                        title=f"Search for related articles about: {tag.strip()}",
                        onmouseover="this.style.backgroundColor='#39ff1466'; this.style.color='#66ff66';",
                        onmouseout="this.style.backgroundColor='#39ff1422'; this.style.color='#39ff14';"
                    )
                )
            
            meta_rows.append(
                Div(
                    Span("Tags:", cls="meta-label", style="color: #39ff14; font-weight: bold; margin-right: 0.5em; align-self: flex-start;"),
                    Div(*tag_elements, style="display: flex; flex-wrap: wrap; gap: 0.3em;"),
                    cls="meta-row",
                    style="margin-bottom: 0.5em; display: flex; align-items: flex-start;"
                )
            )
        
        # Create metadata container with improved styling
        meta_element = ArticleMeta(
            H2("Article Information", style="color: #ffe066; margin-bottom: 1em; font-size: 1.1em; border-bottom: 1px solid #39ff1444; padding-bottom: 0.3em;"),
            *meta_rows,
            cls='article-meta',
            style="background: #222a22; border: 1px solid #39ff1444; border-radius: 4px; padding: 1.5em; margin-bottom: 2em; font-size: 0.9em;"
        )
    
    # Get keywords from meta for link parsing
    keywords_list = meta.get('tags', []) if isinstance(meta, dict) else []
    
    # Process summary with keyword links
    processed_summary = parse_keywords_to_links(summary, keywords_list)
    
    # Create summary section (always visible)
    summary_element = Div(
        H2("Summary", style="color: #ffe066; border-bottom: 1px solid #39ff1444; padding-bottom: 0.3em; margin-bottom: 1em; font-size: 1.2em;"),
        Div(
            NotStr(processed_summary),
            cls='article-summary-body',
            style="color: #cccccc; line-height: 1.6; white-space: pre-wrap; max-width: 100%; overflow-wrap: break-word; background: #222a22; padding: 1.5em; border: 1px solid #39ff1444; border-radius: 4px;"
        ),
        cls='article-summary',
        style="margin-bottom: 2em;"
    )
    
    # Process full content with keyword links
    processed_content = parse_keywords_to_links(content, keywords_list)
    
    # Create full content section with expand/collapse functionality
    content_element = Div(
        # Content header with expand button
        Div(
            H2("Full Content", style="color: #ffe066; border-bottom: 1px solid #39ff1444; padding-bottom: 0.3em; margin-bottom: 1em; font-size: 1.2em; display: inline-block; margin-right: 1em;"),
            Button(
                "▼ Show Full Content",
                id="content-toggle-btn",
                onclick="toggleContent()",
                style="background: #39ff14; color: #000; border: none; padding: 0.4em 0.8em; border-radius: 4px; font-family: monospace; font-weight: bold; cursor: pointer;"
            ),
            style="display: flex; align-items: center; margin-bottom: 1em;"
        ),
        # Hidden content section
        Div(
            Div(
                NotStr(processed_content),
                cls='article-content-body',
                style="color: #cccccc; line-height: 1.6; white-space: pre-wrap; max-width: 100%; overflow-wrap: break-word; background: #1a1f1a; padding: 1.5em; border: 1px solid #39ff1444; border-radius: 4px; max-height: 400px; overflow-y: auto;"
            ),
            id="content-body",
            style="display: none; margin-bottom: 1em;"
        ),
        # JavaScript for toggle functionality
        Script("""
        function toggleContent() {
            const contentBody = document.getElementById('content-body');
            const toggleBtn = document.getElementById('content-toggle-btn');
            
            if (contentBody.style.display === 'none') {
                contentBody.style.display = 'block';
                toggleBtn.textContent = '▲ Hide Full Content';
                toggleBtn.style.background = '#ff6b6b';
            } else {
                contentBody.style.display = 'none';
                toggleBtn.textContent = '▼ Show Full Content';
                toggleBtn.style.background = '#39ff14';
            }
        }
        """),
        cls='article-content',
        style="margin-bottom: 2em;"
    )
    
    # Create back button with improved styling
    back_button = TerminalButton(
        '← Back to Results',
        onclick=f"window.location='{back_url or '/'}'",
        primary=False,
        style="margin-top: 2em; background: #666; color: #fff; padding: 0.6em 1.2em; border-radius: 4px; font-family: monospace; font-weight: bold; border: 1px solid #999; transition: all 0.2s ease; cursor: pointer;",
        onmouseover="this.style.background='#777'; this.style.borderColor='#aaa';",
        onmouseout="this.style.background='#666'; this.style.borderColor='#999';"
    ) if back_url else None
    
    # Use FastHTML's Article component with improved styling
    return FastArticle(
        title_element,
        meta_element,
        summary_element,
        content_element,
        back_button,
        cls='terminal-article-view',
        style="background: #1a1f1a; border: 1px solid #39ff1444; border-radius: 6px; padding: 2.5em; margin: 1em 0; box-shadow: 0 2px 8px rgba(57, 255, 20, 0.1);"
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


# Related articles list with match strength
def TerminalRelatedArticlesList(related_articles, current_article_id=None, algorithm_used="similarity", use_keywords=False):
    """
    Display related articles sorted by match strength with visual indicators and algorithm toggle.
    """
    # Create algorithm toggle header
    toggle_url = f"/article/{current_article_id}?use_keywords={'false' if use_keywords else 'true'}" if current_article_id else "#"
    toggle_text = "Switch to Similarity" if use_keywords else "Switch to Keywords"
    algorithm_label = "Keywords" if use_keywords else "Similarity"
    
    header_section = Div(
        Div(
            H3("Related Articles", style="color: #ffe066; margin-bottom: 0.5em; border-bottom: 1px solid #39ff1444; padding-bottom: 0.3em; display: inline-block;"),
            Div(
                Span(f"Algorithm: {algorithm_label}", style="color: #39ff14; font-weight: bold; margin-right: 1em;"),
                A(
                    f"[{toggle_text}]",
                    href=toggle_url,
                    style="color: #ffe066; text-decoration: underline; font-size: 0.9em; cursor: pointer;",
                    title=f"Switch to {'similarity-based' if use_keywords else 'keyword-based'} algorithm"
                ),
                style="font-size: 0.85em; margin-top: 0.5em;"
            ),
            style="margin-bottom: 1em;"
        )
    )
    
    if not related_articles:
        return Div(
            header_section,
            P("No related articles found.", style="color: #666; font-style: italic;"),
            cls='related-articles-empty',
            style="margin: 2em 0; padding: 1.5em; background: #222a22; border: 1px solid #39ff1444; border-radius: 4px;"
        )
    
    related_items = []
    for i, article in enumerate(related_articles):
        match_score = article.get("match_score", 0.0)
        
        # Create match strength indicator
        if match_score >= 0.7:
            strength_indicator = "🔥🔥🔥"  # High match
            strength_color = "#ff6666"
            strength_text = "High"
        elif match_score >= 0.4:
            strength_indicator = "🔥🔥"    # Medium match
            strength_color = "#ffaa66"
            strength_text = "Medium"
        elif match_score >= 0.2:
            strength_indicator = "🔥"      # Low match
            strength_color = "#ffe066"
            strength_text = "Low"
        else:
            strength_indicator = "○"       # Very low match
            strength_color = "#666666"
            strength_text = "Weak"
        
        # Build article item
        related_items.append(
            Div(
                # Article header with ranking and strength
                Div(
                    Span(f"#{i+1:02d}", cls="article-rank", style="color: #39ff14; font-family: monospace; font-weight: bold; margin-right: 0.5em;"),
                    Span(strength_indicator, style="margin-right: 0.5em;"),
                    A(
                        (article.get("url") or "Untitled") if len(article.get("url") or "Untitled") <= 50 else (article.get("url") or "Untitled")[:47] + "...",
                        href=f"/article/{article['id']}?back_url=/article/{current_article_id}%23related" if current_article_id else f"/article/{article['id']}",
                        cls="related-article-title",
                        style="color: #39ff14; text-decoration: underline; font-weight: bold; word-break: break-all;"
                    ),
                    style="display: flex; align-items: center; margin-bottom: 0.5em;"
                ),
                # Match strength and metadata
                Div(
                    Div(
                        Span("Match:", style="color: #666; margin-right: 0.5em;"),
                        Span(f"{strength_text} ({match_score:.2f})", style=f"color: {strength_color}; font-weight: bold; margin-right: 1em;"),
                        Span("Type:", style="color: #666; margin-right: 0.5em;"),
                        Span(article.get("type", "unknown").title(), style="color: #cccccc; margin-right: 1em;"),
                        Span("ID:", style="color: #666; margin-right: 0.5em;"),
                        Span(str(article["id"]), style="color: #cccccc; font-family: monospace;"),
                        style="font-size: 0.85em; margin-bottom: 0.5em;"
                    ),
                    # Article snippet
                    Div(
                        (article.get("summary") or article.get("content") or "")[:120] + ("..." if len(article.get("summary") or article.get("content") or "") > 120 else ""),
                        style="color: #888; font-size: 0.9em; line-height: 1.4; margin-left: 2em;"
                    ),
                    style="margin-left: 2.5em;"
                ),
                cls="related-article-item",
                style="margin-bottom: 1.5em; padding: 1em; border: 1px solid #39ff1422; border-radius: 4px; transition: all 0.2s ease;",
                onmouseover="this.style.borderColor='#39ff1466'; this.style.backgroundColor='#1a1f1a';",
                onmouseout="this.style.borderColor='#39ff1422'; this.style.backgroundColor='transparent';"
            )
        )
    
    return Div(
        header_section,
        P(f"Found {len(related_articles)} related article{'s' if len(related_articles) != 1 else ''} sorted by relevance:", 
          style="color: #999; margin-bottom: 1.5em; font-size: 0.9em;"),
        *related_items,
        cls='related-articles-list',
        id='related-articles-section',
        style="margin: 2em 0; padding: 1.5em; background: #222a22; border: 1px solid #39ff1444; border-radius: 4px;"
    )


# AI Suggestions Sidebar - collapsible component with button trigger
def TerminalSuggestionsPanel(suggestions=None, article_id=None, show_trigger=True):
    """
    AI-powered suggestions panel that displays as a collapsible sidebar.
    Can be triggered on-demand via button or shown immediately.
    """
    if show_trigger:
        # Show trigger button when suggestions aren't loaded yet
        return Div(
            Button(
                "🤖 Get AI Suggestions",
                id="suggestions-trigger-btn",
                onclick=f"loadSuggestions({article_id})" if article_id else "loadSuggestions()",
                style="background: #39ff14; color: #000; border: none; padding: 0.8em 1.2em; border-radius: 4px; font-family: monospace; font-weight: bold; cursor: pointer; margin: 1em 0; transition: all 0.2s ease;",
                onmouseover="this.style.background='#66ff66'; this.style.transform='scale(1.02)';",
                onmouseout="this.style.background='#39ff14'; this.style.transform='scale(1)';"
            ),
            # Hidden sidebar panel that will be populated with suggestions
            Div(
                id="suggestions-sidebar",
                style="display: none; position: fixed; top: 0; right: -400px; width: 380px; height: 100vh; background: #1a1f1a; border-left: 2px solid #39ff14; box-shadow: -4px 0 8px rgba(0,0,0,0.3); z-index: 1000; transition: right 0.3s ease; overflow-y: auto; padding: 1.5em;"
            ),
            # JavaScript for loading and displaying suggestions
            Script("""
            let suggestionsLoaded = false;
            
            function loadSuggestions(articleId = null) {
                const triggerBtn = document.getElementById('suggestions-trigger-btn');
                const sidebar = document.getElementById('suggestions-sidebar');
                
                console.log('loadSuggestions called with articleId:', articleId);
                console.log('triggerBtn:', triggerBtn);
                console.log('sidebar:', sidebar);
                
                if (!suggestionsLoaded) {
                    // Show loading state
                    triggerBtn.textContent = '🔄 Loading Suggestions...';
                    triggerBtn.disabled = true;
                    
                    // Real API call to fetch suggestions
                    const suggestionCount = 5; // Default count
                    const forceFresh = true; // Always generate fresh
                    const apiBaseUrl = 'http://127.0.0.1:8000'; // FastAPI server
                    const apiUrl = `${apiBaseUrl}/api/suggestions/${articleId}?count=${suggestionCount}&force_fresh=${forceFresh}`;
                    
                    console.log('Fetching suggestions from:', apiUrl);
                    
                    // Add timeout to the fetch request
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
                    
                    fetch(apiUrl, { 
                        signal: controller.signal,
                        mode: 'cors',
                        credentials: 'include'
                    })
                        .then(response => {
                            clearTimeout(timeoutId);
                            console.log('API response status:', response.status);
                            console.log('API response headers:', response.headers);
                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }
                            return response.json();
                        })
                        .then(data => {
                            console.log('API response data:', data);
                            if (data.success && data.suggestions) {
                                showRealSuggestions(data.suggestions, data.context);
                            } else {
                                console.log('API failed or no suggestions, showing fallback');
                                showSampleSuggestions(); // Fallback to sample
                            }
                            suggestionsLoaded = true;
                            triggerBtn.textContent = '🤖 Show/Hide AI Suggestions';
                            triggerBtn.disabled = false;
                        })
                        .catch(error => {
                            clearTimeout(timeoutId);
                            console.error('Error fetching suggestions:', error);
                            console.error('Error type:', error.name);
                            console.error('Error message:', error.message);
                            if (error.name === 'AbortError') {
                                console.log('Request timed out after 30 seconds');
                            }
                            showSampleSuggestions(); // Fallback to sample
                            suggestionsLoaded = true;
                            triggerBtn.textContent = '🤖 Show/Hide AI Suggestions';
                            triggerBtn.disabled = false;
                        });
                } else {
                    console.log('Suggestions already loaded, toggling sidebar');
                    toggleSidebar();
                }
            }
            
            function toggleSidebar() {
                const sidebar = document.getElementById('suggestions-sidebar');
                const isVisible = sidebar.style.right === '0px';
                
                if (isVisible) {
                    sidebar.style.right = '-400px';
                    sidebar.style.display = 'none';
                } else {
                    sidebar.style.display = 'block';
                    sidebar.style.right = '0px';
                }
            }
            
            function closeSidebar() {
                const sidebar = document.getElementById('suggestions-sidebar');
                sidebar.style.right = '-400px';
                sidebar.style.display = 'none';
            }
            
            function showRealSuggestions(suggestions, context) {
                console.log('showRealSuggestions called with:', suggestions, context);
                const sidebar = document.getElementById('suggestions-sidebar');
                
                // Generate suggestions HTML from real API data
                const suggestionsHtml = suggestions.map((suggestion, index) => {
                    const typeColors = {
                        'question': '#ff6b6b',
                        'strategy': '#4ecdc4', 
                        'application': '#45b7d1',
                        'implementation': '#f9ca24',
                        'topic': '#f0932b'
                    };
                    
                    const typeIcons = {
                        'question': '❓',
                        'strategy': '📊',
                        'application': '🏥',
                        'implementation': '⚙️',
                        'topic': '📋'
                    };
                    
                    const suggestionType = suggestion.type || 'topic';
                    const typeColor = typeColors[suggestionType] || '#39ff14';
                    const typeIcon = typeIcons[suggestionType] || '💡';
                    
                    return `
                        <div style="margin-bottom: 1.2em; padding: 1em; background: #222a22; border: 1px solid #39ff1444; border-radius: 4px; transition: all 0.2s ease;" 
                             onmouseover="this.style.borderColor='#39ff1466'; this.style.backgroundColor='#2a2f2a';"
                             onmouseout="this.style.borderColor='#39ff1444'; this.style.backgroundColor='#222a22';">
                            <div style="display: flex; align-items: center; margin-bottom: 0.5em;">
                                <span style="margin-right: 0.5em; font-size: 1.1em;">${typeIcon}</span>
                                <span style="color: ${typeColor}; font-size: 0.75em; text-transform: uppercase; font-weight: bold; margin-right: 0.5em;">${suggestionType}</span>
                                <span style="color: #666; font-size: 0.7em;">#${index + 1}</span>
                            </div>
                            <div style="color: #ffe066; font-weight: bold; margin-bottom: 0.5em; font-size: 0.9em; line-height: 1.3;">
                                ${suggestion.title || `Suggestion ${index + 1}`}
                            </div>
                            <div style="color: #cccccc; font-size: 0.8em; line-height: 1.4;">
                                ${suggestion.description || 'No description available.'}
                            </div>
                        </div>
                    `;
                }).join('');
                
                // Context info for debugging
                const contextInfo = context ? `
                    <div style="margin-bottom: 1em; padding: 0.8em; background: #1a2a1a; border: 1px solid #39ff1422; border-radius: 4px; font-size: 0.75em; color: #999;">
                        <div style="color: #39ff14; margin-bottom: 0.3em;">📊 Generation Info:</div>
                        <div>Suggestions: ${context.suggestion_count || 0}/${context.requested_count || 0}</div>
                        <div>Recent articles: ${context.recent_articles_count || 0}</div>
                        <div>Similar articles: ${context.similar_articles_count || 0}</div>
                        <div>Generation time: ${context.generation_time_ms || 0}ms</div>
                        <div>Fresh generation: ${context.force_fresh ? 'Yes' : 'No'}</div>
                        <div>Generated: ${new Date(context.generated_at || Date.now()).toLocaleTimeString()}</div>
                    </div>
                ` : '';
                
                sidebar.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5em; padding-bottom: 0.5em; border-bottom: 1px solid #39ff1444;">
                        <h3 style="color: #ffe066; margin: 0; font-size: 1.1em;">🤖 AI Suggestions</h3>
                        <button onclick="closeSidebar()" style="background: none; border: none; color: #39ff14; font-size: 1.2em; cursor: pointer; padding: 0.2em;">✕</button>
                    </div>
                    
                    <div style="margin-bottom: 1em; padding: 0.8em; background: #222a22; border: 1px solid #39ff1444; border-radius: 4px;">
                        <div style="color: #39ff14; font-size: 0.85em; margin-bottom: 0.5em; font-weight: bold;">⚙️ Settings</div>
                        <label style="display: block; color: #cccccc; font-size: 0.8em; margin-bottom: 0.8em;">
                            Suggestion Count:
                            <select id="suggestion-count-select" onchange="updateSuggestionCount()" style="margin-left: 0.5em; background: #1a1f1a; color: #39ff14; border: 1px solid #39ff1444; padding: 0.2em;">
                                <option value="3">3</option>
                                <option value="5" selected>5 (default)</option>
                                <option value="8">8</option>
                                <option value="10">10</option>
                                <option value="15">15</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="50">50</option>
                                <option value="100">100 (max)</option>
                            </select>
                        </label>
                        <label style="display: block; color: #cccccc; font-size: 0.8em; margin-bottom: 0.5em;">
                            <input type="checkbox" id="fresh-generation-check" checked style="margin-right: 0.5em; accent-color: #39ff14;">
                            Always generate fresh (no caching)
                        </label>
                        <div style="color: #666; font-size: 0.7em; font-style: italic;">
                            Higher counts may take longer to generate
                        </div>
                    </div>
                    
                    ${contextInfo}
                    
                    <div id="suggestions-content">
                        ${suggestionsHtml}
                    </div>
                    
                    <div style="margin-top: 1.5em; padding-top: 1em; border-top: 1px solid #39ff1444;">
                        <button onclick="regenerateSuggestions()" style="width: 100%; background: #39ff14; color: #000; border: none; padding: 0.6em; border-radius: 4px; font-family: monospace; font-weight: bold; cursor: pointer;">
                            🔄 Regenerate Suggestions
                        </button>
                    </div>
                `;
                
                // Show the sidebar
                console.log('Showing sidebar, setting right to 0px');
                sidebar.style.display = 'block';
                sidebar.style.right = '0px';
            }
            
            function showSampleSuggestions() {
                console.log('showSampleSuggestions called');
                const sidebar = document.getElementById('suggestions-sidebar');
                sidebar.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5em; padding-bottom: 0.5em; border-bottom: 1px solid #39ff1444;">
                        <h3 style="color: #ffe066; margin: 0; font-size: 1.1em;">🤖 AI Suggestions</h3>
                        <button onclick="closeSidebar()" style="background: none; border: none; color: #39ff14; font-size: 1.2em; cursor: pointer; padding: 0.2em;">✕</button>
                    </div>
                    
                    <div style="margin-bottom: 1em; padding: 0.8em; background: #ff4444; border: 1px solid #ff6666; border-radius: 4px;">
                        <div style="color: #fff; font-size: 0.85em; margin-bottom: 0.5em; font-weight: bold;">⚠️ Fallback Mode</div>
                        <div style="color: #ffdddd; font-size: 0.8em;">Using sample suggestions - API unavailable</div>
                    </div>
                    
                    <div style="margin-bottom: 1em; padding: 0.8em; background: #222a22; border: 1px solid #39ff1444; border-radius: 4px;">
                        <div style="color: #39ff14; font-size: 0.85em; margin-bottom: 0.5em; font-weight: bold;">⚙️ Settings</div>
                        <label style="display: block; color: #cccccc; font-size: 0.8em; margin-bottom: 0.8em;">
                            Suggestion Count:
                            <select id="suggestion-count-select-fallback" onchange="updateSuggestionCount()" style="margin-left: 0.5em; background: #1a1f1a; color: #39ff14; border: 1px solid #39ff1444; padding: 0.2em;">
                                <option value="3">3</option>
                                <option value="5" selected>5 (default)</option>
                                <option value="8">8</option>
                                <option value="10">10</option>
                                <option value="15">15</option>
                                <option value="20">20</option>
                                <option value="30">30</option>
                                <option value="50">50</option>
                                <option value="100">100 (max)</option>
                            </select>
                        </label>
                        <label style="display: block; color: #cccccc; font-size: 0.8em; margin-bottom: 0.5em;">
                            <input type="checkbox" id="fresh-generation-check-fallback" checked disabled style="margin-right: 0.5em; accent-color: #39ff14;">
                            Always generate fresh (fallback mode)
                        </label>
                        <div style="color: #666; font-size: 0.7em; font-style: italic;">
                            Using sample suggestions - API unavailable
                        </div>
                    </div>
                    
                    <div id="suggestions-content">
                        ${generateSampleSuggestions()}
                    </div>
                    
                    <div style="margin-top: 1.5em; padding-top: 1em; border-top: 1px solid #39ff1444;">
                        <button onclick="regenerateSuggestions()" style="width: 100%; background: #39ff14; color: #000; border: none; padding: 0.6em; border-radius: 4px; font-family: monospace; font-weight: bold; cursor: pointer;">
                            🔄 Regenerate Suggestions
                        </button>
                    </div>
                `;
                
                // Show the sidebar
                console.log('Showing fallback sidebar, setting right to 0px');
                sidebar.style.display = 'block';
                sidebar.style.right = '0px';
            }
            
            function generateSampleSuggestions() {
                const suggestions = [
                    {
                        type: 'question',
                        title: 'Implementation Challenges',
                        description: 'What are the key technical and regulatory hurdles for implementing this AI solution in healthcare settings?'
                    },
                    {
                        type: 'strategy',
                        title: 'ROI Analysis Framework',
                        description: 'How can we measure and demonstrate the business value and patient outcomes of this approach?'
                    },
                    {
                        type: 'application',
                        title: 'Clinical Workflow Integration',
                        description: 'Which specific healthcare workflows would benefit most from this technology and why?'
                    },
                    {
                        type: 'implementation',
                        title: 'Data Infrastructure Requirements',
                        description: 'What data sources, APIs, and infrastructure would be needed to operationalize this solution?'
                    },
                    {
                        type: 'topic',
                        title: 'Regulatory Compliance Considerations',
                        description: 'How do HIPAA, FDA guidelines, and other regulations impact the development and deployment strategy?'
                    }
                ];
                
                return suggestions.map((suggestion, index) => {
                    const typeColors = {
                        'question': '#ff6b6b',
                        'strategy': '#4ecdc4', 
                        'application': '#45b7d1',
                        'implementation': '#f9ca24',
                        'topic': '#f0932b'
                    };
                    
                    const typeIcons = {
                        'question': '❓',
                        'strategy': '📊',
                        'application': '🏥',
                        'implementation': '⚙️',
                        'topic': '📋'
                    };
                    
                    return `
                        <div style="margin-bottom: 1.2em; padding: 1em; background: #222a22; border: 1px solid #39ff1444; border-radius: 4px; transition: all 0.2s ease;" 
                             onmouseover="this.style.borderColor='#39ff1466'; this.style.backgroundColor='#2a2f2a';"
                             onmouseout="this.style.borderColor='#39ff1444'; this.style.backgroundColor='#222a22';">
                            <div style="display: flex; align-items: center; margin-bottom: 0.5em;">
                                <span style="margin-right: 0.5em; font-size: 1.1em;">${typeIcons[suggestion.type]}</span>
                                <span style="color: ${typeColors[suggestion.type]}; font-size: 0.75em; text-transform: uppercase; font-weight: bold; margin-right: 0.5em;">${suggestion.type}</span>
                                <span style="color: #666; font-size: 0.7em;">#${index + 1}</span>
                            </div>
                            <div style="color: #ffe066; font-weight: bold; margin-bottom: 0.5em; font-size: 0.9em; line-height: 1.3;">
                                ${suggestion.title}
                            </div>
                            <div style="color: #cccccc; font-size: 0.8em; line-height: 1.4;">
                                ${suggestion.description}
                            </div>
                        </div>
                    `;
                }).join('');
            }
            
            function regenerateSuggestions() {
                const content = document.getElementById('suggestions-content');
                content.innerHTML = '<div style="text-align: center; color: #39ff14; padding: 2em;">🔄 Regenerating suggestions...</div>';
                
                // Get current suggestion count and fresh generation setting
                const countSelect = document.getElementById('suggestion-count-select');
                const freshCheck = document.getElementById('fresh-generation-check');
                const suggestionCount = countSelect ? countSelect.value : 5;
                const forceFresh = freshCheck ? freshCheck.checked : true;
                
                // Get article ID from the current page (assuming it's in the URL or passed to loadSuggestions)
                const urlParts = window.location.pathname.split('/');
                const articleId = urlParts[urlParts.indexOf('article') + 1];
                
                if (articleId) {
                    const apiBaseUrl = 'http://127.0.0.1:8000'; // FastAPI server
                    fetch(`${apiBaseUrl}/api/suggestions/${articleId}?count=${suggestionCount}&force_fresh=${forceFresh}`)
                        .then(response => response.json())
                        .then(data => {
                            if (data.success && data.suggestions) {
                                // Update just the content area with new suggestions
                                const suggestionsHtml = data.suggestions.map((suggestion, index) => {
                                    const typeColors = {
                                        'question': '#ff6b6b',
                                        'strategy': '#4ecdc4', 
                                        'application': '#45b7d1',
                                        'implementation': '#f9ca24',
                                        'topic': '#f0932b'
                                    };
                                    
                                    const typeIcons = {
                                        'question': '❓',
                                        'strategy': '📊',
                                        'application': '🏥',
                                        'implementation': '⚙️',
                                        'topic': '📋'
                                    };
                                    
                                    const suggestionType = suggestion.type || 'topic';
                                    const typeColor = typeColors[suggestionType] || '#39ff14';
                                    const typeIcon = typeIcons[suggestionType] || '💡';
                                    
                                    return `
                                        <div style="margin-bottom: 1.2em; padding: 1em; background: #222a22; border: 1px solid #39ff1444; border-radius: 4px; transition: all 0.2s ease;" 
                                             onmouseover="this.style.borderColor='#39ff1466'; this.style.backgroundColor='#2a2f2a';"
                                             onmouseout="this.style.borderColor='#39ff1444'; this.style.backgroundColor='#222a22';">
                                            <div style="display: flex; align-items: center; margin-bottom: 0.5em;">
                                                <span style="margin-right: 0.5em; font-size: 1.1em;">${typeIcon}</span>
                                                <span style="color: ${typeColor}; font-size: 0.75em; text-transform: uppercase; font-weight: bold; margin-right: 0.5em;">${suggestionType}</span>
                                                <span style="color: #666; font-size: 0.7em;">#${index + 1}</span>
                                            </div>
                                            <div style="color: #ffe066; font-weight: bold; margin-bottom: 0.5em; font-size: 0.9em; line-height: 1.3;">
                                                ${suggestion.title || `Suggestion ${index + 1}`}
                                            </div>
                                            <div style="color: #cccccc; font-size: 0.8em; line-height: 1.4;">
                                                ${suggestion.description || 'No description available.'}
                                            </div>
                                        </div>
                                    `;
                                }).join('');
                                
                                content.innerHTML = suggestionsHtml;
                            } else {
                                content.innerHTML = generateSampleSuggestions();
                            }
                        })
                        .catch(error => {
                            console.error('Error regenerating suggestions:', error);
                            content.innerHTML = generateSampleSuggestions();
                        });
                } else {
                    // Fallback to sample suggestions if no article ID
                    setTimeout(() => {
                        content.innerHTML = generateSampleSuggestions();
                    }, 1000);
                }
            }
            
            function updateSuggestionCount() {
                // Trigger regeneration with new count
                regenerateSuggestions();
            }
            """),
            cls="ai-suggestions-panel",
            style="margin: 2em 0;"
        )
    
    # When suggestions are provided, show them directly in the sidebar format
    if suggestions:
        suggestion_items = []
        for i, suggestion in enumerate(suggestions):
            type_colors = {
                'question': '#ff6b6b',
                'strategy': '#4ecdc4', 
                'application': '#45b7d1',
                'implementation': '#f9ca24',
                'topic': '#f0932b'
            }
            
            type_icons = {
                'question': '❓',
                'strategy': '📊',
                'application': '🏥',
                'implementation': '⚙️',
                'topic': '📋'
            }
            
            suggestion_type = suggestion.get('type', 'topic')
            type_color = type_colors.get(suggestion_type, '#39ff14')
            type_icon = type_icons.get(suggestion_type, '💡')
            
            suggestion_items.append(
                Div(
                    Div(
                        Span(type_icon, style="margin-right: 0.5em; font-size: 1.1em;"),
                        Span(suggestion_type.upper(), style=f"color: {type_color}; font-size: 0.75em; text-transform: uppercase; font-weight: bold; margin-right: 0.5em;"),
                        Span(f"#{i + 1}", style="color: #666; font-size: 0.7em;"),
                        style="display: flex; align-items: center; margin-bottom: 0.5em;"
                    ),
                    Div(
                        suggestion.get('title', f'Suggestion {i + 1}'),
                        style="color: #ffe066; font-weight: bold; margin-bottom: 0.5em; font-size: 0.9em; line-height: 1.3;"
                    ),
                    Div(
                        suggestion.get('description', 'No description available.'),
                        style="color: #cccccc; font-size: 0.8em; line-height: 1.4;"
                    ),
                    style="margin-bottom: 1.2em; padding: 1em; background: #222a22; border: 1px solid #39ff1444; border-radius: 4px; transition: all 0.2s ease;",
                    onmouseover="this.style.borderColor='#39ff1466'; this.style.backgroundColor='#2a2f2a';",
                    onmouseout="this.style.borderColor='#39ff1444'; this.style.backgroundColor='#222a22';"
                )
            )
        
        return Div(
            H3("🤖 AI Suggestions", style="color: #ffe066; margin-bottom: 1em; font-size: 1.1em; border-bottom: 1px solid #39ff1444; padding-bottom: 0.3em;"),
            *suggestion_items,
            cls="suggestions-list",
            style="margin: 2em 0; padding: 1.5em; background: #1a1f1a; border: 1px solid #39ff1444; border-radius: 4px;"
        )
    
    # Default empty state
    return Div(
        Button(
            "🤖 Get AI Suggestions",
            style="background: #39ff14; color: #000; border: none; padding: 0.8em 1.2em; border-radius: 4px; font-family: monospace; font-weight: bold; cursor: pointer;",
            onclick="alert('AI suggestions feature will be implemented soon!')"
        ),
        cls="ai-suggestions-placeholder",
        style="margin: 2em 0; text-align: center; padding: 2em; background: #222a22; border: 1px dashed #39ff1444; border-radius: 4px;"
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
