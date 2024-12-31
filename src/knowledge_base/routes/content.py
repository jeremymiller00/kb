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
    # Set up database path
    # db_dir = os.getenv("DB_DIR", "database")
    # db_path = str(Path(db_dir) / "knowledge_base.db")
    # os.makedirs(db_dir, exist_ok=True)
    
    # Initialize database
    db = Database(
        logger=logger,
        # just us the default from the constructor
        # db_path=db_path
    )
    try:
        yield db
    finally:
        if hasattr(db, 'close'):
            db.close()

# def get_db():
#     db = Database(logger=logger)
#     try:
#         yield db
#     finally:
#         db.close()


@router.get("/{content_id}", response_model=DocumentResponse)
def get_content(
    content_id: int,
    debug: bool = Query(False, description="Use knowledge base test database"),
    db: Database = Depends(get_db)
):
    if debug:
        db = Database(logger=logger, db_path=os.getenv('TEST_DB_PATH'))
    try:
        document = db.get_content(content_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        return DocumentResponse(**document)
    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    



@router.post("/{url:path}", response_model=ProcessResponse)
def process_url(
    url: str = Path(..., description="URL to process"),
    debug: bool = Query(False, description="Run in debug mode - do not save json, use test knowledge base database"),
    work: bool = Query(False, description="Work mode - use work latptop"),
    jina: bool = Query(False, description="Use Jina for preparing web content"),
    db: Database = Depends(get_db)
):
    try:
        # Create options from query parameters
        options = ProcessOptions(debug=debug, work=work, jina=jina)

        if options.debug:
            db = Database(logger=logger, db_path=os.getenv('TEST_DB_PATH'))   
     
        # Initialize components
        content_manager = ContentManager(logger=logger)
        url = content_manager.clean_url(url)
        # use Jina for PDFs or optionally
        if options.jina or url.endswith('.pdf'):
            url = content_manager.jinafy_url(url)
            file_type, file_path, time_now, complete_url = content_manager.get_file_path(url, force_general=True)
        else:
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
            # db = Database(logger=logger)
            db_name = "knowledge_base"

        else:
            print(f"[green]Content NOT saved to: {file_path}[/green]\n")
            print(f"[magenta]Summary: {summary}[/magenta]\n")
            print(f"[bright_cyan]Keywords: {keywords}[/bright_cyan]\n")
            print(f"[green]Obsidian markdown: {obsidian_markdown}[/green]\n")
            print(f'[magenta]Embedding: {embedding[:20]}[/magenta]\n')
            logger.info(f"Content NOT saved to: {file_path} due to execution in debug mode")
            # db = Database(logger=logger, db_path=os.getenv('TEST_DB_PATH'))
            db_name = "test_knowledge_base"
            # db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))

        # save to database
        # db_name = db.connection_string.split('/')[-1]
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
# Must be structured data
#  NOT CURRENTLY USED
@router.post("/", response_model=ProcessResponse)
async def create_content(
    document: DocumentCreate,
    options: ProcessOptions = None,
    db: Database = Depends(get_db)
):
    try:
        extractor = ExtractorFactory.create_extractor(document.type)
        llm = LLMFactory.create_llm()
        content_manager = ContentManager(db=db, extractor=extractor, llm=llm)
        
        result = await content_manager.process_document(
            document=document,
            options=options
        )
        return ProcessResponse(**result)
    except Exception as e:
        logger.error(f"Error processing document: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{content_id}", response_model=DocumentResponse)
def update_content(
    content_id: int, 
    document: DocumentCreate,
    debug: bool = Query(False, description="Use knowledge base test database"),
    db: Database = Depends(get_db)
):
    if debug:
        db = Database(logger=logger, db_path=os.getenv('TEST_DB_PATH'))
    try:
        updated = db.update_content(content_id, document.model_dump())
        if not updated:
            raise HTTPException(status_code=404, detail="Document not found")
        return get_content(content_id, db)
    except Exception as e:
        logger.error(f"Error updating document: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{content_id}")
def delete_content(
    content_id: int = Path(..., description="The ID of the content to delete"),
    debug: bool = Query(False, description="Use knowledge base test database"),
    db: Database = Depends(get_db)
):
    if debug:
        db = Database(logger=logger, db_path=os.getenv('TEST_DB_PATH'))
    try:
        if db.delete_content(content_id):
            return {"message": f"Content {content_id} deleted successfully"}
        raise HTTPException(status_code=404, detail="Content not found")
    except Exception as e:
        logger.error(f"Error deleting content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search/", response_model=List[DocumentResponse])
def search_content(
    query: str,
    limit: int = 10,
    debug: bool = Query(False, description="Use knowledge base test database"),
    db: Database = Depends(get_db)
):
    if debug:
        db = Database(logger=logger, db_path=os.getenv('TEST_DB_PATH'))
    try:
        results = db.search_content(query, limit=limit)
        return [DocumentResponse(**doc) for doc in results]
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# postgres stuff
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

# @router.get("/{content_id}", response_model=DocumentResponse)
# def get_content(
#     content_id: int,
#     debug: bool = Query(False, description="Use knowledge base test database"),
#     db: Database = Depends(get_db)
# ):
#     if debug:
#         db = Database(logger=logger, db_path=os.getenv('TEST_DB_PATH'))
#     try:
#         document = db.get_content(content_id)
#         if not document:
#             raise HTTPException(status_code=404, detail="Document not found")
#         return DocumentResponse(**document)
#     except Exception as e:
#         logger.error(f"Error retrieving document: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/", response_model=DocumentResponse)
# def store_content(
#     document: DocumentCreate, 
#     debug: bool = Query(False, description="Use knowledge base test database"),
#     db: Database = Depends(get_db)
# ):
#     if debug:
#         db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))
#     try:
#         doc_id = db.store_content(document.model_dump())
#         return get_content(doc_id, db)
#     except Exception as e:
#         logger.error(f"Error storing document: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.delete("/{content_id}")
# def delete_content(
#     content_id: int,
#     debug: bool = Query(False, description="Use knowledge base test database"),
#     db: Database = Depends(get_db)
# ):
#     if debug:
#         db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))
#     try:
#         deleted = db.delete_content(content_id)
#         if not deleted:
#             raise HTTPException(status_code=404, detail="Document not found")
#         return {"message": "Document deleted successfully"}
#     except Exception as e:
#         logger.error(f"Error deleting document: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.delete("/{content_id}")
# def delete_content(
#     content_id: int = Path(..., description="The ID of the content to delete"),
#     db: Database = Depends(get_db)
# ):
#     try:
#         if db.delete_content(content_id):
#             return {"message": f"Content {content_id} deleted successfully"}
#         raise HTTPException(status_code=404, detail="Content not found")
#     except Exception as e:
#         logger.error(f"Error deleting content: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# @router.get("/", response_model=List[DocumentResponse])
# def list_content(
#     type: str = None,
#     limit: int = 10,
#     offset: int = 0,
#     db: Database = Depends(get_db)
# ):
#     try:
#         documents = db.list_content(type=type, limit=limit, offset=offset)
#         return [DocumentResponse(**doc) for doc in documents]
#     except Exception as e:
#         logger.error(f"Error listing documents: {e}")
#         raise HTTPException(status_code=500, detail=str(e))