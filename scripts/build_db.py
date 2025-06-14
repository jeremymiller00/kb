import os
import sys
import json
import asyncio
from rich.console import Console
from pathlib import Path
from dotenv import load_dotenv

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.knowledge_base.storage.database import Database
from src.knowledge_base.utils.logger import configure_logging


load_dotenv()
logger = configure_logging(print_to_console=True)
console = Console()


async def main(data_dir: str):
    if not data_dir:
        logger.error("Must specify a data directory")
        sys.exit(1)

    with console.status("[bold green]Building DB..."):
        # Initialize database
        db = Database(
            connection_string=os.getenv("DB_CONN_STRING"),
            logger=logger
        )
        logger.info("Database initialized")

        # loop through directories in data_dir
        for subdir, dirs, files in os.walk(data_dir):
            for file in files:
                file_path = os.path.join(subdir, file)
                if file_path.endswith(".json"):
                    logger.info(f"Accessed {file_path}")
                    with open(file_path) as file:
                        data = json.load(file)
                    # Remove null bytes from string values
                    def clean_null_bytes(obj):
                        if isinstance(obj, str):
                            return obj.replace('\x00', '')
                        elif isinstance(obj, dict):
                            return {k: clean_null_bytes(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [clean_null_bytes(item) for item in obj]
                        return obj
                    
                    data = clean_null_bytes(data)
                    content_id = db.store_content(data)
                    logger.info(f"Populated database with record {content_id}")
    
    logger.info("Database build complete")
    return True


if __name__ == '__main__':
    asyncio.run(main(data_dir=os.getenv("DATA_DIR")))