import os
import traceback
from fastapi import APIRouter, HTTPException, Depends, Path, Query

from src.knowledge_base.core.models import ProcessResponse, ProcessOptions
from src.knowledge_base.core.content_manager import ContentManager
from src.knowledge_base.storage.database import Database
from src.knowledge_base.utils.logger import logger
from src.knowledge_base.extractors.extractor_factory import ExtractorFactory
from src.knowledge_base.ai.llm_factory import LLMFactory

# logger = configure_logging()
router = APIRouter(prefix="/process", tags=["process"])


# Dependency
def get_db():
    db = Database(logger=logger)
    try:
        yield db
    finally:
        db.close()


@router.post("/{url:path}", response_model=ProcessResponse)
def process_url(
    url: str = Path(..., description="URL to process"),
    debug: bool = Query(False, description="Run in debug mode - do not save content"),
    work: bool = Query(False, description="Work mode - use work latptop"),
    jina: bool = Query(False, description="Use Jina for preparing web content"),
    db: Database = Depends(get_db)
):
    try:
        # Create options from query parameters
        options = ProcessOptions(debug=debug, work=work, jina=jina)
        
        # Initialize components
        content_manager = ContentManager(logger=logger)
        url = content_manager.clean_url(url)
        # use Jina for PDFs or optionally
        if options.jina or url.endswith('.pdf'):
            url = content_manager.jinafy_url(url)
        file_type, file_path, time_now, complete_url = content_manager.get_file_path(url)
        
        # Extract content
        extractor = ExtractorFactory().get_extractor(complete_url)
        extractor.set_logger(logger)
        content = extractor.extract(complete_url, work=options.work)

        # Process with LLM
        llm = LLMFactory().create_llm('openai')
        llm.set_logger(logger)
        summary = llm.generate_summary(content, summary_type=file_type)
        keywords = llm.extract_keywords_from_summary(summary)
        embedding = llm.generate_embedding(content)
        obsidian_markdown = llm.summary_to_obsidian_markdown(summary, keywords)

        # Save to obsidian and database if not in debug mode
        if not options.debug:
            content_manager.save_content(
                file_type=file_type,
                file_path=file_path,
                content=content,
                summary=summary,
                keywords=keywords,
                embeddings=embedding,
                url=complete_url,
                timestamp=time_now,
                obsidian_markdown=obsidian_markdown
            )
            logger.info(f"[green]Content saved to: {file_path}[/green]\n")
            logger.info(f"[magenta]Summary: {summary}[/magenta]\n")
            logger.info(f"[bright_cyan]Keywords: {keywords}[/bright_cyan]\n")
            logger.info(f"Content saved to: {file_path}")
            content_manager.create_obsidian_note(file_path, f"{os.getenv('DSV_KB_PATH')}/new-notes/")
            logger.info(f"Obsidian note created for {file_path}")
            db = Database(logger=logger)

        else:
            print(f"[green]Content NOT saved to: {file_path}[/green]\n")
            print(f"[magenta]Summary: {summary}[/magenta]\n")
            print(f"[bright_cyan]Keywords: {keywords}[/bright_cyan]\n")
            print(f"[green]Obsidian markdown: {obsidian_markdown}[/green]\n")
            print(f'[magenta]Embedding: {embedding[:20]}[/magenta]\n')
            logger.info(f"Content NOT saved to: {file_path} due to execution in debug mode")
            db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))

        # save to database
        db_name = db.connection_string.split('/')[-1]
        logger.info(f"Saving record to database: {db_name}")
        doc_data = {
            'url': complete_url,
            'type': file_type,
            'timestamp': time_now,
            'content': content,
            'summary': summary,
            'embeddings': embedding,
            'obsidian_markdown': obsidian_markdown,
            'keywords': keywords
        }
        record_id = db.store_content(doc_data)
        db.close()
        logger.info("Database connection closed")
        logger.info(f"Record {record_id} saved to database {db_name}: url: {doc_data['url']}, timestamp: {doc_data['timestamp']}")
        logger.debug(f"Record {record_id}  saved to database: {record_id}")

        return ProcessResponse(
            file_type=file_type,
            file_path=file_path,
            timestamp=time_now,
            url=complete_url,
            content=content,
            summary=summary,
            keywords=keywords,
            obsidian_markdown=obsidian_markdown,
            embedding=embedding
        )

    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}")
        stack_trace = "".join(traceback.format_tb(e.__traceback__))
        logger.error(f"Stack trace: {stack_trace}")
        raise HTTPException(status_code=500, detail=str(e))
