"""
Knowledge Base Application Entry Point.

This module serves as the main entry point for the knowledge base application.
It initializes all necessary components and starts the GUI interface.
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from knowledge_base.ui.main_window import MainWindow
from knowledge_base.core.content_manager import ContentManager
from knowledge_base.storage.database import Database
from knowledge_base.ai.llm_manager import LLMManager
from knowledge_base.ai.embedding_manager import EmbeddingManager
from knowledge_base.utils.logger import get_logger
from knowledge_base.utils.config import load_config

logger = get_logger(__name__)

class Application:
    """Main application class that orchestrates all components."""
    
    def __init__(self):
        """Initialize the application and all its components."""
        # Load configuration
        self.config = load_config()
        
        # Initialize components
        self.db = Database(
            connection_string=self.config.get('database', {}).get('connection_string')
        )
        self.llm_manager = LLMManager(
            local_model_path=self.config.get('ai', {}).get('local_model_path')
        )
        self.embedding_manager = EmbeddingManager()
        self.content_manager = ContentManager(
            db=self.db,
            llm_manager=self.llm_manager,
            embedding_manager=self.embedding_manager
        )
        
        # Initialize GUI
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow(
            content_manager=self.content_manager,
            config=self.config
        )
        
        # Set up periodic tasks
        self.setup_periodic_tasks()
        
    def setup_periodic_tasks(self):
        """Set up periodic maintenance tasks."""
        # Update embeddings every 24 hours
        self.embedding_update_timer = QTimer()
        self.embedding_update_timer.timeout.connect(self.update_embeddings)
        self.embedding_update_timer.start(24 * 60 * 60 * 1000)  # 24 hours in milliseconds
        
        # Database cleanup every week
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_database)
        self.cleanup_timer.start(7 * 24 * 60 * 60 * 1000)  # 7 days in milliseconds
        
    async def update_embeddings(self):
        """Update embeddings for all content periodically."""
        try:
            await self.content_manager.update_all_embeddings()
            logger.info("Successfully updated embeddings")
        except Exception as e:
            logger.error(f"Error updating embeddings: {e}")
            
    async def cleanup_database(self):
        """Perform periodic database maintenance."""
        try:
            await self.db.cleanup()
            logger.info("Successfully cleaned up database")
        except Exception as e:
            logger.error(f"Error cleaning up database: {e}")
            
    def run(self):
        """Start the application."""
        try:
            logger.info("Starting Knowledge Base application...")
            self.main_window.show()
            return self.app.exec()
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            return 1
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources before shutting down."""
        try:
            self.db.close()
            logger.info("Successfully cleaned up resources")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

class ConsoleApplication:
    """Console version of the application for command-line usage."""
    
    def __init__(self):
        """Initialize console application."""
        self.config = load_config()
        self.db = Database(
            connection_string=self.config.get('database', {}).get('connection_string')
        )
        self.llm_manager = LLMManager(
            local_model_path=self.config.get('ai', {}).get('local_model_path')
        )
        self.embedding_manager = EmbeddingManager()
        self.content_manager = ContentManager(
            db=self.db,
            llm_manager=self.llm_manager,
            embedding_manager=self.embedding_manager
        )
        
    async def process_url(self, url: str, save: bool = True) -> None:
        """Process a single URL.
        
        Args:
            url: URL to process
            save: Whether to save the processed content
        """
        try:
            content = await self.content_manager.process_url(url)
            if save:
                await self.content_manager.save_content(content)
                logger.info(f"Successfully processed and saved: {url}")
            logger.info(f"\nSummary: {content['summary']}\n\nKeywords: {content['keywords']}")
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            
    async def run(self, args) -> int:
        """Run the console application with provided arguments.
        
        Args:
            args: Command line arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            if args.url:
                await self.process_url(args.url, save=not args.debug)
                return 0
            elif args.batch_file:
                with open(args.batch_file) as f:
                    urls = [line.strip() for line in f if line.strip()]
                for url in urls:
                    await self.process_url(url, save=not args.debug)
                return 0
            else:
                logger.error("No URL or batch file provided")
                return 1
        except Exception as e:
            logger.error(f"Error in console application: {e}")
            return 1
        finally:
            self.cleanup()
            
    def cleanup(self):
        """Clean up resources."""
        try:
            self.db.close()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(
        description='Process URLs and generate content summaries'
    )
    parser.add_argument('url', nargs='?', help='The URL to process')
    parser.add_argument('-d', '--debug', action='store_true', 
                       help='Run in debug mode (no saving)')
    parser.add_argument('-b', '--batch-file', help='File containing URLs to process')
    parser.add_argument('--console', action='store_true',
                       help='Run in console mode instead of GUI')
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    args = parse_args()
    
    if args.console:
        # Run in console mode
        app = ConsoleApplication()
        return asyncio.run(app.run(args))
    else:
        # Run in GUI mode
        app = Application()
        return app.run()

if __name__ == '__main__':
    sys.exit(main())