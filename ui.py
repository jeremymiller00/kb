#!/usr/bin/env python3
"""
ASGI entry point for the Knowledge Base FastHTML UI
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.knowledge_base.routes.ui import app

# Export the app for ASGI servers
__all__ = ['app']