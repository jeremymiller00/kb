"""Routes for data viewer API."""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query

from knowledge_base.utils.data_viewer import DataViewer
from knowledge_base.utils.logger import logger

router = APIRouter(prefix="/data", tags=["Data"])


@router.get("/directories")
def list_directories():
    """List all data directories in the knowledge base."""
    try:
        viewer = DataViewer(logger=logger)
        directories = viewer.list_data_directories()
        return [{"name": dir_path.name, "path": str(dir_path)} for dir_path in directories]
    except Exception as e:
        logger.error(f"Error listing directories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files")
def list_files(
    directory: Optional[str] = Query(None, description="Directory to list files from"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    days: Optional[int] = Query(None, description="Only show files from the last N days")
):
    """List all data files with optional filtering."""
    try:
        viewer = DataViewer(logger=logger)
        files = viewer.list_data_files(directory=directory, file_type=file_type, days=days)
        return files
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/file/{file_path:path}")
def get_file_content(file_path: str):
    """Get the content of a specific file."""
    try:
        viewer = DataViewer(logger=logger)
        content = viewer.get_file_content(file_path)
        return content
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
def get_file_types():
    """Get a list of all file types in the knowledge base."""
    try:
        viewer = DataViewer(logger=logger)
        types = viewer.get_file_types()
        return types
    except Exception as e:
        logger.error(f"Error getting file types: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
def get_stats():
    """Get statistics about the knowledge base."""
    try:
        viewer = DataViewer(logger=logger)
        stats = viewer.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))