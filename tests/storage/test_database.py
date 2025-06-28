import pytest
import logging
from unittest.mock import patch, MagicMock, call # import call for checking multiple calls
import psycopg2 # For raising psycopg2 errors

from src.knowledge_base.storage.database import Database
from src.knowledge_base.utils.logger import configure_logging

test_logger = configure_logging(level=logging.DEBUG, print_to_console=False)

# Sample data for testing
SAMPLE_CONTENT_DICT = {
    'url': 'http://example.com/test',
    'type': 'web',
    'timestamp': 1678886400, # Example Unix timestamp
    'content': 'This is test content.',
    'summary': 'Test summary.',
    'embeddings': [0.1, 0.2, 0.3] * 512, # Ensure 1536 dimension
    'obsidian_markdown': '# Test\nTest content',
    'keywords': ['test', 'example']
}

@pytest.fixture
def mock_db_connection():
    """Mocks the psycopg2.connect call and the connection/cursor objects."""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = MagicMock(spec=psycopg2.extensions.connection)
        mock_cursor = MagicMock(spec=psycopg2.extensions.cursor)
        
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock fetchone and fetchall for various scenarios
        # These can be overridden in specific tests if needed
        mock_cursor.fetchone.return_value = None 
        mock_cursor.fetchall.return_value = []
        
        yield mock_connect, mock_conn, mock_cursor

@pytest.fixture
def db_instance(mock_db_connection):
    """Fixture to create a Database instance with mocked connection."""
    # Patch _setup_database to prevent it from running during these unit tests
    # as it makes actual DB calls for CREATE EXTENSION, CREATE TABLE etc.
    with patch.object(Database, '_setup_database', return_value=None) as mock_setup:
        db = Database(connection_string="dummy_connection_string", logger=test_logger)
        # The actual mock_conn and mock_cursor are from mock_db_connection
        db._connection = mock_db_connection[1] # Assign the mocked connection object
        yield db


def test_database_init_and_setup_mocked(mock_db_connection):
    """Test Database initialization (with _setup_database mocked)."""
    mock_connect, mock_conn, mock_cursor = mock_db_connection
    with patch.object(Database, '_setup_database', return_value=None) as mock_setup:
        db = Database(connection_string="dummy_connection_string", logger=test_logger)
        assert db.logger is not None
        assert db.connection_string == "dummy_connection_string"
        # _get_connection would be called by _setup_database if not mocked
        # If _setup_database is mocked, _get_connection might not be called on init.
        # Let's test _get_connection separately or ensure it's called if _setup_database wasn't mocked.
        # For this test, we confirm _setup_database was called (or would have been).
        mock_setup.assert_called_once() 
        # To test _get_connection, we can call it directly if needed, or rely on methods that use it.


def test_get_connection_establishes_connection(db_instance, mock_db_connection):
    """Test _get_connection method establishes and returns a connection."""
    mock_connect, mock_conn, mock_cursor = mock_db_connection
    
    db_instance._connection = None # Ensure connection is initially None
    conn = db_instance._get_connection()
    
    mock_connect.assert_called_with(db_instance.connection_string)
    assert conn == mock_conn

def test_get_connection_returns_existing_connection(db_instance, mock_db_connection):
    """Test _get_connection returns existing connection if already established."""
    mock_connect, mock_conn, mock_cursor = mock_db_connection
    
    # Connection is already set by db_instance fixture via its _connection assignment
    # db_instance._connection = mock_conn 
    
    conn = db_instance._get_connection()
    # mock_connect should not be called again if connection exists and is not closed
    # In our fixture, db_instance._connection is set, so _get_connection should use it.
    # However, the mock_connect is for psycopg2.connect, not for db_instance._connection itself.
    # Let's refine:
    
    db_instance._connection = mock_conn # Explicitly set it
    mock_conn.closed = False # Ensure it's not marked as closed
    
    # Reset call count for mock_connect before this specific call
    mock_connect.reset_mock() 
    
    conn_returned = db_instance._get_connection()
    assert conn_returned == mock_conn
    mock_connect.assert_not_called() # Should not make a new connection


