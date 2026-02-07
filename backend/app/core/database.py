"""
Re-export database utilities from app.models.database.

This module exists so that imports like `from app.core.database import get_db`
work across the codebase.
"""
from app.models.database import get_db, Base, init_db, close_db

__all__ = ["get_db", "Base", "init_db", "close_db"]
