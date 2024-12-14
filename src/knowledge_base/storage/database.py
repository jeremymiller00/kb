"""
Database management for the knowledge base application.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import Json, execute_values
import numpy as np
from functools import wraps

from ..utils.logger import get_logger

logger = get_logger(__name__)

def retry_on_connection_error(max_attempts=3):
    """Decorator to retry database operations on connection failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except psycopg2.OperationalError as e:
                    last_error = e
                    logger.warning(
                        f"Connection attempt {attempt + 1} failed: {str(e)}"
                    )
                    if attempt < max_attempts - 1:
                        logger.info("Retrying connection...")
                    continue
            logger.error(f"All {max_attempts} connection attempts failed")
            raise last_error
        return wrapper
    return decorator

class Database:
    """Database manager for the knowledge base."""
    
    def __init__(
        self,
        connection_string: str = os.getenv(
            'DB_CONN_STRING',
            "postgresql://postgres:postgres@localhost:5432/knowledge_base"
        ),
        enable_caching: bool = True,
        max_connections: int = 5
    ):
        """Initialize database connection and setup."""
        self.connection_string = connection_string
        self.enable_caching = enable_caching
        self._connection = None
        self._setup_database()
    
    def _get_connection(self) -> psycopg2.extensions.connection:
        """Get a database connection, creating it if necessary."""
        if self._connection is None or self._connection.closed:
            self._connection = psycopg2.connect(self.connection_string)
        return self._connection
    
    def _setup_database(self) -> None:
        """Set up database tables and extensions if they don't exist."""
        # First ensure the database exists
        base_conn = psycopg2.connect(
            " ".join(self.connection_string.split()[:-1] + ["dbname=postgres"])
        )
        base_conn.autocommit = True
        
        try:
            with base_conn.cursor() as cur:
                # Check if database exists
                cur.execute(
                    "SELECT 1 FROM pg_database WHERE datname='knowledge_base'"
                )
                if not cur.fetchone():
                    cur.execute('CREATE DATABASE knowledge_base')
        finally:
            base_conn.close()
        
        # Now set up tables in the knowledge_base database
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Enable vector extension
                cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
                cur.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
                
                # Create tables
                cur.execute('''
                    CREATE TABLE IF NOT EXISTS content (
                        id SERIAL PRIMARY KEY,
                        url TEXT UNIQUE NOT NULL,
                        type TEXT NOT NULL,
                        timestamp BIGINT NOT NULL,
                        content TEXT NOT NULL,
                        summary TEXT,
                        keywords TEXT[],
                        embedding vector(384),
                        metadata JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create indexes
                cur.execute(
                    'CREATE INDEX IF NOT EXISTS idx_content_type ON content(type)'
                )
                cur.execute(
                    'CREATE INDEX IF NOT EXISTS idx_content_timestamp ON content(timestamp)'
                )
                cur.execute(
                    'CREATE INDEX IF NOT EXISTS idx_content_embedding ON content USING hnsw (embedding vector_cosine_ops)'
                )
                cur.execute(
                    'CREATE INDEX IF NOT EXISTS idx_content_keywords ON content USING GIN (keywords)'
                )
                cur.execute(
                    'CREATE INDEX IF NOT EXISTS idx_content_metadata ON content USING GIN (metadata)'
                )
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error setting up database: {e}")
            conn.rollback()
            raise
    
    async def store_content(self, content: Dict[str, Any]) -> str:
        """Store content in the database.
        
        Args:
            content: Content to store
            
        Returns:
            ID of stored content
            
        Raises:
            psycopg2.Error: If database operation fails
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    INSERT INTO content
                    (url, type, timestamp, content, summary, keywords, embedding, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (url) DO UPDATE SET
                        type = EXCLUDED.type,
                        timestamp = EXCLUDED.timestamp,
                        content = EXCLUDED.content,
                        summary = EXCLUDED.summary,
                        keywords = EXCLUDED.keywords,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                ''', (
                    content['url'],
                    content['type'],
                    content['timestamp'],
                    content['content'],
                    content.get('summary'),
                    content.get('keywords', []),
                    content.get('embedding'),
                    Json(content.get('metadata', {}))
                ))
                
                content_id = cur.fetchone()[0]
                conn.commit()
                return str(content_id)
                
        except Exception as e:
            logger.error(f"Error storing content: {e}")
            conn.rollback()
            raise
    
    async def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve content by ID.
        
        Args:
            content_id: ID of content to retrieve
            
        Returns:
            Content dictionary or None if not found
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT 
                        id, url, type, timestamp, content, summary,
                        keywords, embedding, metadata
                    FROM content
                    WHERE id = %s
                ''', (content_id,))
                
                result = cur.fetchone()
                if not result:
                    return None
                
                return {
                    'id': str(result[0]),
                    'url': result[1],
                    'type': result[2],
                    'timestamp': result[3],
                    'content': result[4],
                    'summary': result[5],
                    'keywords': result[6] or [],
                    'embedding': result[7],
                    'metadata': result[8] or {}
                }
                
        except Exception as e:
            logger.error(f"Error retrieving content: {e}")
            raise
    
    async def get_all_content(self) -> List[Dict[str, Any]]:
        """Retrieve all content.
        
        Returns:
            List of all content items
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT 
                        id, url, type, timestamp, content, summary,
                        keywords, embedding, metadata
                    FROM content
                    ORDER BY timestamp DESC
                ''')
                
                return [
                    {
                        'id': str(row[0]),
                        'url': row[1],
                        'type': row[2],
                        'timestamp': row[3],
                        'content': row[4],
                        'summary': row[5],
                        'keywords': row[6] or [],
                        'embedding': row[7],
                        'metadata': row[8] or {}
                    }
                    for row in cur.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error retrieving all content: {e}")
            raise
    
    async def search_content(
        self,
        query: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for content.
        
        Args:
            query: Search parameters
            limit: Maximum number of results
            
        Returns:
            List of matching content items
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                conditions = []
                params = []
                
                # Handle different query types
                if 'keywords' in query:
                    conditions.append('keywords && %s')
                    params.append(query['keywords'])
                
                if 'type' in query:
                    conditions.append('type = %s')
                    params.append(query['type'])
                
                if 'text_search' in query:
                    conditions.append('''
                        to_tsvector('english', content || ' ' || COALESCE(summary, '')) @@
                        plainto_tsquery('english', %s)
                    ''')
                    params.append(query['text_search'])
                
                if 'embedding' in query:
                    conditions.append('embedding <=> %s < %s')
                    params.extend([
                        query['embedding'],
                        query.get('similarity_threshold', 0.3)
                    ])
                
                if 'date_range' in query:
                    conditions.append('timestamp BETWEEN %s AND %s')
                    params.extend([
                        query['date_range']['start'],
                        query['date_range']['end']
                    ])
                
                # Construct query
                base_query = '''
                    SELECT 
                        id, url, type, timestamp, content, summary,
                        keywords, embedding, metadata
                    FROM content
                '''
                
                where_clause = ' AND '.join(conditions) if conditions else 'TRUE'
                full_query = f"{base_query} WHERE {where_clause} LIMIT %s"
                params.append(limit)
                
                cur.execute(full_query, params)
                
                return [
                    {
                        'id': str(row[0]),
                        'url': row[1],
                        'type': row[2],
                        'timestamp': row[3],
                        'content': row[4],
                        'summary': row[5],
                        'keywords': row[6] or [],
                        'embedding': row[7],
                        'metadata': row[8] or {}
                    }
                    for row in cur.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error searching content: {e}")
            raise
    
    async def find_similar(
        self,
        embedding: np.ndarray,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Find similar content using embedding.
        
        Args:
            embedding: Content embedding
            limit: Maximum number of results
            
        Returns:
            List of similar content items
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute('''
                    SELECT 
                        id, url, type, timestamp, content, summary,
                        keywords, embedding, metadata,
                        1 - (embedding <=> %s) as similarity
                    FROM content
                    WHERE embedding IS NOT NULL
                    ORDER BY embedding <=> %s
                    LIMIT %s
                ''', (embedding, embedding, limit))
                
                return [
                    {
                        'id': str(row[0]),
                        'url': row[1],
                        'type': row[2],
                        'timestamp': row[3],
                        'content': row[4],
                        'summary': row[5],
                        'keywords': row[6] or [],
                        'embedding': row[7],
                        'metadata': row[8] or {},
                        'similarity': row[9]
                    }
                    for row in cur.fetchall()
                ]
                
        except Exception as e:
            logger.error(f"Error finding similar content: {e}")
            raise
    
    async def update_content(
        self,
        content_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update existing content.
        
        Args:
            content_id: ID of content to update
            updates: Fields to update
            
        Returns:
            True if successful
            
        Raises:
            psycopg2.Error: If database operation fails
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                fields = []
                values = []
                
                for key, value in updates.items():
                    if key in {
                        'url', 'type', 'timestamp', 'content',
                        'summary', 'keywords', 'embedding', 'metadata'
                    }:
                        fields.append(f"{key} = %s")
                        values.append(
                            Json(value) if key == 'metadata' else value
                        )
                
                if fields:
                    values.append(content_id)
                    query = f'''
                        UPDATE content
                        SET {", ".join(fields)},
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    '''
                    cur.execute(query, values)
                    conn.commit()
                    return True
                
                return False
                
        except Exception as e:
            logger.error(f"Error updating content: {e}")
            conn.rollback()
            raise
    
    async def delete_content(self, content_id: str) -> bool:
        """Delete content.
        
        Args:
            content_id: ID of content to delete
            
        Returns:
            True if successful
            
        Raises:
            psycopg2.Error: If database operation fails
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute('DELETE FROM content WHERE id = %s', (content_id,))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error deleting content: {e}")
            conn.rollback()
            raise
    
    async def cleanup(self) -> None:
        """Perform database maintenance."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Vacuum analyze tables
                cur.execute('VACUUM ANALYZE content')
                
                # Remove duplicate keywords
                cur.execute('''
                    UPDATE content
                    SET keywords = array(
                        SELECT DISTINCT unnest(keywords)
                        ORDER BY 1
                    )
                ''')
                
                # Update statistics
                cur.execute('ANALYZE content')
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}")
            conn.rollback()
            raise
    
    def close(self) -> None:
        """Close database connection."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None