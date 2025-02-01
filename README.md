# Knowledge Base

This is the Swagger / FASTAPI version of the Knowledge Base App
This is what I am currently working on
The GUI version is knowledge-base-loader
If any visualizations are needed, use Jupyter

The CLI is useful for when the database is not present
As of 2025-01-03, workflow is to add articles via cli, worry about database later
Building the DB is easy and fast

# NOTE set DB_CONN_STRING in .env to use test or prod db

## To Do
* Basic Unit Tests
 * Content Manager - done
 * Storage
 * Models
 * Routes
 * Utils
 * AI stuff
* Discovery module
 * Find related content based on some input
  * topic, title, keyword, relationship
 * recommend content
* be able to add items from work laptop, even though DB lives on personal laptop - how important is this really?
 * Try catch DB insert
 * Somehow mark that it wasn't inserted
 * At each new insert, check for uninserted
 * Manually trigger check for uninserted
* put constants in a database table, like default llm, dsv_kb_path, etc
 * Like Academic AI Platform
 * Use configs to update software and launch
 * Data driven build and update
 * Configs live in a database
 * API to interact with the database
* Fix obsidian note titles, not dashes or underscore
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


## Jina online html to markdown
jina_url = "https://r.jina.ai/<URL>"

## Features

- Supports summarization of web content from URLs, ArXiv papers, and GitHub repositories
- Uses OpenAI GPT model for generating high-quality summaries

## Installation

1. Create and start virtual environment:
```sh
pyenv virtualenv kb-env
pyenv activate kb-env
```

2. Install the required dependencies:
```sh
pip install -r requirements.txt
```

3. Set up your .env file with the following constants:
```sh
touch .env
OPENAI_API_KEY="<key>"
DSV_KB_PATH="<path to Data-Science-Vault/Knowledge-base>" # for obsidian integration
DB_CONN_STRING="<postgres connection string for prod db>"
TEST_DB_CONN_STRING="<postgres connection string for test db>"
DATA_DIR="<typically the same as the DSV_KB_PATH>"
LLM_MODEL_NAME="<default llm>"

```

4. Update DSV_KB_PATH in .env with absolute path
This is to connect to the Obsidian Vault Knowledge Base
```sh
echo "DSV_KB_PATH='/Users/jeremy.miller/Desktop/Data-Science-Vault/Knowledge-base'" >> .env
```

## Usage
### Start venv
```sh
pyenv activate kb-env
```

## CLI
### Process URL
```sh
python cli.py process https://example.com
```

### Debug mode: do not save
```sh
python cli.py process -d https://example.com
```

### From work laptop
```sh
python cli.py process -w https://example.com
```
_Might not work with youtube and github_


### Process batch of URLs
```sh
python cli.py process batch <urls.txt>
```

### Set up database
```sh
python scripts/build_db.py
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

### Search database
```sh
python cli.py db query "machine learning"
```

### Generate visualization
```sh
python cli.py viz graph --output graph.html
```

### Export content
```sh
python cli.py export --format markdown
```
