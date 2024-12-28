# Knowledge Base Loader

Loader for create knowledge base records for web document

# NOTE set DB_CONN_STRING in .env to use test or prod db

# NOTE UI stuff is a rabbit holel stick to cli

## To Do
* reset understanding and scope with cli
* map out the app
* Fix obsidian note titles, not dashes or underscore
* Tests
* Add safety feature for deletes
* Content Manger (do I want this both at the DB and raw content layer? probably not)
 * clean
 * dedupe
 * delete
 * update
* specify llm from cli
* set default llm
* specify embedding model from cli
* set default embedding model
* fix debug mode to use logger instead of -d and my phony debug mode
* Deal with files that are too long to fit in context window
* Fallback for LLM failures where I still want the item in my database
 * Semi-manual mode?
* Method for deduping the db
* Way to complete missing data, such as ai summary or embeddings
* New embedding model, recalculate
* option to set logging level from cli
* Claude integration
* Local embedding model option
* Local summarization model option
* UI
 * basic db stats
 * clusters of articles, top, recent
 * search, semantic
 * article type distribution
 * article relationship network
 * how can I discover new ideas and help make connections, possibly to my writing topics
 * keyword counts, similarity
 * export data

 

# Notes on what the heck I am doing
This repo is now the home
knowledge-base-explorer contains code to build a db, which needs to be migrated here: DONE
knowledgebaseinterface contains code from replit agent as a poc interface using streamlit; don't need it
kb contains the structure I like, from Claude, but the code is all a mess. use as inspiration


## Jina online html to markdown
jina_url = "https://r.jina.ai/<URL>"

## Features

- Supports summarization of web content from URLs, ArXiv papers, and GitHub repositories
- Uses OpenAI GPT model for generating high-quality summaries

## Installation

1. Create and start virtual environment:
```sh
pyenv virtualenv knowledge-base-loader-env
pyenv activate knowledge-base-loader-env
```

2. Install the required dependencies:
```sh
pip install -r requirements.txt
```

3. Set up your OpenAI API key by placing it in .env:
```sh
touch .env
echo "OPENAI_API_KEY='key'" > .env
```

4. Update DSV_KB_PATH in .env with absolute path
This is to connect to the Obsidian Vault Knowledge Base
```sh
echo "DSV_KB_PATH='/Users/jeremy.miller/Desktop/Data-Science-Vault/Knowledge-base'" >> .env
```

## Usage
### Start venv
```sh
pyenv activate knowledge-base-loader-env
```

## Basic GUI using Swagger
```sh
python api.py
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
