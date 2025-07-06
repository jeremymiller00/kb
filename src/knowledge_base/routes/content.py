import os
import traceback

from typing import List
from fastapi import APIRouter, HTTPException, Depends, Path, Query

from ..core.models import DocumentResponse, DocumentCreate, ProcessResponse, ProcessOptions
from ..storage.database import Database
from ..utils.logger import logger
from ..core.content_manager import ContentManager
from ..extractors.extractor_factory import ExtractorFactory
from ..ai.llm_factory import LLMFactory


router = APIRouter(prefix="/content", tags=["Content"])


def get_db():
    db = Database(logger=logger)
    try:
        yield db
    finally:
        db.close()


@router.get("/{content_id}", response_model=DocumentResponse)
def get_content(
    content_id: int,
    debug: bool = Query(False, description="Use knowledge base test database"),
    db: Database = Depends(get_db)
):
    if debug:
        db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))
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
    debug: bool = Query(False, description="Run in debug mode - do not save content to disk, use test DB."),
    work: bool = Query(False, description="Work mode - use work laptop"),
    jina: bool = Query(False, description="Use Jina for preparing web content"),
    db_save: bool = Query(True, description="Save processed content to the database."),
    db: Database = Depends(get_db)
):
    try:
        # Create options from query parameters
        options = ProcessOptions(debug=debug, work=work, jina=jina, db_save=db_save)
        
        # Initialize components
        content_manager = ContentManager(logger=logger)
        url = content_manager.clean_url(url)
        # use Jina for PDFs or optionally
        original_url = url
        if options.jina or url.endswith('.pdf'):
            original_url, url = content_manager.jinafy_url(url)
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
                url=original_url,
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

        # Save to database if requested
        record_id_str = None 
        if options.db_save:
            actual_db_instance = db 
            conn_to_close_if_new = None # To manage DB connection if a new one is made for test DB

            if options.debug:
                test_db_conn_string = os.getenv('TEST_DB_CONN_STRING')
                # Check if the current DB instance from DI is already the test DB
                if test_db_conn_string and actual_db_instance.connection_string != test_db_conn_string:
                    logger.info(f"Debug mode: Switching to TEST_DB_CONN_STRING for this operation.")
                    actual_db_instance = Database(logger=logger, connection_string=test_db_conn_string)
                    conn_to_close_if_new = actual_db_instance # This new instance needs explicit closing
                elif not test_db_conn_string:
                     logger.warning("TEST_DB_CONN_STRING not set for debug mode. Using default DB or live DB provided by Depends(get_db).")
            try:
                db_name = actual_db_instance.connection_string.split('/')[-1]
                logger.info(f"Attempting to save record to database: {db_name}")

                # Ensure timestamp is correctly formatted (integer)
                try:
                    timestamp_int = int(time_now)
                except ValueError:
                    logger.error(f"Invalid timestamp format: {time_now}. Cannot convert to int.")
                    raise ValueError(f"Invalid timestamp format for DB: {time_now}") # Or handle differently

                doc_data = {
                    'url': complete_url,
                    'type': file_type,
                    'timestamp': timestamp_int, 
                    'content': content,
                    'summary': summary,
                    'embeddings': embedding, 
                    'obsidian_markdown': obsidian_markdown,
                    'keywords': keywords 
                }
                
                # Ensure embedding is a list of floats
                current_embedding = doc_data['embeddings']
                if isinstance(current_embedding, str):
                    import json
                    try:
                        embedding_list = json.loads(current_embedding)
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode embedding string: {current_embedding[:100]}")
                        embedding_list = [] 
                    doc_data['embeddings'] = embedding_list
                elif not isinstance(current_embedding, list): 
                    logger.warning(f"Embedding is not a list (type: {type(current_embedding)}). Storing as empty list.")
                    doc_data['embeddings'] = []
                
                record_id = actual_db_instance.store_content(doc_data)
                record_id_str = str(record_id) 
                logger.info(f"Record {record_id_str} saved to database {db_name}: url: {doc_data['url']}, timestamp: {doc_data['timestamp']}")
            
            except Exception as db_exc:
                logger.error(f"Failed to save to database: {db_exc}. Stack trace: {traceback.format_exc()}")
                # Not raising HTTPException to allow processing to continue, but client won't know about DB failure unless response is modified
            finally:
                if conn_to_close_if_new: # If a new DB instance was created for test, close it.
                    conn_to_close_if_new.close()
                    logger.info(f"Closed explicitly created DB connection to {db_name}")
        else:
            logger.info("Database save skipped as per db_save=False option.")

        response_data = ProcessResponse(
            file_type=file_type,
            file_path=file_path,
            timestamp=time_now,
            url=complete_url,
            content=content,
            summary=summary,
            keywords=keywords,
            obsidian_markdown=obsidian_markdown,
            embedding=embedding
            # Consider adding record_id_str to ProcessResponse model if it's useful for clients
        )
        return response_data

    except Exception as e:
        logger.error(f"Error processing URL: {str(e)}")
        stack_trace = "".join(traceback.format_tb(e.__traceback__))
        logger.error(f"Stack trace: {stack_trace}")
        raise HTTPException(status_code=500, detail=str(e))


# Store content that has already been processed from a url or other source
#  NOT CURRENTLY USED
@router.post("/", response_model=DocumentResponse)
def store_content(
    document: DocumentCreate, 
    debug: bool = Query(False, description="Use knowledge base test database"),
    db: Database = Depends(get_db)
):
    if debug:
        db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))
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
    debug: bool = Query(False, description="Use knowledge base test database"),
    db: Database = Depends(get_db)
):
    if debug:
        db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))
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
    content_id: int,
    debug: bool = Query(False, description="Use knowledge base test database"),
    db: Database = Depends(get_db)
):
    if debug:
        db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))
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
    debug: bool = Query(False, description="Use knowledge base test database"),
    db: Database = Depends(get_db)
):
    if debug:
        db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))
    try:
        # Convert string query to dictionary format expected by db.search_content
        search_params = {}
        if query.strip():  # Only add text_search if query is not empty
            search_params['text_search'] = query
        
        results = db.search_content(search_params, limit=limit)
        return [DocumentResponse(**doc) for doc in results]
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{content_id}/similar", response_model=List[DocumentResponse])
def get_similar_articles(
    content_id: int,
    n: int = Query(20, description="Number of similar articles to return", ge=1, le=100),
    debug: bool = Query(False, description="Use knowledge base test database"),
    db: Database = Depends(get_db)
):
    """Find articles similar to the given article using cosine similarity on embeddings."""
    if debug:
        db = Database(logger=logger, connection_string=os.getenv('TEST_DB_CONN_STRING'))
    try:
        # First get the embedding of the source document
        source_doc = db.get_content(content_id)
        if not source_doc:
            raise HTTPException(status_code=404, detail="Source document not found")
        
        if not source_doc.get('embeddings'):
            raise HTTPException(status_code=400, detail="Source document has no embeddings")
        
        # Find similar documents using the new similarity method
        similar_docs = db.find_similar_documents(
            source_embedding=source_doc['embeddings'],
            limit=n,
            exclude_id=content_id
        )
        
        # Create DocumentResponse objects with similarity scores
        response_docs = []
        for doc in similar_docs:
            # Map similarity_distance to similarity_score
            doc_data = doc.copy()
            doc_data['similarity_score'] = doc_data.pop('similarity_distance', None)
            response_docs.append(DocumentResponse(**doc_data))
        
        return response_docs
    except Exception as e:
        logger.error(f"Error finding similar articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))