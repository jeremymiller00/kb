import os
import sqlite3
import json
from typing import Dict, List, Any, Optional
# import psycopg2
# from psycopg2.extras import Json, execute_values
from dotenv import load_dotenv

load_dotenv()


class Database:
    """Handles database operations for the knowledge base."""
    
    def __init__(
        self,
        db_path: str = os.getenv('DB_PATH', 'knowledge_base.db'),
        # db_path: str = 'datbase/knowledge_base.db',
        enable_caching: bool = True,
        logger=None
    ):
        """
        Initialize database connection and ensure required setup.
        
        Args:
            db_path: Path to SQLite database file
            enable_caching: Whether to enable query result caching
        """
        self.logger = logger
        self.db_path = db_path
        self.enable_caching = enable_caching
        self._connection = None
        self._setup_database()
    
    # def _get_connection(self) -> psycopg2.extensions.connection:
    #     """Get a database connection, creating it if necessary."""
    #     if self._connection is None or self._connection.closed:
    #         self._connection = psycopg2.connect(self.connection_string)
    #     self.logger.info("Database Connection Established")
    #     return self._connection

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection, creating it if necessary."""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Enable foreign key support
            self._connection.execute("PRAGMA foreign_keys = ON")
            # Return rows as dictionaries
            self._connection.row_factory = sqlite3.Row
        return self._connection
    
    
    def _setup_database(self):
        """Initialize database schema if needed."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT,
                type TEXT,
                timestamp INTEGER,
                content TEXT,
                summary TEXT,
                embeddings TEXT,
                obsidian_markdown TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create keywords table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER,
                keyword TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)')
        
        conn.commit()
        self.logger.info("Database setup complete")

    
    def store_content(self, doc_data: Dict[str, Any]) -> int:
        """Store document content in database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Insert document
            cursor.execute("""
                INSERT INTO documents 
                (url, type, timestamp, content, summary, embeddings, obsidian_markdown)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_data['url'],
                doc_data['type'],
                doc_data['timestamp'],
                doc_data['content'],
                doc_data['summary'],
                json.dumps(doc_data['embeddings']),
                doc_data['obsidian_markdown']
            ))

            doc_id = cursor.lastrowid

            # Insert keywords
            if doc_data.get('keywords'):
                cursor.executemany(
                    'INSERT INTO keywords (document_id, keyword) VALUES (?, ?)',
                    [(doc_id, keyword) for keyword in doc_data['keywords']]
                )

            conn.commit()
            return doc_id

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
    
    def get_content(self, content_id: int) -> Optional[Dict]:
        """Get content by ID."""
        cursor = self._get_connection().cursor()
        try:
            cursor.execute("""
                SELECT d.*, GROUP_CONCAT(k.keyword) as keywords
                FROM documents d
                LEFT JOIN keywords k ON d.id = k.document_id
                WHERE d.id = ?
                GROUP BY d.id
            """, (content_id,))
            row = cursor.fetchone()
            if row:
                # Convert Row to dict and parse keywords
                result = dict(row)
                if result['keywords']:
                    result['keywords'] = result['keywords'].split(',')
                else:
                    result['keywords'] = []
                return result
            return None
        finally:
            cursor.close()
    

    def search_content(
        self,
        query: Dict[str, Any],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for content based on specified criteria.
        
        Args:
            query: Search parameters
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: Matching documents
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                conditions = []
                params = []
                
                # Handle different query types
                if 'keywords' in query:
                    conditions.append('''
                        EXISTS (
                            SELECT 1 FROM keywords k 
                            WHERE k.document_id = d.id 
                            AND k.keyword = ANY(%s)
                        )
                    ''')
                    params.append(query['keywords'])
                
                if 'type' in query:
                    conditions.append('d.type = %s')
                    params.append(query['type'])
                
                if 'text_search' in query:
                    conditions.append('''
                        to_tsvector('english', d.content || ' ' || d.summary) @@ 
                        to_tsquery('english', %s)
                    ''')
                    params.append(query['text_search'])
                
                if 'embedding' in query:
                    conditions.append('d.embeddings <-> %s < %s')
                    params.extend([query['embedding'], query.get('similarity_threshold', 0.8)])
                
                # Construct and execute query
                base_query = '''
                    SELECT DISTINCT
                        d.id, d.url, d.type, d.timestamp, d.content, 
                        d.summary, d.embeddings, d.obsidian_markdown
                    FROM documents d
                '''
                
                where_clause = ' AND '.join(conditions) if conditions else 'TRUE'
                full_query = f"{base_query} WHERE {where_clause} LIMIT %s"
                params.append(limit)
                
                cur.execute(full_query, params)
                results = []
                
                for doc in cur.fetchall():
                    # Get keywords for each document
                    cur.execute(
                        'SELECT keyword FROM keywords WHERE document_id = %s',
                        (doc[0],)
                    )
                    keywords = [row[0] for row in cur.fetchall()]
                    
                    results.append({
                        'id': doc[0],
                        'url': doc[1],
                        'type': doc[2],
                        'timestamp': doc[3],
                        'content': doc[4],
                        'summary': doc[5],
                        'embeddings': doc[6],
                        'obsidian_markdown': doc[7],
                        'keywords': keywords
                    })
                
                return results
   
        except Exception as e:
            print(f"Error searching content: {e}")
            raise

    def update_content(
        self,
        content_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update existing content in the database.
        
        Args:
            content_id: ID of document to update
            updates: Fields to update and their new values
            
        Returns:
            bool: True if successful
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # Update document fields
                fields = []
                values = []
                for key, value in updates.items():
                    if key != 'keywords':
                        fields.append(f"{key} = %s")
                        values.append(value)
                
                if fields:
                    values.append(content_id)
                    query = f'''
                        UPDATE documents 
                        SET {", ".join(fields)}, updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    '''
                    cur.execute(query, values)
                
                # Update keywords if present
                if 'keywords' in updates:
                    # Remove old keywords
                    cur.execute(
                        'DELETE FROM keywords WHERE document_id = %s',
                        (content_id,)
                    )
                    # Insert new keywords
                    keywords_data = [
                        (content_id, keyword) 
                        for keyword in updates['keywords']
                    ]
                    execute_values(
                        cur,
                        'INSERT INTO keywords (document_id, keyword) VALUES %s',
                        keywords_data
                    )
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"Error updating content: {e}")
            conn.rollback()
            raise

    def delete_content(self, content_id: int) -> bool:
        """Delete document and associated keywords by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            # Delete keywords first due to foreign key constraint
            cursor.execute("DELETE FROM keywords WHERE document_id = ?", (content_id,))
            cursor.execute("DELETE FROM documents WHERE id = ?", (content_id,))

            # Check if any rows were affected
            rows_deleted = cursor.rowcount
            conn.commit()

            return rows_deleted > 0

        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None



# postgres stuff
    # def delete_content(self, content_id: str) -> bool:
    #     """
    #     Delete content from the database.
        
    #     Args:
    #         content_id: ID of document to delete
            
    #     Returns:
    #         bool: True if successful
    #     """
    #     conn = self._get_connection()
    #     try:
    #         with conn.cursor() as cur:
    #             # Delete keywords first (due to foreign key)
    #             cur.execute(
    #                 'DELETE FROM keywords WHERE document_id = %s',
    #                 (content_id,)
    #             )
    #             # Delete document
    #             cur.execute(
    #                 'DELETE FROM documents WHERE id = %s',
    #                 (content_id,)
    #             )
    #             conn.commit()
    #             return True
                
    #     except Exception as e:
    #         print(f"Error deleting content: {e}")
    #         conn.rollback()
    #         raise
    
    # def close(self) -> None:
    #     """Close the database connection."""
    #     if self._connection is not None:
    #         self._connection.close()
    #         self._connection = None



# class Database:
#     """Handles database operations for the knowledge base."""
    
#     def __init__(
#         self,
#         connection_string: str = os.getenv('DB_CONN_STRING'),
#         enable_caching: bool = True,
#         max_connections: int = 5,
#         logger=None
#     ):
#         """
#         Initialize database connection and ensure required setup.
        
#         Args:
#             connection_string: PostgreSQL connection string
#             enable_caching: Whether to enable query result caching
#             max_connections: Maximum number of concurrent connections
#         """
#         self.logger = logger
#         self.connection_string = connection_string
#         self.enable_caching = enable_caching
#         self._connection = None
#         self._setup_database()

    # def _setup_database(self) -> None:
    #     """Set up database tables and extensions if they don't exist."""
    #     # First ensure the database exists
    #     base_conn = psycopg2.connect(
    #         " ".join(self.connection_string.split()[:-1] + ["dbname=postgres"])
    #     )
    #     base_conn.autocommit = True
        
    #     try:
    #         with base_conn.cursor() as cur:
    #             # Check if database exists
    #             dbname = self.connection_string.split("/")[-1]
    #             cur.execute(
    #                 f"SELECT 1 FROM pg_database WHERE datname='{dbname}'"
    #             )
    #             if not cur.fetchone():
    #                 cur.execute(f'CREATE DATABASE {dbname}')
    #     finally:
    #         base_conn.close()
        
    #     # Now set up tables in the knowledge_base database
    #     conn = self._get_connection()
    #     try:
    #         with conn.cursor() as cur:
    #             # Enable vector extension
    #             cur.execute('CREATE EXTENSION IF NOT EXISTS vector')
                
    #             # Create documents table
    #             cur.execute('''
    #                 CREATE TABLE IF NOT EXISTS documents (
    #                     id SERIAL PRIMARY KEY,
    #                     url TEXT,
    #                     type TEXT,
    #                     timestamp BIGINT,
    #                     content TEXT,
    #                     summary TEXT,
    #                     embeddings vector(1536),
    #                     obsidian_markdown TEXT,
    #                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #                     updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #                 )
    #             ''')
                
    #             # Create keywords table
    #             cur.execute('''
    #                 CREATE TABLE IF NOT EXISTS keywords (
    #                     id SERIAL PRIMARY KEY,
    #                     document_id INTEGER REFERENCES documents(id),
    #                     keyword TEXT,
    #                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    #                 )
    #             ''')
                
    #             # Create necessary indexes
    #             cur.execute(
    #                 'CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type)'
    #             )
    #             cur.execute(
    #                 'CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)'
    #             )
    #             cur.execute(
    #                 'CREATE INDEX IF NOT EXISTS idx_embeddings ON documents USING hnsw (embeddings vector_cosine_ops)'
    #             )
                
    #             conn.commit()
    #     except Exception as e:
    #         print.error(f"Error setting up database: {e}")
    #         conn.rollback()
    #         raise
    #     self.logger.info("Database setup complete")

    # def get_content(self, content_id: str) -> Optional[Dict[str, Any]]:
    #     """
    #     Retrieve content by ID.
        
    #     Args:
    #         content_id: Document ID to retrieve
            
    #     Returns:
    #         Optional[Dict[str, Any]]: Document data if found
    #     """
    #     conn = self._get_connection()
    #     try:
    #         with conn.cursor() as cur:
    #             # Get document
    #             cur.execute('''
    #                 SELECT 
    #                     id, url, type, timestamp, content, summary, 
    #                     embeddings, obsidian_markdown
    #                 FROM documents
    #                 WHERE id = %s
    #             ''', (content_id,))
                
    #             doc = cur.fetchone()
    #             if not doc:
    #                 return None
                
    #             # Get keywords
    #             cur.execute(
    #                 'SELECT keyword FROM keywords WHERE document_id = %s',
    #                 (content_id,)
    #             )
    #             keywords = [row[0] for row in cur.fetchall()]
                
    #             return {
    #                 'id': doc[0],
    #                 'url': doc[1],
    #                 'type': doc[2],
    #                 'timestamp': doc[3],
    #                 'content': doc[4],
    #                 'summary': doc[5],
    #                 'embeddings': doc[6],
    #                 'obsidian_markdown': doc[7],
    #                 'keywords': keywords
    #             }
                
    #     except Exception as e:
    #         print(f"Error retrieving content: {e}")
    #         raise
