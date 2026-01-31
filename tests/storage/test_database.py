import pytest
import json
import os
import tempfile
import logging

from src.knowledge_base.storage.database import Database
from src.knowledge_base.utils.logger import configure_logging

test_logger = configure_logging(level=logging.DEBUG, print_to_console=False)

SAMPLE_CONTENT = {
    'url': 'http://example.com/test',
    'type': 'web',
    'timestamp': 1678886400,
    'content': 'This is test content.',
    'summary': 'Test summary.',
    'embeddings': [0.1, 0.2, 0.3] * 512,  # 1536 dimensions
    'obsidian_markdown': '# Test\nTest content',
    'keywords': ['test', 'example']
}

SAMPLE_CONTENT_2 = {
    'url': 'http://example.com/second',
    'type': 'github',
    'timestamp': 1678900000,
    'content': 'Second document about machine learning.',
    'summary': 'ML summary about deep learning.',
    'embeddings': [0.4, 0.5, 0.6] * 512,
    'obsidian_markdown': '# Second\nML content',
    'keywords': ['ml', 'deep-learning']
}


@pytest.fixture
def data_dir():
    """Create a temp directory with sample JSON files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write sample files
        for i, content in enumerate([SAMPLE_CONTENT, SAMPLE_CONTENT_2]):
            filepath = os.path.join(tmpdir, f"doc_{i}.json")
            with open(filepath, 'w') as f:
                json.dump(content, f)
        yield tmpdir


@pytest.fixture
def empty_data_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def db(data_dir):
    return Database(data_dir=data_dir, logger=test_logger)


@pytest.fixture
def empty_db(empty_data_dir):
    return Database(data_dir=empty_data_dir, logger=test_logger)


def test_load_documents(db):
    """Test that documents are loaded from JSON files on init."""
    results = db.search_content({}, limit=100)
    assert len(results) == 2


def test_get_content_found(db):
    """Test retrieving a document by ID."""
    doc = db.get_content("1")
    assert doc is not None
    assert doc['url'] == SAMPLE_CONTENT['url']
    assert doc['keywords'] == SAMPLE_CONTENT['keywords']


def test_get_content_not_found(db):
    doc = db.get_content("999")
    assert doc is None


def test_store_content(empty_db, empty_data_dir):
    """Test storing new content."""
    doc_id = empty_db.store_content(SAMPLE_CONTENT)
    assert doc_id == "1"

    # Verify in memory
    doc = empty_db.get_content(doc_id)
    assert doc is not None
    assert doc['url'] == SAMPLE_CONTENT['url']

    # Verify file on disk
    json_files = [f for f in os.listdir(empty_data_dir) if f.endswith('.json')]
    assert len(json_files) == 1


def test_search_by_type(db):
    results = db.search_content({'type': 'github'}, limit=10)
    assert len(results) == 1
    assert results[0]['type'] == 'github'


def test_search_by_keywords(db):
    results = db.search_content({'keywords': ['test']}, limit=10)
    assert len(results) == 1
    assert results[0]['url'] == SAMPLE_CONTENT['url']


def test_search_by_text(db):
    results = db.search_content({'text_search': 'machine learning'}, limit=10)
    assert len(results) == 1
    assert results[0]['url'] == SAMPLE_CONTENT_2['url']


def test_search_no_results(db):
    results = db.search_content({'text_search': 'nonexistent term xyz'}, limit=10)
    assert len(results) == 0


def test_search_empty_query(db):
    results = db.search_content({}, limit=100)
    assert len(results) == 2


def test_update_content(db):
    doc = db.get_content("1")
    assert doc['summary'] == SAMPLE_CONTENT['summary']

    result = db.update_content("1", {'summary': 'Updated summary'})
    assert result is True

    updated = db.get_content("1")
    assert updated['summary'] == 'Updated summary'


def test_update_nonexistent(db):
    result = db.update_content("999", {'summary': 'nope'})
    assert result is False


def test_delete_content(db, data_dir):
    result = db.delete_content("1")
    assert result is True
    assert db.get_content("1") is None

    # Verify remaining
    results = db.search_content({}, limit=100)
    assert len(results) == 1


def test_delete_nonexistent(db):
    result = db.delete_content("999")
    assert result is False


def test_find_similar_documents(db):
    """Test similarity search."""
    source_emb = SAMPLE_CONTENT['embeddings']
    results = db.find_similar_documents(source_emb, limit=5, exclude_id=1)

    assert len(results) >= 1
    assert all(r['id'] != 1 for r in results)
    assert 'similarity_distance' in results[0]


def test_find_similar_no_embedding(empty_db):
    results = empty_db.find_similar_documents([0.0] * 1536, limit=5)
    assert len(results) == 0


def test_close_is_noop(db):
    db.close()
    # Should still work after close
    doc = db.get_content("1")
    assert doc is not None
