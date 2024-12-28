import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine
from dotenv import load_dotenv

from src.knowledge_base.utils.config import configure_logging
from src.knowledge_base.routes import process, database

# Load environment variables
load_dotenv()
logger = configure_logging()

# Web content directory
STATIC_DIR = "src/knowledge_base/static"

# Database connection
DB_CONN_STRING = os.getenv("DB_CONN_STRING")
engine = create_engine(DB_CONN_STRING)

# FastAPI app
app = FastAPI(title="Knowledge Base API")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include routers
app.include_router(process.router)
app.include_router(database.router)


@app.get("/")
def read_index():
    return FileResponse(STATIC_DIR + "/index.html")


# # Dependency
# def get_db():
#     db = Database(logger=logger)
#     try:
#         yield db
#     finally:
#         db.close()


# @app.post("/process/{url:path}", response_model=ProcessResponse)
# def process_url(
#     url: str = Path(..., description="URL to process"),
#     debug: bool = Query(False, description="Run in debug mode - do not save content"),
#     work: bool = Query(False, description="Work mode - use work latptop"),
#     jina: bool = Query(False, description="Use Jina for preparing web content"),
#     db: Database = Depends(get_db)
# ):
#     try:
#         # Create options from query parameters
#         options = ProcessOptions(debug=debug, work=work, jina=jina)
        
#         # Initialize components
#         content_manager = ContentManager(logger=logger)
#         url = content_manager.clean_url(url)
#         # use Jina for PDFs or optionally
#         if options.jina or url.endswith('.pdf'):
#             url = content_manager.jinafy_url(url)
#         file_type, file_path, time_now, complete_url = content_manager.get_file_path(url)
        
#         # Extract content
#         extractor = ExtractorFactory().get_extractor(complete_url)
#         extractor.set_logger(logger)
#         content = extractor.extract(complete_url, work=options.work)

#         # Process with LLM
#         llm = LLMFactory().create_llm('openai')
#         llm.set_logger(logger)
#         summary = llm.generate_summary(content, summary_type=file_type)
#         keywords = llm.extract_keywords_from_summary(summary)
#         embedding = llm.generate_embedding(content)
#         obsidian_markdown = llm.summary_to_obsidian_markdown(summary, keywords)

#         # Save to obsidian and database if not in debug mode
#         if not options.debug:
#             content_manager.save_content(
#                 file_type=file_type,
#                 file_path=file_path,
#                 content=content,
#                 summary=summary,
#                 keywords=keywords,
#                 embeddings=embedding,
#                 url=complete_url,
#                 timestamp=time_now,
#                 obsidian_markdown=obsidian_markdown
#             )
#             logger.info(f"Content saved to: {file_path}")

#             content_manager.create_obsidian_note(file_path, f"{os.getenv('DSV_KB_PATH')}/new-notes/")
#             logger.info(f"Obsidian note created for {file_path}")

#             doc_data = {
#                 'url': complete_url,
#                 'type': file_type,
#                 'timestamp': time_now,
#                 'content': content,
#                 'summary': summary,
#                 'embeddings': embedding,
#                 'obsidian_markdown': obsidian_markdown,
#                 'keywords': keywords
#             }
#             db.store_content(doc_data)
#             logger.info(f"Content stored in database for: {url}")

#         return ProcessResponse(
#             file_type=file_type,
#             file_path=file_path,
#             timestamp=time_now,
#             url=complete_url,
#             content=content,
#             summary=summary,
#             keywords=keywords,
#             obsidian_markdown=obsidian_markdown,
#             embedding=embedding
#         )

#     except Exception as e:
#         logger.error(f"Error processing URL: {str(e)}")
#         stack_trace = "".join(traceback.format_tb(e.__traceback__))
#         logger.error(f"Stack trace: {stack_trace}")
#         raise HTTPException(status_code=500, detail=str(e))


# # Add a document
# @app.post("/documents/", response_model=DocumentResponse)
# def create_document(
#     document: DocumentCreate, 
#     db: Database = Depends(get_db)
# ):
#     try:
#         doc_id = db.store_content(document.dict())
#         stored_doc = db.get_content(doc_id)
#         return DocumentResponse(**stored_doc)
#     except Exception as e:
#         logger.error(f"Error creating document: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # Get all documents
# @app.get("/documents/", response_model=List[DocumentResponse])
# def read_documents(
#     skip: int = 0, 
#     limit: int = 100, 
#     db: Database = Depends(get_db)
# ):
#     try:
#         documents = db.get_all_content(skip=skip, limit=limit)
#         return [DocumentResponse(**doc) for doc in documents]
#     except Exception as e:
#         logger.error(f"Error retrieving documents: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # Get a document by ID
# @app.get("/documents/{document_id}", response_model=DocumentResponse)
# def read_document(
#     document_id: str, 
#     db: Database = Depends(get_db)
# ):
#     try:
#         document = db.get_content(document_id)
#         if document is None:
#             raise HTTPException(status_code=404, detail="Document not found")
#         return DocumentResponse(**document)
#     except Exception as e:
#         logger.error(f"Error retrieving document {document_id}: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @app.put("/documents/{document_id}", response_model=DocumentResponse)
# def update_document(
#     document_id: str,
#     document: DocumentUpdate,
#     db: Database = Depends(get_db)
# ):
#     try:
#         updated_doc = db.update_content(document_id, document.dict(exclude_unset=True))
#         if updated_doc is None:
#             raise HTTPException(status_code=404, detail="Document not found")
#         return DocumentResponse(**updated_doc)
#     except Exception as e:
#         logger.error(f"Error updating document {document_id}: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# # Keyword endpoints
# @app.post("/documents/{document_id}/keywords/", response_model=KeywordResponse)
# def create_keyword(document_id: int, keyword: KeywordCreate, db: Session = Depends(get_db)):
#     document = db.query(Document).filter(Document.id == document_id).first()
#     if document is None:
#         raise HTTPException(status_code=404, detail="Document not found")
    
#     db_keyword = Keyword(**keyword.dict(), document_id=document_id)
#     db.add(db_keyword)
#     db.commit()
#     db.refresh(db_keyword)
#     return db_keyword


# @app.get("/documents/{document_id}/keywords/", response_model=List[KeywordResponse])
# def read_keywords(document_id: int, db: Session = Depends(get_db)):
#     document = db.query(Document).filter(Document.id == document_id).first()
#     if document is None:
#         raise HTTPException(status_code=404, detail="Document not found")
#     return document.keywords


# @app.delete("/keywords/{keyword_id}")
# def delete_keyword(keyword_id: int, db: Session = Depends(get_db)):
#     keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
#     if keyword is None:
#         raise HTTPException(status_code=404, detail="Keyword not found")
    
#     db.delete(keyword)
#     db.commit()
#     return {"message": "Keyword deleted successfully"}


###############################################
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)