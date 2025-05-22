import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from pathlib import Path # For Path objects if DataViewer returns them

# Adjust the import path if your app instance is located elsewhere.
from src.app import app 

client = TestClient(app)

# Sample data that DataViewer might return
SAMPLE_DIRECTORIES_DATA = [
    {"name": "2023-01-01", "path": "/fake/kb/2023-01-01"},
    {"name": "2023-01-02", "path": "/fake/kb/2023-01-02"},
]
SAMPLE_FILES_DATA = [
    {"file_name": "file1.json", "type": "web", "date": "2023-01-01 10:00:00", "file_path": "/fake/kb/2023-01-01/file1.json"},
    {"file_name": "file2.json", "type": "arxiv", "date": "2023-01-02 11:00:00", "file_path": "/fake/kb/2023-01-02/file2.json"},
]
SAMPLE_FILE_CONTENT_DATA = {
    "url": "http://example.com/file1",
    "type": "web",
    "timestamp": 1672567200, # 2023-01-01 10:00:00
    "content": "This is content of file1.",
    "summary": "Summary of file1.",
    "keywords": ["file1", "example"]
}
SAMPLE_FILE_TYPES_DATA = ["web", "arxiv", "github"]
SAMPLE_STATS_DATA = {
    "total_files": 100,
    "total_size_bytes": 1024000,
    "types": {"web": 50, "arxiv": 30, "github": 20},
    "files_by_date": {"2023-01-01": 5, "2023-01-02": 8}
}

@pytest.fixture
def mock_data_viewer():
    """Mocks the DataViewer class used by the data routes."""
    # Patching where DataViewer is lookup up by the routes module
    with patch('src.knowledge_base.routes.data.DataViewer') as MockDataViewer:
        mock_instance = MockDataViewer.return_value
        
        # Configure mock methods
        mock_instance.list_data_directories.return_value = [Path(d["path"]) for d in SAMPLE_DIRECTORIES_DATA] # Assuming it returns Path objects
        mock_instance.list_data_files.return_value = SAMPLE_FILES_DATA
        mock_instance.get_file_content.return_value = SAMPLE_FILE_CONTENT_DATA
        mock_instance.get_file_types.return_value = SAMPLE_FILE_TYPES_DATA
        mock_instance.get_stats.return_value = SAMPLE_STATS_DATA
        
        yield mock_instance

# Test GET /data/directories
def test_list_directories(mock_data_viewer):
    response = client.get("/data/directories")
    assert response.status_code == 200
    # The route converts Path objects to dicts with name and path (as strings)
    expected_response = [{"name": Path(d["path"]).name, "path": d["path"]} for d in SAMPLE_DIRECTORIES_DATA]
    assert response.json() == expected_response
    mock_data_viewer.list_data_directories.assert_called_once()

# Test GET /data/files
def test_list_files_no_filters(mock_data_viewer):
    response = client.get("/data/files")
    assert response.status_code == 200
    assert response.json() == SAMPLE_FILES_DATA
    mock_data_viewer.list_data_files.assert_called_once_with(directory=None, file_type=None, days=None)

def test_list_files_with_filters(mock_data_viewer):
    response = client.get("/data/files?directory=2023-01-01&file_type=web&days=7")
    assert response.status_code == 200
    assert response.json() == SAMPLE_FILES_DATA # Mock returns same data regardless of filter for this test
    mock_data_viewer.list_data_files.assert_called_once_with(directory="2023-01-01", file_type="web", days=7)

# Test GET /data/file/{file_path:path}
def test_get_file_content_success(mock_data_viewer):
    # The file_path parameter is URL encoded. For testing, use a simple path.
    test_file_path = "2023-01-01/file1.json" 
    # URL encode if it contains special characters, but not needed for this simple path.
    
    response = client.get(f"/data/file/{test_file_path}")
    assert response.status_code == 200
    assert response.json() == SAMPLE_FILE_CONTENT_DATA
    mock_data_viewer.get_file_content.assert_called_once_with(test_file_path)

def test_get_file_content_not_found(mock_data_viewer):
    mock_data_viewer.get_file_content.side_effect = FileNotFoundError("File not found simulation")
    test_file_path = "non/existent/file.json"
    
    response = client.get(f"/data/file/{test_file_path}")
    assert response.status_code == 404
    assert "File not found simulation" in response.json()["detail"]

# Test GET /data/types
def test_get_file_types(mock_data_viewer):
    response = client.get("/data/types")
    assert response.status_code == 200
    assert response.json() == SAMPLE_FILE_TYPES_DATA
    mock_data_viewer.get_file_types.assert_called_once()

# Test GET /data/stats
def test_get_stats(mock_data_viewer):
    response = client.get("/data/stats")
    assert response.status_code == 200
    assert response.json() == SAMPLE_STATS_DATA
    mock_data_viewer.get_stats.assert_called_once()

# Test error handling in routes (e.g., if DataViewer raises an unexpected Exception)
def test_list_files_unexpected_error(mock_data_viewer):
    mock_data_viewer.list_data_files.side_effect = Exception("Unexpected DataViewer error")
    response = client.get("/data/files")
    assert response.status_code == 500
    assert "Unexpected DataViewer error" in response.json()["detail"]

# Note: The `DataViewer` is instantiated within each route function.
# The `patch('src.knowledge_base.routes.data.DataViewer')` correctly mocks the class,
# so when a route calls `DataViewer(...)`, it gets the `mock_instance` configured in the fixture.
# This is appropriate for testing the routes' interaction with the `DataViewer` interface.
