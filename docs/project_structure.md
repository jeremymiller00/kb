# Project Structure

This document outlines the structure of the Knowledge Base project.

```
knowledge-base-project-root/
│
├── README.md                  # Main project documentation, setup, and usage
├── pyproject.toml             # Project metadata, dependencies (Poetry)
├── Makefile                   # Optional: Common commands and utilities
├── .env.example               # Example environment variables
│
├── src/                       # Source code
│   ├── app.py                 # FastAPI application entry point
│   │
│   └── knowledge_base/        # Main application package
│       ├── __init__.py
│       │
│       ├── ai/                # AI/ML components
│       │   ├── __init__.py
│       │   ├── base_llm.py
│       │   ├── llm_factory.py
│       │   ├── openai_llm.py
│       │   ├── anthropic_llm.py  # (Conceptual: if implemented)
│       │   ├── remote_llm.py     # (Conceptual: if used for other remote models)
│       │   └── embedding_manager.py # (Conceptual: for future centralized embedding logic)
│       │
│       ├── config_manager.py  # Manages global configurations (default models)
│       │
│       ├── core/              # Core application logic and Pydantic models
│       │   ├── __init__.py
│       │   ├── content_manager.py
│       │   └── models.py
│       │
│       ├── extractors/        # Content source extractors
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── arxiv_extractor.py
│       │   ├── github_repo_extractor.py
│       │   ├── github_notebook_extractor.py
│       │   ├── html_extractor.py
│       │   ├── huggingface_extractor.py
│       │   └── youtube_extractor.py
│       │
│       ├── routes/            # API route definitions (FastAPI)
│       │   ├── __init__.py
│       │   ├── admin.py       # Admin routes for configuration
│       │   ├── content.py     # Main content processing and CRUD
│       │   └── process.py     # (Note: process.py's role might be reduced, with logic in content.py)
│       │
│       ├── storage/           # Data persistence logic
│       │   ├── __init__.py
│       │   └── database.py    # PostgreSQL interactions
│       │
│       └── utils/             # Shared utilities
│           ├── __init__.py
│           ├── logger.py
│           └── prompts.py     # LLM prompts
│
├── tests/                   # Test suite (mirroring src structure)
│   ├── __init__.py
│   ├── conftest.py          # (Optional: Pytest fixtures)
│   ├── ai/
│   │   ├── __init__.py
│   │   └── ... (test_config_manager.py, test_llm_factory.py, etc.)
│   ├── core/
│   │   ├── __init__.py
│   │   └── ... (test_content_manager.py, test_models.py)
│   ├── extractors/
│   │   ├── __init__.py
│   │   └── ...
│   ├── routes/
│   │   ├── __init__.py
│   │   └── ... (test_admin_routes.py, test_content_routes.py, etc.)
│   └── storage/
│       ├── __init__.py
│       └── ... (test_database.py)
│
├── scripts/                 # Utility and maintenance scripts
│   ├── build_db.py          # Script to build/initialize the database
│   └── ...                  # (Other scripts like migrate_data.py, backup.py if they exist)
│
└── docs/                    # Project documentation
    ├── project_structure.md # This file
    ├── api_design.md        # API endpoint details
    ├── prd.md               # Product Requirements Document
    └── ...                  # (Other relevant markdown files)

```

### Key Aspects of the Structure:
-   **`src/` Directory**: Contains all application source code.
    -   **`app.py`**: Entry point for the FastAPI web application.
    -   **`knowledge_base/`**: The main Python package for the application.
        -   **`ai/`**: Modules related to artificial intelligence, including LLM interactions and embedding management.
        -   **`config_manager.py`**: Manages global application configurations, such as default model choices.
        -   **`core/`**: Central application logic, including content management (`content_manager.py`) and data models (`models.py`).
        -   **`extractors/`**: Modules for extracting content from various sources (e.g., ArXiv, GitHub, web pages).
        -   **`routes/`**: Defines the FastAPI API endpoints for different functionalities (admin, content, data).
        -   **`static/`**: Contains static assets (HTML, CSS) for any simple web UIs provided by the application.
        -   **`storage/`**: Handles data persistence, primarily database interactions (`database.py`).
        -   **`utils/`**: Shared utility functions and classes, like logging, data viewing helpers, and prompts.
-   **`tests/` Directory**: Contains unit and integration tests, mirroring the structure of the `src/knowledge_base/` package.
-   **`scripts/` Directory**: For operational scripts, such as database setup or data migration.
-   **`docs/` Directory**: Contains project documentation.
-   **`pyproject.toml`**: Manages project dependencies and build settings using Poetry.
-   **`.env.example`**: Template for environment variables.

### Departures from Older Conceptual Structures:
-   **FastHTML UI**: The project uses FastHTML for UI rather than JavaScript. The UI is built with FastHTML components in the ui/ directory.
-   **No Dedicated `processors/` Package**: Content processing logic is generally integrated within `ContentManager`, AI modules, or extractors as needed.
-   **No JavaScript UI**: The project does not use static HTML/JavaScript files for UI. All UI is built with FastHTML in Python.
-   **Data Storage Paths**: The actual storage locations for user-generated data (JSON files, Obsidian notes, etc.) are defined by environment variables (`DSV_KB_PATH`, `DATA_DIR`) and are not part of the tracked repository structure.

This structure promotes modularity and clear separation of concerns, facilitating development and maintenance.
```
