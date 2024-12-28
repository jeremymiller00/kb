"""WORK IN PROGRESS"""

from typing import List

from fastapi import APIRouter, HTTPException, Depends
from fastapi.staticfiles import StaticFiles

from src.knowledge_base.core.models import DocumentResponse
from src.knowledge_base.storage.database import Database
from src.knowledge_base.utils.config import configure_logging

logger = configure_logging()
router = APIRouter(tags=["database"])


# Dependency
def get_db():
    db = Database(logger=logger)
    try:
        yield db
    finally:
        db.close()


# Get all documents
@router.get("/", response_model=List[DocumentResponse])
def read_document(
    content_id: int = 0, 
    db: Database = Depends(get_db)
):
    try:
        document = db.get_content(content_id=content_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # Convert document to dict if it isn't already
        if not isinstance(document, dict):
            document = dict(document)
            
        # Create DocumentResponse with unpacked dictionary
        return [DocumentResponse(**document)]
    except Exception as e:
        logger.error(f"Error retrieving document: {e}")
        logger.debug(f"Document data: {document}")
        raise HTTPException(status_code=500, detail=str(e))


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

