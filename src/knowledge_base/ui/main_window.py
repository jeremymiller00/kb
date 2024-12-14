"""
Main application window.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QMessageBox, QFileDialog, QMenu, QMenuBar,
    QStatusBar
)
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction

from .content_browser import ContentBrowser
from .search import SearchWidget
from .visualizations import VisualizationWidget
from .settings import SettingsDialog
from ..core.content_manager import ContentManager
from ..ai.llm_manager import LLMManager
from ..ai.embedding_manager import EmbeddingManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(
        self,
        config: Dict[str, Any],
        parent: Optional[QWidget] = None
    ):
        """Initialize main window.
        
        Args:
            config: Application configuration
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.config = config
        self._setup_managers()
        self._setup_ui()
        self._load_settings()
    
    def _setup_managers(self) -> None:
        """Set up core managers."""
        try:
            self.llm_manager = LLMManager(
                openai_api_key=self.config.get('ai', {}).get('openai_api_key'),
                local_model_path=self.config.get('ai', {}).get('local_model_path'),
                use_local_models=self.config.get('ai', {}).get('use_local_models', False)
            )
            
            self.embedding_manager = EmbeddingManager(
                model_name=self.config.get('ai', {}).get('embedding_model', 'all-MiniLM-L6-v2')
            )
            
            self.content_manager = ContentManager(
                llm_manager=self.llm_manager,
                embedding_manager=self.embedding_manager
            )
        except Exception as e:
            logger.error(f"Error setting up managers: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to initialize application: {str(e)}"
            )
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        self.setWindowTitle("Knowledge Base")
        self.resize(1200, 800)
        
        # Menu bar
        self._create_menus()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Tab widget
        self.tabs = QTabWidget()
        
        # Content browser tab
        self.content_browser = ContentBrowser(self.content_manager)
        self.tabs.addTab(self.content_browser, "Content")
        
        # Search tab
        self.search_widget = SearchWidget(self.content_manager)
        self.tabs.addTab(self.search_widget, "Search")
        
        # Visualization tab
        self.viz_widget = VisualizationWidget(self.content_manager)
        self.tabs.addTab(self.viz_widget, "Visualize")
        
        layout.addWidget(self.tabs)
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _create_menus(self) -> None:
        """Create application menus."""
        menu_bar = QMenuBar()
        self.setMenuBar(menu_bar)
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        new_action = QAction("&New Content", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_content)
        file_menu.addAction(new_action)
        
        import_action = QAction("&Import...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self._import_content)
        file_menu.addAction(import_action)
        
        export_action = QAction("&Export...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_content)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")
        
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self._show_settings)
        edit_menu.addAction(settings_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_all)
        view_menu.addAction(refresh_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _load_settings(self) -> None:
        """Load application settings."""
        settings = QSettings('Knowledge Base', 'App')
        
        # Window geometry
        geometry = settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        # Window state
        state = settings.value('windowState')
        if state:
            self.restoreState(state)
    
    def _save_settings(self) -> None:
        """Save application settings."""
        settings = QSettings('Knowledge Base', 'App')
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('windowState', self.saveState())
    
    async def _new_content(self) -> None:
        """Add new content."""
        url, ok = QFileDialog.getOpenFileName(
            self,
            "Select Content File",
            "",
            "All Files (*.*)"
        )
        if ok and url:
            try:
                await self.content_manager.process_url(url)
                self.content_browser._refresh_content()
                self.status_bar.showMessage("Content added successfully")
            except Exception as e:
                logger.error(f"Error adding content: {e}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to add content: {str(e)}"
                )
    
    def _import_content(self) -> None:
        """Import content from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Content",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            try:
                # TODO: Implement content import
                self.status_bar.showMessage("Content imported successfully")
            except Exception as e:
                logger.error(f"Error importing content: {e}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to import content: {str(e)}"
                )
    
    def _export_content(self) -> None:
        """Export content to file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Content",
            "",
            "JSON Files (*.json);;All Files (*.*)"
        )
        if file_path:
            try:
                # TODO: Implement content export
                self.status_bar.showMessage("Content exported successfully")
            except Exception as e:
                logger.error(f"Error exporting content: {e}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to export content: {str(e)}"
                )
    
    def _show_settings(self) -> None:
        """Show settings dialog."""
        dialog = SettingsDialog(self.config, self)
        if dialog.exec():
            # Apply new settings
            new_config = dialog.get_config()
            self.config.update(new_config)
            self._setup_managers()
            self.status_bar.showMessage("Settings updated successfully")
    
    async def _refresh_all(self) -> None:
        """Refresh all views."""
        try:
            await self.content_browser._refresh_content()
            await self.search_widget._refresh_content()
            await self.viz_widget._refresh_content()
            self.status_bar.showMessage("Content refreshed successfully")
        except Exception as e:
            logger.error(f"Error refreshing content: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to refresh content: {str(e)}"
            )
    
    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Knowledge Base",
            "Knowledge Base Manager\nVersion 0.1.0\n\n"
            "A tool for managing and analyzing technical content."
        )
    
    def closeEvent(self, event) -> None:
        """Handle application close event.
        
        Args:
            event: Close event
        """
        self._save_settings()
        event.accept()