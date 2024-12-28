import os
import traceback

from typing import List
from fastapi import APIRouter, HTTPException, Depends, Path, Query

from src.knowledge_base.core.models import DocumentResponse, DocumentCreate, ProcessResponse, ProcessOptions
from src.knowledge_base.storage.database import Database
from src.knowledge_base.utils.logger import logger
from src.knowledge_base.core.content_manager import ContentManager
from src.knowledge_base.extractors.extractor_factory import ExtractorFactory
from src.knowledge_base.ai.llm_factory import LLMFactory


router = APIRouter(prefix="/content", tags=["Content"])


def get_db():
    db = Database(logger=logger)
    try:
        yield db
    finally:
        db.close()


@router.get("/{content_id}", response_model=DocumentResponse)
def get_content(content_id: int, db: Database = Depends(get_db)):
    try:
        document = db.get_content(content_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentResponse(**document)
    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# @router.get("/", response_model=List[DocumentResponse])
# async def get_all_content(
#     skip: int = 0, 
#     limit: int = 100, 
#     db: Database = Depends(get_db)
# ):
#     try:
#         documents = await db.get_all_content(skip=skip, limit=limit)
#         return [DocumentResponse(**doc) for doc in documents]
#     except Exception as e:
#         logger.error(f"Error retrieving documents: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

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


# Store content that has already been processed from a url or other source
#  NOT CURRENTLY USED
@router.post("/", response_model=DocumentResponse)
def store_content(document: DocumentCreate, db: Database = Depends(get_db)):
    try:
        doc_id = db.store_content(document.model_dump())
        return get_content(doc_id, db)
    except Exception as e:
        logger.error(f"Error storing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{content_id}", response_model=DocumentResponse)
def update_content(
    content_id: int, 
    document: DocumentCreate, 
    db: Database = Depends(get_db)
):
    try:
        updated = db.update_content(content_id, document.model_dump())
        if not updated:
            raise HTTPException(status_code=404, detail="Document not found")
        return get_content(content_id, db)
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{content_id}")
def delete_content(content_id: int, db: Database = Depends(get_db)):
    try:
        deleted = db.delete_content(content_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", response_model=List[DocumentResponse])
def search_content(
    query: str,
    limit: int = 10,
    db: Database = Depends(get_db)
):
    try:
        results = db.search_content(query, limit=limit)
        return [DocumentResponse(**doc) for doc in results]
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))