# Knowledge Base

## Features
- Supports summarization of web content from URLs, ArXiv papers, and GitHub repositories
- Uses OpenAI GPT model for generating high-quality summaries

## Installation
1. **Clone the repository:**
   ```sh
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Install dependencies:**
   ```sh
   pyenv virtualenv kb-env
   pyenv activate kb-env
   pip install -r requirements.txt
   ```

3. **Set up your .env file with the following constants:**
```sh
touch .env
OPENAI_API_KEY="<key>"
DSV_KB_PATH="<path to Data-Science-Vault/Knowledge-base>" # for obsidian integration
DB_CONN_STRING="<postgres connection string for prod db>"
TEST_DB_CONN_STRING="<postgres connection string for test db>"
DATA_DIR="<typically the same as the DSV_KB_PATH>"
LLM_MODEL_NAME="<default llm>" # Example: "gpt-4o-mini" or other model identifier used by LLMFactory

```

## Usage
Once the virtual environment is activated, you can run the application and CLI commands.

### Single Command Option
```sh
./start.sh
```
The script will:
- Check/start PostgreSQL via Homebrew
- Start FastAPI backend on port 8000
- Start FastHTML UI on port 5001
- Handle graceful shutdown with Ctrl+C

### Multi Command Option
* Start postgres
* Start the fastapi backend in a separate terminal window
```sh
python src/app.py
```
* Start the UI in a separate terminal window
```sh
uvicorn ui:app --reload --host 0.0.0.0 --port 5001
```

* A dev server can also be started by
```sh
python src/knowledge_base/ui/main.py
```

## CLI
All CLI commands should be run using `python src/cli.py ...`.

### Process URL
```sh
python src/cli.py process https://example.com
```

### Debug mode: do not save
```sh
python src/cli.py process -d https://example.com
```

### Process batch of URLs
```sh
python src/cli.py process batch <urls.txt>
```

### List and browse data files - TO BE BUILT
```sh
# List all data files (default shows 20 most recent)
python src/cli.py data list

# Filter by file type
python src/cli.py data list --type github

# Show only files from last 7 days
python src/cli.py data list --days 7

# View file details in pretty format
python src/cli.py data view /path/to/file.json

# View raw JSON content
python src/cli.py data view /path/to/file.json --format raw

# View as markdown
python src/cli.py data view /path/to/file.json --format markdown

# Show stats about knowledge base files
python src/cli.py data stats

# List all file types
python src/cli.py data types
```

### Set up database
```sh
python scripts/build_db.py
```

### Load Processed Data into Database
To load processed JSON files (e.g., from a directory specified by `DATA_DIR` or a custom path) into the database:
```sh
python src/cli.py db load
```
**Options:**
-   `--dir DIRECTORY`: Specify the directory containing JSON files to load. Defaults to the `DATA_DIR` environment variable.
-   `--debug`: Use the test database connection string (`TEST_DB_CONN_STRING`).
-   `--skip-duplicates` / `--no-skip-duplicates`: Skip loading if a record with the same URL and timestamp already exists (default is to skip).

Example:
```sh
python src/cli.py db load --dir /path/to/my/json_data --debug
```

### Query Database - BROKEN
To search for content within the database:
```sh
python src/cli.py db query "your search query text" [options]
```
**Arguments:**
-   `query_text`: The text to search for in document content and summaries.

**Options:**
-   `--keywords TEXT`: Comma-separated keywords to filter by (e.g., "ai,python").
-   `--type TEXT`: Filter by document type (e.g., "github", "arxiv", "web").
-   `--limit INTEGER`: Maximum number of results to return (default: 10).
-   `--debug`: Use the test database connection string.

Example:
```sh
python src/cli.py db query "transformer models" --keywords "nlp,deep-learning" --type arxiv --limit 5
```

# DANGER ZONE
```sh
createdb knowledge_base # manually create the db if setup script fails to
createdb knowledge_base_test # manually create the db if setup script fails to
```

```sh
dropdb knowledge_base # THIS IS PERMANENT
dropdb knowledge_base_test # THIS IS PERMANENT
```


## Running the FastAPI Application
To run the FastAPI application:
```sh
python src/app.py
```

The application will typically be available at `http://127.0.0.1:8000`.

## Jina online html to markdown
jina_url = "https://r.jina.ai/<URL>"

## Note on Obsidian Note Titles
Obsidian note titles (filenames) are now standardized:
-   Titles are derived from the content's H1 heading if available, otherwise from the URL.
-   Dashes (`-`) and underscores (`_`) in the derived title are replaced with spaces.
-   Other special characters are removed to create cleaner filenames.
-   The H1 heading within the note content is also updated to match this standardized title.
This ensures more readable and consistent note titles in your Obsidian vault.

# NOTE set DB_CONN_STRING in .env to use test or prod db
## Features to Build
* Data Viewer
 * Hamel [Blog](https://hamel.dev/blog/posts/field-guide/#the-most-important-ai-investment-a-simple-data-viewer)
 * Here’s what makes a good data annotation tool:
 * Show all context in one place. Don’t make users hunt through different systems to understand what happened.
 * Make feedback trivial to capture. One-click correct/incorrect buttons beat lengthy forms.
 * Capture open-ended feedback. This lets you capture nuanced issues that don’t fit into a pre-defined taxonomy.
 * Enable quick filtering and sorting. Teams need to easily dive into specific error types. In the example above, NurtureBoss can quickly filter by the channel (voice, text, chat) or the specific property they want to look at quickly.
 * Have hotkeys that allow users to navigate between data examples and annotate without clicking.


## To Do
* Build a context of articles and chat with it
* Content recommendations
* DB Maintenance module
   * Update, delete
   * Rebuild
* Manually update a record via UI
* UI
   * View article content
   * basic db stats
   * clusters of articles, top, recent
   * search, semantic
   * article type distribution
   * article relationship network
   * how can I discover new ideas and help make connections, possibly to my writing topics
   * keyword counts, similarity
   * export data
* put constants in a database table, like default llm, dsv_kb_path, etc
   * Like Academic AI Platform
   * Use configs to update software and launch
   * Data driven build and update
   * Configs live in a database
   * API to interact with the database
* Add safety feature for deletes - must enter a code as a url parameter
* Content Manager functions
   * clean
   * dedupe
   * delete
   * update
   * Method for deduping the db
   * Way to complete missing data, such as ai summary or embeddings
* specify llm from API
* get default embedding model from API
* set default embedding model from API
* specify embedding model from API
* get default embedding model from API
* set default embedding model from API
* Deal with files that are too long to fit in context window
* Fallback for LLM failures where I still want the item in my database
   * Semi-manual mode?
* Claude integration
* Local embedding model option
* Local summarization model option
