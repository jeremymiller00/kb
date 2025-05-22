Keyword endpoints?
Search by keyword
Get keyword similairty
Get keywords for doc


Core Content Management:
1. `POST /content/{url:path}` (Example: `/content/https://example.com/article`)
   - Ingests new content from the web.
   - Extracts keywords, creates AI summary, creates Obsidian markdown.
   - Saves raw JSON file to disk (if not in debug mode).
   - Optionally writes to the database (controlled by `db_save` query parameter, defaults to true).
   - Creates a new Obsidian note (if not in debug mode).
   - Query Parameters:
     - `debug: bool` (default: `false`) - If true, uses test DB, may skip saving to disk.
     - `work: bool` (default: `false`) - Special work mode processing.
     - `jina: bool` (default: `false`) - Use Jina for pre-processing.
     - `db_save: bool` (default: `true`) - Whether to save the processed content to the database.
   - Returns: `ProcessResponse` model containing details of the processed content.

1. `POST /content/` (Note: trailing slash for consistency if it's a base path for this type of POST)
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
(Existing admin endpoints like update-embeddings, dedupe-db, etc., would remain here)

1. `GET /admin/default-llm`
   - **Purpose**: Get the current default LLM provider key.
   - **Response Body**: `ModelConfig` (e.g., `{"model_name": "openai"}`)

2. `POST /admin/default-llm`
   - **Purpose**: Set the default LLM provider key.
   - **Request Body**: `ModelConfig` (e.g., `{"model_name": "new_provider_key"}`)
   - **Response Body**: `ModelConfig` with the updated key or a success message.
   - **Error Responses**: 400 for invalid input, 500 for internal errors.

3. `GET /admin/default-embedding-model`
   - **Purpose**: Get the current default embedding model name.
   - **Response Body**: `ModelConfig` (e.g., `{"model_name": "text-embedding-ada-002"}`)

4. `POST /admin/default-embedding-model`
   - **Purpose**: Set the default embedding model name.
   - **Request Body**: `ModelConfig` (e.g., `{"model_name": "new_embedding_model_name"}`)
   - **Response Body**: `ModelConfig` with the updated name or a success message.
   - **Error Responses**: 400 for invalid input, 500 for internal errors.

(Other existing admin endpoints like `PUT /admin/update-embeddings`, `DELETE /admin/dedupe-db` would follow)
   `PUT /admin/update-embeddings`
   - Regenerates embeddings for specified content
   - Parameters: embedding model, content_ids (optional), all as default
   - Actions: updates database records embedding column

   `DELETE /admin/dedupe-db`
   - Remove duplicate rows from the database
   - Parameters: model_type, content_ids (optional), safety code
   - Return deleted rows as json objects

   `POST /admin/clean-db-record`
   - Exact functionality to be specified
   - Parameters: function(s), content_ids

   `PUT /admin/rebuild-db`
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
