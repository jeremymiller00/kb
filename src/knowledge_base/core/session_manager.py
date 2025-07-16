import os
import json
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from uuid import uuid4

from .models import DocumentResponse

logger = logging.getLogger(__name__)


@dataclass
class BrowsingSession:
    """Represents a user's browsing session with article history."""
    session_id: str
    created_at: datetime
    last_accessed: datetime
    viewed_articles: List[Dict[str, Any]]  # Store article IDs and timestamps
    max_history: int = 5
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for storage."""
        return {
            'session_id': self.session_id,
            'created_at': self.created_at.isoformat(),
            'last_accessed': self.last_accessed.isoformat(),
            'viewed_articles': self.viewed_articles,
            'max_history': self.max_history
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrowsingSession':
        """Create session from dictionary."""
        return cls(
            session_id=data['session_id'],
            created_at=datetime.fromisoformat(data['created_at']),
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            viewed_articles=data.get('viewed_articles', []),
            max_history=data.get('max_history', 5)
        )
    
    def add_article_view(self, article_id: str, article_url: str = None, article_summary: str = None):
        """Add an article view to the session history."""
        now = datetime.now()
        
        # Create article view record
        view_record = {
            'article_id': article_id,
            'viewed_at': now.isoformat(),
            'article_url': article_url,
            'article_summary': article_summary
        }
        
        # Remove existing view of same article (to move it to front)
        self.viewed_articles = [
            view for view in self.viewed_articles 
            if view.get('article_id') != article_id
        ]
        
        # Add new view at the beginning
        self.viewed_articles.insert(0, view_record)
        
        # Trim to max history
        if len(self.viewed_articles) > self.max_history:
            self.viewed_articles = self.viewed_articles[:self.max_history]
        
        # Update last accessed
        self.last_accessed = now
    
    def get_recent_articles(self, limit: int = None) -> List[Dict[str, Any]]:
        """Get recently viewed articles, optionally limited."""
        limit = limit or self.max_history
        return self.viewed_articles[:limit]
    
    def is_expired(self, expiry_hours: int = 24) -> bool:
        """Check if session has expired."""
        expiry_time = datetime.now() - timedelta(hours=expiry_hours)
        return self.last_accessed < expiry_time


class SessionManager:
    """Manages user browsing sessions for context-aware suggestions."""
    
    def __init__(self, storage_path: str = None, session_expiry_hours: int = 24):
        """Initialize session manager.
        
        Args:
            storage_path: Path to store session data (default: temp directory)
            session_expiry_hours: Hours after which sessions expire (default: 24)
        """
        self.storage_path = storage_path or os.path.join(
            os.path.expanduser("~"), ".kb_sessions"
        )
        self.session_expiry_hours = session_expiry_hours
        self.sessions: Dict[str, BrowsingSession] = {}
        
        # Ensure storage directory exists
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        # Load existing sessions
        self._load_sessions()
        
        # Clean up expired sessions
        self._cleanup_expired_sessions()
    
    def create_session(self) -> str:
        """Create a new browsing session and return session ID."""
        session_id = str(uuid4())
        now = datetime.now()
        
        session = BrowsingSession(
            session_id=session_id,
            created_at=now,
            last_accessed=now,
            viewed_articles=[]
        )
        
        self.sessions[session_id] = session
        self._save_sessions()
        
        logger.info(f"Created new browsing session: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[BrowsingSession]:
        """Get a session by ID, return None if not found or expired."""
        if not session_id or session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if expired
        if session.is_expired(self.session_expiry_hours):
            self._remove_session(session_id)
            return None
        
        return session
    
    def record_article_view(
        self, 
        session_id: str, 
        article_id: str, 
        article_url: str = None,
        article_summary: str = None
    ) -> bool:
        """Record an article view in the session.
        
        Args:
            session_id: The session ID
            article_id: ID of the viewed article
            article_url: URL of the article (optional)
            article_summary: Summary of the article (optional)
            
        Returns:
            True if recorded successfully, False otherwise
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Cannot record article view: session {session_id} not found")
            return False
        
        session.add_article_view(
            article_id=str(article_id),
            article_url=article_url,
            article_summary=article_summary
        )
        
        self._save_sessions()
        logger.debug(f"Recorded article view: session={session_id}, article={article_id}")
        return True
    
    def get_recent_articles(
        self, 
        session_id: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recently viewed articles for a session.
        
        Args:
            session_id: The session ID
            limit: Maximum number of articles to return
            
        Returns:
            List of article view records
        """
        session = self.get_session(session_id)
        if not session:
            return []
        
        return session.get_recent_articles(limit)
    
    def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Get comprehensive session context for suggestions.
        
        Returns:
            Dictionary with session info and recent articles
        """
        session = self.get_session(session_id)
        if not session:
            return {
                'session_id': None,
                'recent_articles': [],
                'session_duration': 0,
                'total_articles_viewed': 0
            }
        
        now = datetime.now()
        session_duration = (now - session.created_at).total_seconds() / 3600  # hours
        
        return {
            'session_id': session_id,
            'recent_articles': session.get_recent_articles(),
            'session_duration': round(session_duration, 2),
            'total_articles_viewed': len(session.viewed_articles),
            'last_accessed': session.last_accessed.isoformat()
        }
    
    def cleanup_session(self, session_id: str) -> bool:
        """Manually cleanup/remove a session."""
        return self._remove_session(session_id)
    
    def _load_sessions(self):
        """Load sessions from storage."""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'r') as f:
                    sessions_data = json.load(f)
                
                for session_id, session_data in sessions_data.items():
                    try:
                        session = BrowsingSession.from_dict(session_data)
                        self.sessions[session_id] = session
                    except Exception as e:
                        logger.warning(f"Failed to load session {session_id}: {e}")
                
                logger.info(f"Loaded {len(self.sessions)} sessions from storage")
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
    
    def _save_sessions(self):
        """Save sessions to storage."""
        try:
            sessions_data = {}
            for session_id, session in self.sessions.items():
                sessions_data[session_id] = session.to_dict()
            
            with open(self.storage_path, 'w') as f:
                json.dump(sessions_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    def _remove_session(self, session_id: str) -> bool:
        """Remove a session from memory and storage."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self._save_sessions()
            logger.info(f"Removed session: {session_id}")
            return True
        return False
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            if session.is_expired(self.session_expiry_hours):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self._remove_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session manager statistics."""
        active_sessions = len(self.sessions)
        total_article_views = sum(
            len(session.viewed_articles) 
            for session in self.sessions.values()
        )
        
        return {
            'active_sessions': active_sessions,
            'total_article_views': total_article_views,
            'storage_path': self.storage_path,
            'session_expiry_hours': self.session_expiry_hours
        }