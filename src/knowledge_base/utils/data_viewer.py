"""Data viewer module for browsing and displaying knowledge base data files.

This module provides utilities for:
- Listing all data files in the DSV_KB_PATH directory
- Reading and parsing JSON data files
- Filtering and sorting files by type, date, and other criteria
- Displaying file contents and metadata

Dependencies:
    os: File and directory operations
    json: JSON data encoding/decoding
    pathlib: Object-oriented filesystem paths
    datetime: Date and time manipulation
"""

import os
import json
import time
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from src.knowledge_base.utils.logger import logger


class DataViewer:
    """Class for viewing and managing knowledge base data files."""
    
    def __init__(self, logger=None):
        """Initialize the DataViewer with optional logger."""
        self.logger = logger
        self.kb_path = os.getenv('DSV_KB_PATH')
        if not self.kb_path:
            raise ValueError("DSV_KB_PATH environment variable not set")
        self.kb_path = Path(self.kb_path)
        
    def list_data_directories(self) -> List[Path]:
        """List all date-based directories in the knowledge base."""
        if self.logger:
            self.logger.debug(f"Listing directories in {self.kb_path}")
        
        # Get all directories that match the YYYY-MM-DD pattern
        date_dirs = [d for d in self.kb_path.iterdir() 
                    if d.is_dir() and self._is_date_directory(d.name)]
        
        # Sort by date (newest first)
        date_dirs.sort(reverse=True)
        
        if self.logger:
            self.logger.debug(f"Found {len(date_dirs)} date directories")
        
        return date_dirs
    
    def list_data_files(self, 
                        directory: Optional[Union[str, Path]] = None, 
                        file_type: Optional[str] = None,
                        days: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List all data files with metadata.
        
        Args:
            directory: Specific directory to list files from (optional)
            file_type: Filter by file type (github, arxiv, youtube, etc.)
            days: Only show files from the last N days
            
        Returns:
            List of dictionaries with file metadata
        """
        if self.logger:
            self.logger.debug(f"Listing data files with filters: dir={directory}, type={file_type}, days={days}")
        
        files = []
        
        # If directory is specified, only look there
        if directory:
            dir_path = Path(directory) if isinstance(directory, str) else directory
            if not dir_path.is_absolute():
                dir_path = self.kb_path / dir_path
            
            dirs_to_search = [dir_path] if dir_path.exists() and dir_path.is_dir() else []
        else:
            # Get directories based on days filter or all directories
            all_dirs = self.list_data_directories()
            if days:
                # Filter to only include directories from the last N days
                cutoff_time = time.time() - (days * 86400)
                dirs_to_search = []
                for dir_path in all_dirs:
                    dir_date = self._parse_date_from_directory(dir_path.name)
                    if dir_date and dir_date.timestamp() >= cutoff_time:
                        dirs_to_search.append(dir_path)
            else:
                dirs_to_search = all_dirs
        
        # Iterate through directories and collect files
        for dir_path in dirs_to_search:
            for file_path in dir_path.glob("*.json"):
                try:
                    file_info = self._extract_file_info(file_path)
                    
                    # Apply file type filter if specified
                    if file_type and file_info.get("type") != file_type:
                        continue
                        
                    files.append(file_info)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"Error processing file {file_path}: {str(e)}")
        
        # Sort files by timestamp (newest first)
        files.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        if self.logger:
            self.logger.debug(f"Found {len(files)} data files matching criteria")
            
        return files
    
    def get_file_content(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Read and parse a data file.
        
        Args:
            file_path: Path to the JSON data file
            
        Returns:
            Dictionary with file content data
        """
        path = Path(file_path) if isinstance(file_path, str) else file_path
        
        if not path.is_absolute():
            path = self.kb_path / path
            
        if not path.exists() or not path.is_file():
            if self.logger:
                self.logger.error(f"File not found: {path}")
            raise FileNotFoundError(f"File not found: {path}")
            
        try:
            if self.logger:
                self.logger.debug(f"Reading file: {path}")
                
            with open(path, 'r') as f:
                content = json.load(f)
                
            return content
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error reading file {path}: {str(e)}")
            raise
    
    def get_file_types(self) -> List[str]:
        """Get a list of all file types in the knowledge base."""
        file_types = set()
        
        try:
            # Check if index.csv exists for faster processing
            index_path = self.kb_path / "index.csv"
            if index_path.exists():
                with open(index_path, 'r') as f:
                    for line in f:
                        parts = line.strip().split(',')
                        if parts and len(parts) >= 1:
                            file_types.add(parts[0])
            else:
                # Fall back to scanning files
                for file_info in self.list_data_files():
                    if "type" in file_info:
                        file_types.add(file_info["type"])
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting file types: {str(e)}")
                
        return sorted(list(file_types))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base files."""
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "oldest_file": None,
            "newest_file": None,
            "types": {},
            "files_by_date": {}
        }
        
        try:
            files = self.list_data_files()
            stats["total_files"] = len(files)
            
            if files:
                # Get oldest and newest files
                files_by_time = sorted(files, key=lambda x: x.get("timestamp", 0))
                if files_by_time:
                    stats["oldest_file"] = files_by_time[0]
                    stats["newest_file"] = files_by_time[-1]
                
                # Collect stats by type and date
                for file in files:
                    # Stats by type
                    file_type = file.get("type", "unknown")
                    if file_type not in stats["types"]:
                        stats["types"][file_type] = 0
                    stats["types"][file_type] += 1
                    
                    # Stats by date
                    date_str = datetime.fromtimestamp(int(file.get("timestamp", 0))).strftime("%Y-%m-%d")
                    if date_str not in stats["files_by_date"]:
                        stats["files_by_date"][date_str] = 0
                    stats["files_by_date"][date_str] += 1
                    
                    # Calculate total size
                    file_path = file.get("file_path")
                    if file_path and Path(file_path).exists():
                        stats["total_size_bytes"] += Path(file_path).stat().st_size
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error calculating stats: {str(e)}")
                
        return stats
    
    def _extract_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Extract basic information from a file without loading full content."""
        file_info = {
            "file_path": str(file_path),
            "file_name": file_path.name,
            "directory": file_path.parent.name
        }
        
        # Try to extract info from filename
        parts = file_path.stem.split('_')
        if len(parts) > 1 and parts[-1].isdigit():
            file_info["timestamp"] = int(parts[-1])
            file_info["date"] = datetime.fromtimestamp(file_info["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        
        # Try to load minimal info from file
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                
            # Extract key metadata without loading full content
            for key in ["url", "type", "timestamp", "keywords"]:
                if key in data:
                    file_info[key] = data[key]
                    
            # Add formatted date if timestamp exists
            if "timestamp" in data and "date" not in file_info:
                file_info["date"] = datetime.fromtimestamp(int(data["timestamp"])).strftime("%Y-%m-%d %H:%M:%S")
                
            # Add summary snippet
            if "summary" in data:
                max_len = 100
                summary = data["summary"]
                file_info["summary_snippet"] = summary[:max_len] + "..." if len(summary) > max_len else summary
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Could not read metadata from {file_path}: {str(e)}")
        
        return file_info
    
    def _is_date_directory(self, dirname: str) -> bool:
        """Check if a directory name matches the YYYY-MM-DD pattern."""
        return bool(re.match(r'^\d{4}-\d{2}-\d{2}$', dirname))
    
    def _parse_date_from_directory(self, dirname: str) -> Optional[datetime]:
        """Parse a datetime object from a directory name in YYYY-MM-DD format."""
        if self._is_date_directory(dirname):
            try:
                return datetime.strptime(dirname, "%Y-%m-%d")
            except ValueError:
                return None
        return None