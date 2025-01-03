Keyword endpoints?
Search by keyword
Get keyword similairty
Get keywords for doc


Core Content Management:
1. `POST /content/{url}`
   - Ingests new content from the web
   - Extracts keywords, creates AI summary, creates Obsidian markdown
   - Saves raw JSON file, writes to database, creates new Obsidian note
   - Returns: Process Response

1. `POST /content`
   - Ingests new content from structured object
   - A direct write to the database
   - Returns: content_id

1. `POST /content/process`
   - Batch processing of content from object or file input
   - Parameters: list of content_ids, operations (summarize/embed/extract_keywords)
   - Returns: Processing results

2. `GET /content/{content_id}`
   - Retrieves specific content by ID
   - Returns: Full content object with metadata

3. `PUT /content/{content_id}`
   - Updates existing content
   - Parameters: updated fields and values
   - Returns: Updated content object

4. `DELETE /content/{content_id}`
   - Removes content from the knowledge base

Search and Retrieval:
1. `GET /search`
   - Text-based and semantic search
   - Query parameters: q (query text), type (content type), use_embeddings (boolean)
   - Returns: List of matching content

2. `GET /search/similar/{content_id}`
   - Finds similar content to a given item
   - Query parameters: threshold, limit
   - Returns: List of similar content

Analysis and Insights:
1. `GET /insights/statistics`
   - Returns system-wide statistics
   - Content counts, type distribution, etc.

2. `GET /insights/timeline`
   - Gets temporal distribution of content
   - Query parameters: start_date, end_date, type

2. `GET /insights/clusters`
   - Gets clusters of documents by topic, or other ?
   - Query parameters: start_date, end_date, filters
   - Return: cluster id, cluster name, [document ids]

2. `GET /insights/knowledge-graph`
   - Gets knowledge graph triples
   - Query parameters: start_date, end_date, filters
   - Return: document id, document id, relation, attributes

2. `GET /insights/discover`
   - Discover new connections ?
   - Query parameters: ?
   - Return: ?


Admin:
2. `PUT /admin/update-embeddings`
   - Regenerates embeddings for specified content
   - Parameters: embedding model, content_ids (optional), all as default
   - Actions: updates database records embedding column

2. `DELETE /admin/dedupe-db`
   - Remove duplicate rows from the database
   - Parameters: model_type, content_ids (optional), safety code
   - Return deleted rows as json objects

2. `POST /admin/clean-db-record`
   - Exact functionality to be specified
   - Parameters: function(s), content_ids

2. `GET /admin/default-llm`
   - Get default llm

2. `POST /admin/default-llm`
   - Set default llm
   - Parameters: llm string, provider?

2. `GET /admin/default-embedding-model`
   - Get default embedding model

2. `POST /admin/default-embedding-model`
   - Set default embedding model
   - Parameters: model string

2. `PUT /admin/rebuild-db`
   - Rebuild the pg database from raw json files
   - Parameters: new database name





Export:
1. `GET /export`
   - Exports content in specified format
   - Query parameters: format (json/csv), content_ids (optional)
   - Returns: Formatted data file

Each endpoint should have:
- Proper error handling
- Input validation
- Rate limiting (if needed)
- Authentication (if you decide to add it later)
- Detailed logging for debugging
