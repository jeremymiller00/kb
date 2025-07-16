"""
FastAPI routes for AI suggestion generation and session management.
"""

import os
import logging
from typing import Optional
from fastapi import APIRouter, Request, HTTPException, Depends, Cookie
from fastapi.responses import JSONResponse

from ..ai.suggestion_service import SuggestionService
from ..core.session_manager import SessionManager

# Initialize logger
logger = logging.getLogger(__name__)

# Lazy initialization - these will be initialized on first use
session_manager = None
suggestion_service = None

def get_session_manager():
    """Lazy initialization of session manager"""
    global session_manager
    if session_manager is None:
        try:
            session_manager = SessionManager(
                storage_path=os.path.expanduser("~/.kb_sessions.json"),
                session_expiry_hours=24
            )
            logger.info("Successfully initialized session manager")
        except Exception as e:
            logger.error(f"Failed to initialize session manager: {e}")
            session_manager = False  # Mark as failed
    return session_manager if session_manager is not False else None

def get_suggestion_service():
    """Lazy initialization of suggestion service"""
    global suggestion_service
    if suggestion_service is None:
        try:
            sm = get_session_manager()
            if sm:
                suggestion_service = SuggestionService(
                    session_manager=sm,
                    api_base_url=os.getenv('API_BASE_URL', 'http://localhost:8000')
                )
                logger.info("Successfully initialized suggestion service")
            else:
                suggestion_service = False  # Mark as failed
        except Exception as e:
            logger.error(f"Failed to initialize suggestion service: {e}")
            suggestion_service = False  # Mark as failed
    return suggestion_service if suggestion_service is not False else None

# Create router
router = APIRouter(prefix="/api", tags=["suggestions"])


def get_session_id(kb_session_id: Optional[str] = Cookie(None)) -> Optional[str]:
    """Dependency to extract session ID from cookie."""
    return kb_session_id


@router.get("/suggestions/{article_id}")
async def get_suggestions(
    article_id: str,
    count: int = 5,
    force_fresh: bool = True,
    session_id: Optional[str] = Depends(get_session_id)
):
    """Generate AI suggestions for an article with full context.
    
    Args:
        article_id: ID of the article to generate suggestions for
        count: Number of suggestions to generate (1-100, default: 5)
        force_fresh: Always generate fresh suggestions, no caching (default: True)
        session_id: User session ID from cookie (optional)
    
    Returns:
        JSON response with suggestions and context metadata
    """
    try:
        # Get suggestion service (lazy initialization)
        svc = get_suggestion_service()
        if not svc:
            raise HTTPException(
                status_code=503,
                detail={
                    "suggestions": [],
                    "context": {"error": "Suggestion service not available"},
                    "success": False
                }
            )
        
        # Validate suggestion count
        suggestion_count = min(max(count, 1), 100)  # Between 1 and 100

        # Generate contextual suggestions
        result = svc.generate_contextual_suggestions(
            current_article_id=article_id,
            session_id=session_id,
            suggestion_count=suggestion_count,
            include_recent_articles=True,
            include_similar_articles=True,
            force_fresh=force_fresh
        )
        print(f"DEBUG: Suggestions generated: {result}")  # Debugging line

        logger.info(f"Generated {len(result.get('suggestions', []))} suggestions for article {article_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating suggestions for article {article_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "suggestions": [],
                "context": {"error": str(e)},
                "success": False
            }
        )


@router.get("/suggestions/{article_id}/context")
async def get_suggestion_context(
    article_id: str,
    session_id: Optional[str] = Depends(get_session_id)
):
    """Get context summary for suggestion generation (debugging endpoint).
    
    Args:
        article_id: ID of the article
        session_id: User session ID from cookie (optional)
    
    Returns:
        JSON response with context summary for debugging
    """
    try:
        svc = get_suggestion_service()
        if not svc:
            raise HTTPException(
                status_code=503,
                detail={"error": "Suggestion service not available"}
            )
        
        context_summary = svc.get_suggestion_context_summary(
            article_id=article_id,
            session_id=session_id
        )
        
        logger.debug(f"Retrieved context summary for article {article_id}")
        return context_summary
        
    except Exception as e:
        logger.error(f"Error getting suggestion context for article {article_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": str(e)}
        )


@router.get("/session/{session_id}")
async def get_session_context(session_id: str):
    """Get session context for AI suggestions.
    
    Args:
        session_id: The session ID to retrieve context for
    
    Returns:
        JSON response with session information and recent articles
    """
    try:
        sm = get_session_manager()
        if not sm:
            raise HTTPException(
                status_code=503,
                detail={"error": "Session manager not available", "session_id": None}
            )
        
        context = sm.get_session_context(session_id)
        logger.debug(f"Retrieved session context for {session_id}")
        return context
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session context: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to get session context", "session_id": None}
        )


@router.get("/session/stats")
async def get_session_stats():
    """Get session manager statistics.
    
    Returns:
        JSON response with session statistics
    """
    try:
        sm = get_session_manager()
        if not sm:
            raise HTTPException(
                status_code=503,
                detail={"error": "Session manager not available"}
            )
        
        stats = sm.get_stats()
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session stats: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "Failed to get session stats"}
        )


@router.post("/session/{session_id}/record-view")
async def record_article_view(
    session_id: str,
    article_id: str,
    article_url: Optional[str] = None,
    article_summary: Optional[str] = None
):
    """Record an article view in the session for context tracking.
    
    Args:
        session_id: The session ID
        article_id: ID of the viewed article
        article_url: URL of the article (optional)
        article_summary: Summary of the article (optional)
    
    Returns:
        JSON response indicating success/failure
    """
    try:
        sm = get_session_manager()
        if not sm:
            raise HTTPException(
                status_code=503,
                detail={"success": False, "error": "Session manager not available"}
            )
        
        success = sm.record_article_view(
            session_id=session_id,
            article_id=article_id,
            article_url=article_url,
            article_summary=article_summary
        )
        
        if success:
            logger.debug(f"Recorded article view: session={session_id}, article={article_id}")
            return {"success": True, "message": "Article view recorded"}
        else:
            logger.warning(f"Failed to record article view: session={session_id}, article={article_id}")
            return {"success": False, "message": "Failed to record article view"}
            
    except Exception as e:
        logger.error(f"Error recording article view: {e}")
        raise HTTPException(
            status_code=500,
            detail={"success": False, "error": str(e)}
        )