def test_store_content_success(db_instance, mock_db_connection):
    """Test successful storage of content."""
    _, mock_conn, mock_cursor = mock_db_connection
    
    # Simulate RETURNING id
    mock_cursor.fetchone.return_value = (1,) # Document ID 1
    
    doc_id = db_instance.store_content(SAMPLE_CONTENT_DICT)
    
    assert doc_id == "1"
    # Check document insert
    mock_cursor.execute.assert_any_call(
        """
                    INSERT INTO documents 
                    (url, type, timestamp, content, summary, embeddings, obsidian_markdown)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """,
        (
            SAMPLE_CONTENT_DICT['url'], SAMPLE_CONTENT_DICT['type'], SAMPLE_CONTENT_DICT['timestamp'],
            SAMPLE_CONTENT_DICT['content'], SAMPLE_CONTENT_DICT['summary'], SAMPLE_CONTENT_DICT['embeddings'],
            SAMPLE_CONTENT_DICT['obsidian_markdown']
        )
    )
    # Check keyword insert (using execute_values mock if possible, or check the SQL string)
    # For execute_values, the actual call might be complex to mock perfectly without knowing its internals
    # or using a library that helps mock it. We'll check the SQL for now.
    # The `psycopg2.extras.execute_values` is not directly on the cursor, so we need to patch it.
    with patch('psycopg2.extras.execute_values') as mock_execute_values:
        db_instance.store_content(SAMPLE_CONTENT_DICT) # Call again to test execute_values path
        
        keywords_data = [(1, keyword) for keyword in SAMPLE_CONTENT_DICT['keywords']]
        mock_execute_values.assert_called_once_with(
            mock_cursor, # The cursor object
            'INSERT INTO keywords (document_id, keyword) VALUES %s', # SQL template
            keywords_data # Data
        )
    
    mock_conn.commit.assert_called()

def test_store_content_db_error(db_instance, mock_db_connection):
    """Test handling of database error during content storage."""
    _, mock_conn, mock_cursor = mock_db_connection
    
    mock_cursor.execute.side_effect = psycopg2.Error("Simulated DB error")
    
    with pytest.raises(psycopg2.Error, match="Simulated DB error"):
        db_instance.store_content(SAMPLE_CONTENT_DICT)
    
    mock_conn.rollback.assert_called_once()


def test_get_content_found(db_instance, mock_db_connection):
    """Test retrieving content that exists."""
    _, _, mock_cursor = mock_db_connection
    
    doc_id_to_get = "1"
    # Mock return for document query
    db_doc_data = (
        1, SAMPLE_CONTENT_DICT['url'], SAMPLE_CONTENT_DICT['type'], SAMPLE_CONTENT_DICT['timestamp'],
        SAMPLE_CONTENT_DICT['content'], SAMPLE_CONTENT_DICT['summary'], SAMPLE_CONTENT_DICT['embeddings'],
        SAMPLE_CONTENT_DICT['obsidian_markdown']
    )
    # Mock return for keywords query
    db_keywords_data = [('test',), ('example',)]
    
    # fetchone for doc, fetchall for keywords
    mock_cursor.fetchone.return_value = db_doc_data
    mock_cursor.fetchall.return_value = db_keywords_data
    
    retrieved_doc = db_instance.get_content(doc_id_to_get)
    
    assert retrieved_doc is not None
    assert retrieved_doc['id'] == 1 # Note: returns int ID from DB
    assert retrieved_doc['url'] == SAMPLE_CONTENT_DICT['url']
    assert retrieved_doc['keywords'] == SAMPLE_CONTENT_DICT['keywords']
    
    expected_doc_select = """
                    SELECT 
                        id, url, type, timestamp, content, summary, 
                        embeddings, obsidian_markdown
                    FROM documents
                    WHERE id = %s
                """
    expected_keywords_select = 'SELECT keyword FROM keywords WHERE document_id = %s'
    
    # Check calls were made
    mock_cursor.execute.assert_any_call(expected_doc_select.strip(), (doc_id_to_get,))
    mock_cursor.execute.assert_any_call(expected_keywords_select, (doc_id_to_get,))


