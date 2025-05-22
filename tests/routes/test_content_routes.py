import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, ANY # ANY is useful for some mock assertions
import os # For os.getenv

# Adjust the import path if your app instance is located elsewhere.
from src.app import app 
from src.knowledge_base.core.models import ProcessResponse, DocumentResponse, DocumentCreate

client = TestClient(app)

# Sample data for mocking and requests
SAMPLE_URL = "http://example.com/test-article"
SAMPLE_CONTENT_ID = 123
MOCK_PROCESSED_DATA = {
    "file_type": "web",
    "file_path": "/fake/path/to/content.json",
    "timestamp": "1678886400",
    "url": SAMPLE_URL,
    "content": "This is the extracted content.",
    "summary": "This is a summary.",
    "keywords": ["test", "example"],
    "obsidian_markdown": "# Test Article\nThis is the content.",
    "embedding": [0.1, 0.2] * 768 # Assuming 1536 dim
}
MOCK_DOCUMENT_RESPONSE_DATA = {
    "id": SAMPLE_CONTENT_ID,
    "url": SAMPLE_URL,
    "type": "web",
    "timestamp": 1678886400,
    "content": "This is the extracted content.",
    "summary": "This is a summary.",
    "keywords": ["test", "example"],
    "embeddings": [0.1, 0.2] * 768,
}


@pytest.fixture
def mock_content_processing_dependencies():
    """Mocks dependencies for the POST /content/{url:path} endpoint."""
    with patch('src.knowledge_base.routes.content.ContentManager') as MockContentManager, \
         patch('src.knowledge_base.routes.content.ExtractorFactory') as MockExtractorFactory, \
         patch('src.knowledge_base.routes.content.LLMFactory') as MockLLMFactory, \
         patch('src.knowledge_base.routes.content.Database') as MockDatabase, \
         patch('os.getenv') as mock_os_getenv: # Mock os.getenv for DSV_KB_PATH etc.

        # Setup common mock returns
        mock_content_manager_instance = MockContentManager.return_value
        mock_content_manager_instance.clean_url.return_value = SAMPLE_URL
        mock_content_manager_instance.jinafy_url.return_value = f"https://r.jina.ai/{SAMPLE_URL}"
        mock_content_manager_instance.get_file_path.return_value = (
            MOCK_PROCESSED_DATA["file_type"],
            MOCK_PROCESSED_DATA["file_path"],
            MOCK_PROCESSED_DATA["timestamp"],
            MOCK_PROCESSED_DATA["url"]
        )

        mock_extractor_instance = MockExtractorFactory.return_value.get_extractor.return_value
        mock_extractor_instance.extract.return_value = MOCK_PROCESSED_DATA["content"]
        mock_extractor_instance.normalize_url.return_value = MOCK_PROCESSED_DATA["url"]


        mock_llm_instance = MockLLMFactory.return_value.create_llm.return_value
        mock_llm_instance.generate_summary.return_value = MOCK_PROCESSED_DATA["summary"]
        mock_llm_instance.extract_keywords_from_summary.return_value = MOCK_PROCESSED_DATA["keywords"]
        mock_llm_instance.generate_embedding.return_value = MOCK_PROCESSED_DATA["embedding"]
        mock_llm_instance.summary_to_obsidian_markdown.return_value = MOCK_PROCESSED_DATA["obsidian_markdown"]
        
        # Mock for database instance within the route, if db_save is true
        mock_db_instance_route_scope = MockDatabase.return_value # For new instance in route if debug + test_db
        mock_db_instance_route_scope.store_content.return_value = "mock_record_id_123"
        # Mock connection_string for db_name = ...split('/')[-1]
        mock_db_instance_route_scope.connection_string = "mock_db_conn_string/mock_db"


        # Mock for os.getenv calls if any are made directly in the route for paths etc.
        # Example: mock_os_getenv.return_value = "/fake/dsv/kb/path"
        # Specific getenv calls can be configured:
        def getenv_side_effect(key, default=None):
            if key == 'DSV_KB_PATH':
                return '/fake_dsv_kb_path_for_obsidian_notes'
            elif key == 'TEST_DB_CONN_STRING':
                return 'mock_test_db_conn_string/test_db'
            elif key == 'DB_CONN_STRING':
                return 'mock_prod_db_conn_string/prod_db'
            return default
        mock_os_getenv.side_effect = getenv_side_effect


        yield {
            "content_manager": mock_content_manager_instance,
            "extractor_factory": MockExtractorFactory.return_value,
            "llm_factory": MockLLMFactory.return_value,
            "database": MockDatabase, # The class, to check instantiation or if its methods are called via Depends(get_db)
            "mock_os_getenv": mock_os_getenv
        }


