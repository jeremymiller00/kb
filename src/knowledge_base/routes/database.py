from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from src.knowledge_base.core.models import DocumentResponse, DocumentCreate
from src.knowledge_base.storage.database import Database
from src.knowledge_base.utils.config import configure_logging

logger = configure_logging()
router = APIRouter(prefix="/content", tags=["database"])


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


@router.post("/", response_model=DocumentResponse)
def store_content(document: DocumentCreate, db: Database = Depends(get_db)):
    try:
        doc_id = db.store_content(document.dict())
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
        updated = db.update_content(content_id, document.dict())
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
        results =  db.search_content(query, limit=limit)
        return [DocumentResponse(**doc) for doc in results]
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))