def test_get_content_not_found(db_instance, mock_db_connection):
    """Test retrieving content that does not exist."""
    _, _, mock_cursor = mock_db_connection
    mock_cursor.fetchone.return_value = None # Simulate document not found
    
    retrieved_doc = db_instance.get_content("non_existent_id")
    assert retrieved_doc is None

def test_search_content_by_text(db_instance, mock_db_connection):
    """Test searching content by text."""
    _, _, mock_cursor = mock_db_connection
    
    # Mock results for search_content
    # search_content fetches doc, then keywords for each doc.
    doc_tuple = (1, 'url1', 'type1', 123, 'content1', 'summary1', [0.1]*1536, 'md1')
    keywords_tuple = [('kw1',), ('kw2',)]

    # First call to execute (search) returns list of docs
    # Subsequent calls (keywords) need to be handled.
    # Let's make fetchall return a list of docs for the main search,
    # then a list of keywords when called for keywords.
    
    # If we fetchone for each doc in a loop inside search_content, that's different.
    # The code uses `cur.fetchall()` for the main docs list.
    # Then, for each doc, it executes another query for keywords and uses `cur.fetchall()`.
    
    mock_cursor.fetchall.side_effect = [
        [doc_tuple], # Result for the main document search
        keywords_tuple  # Result for the keywords search for doc_tuple
    ]

    query_dict = {'text_search': 'search term'}
    results = db_instance.search_content(query=query_dict, limit=5)
    
    assert len(results) == 1
    assert results[0]['id'] == 1
    assert results[0]['keywords'] == ['kw1', 'kw2']
    
    # Verify the SQL query construction (simplified check)
    # The actual SQL construction is complex, check for key parts.
    # This call is for the main document search.
    main_search_call_args = mock_cursor.execute.call_args_list[0]
    sql_query_str = main_search_call_args[0][0] # First arg of first call
    params_tuple = main_search_call_args[0][1]  # Second arg of first call

    assert "to_tsvector('english', d.content || ' ' || d.summary) @@ to_tsquery('english', %s)" in sql_query_str
    assert params_tuple[0] == 'search term'
    assert params_tuple[-1] == 5 # Limit

    # Also check the keyword query for the found document
    keyword_search_call_args = mock_cursor.execute.call_args_list[1]
    assert keyword_search_call_args[0][0] == 'SELECT keyword FROM keywords WHERE document_id = %s'
    assert keyword_search_call_args[0][1] == (1,) # doc_id from doc_tuple


def test_search_content_by_keywords(db_instance, mock_db_connection):
    """Test searching content by a list of keywords."""
    _, _, mock_cursor = mock_db_connection
    
    doc_tuple = (2, 'url2', 'type2', 456, 'content2', 'summary2', [0.2]*1536, 'md2')
    keywords_tuple_for_doc2 = [('search_kw',)]
    
    mock_cursor.fetchall.side_effect = [
        [doc_tuple], 
        keywords_tuple_for_doc2
    ]
    
    query_dict = {'keywords': ['search_kw', 'another_kw']}
    results = db_instance.search_content(query=query_dict, limit=3)
    
    assert len(results) == 1
    assert results[0]['id'] == 2
    
    main_search_call_args = mock_cursor.execute.call_args_list[0]
    sql_query_str = main_search_call_args[0][0]
    params_tuple = main_search_call_args[0][1]

    assert "k.keyword = ANY(%s)" in sql_query_str
    assert params_tuple[0] == ['search_kw', 'another_kw'] # The list of keywords
    assert params_tuple[-1] == 3 # Limit