# Test POST /content/{url:path}
def test_process_url_success_db_save_true(mock_content_processing_dependencies):
    """Test successful URL processing with database save enabled."""
    # The get_db dependency will provide a mock Database instance.
    # We need to ensure that its store_content method is correctly called.
    
    # The `MockDatabase` class itself is what's patched.
    # `Depends(get_db)` in the route will use the *real* `get_db`, which instantiates `Database`.
    # If `Database` is patched (as above), `get_db` will yield an instance of `MagicMock` (MockDatabase.return_value).
    
    mock_db_class = mock_content_processing_dependencies["database"]
    mock_db_instance_from_get_db = mock_db_class.return_value # This is what Depends(get_db) will yield
    mock_db_instance_from_get_db.store_content.return_value = "mock_record_id_from_get_db"
    # Configure its connection_string if db_name is derived from it in the route
    mock_db_instance_from_get_db.connection_string = "depends_get_db_conn/db"


    response = client.post(f"/content/{SAMPLE_URL}?db_save=true")
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["url"] == SAMPLE_URL
    assert json_response["summary"] == MOCK_PROCESSED_DATA["summary"]
    # Check if store_content was called on the Database instance from get_db
    # This depends on whether debug mode was false (default).
    # If debug is false, it uses the `db` from `Depends(get_db)`.
    mock_db_instance_from_get_db.store_content.assert_called_once()


def test_process_url_success_db_save_false(mock_content_processing_dependencies):
    """Test successful URL processing with database save disabled."""
    mock_db_class = mock_content_processing_dependencies["database"]
    mock_db_instance_from_get_db = mock_db_class.return_value
    
    response = client.post(f"/content/{SAMPLE_URL}?db_save=false")
    
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["url"] == SAMPLE_URL
    mock_db_instance_from_get_db.store_content.assert_not_called()

def test_process_url_success_debug_mode_db_save_true(mock_content_processing_dependencies):
    """Test URL processing in debug mode with database save (should use test DB)."""
    mock_db_class = mock_content_processing_dependencies["database"]
    
    # In debug mode, the route logic might create a *new* Database instance for the test DB.
    # The mock_db_class will be used for this new instantiation.
    # Let's simulate this:
    # The instance from Depends(get_db) (prod)
    mock_db_prod_instance = MagicMock() 
    mock_db_prod_instance.connection_string = "prod_conn_string/prod_db"
    
    # The instance created inside the route for test DB
    mock_db_test_instance = MagicMock()
    mock_db_test_instance.store_content.return_value = "mock_record_id_test_db"
    mock_db_test_instance.connection_string = "test_conn_string/test_db"

    # `mock_db_class` (which is MockDatabase) needs to handle multiple return_values
    # if it's called by Depends(get_db) and then again inside the route.
    # Or, more simply, Depends(get_db) yields one mock, and if a new Database() is called,
    # MockDatabase() is called again.
    
    # If Depends(get_db) is called, it gets a mock.
    # If Database() is called inside the route, it also gets a mock.
    # We need to differentiate them if their behavior is different.
    
    # For this test, let's assume the route logic correctly instantiates a new Database
    # client for the test DB when debug=true. `MockDatabase.return_value` will be this instance.
    
    # Reset the main mock_db_class.return_value to represent the one explicitly created for test DB
    mock_db_class.return_value = mock_db_test_instance 
    
    # How to handle the `db: Database = Depends(get_db)` when `debug=true`?
    # The `Depends(get_db)` will still yield an instance. If the code uses that one, it's an issue.
    # The current route code: `actual_db_instance = db` then potentially reassigns if debug.
    # So, the one from `Depends(get_db)` might not be used for `store_content` in debug.
    
    # To be safe, let's provide distinct mocks if `Database` is instantiated multiple times.
    # For this test, the critical part is that `store_content` is called on a DB instance
    # that was (or should have been) configured with the TEST_DB_CONN_STRING.
    # The `mock_os_getenv` already provides TEST_DB_CONN_STRING.
    
    # If `actual_db_instance = Database(...)` is called inside the route,
    # `mock_db_class` (which is `MockDatabase`) will be called, and its `return_value`
    # (which we set to `mock_db_test_instance`) will be used.

    response = client.post(f"/content/{SAMPLE_URL}?debug=true&db_save=true")
    
    assert response.status_code == 200
    # Assert that store_content was called on the instance that should be the test DB instance.
    mock_db_test_instance.store_content.assert_called_once()
    # And not on the "prod" one if it was different and distinguishable.
    # This requires more complex mocking of `Depends(get_db)` vs `Database()` calls.
    # For now, assume `mock_db_class.return_value` correctly represents the instance used for storing.

def test_process_url_extractor_error(mock_content_processing_dependencies):
    """Test error handling if extractor fails."""
    mock_extractor_factory = mock_content_processing_dependencies["extractor_factory"]
    mock_extractor_instance = mock_extractor_factory.get_extractor.return_value
    mock_extractor_instance.extract.side_effect = Exception("Extractor failed")
    
    response = client.post(f"/content/{SAMPLE_URL}")
    assert response.status_code == 500
    assert "Extractor failed" in response.json()["detail"]


