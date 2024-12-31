""" 
python scripts/build_db_sqlite.py
"""

import os
import sys
import json
import sqlite3
from rich.console import Console
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.knowledge_base.utils.logger import logger

load_dotenv()
console = Console()

def init_sqlite_db(db_path: str):
    """Initialize SQLite database with required schema"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Create documents table
    cur.execute('''
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
    cur.execute('''
        CREATE TABLE IF NOT EXISTS keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER,
            keyword TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    ''')
    
    # Create indexes
    cur.execute('CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type)')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_keywords_keyword ON keywords(keyword)')
    
    conn.commit()
    return conn

def main(data_dir: str, db_path: str):
    if not data_dir:
        logger.error("Must specify a data directory")
        sys.exit(1)

    with console.status("[bold green]Building DB..."):
        # Initialize SQLite database
        conn = init_sqlite_db(db_path)
        cur = conn.cursor()
        logger.info(f"Database initialized at {db_path}")

        # Loop through directories in data_dir
        for subdir, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(subdir, file)
                    logger.info(f"Processing {file_path}")
                    
                    try:
                        with open(file_path) as f:
                            data = json.load(f)
                            
                        # Insert document
                        cur.execute('''
                            INSERT INTO documents 
                            (url, type, timestamp, content, summary, embeddings, obsidian_markdown)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            data.get('url'),
                            data.get('type'),
                            data.get('timestamp'),
                            data.get('content'),
                            data.get('summary'),
                            json.dumps(data.get('embeddings')),
                            data.get('obsidian_markdown')
                        ))
                        
                        doc_id = cur.lastrowid
                        
                        # Insert keywords
                        if 'keywords' in data:
                            cur.executemany(
                                'INSERT INTO keywords (document_id, keyword) VALUES (?, ?)',
                                [(doc_id, keyword) for keyword in data['keywords']]
                            )
                        
                        conn.commit()
                        logger.info(f"Inserted document ID {doc_id}")
                        
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                        continue

        conn.close()
        logger.info("Database build complete")

if __name__ == '__main__':
    db_path = os.path.join(project_root, 'database', 'knowledge_base.db')
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    main(data_dir=os.getenv("DSV_KB_PATH"), db_path=db_path)