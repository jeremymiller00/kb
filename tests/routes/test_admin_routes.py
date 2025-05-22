import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Assuming your FastAPI app instance is created in src.app
# Adjust the import path if your app instance is located elsewhere.
from src.app import app 
from src.knowledge_base.core.models import ModelConfig # For request/response validation

# Initialize TestClient
client = TestClient(app)

# --- Test /admin/default-llm ---

def test_get_default_llm_provider():
    """Test GET /admin/default-llm endpoint."""
    # We need to mock the config_manager's get_default_llm_provider function
    # that the endpoint calls.
    with patch('src.knowledge_base.routes.admin.get_default_llm_provider') as mock_get:
        mock_get.return_value = "openai" # Expected default or current value
        
        response = client.get("/admin/default-llm")
        assert response.status_code == 200
        assert response.json() == {"model_name": "openai"}
        mock_get.assert_called_once()

def test_set_default_llm_provider_success():
    """Test successful POST to /admin/default-llm."""
    new_provider_key = "anthropic_test"
    request_payload = {"model_name": new_provider_key}
    
    # Mock both set and get functions in config_manager used by the endpoint
    with patch('src.knowledge_base.routes.admin.set_default_llm_provider') as mock_set, \
         patch('src.knowledge_base.routes.admin.get_default_llm_provider') as mock_get:
        
        # After setting, the endpoint calls get to return the new value
        mock_get.return_value = new_provider_key 
        
        response = client.post("/admin/default-llm", json=request_payload)
        
        assert response.status_code == 200
        assert response.json() == {"model_name": new_provider_key}
        mock_set.assert_called_once_with(new_provider_key)
        mock_get.assert_called_once() # Called to confirm the new value

def test_set_default_llm_provider_validation_error():
    """Test POST to /admin/default-llm with invalid data (e.g., empty string via config_manager)."""
    request_payload = {"model_name": ""} # Empty string should cause ValueError in config_manager
    
    # Mock set_default_llm_provider to simulate raising ValueError
    with patch('src.knowledge_base.routes.admin.set_default_llm_provider') as mock_set:
        mock_set.side_effect = ValueError("LLM provider key must be a non-empty string.")
        
        response = client.post("/admin/default-llm", json=request_payload)
        
        assert response.status_code == 400 # Bad Request
        assert "LLM provider key must be a non-empty string." in response.json()["detail"]
        mock_set.assert_called_once_with("")

def test_set_default_llm_provider_unexpected_error():
    """Test POST to /admin/default-llm when an unexpected error occurs."""
    request_payload = {"model_name": "some_provider"}
    
    with patch('src.knowledge_base.routes.admin.set_default_llm_provider') as mock_set:
        mock_set.side_effect = Exception("Some internal error")
        
        response = client.post("/admin/default-llm", json=request_payload)
        
        assert response.status_code == 500 # Internal Server Error
        assert "An unexpected error occurred: Some internal error" in response.json()["detail"]
        mock_set.assert_called_once_with("some_provider")


# --- Test /admin/default-embedding-model ---

def test_get_default_embedding_model():
    """Test GET /admin/default-embedding-model endpoint."""
    with patch('src.knowledge_base.routes.admin.get_default_embedding_model') as mock_get:
        mock_get.return_value = "text-embedding-ada-002"
        
        response = client.get("/admin/default-embedding-model")
        assert response.status_code == 200
        assert response.json() == {"model_name": "text-embedding-ada-002"}
        mock_get.assert_called_once()

def test_set_default_embedding_model_success():
    """Test successful POST to /admin/default-embedding-model."""
    new_model_name = "custom-embedding-v2"
    request_payload = {"model_name": new_model_name}
    
    with patch('src.knowledge_base.routes.admin.set_default_embedding_model') as mock_set, \
         patch('src.knowledge_base.routes.admin.get_default_embedding_model') as mock_get:
        
        mock_get.return_value = new_model_name
        
        response = client.post("/admin/default-embedding-model", json=request_payload)
        
        assert response.status_code == 200
        assert response.json() == {"model_name": new_model_name}
        mock_set.assert_called_once_with(new_model_name)
        mock_get.assert_called_once()

def test_set_default_embedding_model_validation_error():
    """Test POST to /admin/default-embedding-model with invalid data."""
    request_payload = {"model_name": ""}
    
    with patch('src.knowledge_base.routes.admin.set_default_embedding_model') as mock_set:
        mock_set.side_effect = ValueError("Embedding model name must be a non-empty string.")
        
        response = client.post("/admin/default-embedding-model", json=request_payload)
        
        assert response.status_code == 400
        assert "Embedding model name must be a non-empty string." in response.json()["detail"]
        mock_set.assert_called_once_with("")

# --- Test /admin/status ---
def test_get_admin_status():
    """Test the /admin/status endpoint."""
    response = client.get("/admin/status")
    assert response.status_code == 200
    assert response.json() == {"status": "Admin router is active"}

# It's important that the paths in `patch('src.knowledge_base.routes.admin.FUNCTION_NAME')`
# correctly point to where `FUNCTION_NAME` (e.g., `get_default_llm_provider`) is *looked up* by the
# `admin.py` module. If `admin.py` imports `get_default_llm_provider` directly from
# `knowledge_base.config_manager`, then the patch path should be
# `patch('knowledge_base.config_manager.get_default_llm_provider')` if we want to affect its behavior
# *everywhere*. However, for testing the route's interaction with what it *thinks* it's calling,
# patching it within the route's module scope (`src.knowledge_base.routes.admin.FUNCTION_NAME`) is often
# what's intended for unit testing the route handler in isolation from the actual function's implementation.
# Given that `admin.py` has `from knowledge_base.config_manager import ...`, patching within
# `src.knowledge_base.routes.admin` is correct for testing the route handler's direct calls.
# If we wanted to test the route handler *and* ensure the `config_manager` functions behave as expected
# without mocking them, that would be more of an integration test for this specific part.
# The current approach correctly unit tests the route handlers' logic.Okay, I've created the test files for AI modules and database operations in the previous turns:
*   `tests/ai/test_config_manager.py`
*   `tests/ai/test_llm_factory.py`
*   `tests/ai/test_openai_llm.py`
*   `tests/storage/test_database.py`
*   `tests/routes/test_admin_routes.py`

Now, I will proceed to create **`tests/routes/test_content_routes.py`**.
This file will test the content processing and management API endpoints.