# Test GET /content/{content_id}
@patch('src.knowledge_base.routes.content.Database')
def test_get_content_found(MockDatabase):
    mock_db_instance = MockDatabase.return_value
    mock_db_instance.get_content.return_value = MOCK_DOCUMENT_RESPONSE_DATA
    # If get_db is called, it instantiates Database, which is MockDatabase.
    # So, mock_db_instance is what db.get_content will be called on.
    
    response = client.get(f"/content/{SAMPLE_CONTENT_ID}")
    assert response.status_code == 200
    assert response.json()["id"] == SAMPLE_CONTENT_ID
    mock_db_instance.get_content.assert_called_once_with(SAMPLE_CONTENT_ID)

@patch('src.knowledge_base.routes.content.Database')
def test_get_content_not_found(MockDatabase):
    mock_db_instance = MockDatabase.return_value
    mock_db_instance.get_content.return_value = None # Simulate not found
    
    response = client.get(f"/content/{SAMPLE_CONTENT_ID + 1}") # Different ID
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]


# Test POST /content/ (direct store)
@patch('src.knowledge_base.routes.content.Database')
def test_store_content_direct_success(MockDatabase):
    mock_db_instance = MockDatabase.return_value
    # store_content returns the ID, get_content is then called.
    mock_db_instance.store_content.return_value = SAMPLE_CONTENT_ID 
    mock_db_instance.get_content.return_value = MOCK_DOCUMENT_RESPONSE_DATA

    # Prepare a valid DocumentCreate payload
    doc_create_payload = {
        "url": SAMPLE_URL, "type": "web", "content": "Direct content",
        "summary": "Direct summary", "keywords": ["direct"], 
        "embeddings": [0.3]*1536, "obsidian_markdown": "# Direct"
    }
    
    response = client.post("/content/", json=doc_create_payload)
    assert response.status_code == 200
    assert response.json()["id"] == SAMPLE_CONTENT_ID
    mock_db_instance.store_content.assert_called_once_with(doc_create_payload)
    mock_db_instance.get_content.assert_called_once_with(SAMPLE_CONTENT_ID, ANY) # ANY for db from Depends

# Test PUT /content/{content_id}
@patch('src.knowledge_base.routes.content.Database')
def test_update_content_success(MockDatabase):
    mock_db_instance = MockDatabase.return_value
    mock_db_instance.update_content.return_value = True # Simulate successful update
    mock_db_instance.get_content.return_value = MOCK_DOCUMENT_RESPONSE_DATA # For returning updated doc
    
    doc_update_payload = {
        "url": SAMPLE_URL, "type": "web_updated", "content": "Updated content"
    }
    
    response = client.put(f"/content/{SAMPLE_CONTENT_ID}", json=doc_update_payload)
    assert response.status_code == 200
    assert response.json()["type"] == "web_updated" # Or check full response if it's MOCK_DOCUMENT_RESPONSE_DATA
    mock_db_instance.update_content.assert_called_once_with(SAMPLE_CONTENT_ID, doc_update_payload)

# Test DELETE /content/{content_id}
@patch('src.knowledge_base.routes.content.Database')
def test_delete_content_success(MockDatabase):
    mock_db_instance = MockDatabase.return_value
    mock_db_instance.delete_content.return_value = True # Simulate successful delete
    
    response = client.delete(f"/content/{SAMPLE_CONTENT_ID}")
    assert response.status_code == 200
    assert response.json() == {"message": "Document deleted successfully"}
    mock_db_instance.delete_content.assert_called_once_with(SAMPLE_CONTENT_ID)

# Test GET /content/search/
@patch('src.knowledge_base.routes.content.Database')
def test_search_content_success(MockDatabase):
    mock_db_instance = MockDatabase.return_value
    mock_db_instance.search_content.return_value = [MOCK_DOCUMENT_RESPONSE_DATA]
    
    response = client.get("/content/search/?query=test_query_text")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["url"] == SAMPLE_URL
    mock_db_instance.search_content.assert_called_once_with("test_query_text", limit=10) # Default limit
                                                                                      # Query construction in route is simple

# Note on Dependency Injection and Mocking for Routes:
# When testing routes, `Depends` will execute the dependency function.
# If `get_db` instantiates `Database()`, and `Database` is patched at the module level
# (e.g., `patch('src.knowledge_base.routes.content.Database')`), then `Depends(get_db)`
# will yield `MockDatabase.return_value`. This is usually what's needed for testing
# the route's interaction with the direct dependency (the Database service).
# If `get_db` itself has more complex logic or needs to be mocked, that's also possible.
# The current tests assume `get_db` is simple enough that patching `Database` class is sufficient.
# The `mock_content_processing_dependencies` fixture is more complex because `process_url`
# involves multiple components, some instantiated directly, some via factories.Okay, I have created the following test files in the previous turns:
*   `tests/ai/test_config_manager.py`
*   `tests/ai/test_llm_factory.py`
*   `tests/ai/test_openai_llm.py`
*   `tests/storage/test_database.py`
*   `tests/routes/test_admin_routes.py`
*   `tests/routes/test_content_routes.py`

Now, I will proceed to create **`tests/routes/test_data_routes.py`**.
This file will test the data viewing API endpoints, mocking the `DataViewer` utility.
