## Relevant Files

- `src/knowledge_base/routes/ui.py` - Main FastHTML route handlers for the Knowledge Base UI.
- `src/knowledge_base/ui/components.py` - FastHTML UI components for retro terminal look and article rendering.
- `src/knowledge_base/ui/styles/retro_terminal.css` - CSS for 80s retro terminal theme.
- `src/knowledge_base/core/content_manager.py` - Logic for retrieving, searching, and filtering articles.
- `src/knowledge_base/core/models.py` - Data models for articles, metadata, and suggestions.
- `src/knowledge_base/ai/suggestion_engine.py` - AI/ML logic for generating idea/question suggestions.
- `tests/routes/test_ui.py` - Unit tests for UI route handlers.
- `tests/ui/test_components.py` - Unit tests for UI components.
- `tests/ai/test_suggestion_engine.py` - Unit tests for the suggestion engine.

### Notes

- Unit tests should typically be placed alongside the code files they are testing (e.g., `MyComponent.py` and `MyComponent.test.py` in the same directory).
- Use `npx jest [optional/path/to/test/file]` to run tests. Running without a path executes all tests found by the Jest configuration.

## Tasks

- [x] 1.0 Design and Set Up the 80s Retro Terminal UI Framework
  - [x] 1.1 Create `retro_terminal.css` for dark background, green/amber text, monospace font, and blinking cursor (see PRD and FastHTML docs for custom styles).
  - [x] 1.2 Build FastHTML UI components in `components.py` for containers, buttons, search bar, results list, article view, and navigation controls, using FastHTML primitives (see `llms-ctx.txt` for `Container`, `Button`, `Titled`, etc).
  - [x] 1.3 Integrate the CSS and components into a FastHTML layout for the main UI.
  - [x] 1.4 Ensure keyboard navigation and sufficient contrast for accessibility.
  - [x] 1.5 Write unit tests for UI components.

- [x] 2.0 Implement Article Search and Filtering Functionality
  - [x] 2.1 Add a FastHTML route and handler for the search page in `ui.py`.
  - [x] 2.2 Implement a search form using FastHTML's `Form`, `Input`, and `Button` components.
  - [x] 2.3 Connect the search form to backend logic in `content_manager.py` for full-text and keyword search.
  - [x] 2.3.1 Make the url on each individual article page a link that opens in a new tab.
  - [x] 2.4 Add filtering controls for tags, date, and author using FastHTML form elements.
  - [x] 2.5 Display search results using a styled results list component.
  - [x] 2.6 Paginate or lazy-load results for large result sets.
  - [x] 2.7 Write unit tests for search/filter logic and routes.

- [ ] 3.0 Build Article View with Metadata, Content, and Navigation
  - [ ] 3.1 Create an article view component using FastHTML (`Article`, `ArticleTitle`, `ArticleMeta`).
  - [ ] 3.2 Render article metadata (title, author, date, tags) at the top, content below.
  - [ ] 3.3 Add a back button using FastHTML's `Button` component to return to previous results or articles.
  - [ ] 3.4 Ensure clear, readable formatting for article content and metadata.
  - [ ] 3.5 Write unit tests for article view rendering and navigation.

- [ ] 4.0 Implement Related Articles and Obsidian-Style Link Navigation
  - [ ] 4.1 Parse article content for keywords/links and render them as clickable FastHTML `A` components.
  - [ ] 4.2 On click, show a list of related articles sorted by match strength.
  - [ ] 4.3 Support navigation history for back/forward between articles and search results.
  - [ ] 4.4 Highlight or style links for easy navigation (using retro terminal theme).
  - [ ] 4.5 Write unit tests for link navigation and related article logic.

- [ ] 5.0 Add AI-Driven Suggestions for New Ideas or Questions
  - [ ] 5.1 Implement a suggestion engine in `suggestion_engine.py` (use simple keyword matching or integrate with existing AI/ML modules).
  - [ ] 5.2 Display suggestions in the article view using a FastHTML component (e.g., below the article or in a sidebar).
  - [ ] 5.3 Ensure suggestions update based on current article or search context.
  - [ ] 5.4 Write unit tests for suggestion generation and display.

- [ ] 6.0 Ensure Accessibility, Deep-Linking, and Performance Requirements
  - [ ] 6.1 Test and improve keyboard navigation and screen reader support.
  - [ ] 6.2 Implement deep-linking/bookmarking for articles and searches (e.g., via URL params).
  - [ ] 6.3 Optimize UI and backend for <500ms response time on search/navigation.
  - [ ] 6.4 Monitor and log system uptime and responsiveness.
  - [ ] 6.5 Write integration tests for accessibility and performance features.