def test_search_content_multiple_criteria(db_instance, mock_db_connection):
    """Test searching with multiple criteria (e.g., text and type)."""
    _, _, mock_cursor = mock_db_connection
    
    doc_tuple = (3, 'url3', 'type_filter', 789, 'content3 with search term', 'summary3', [0.3]*1536, 'md3')
    keywords_tuple_for_doc3 = [] # No keywords for this doc

    mock_cursor.fetchall.side_effect = [
        [doc_tuple], 
        keywords_tuple_for_doc3 
    ]
    
    query_dict = {'text_search': 'search term', 'type': 'type_filter'}
    results = db_instance.search_content(query=query_dict, limit=1)
    
    assert len(results) == 1
    assert results[0]['id'] == 3
    
    main_search_call_args = mock_cursor.execute.call_args_list[0]
    sql_query_str = main_search_call_args[0][0]
    params_tuple = main_search_call_args[0][1]

    assert "d.type = %s" in sql_query_str
    assert "to_tsvector('english', d.content || ' ' || d.summary) @@ to_tsquery('english', %s)" in sql_query_str
    # Order of params depends on dict iteration order or explicit construction order in SUT
    assert 'type_filter' in params_tuple 
    assert 'search term' in params_tuple
    assert params_tuple[-1] == 1 # Limit


def test_search_content_no_results(db_instance, mock_db_connection):
    """Test search returning no results."""
    _, _, mock_cursor = mock_db_connection
    mock_cursor.fetchall.return_value = [] # For the main document search
    
    results = db_instance.search_content(query={'text_search': 'non_existent_term'})
    assert len(results) == 0


def test_update_content_success(db_instance, mock_db_connection):
    """Test successful update of content."""
    _, mock_conn, mock_cursor = mock_db_connection
    
    content_id_to_update = "1"
    updates_dict = {'summary': 'Updated summary', 'keywords': ['new_kw1', 'new_kw2']}
    
    # For execute_values used for keywords
    with patch('psycopg2.extras.execute_values') as mock_execute_values:
        result = db_instance.update_content(content_id_to_update, updates_dict)
        
        assert result is True
        
        # Check document update SQL
        update_call_args = mock_cursor.execute.call_args_list[0] # First execute call for the UPDATE
        sql_update_query = update_call_args[0][0]
        params_update = update_call_args[0][1]

        assert "UPDATE documents SET summary = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s" in sql_update_query.replace("\n", "").replace("  ", " ")
        assert params_update == ('Updated summary', content_id_to_update)
        
        # Check keywords delete SQL
        delete_keywords_call_args = mock_cursor.execute.call_args_list[1] # Second execute for DELETE keywords
        assert delete_keywords_call_args[0][0] == 'DELETE FROM keywords WHERE document_id = %s'
        assert delete_keywords_call_args[0][1] == (content_id_to_update,)

        # Check keywords insert (via execute_values)
        expected_keywords_data = [(content_id_to_update, 'new_kw1'), (content_id_to_update, 'new_kw2')]
        mock_execute_values.assert_called_once_with(
            mock_cursor,
            'INSERT INTO keywords (document_id, keyword) VALUES %s',
            expected_keywords_data
        )
        
    mock_conn.commit.assert_called_once()


def test_delete_content_success(db_instance, mock_db_connection):
    """Test successful deletion of content."""
    _, mock_conn, mock_cursor = mock_db_connection
    
    content_id_to_delete = "1"
    result = db_instance.delete_content(content_id_to_delete)
    
    assert result is True
    
    # Check keywords delete SQL
    delete_keywords_call = mock_cursor.execute.call_args_list[0]
    assert delete_keywords_call[0][0] == 'DELETE FROM keywords WHERE document_id = %s'
    assert delete_keywords_call[0][1] == (content_id_to_delete,)

    # Check document delete SQL
    delete_doc_call = mock_cursor.execute.call_args_list[1]
    assert delete_doc_call[0][0] == 'DELETE FROM documents WHERE id = %s'
    assert delete_doc_call[0][1] == (content_id_to_delete,)
    
    mock_conn.commit.assert_called_once()


def test_database_close_connection(db_instance, mock_db_connection):
    """Test closing the database connection."""
    _, mock_conn, _ = mock_db_connection
    db_instance._connection = mock_conn # Ensure there's a connection to close
    
    db_instance.close()
    
    mock_conn.close.assert_called_once()
    assert db_instance._connection is None

# Add tests for _setup_database if it weren't mocked.
# This would involve more complex mocking of initial DB connection for CREATE DATABASE
# and then the main connection for CREATE EXTENSION, CREATE TABLE, CREATE INDEX.
# For unit tests, mocking _setup_database is often pragmatic.
# Integration tests would cover the actual _setup_database logic.
