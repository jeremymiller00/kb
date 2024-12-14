"""
Content browser interface component.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTextEdit,
    QPushButton, QLabel, QComboBox, QLineEdit,
    QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.content_manager import ContentManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ContentBrowser(QWidget):
    """Content browser widget."""
    
    content_selected = pyqtSignal(str)  # Emits content ID when selected
    
    def __init__(
        self,
        content_manager: ContentManager,
        parent: Optional[QWidget] = None
    ):
        """Initialize content browser.
        
        Args:
            content_manager: Content manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.content_manager = content_manager
        self._current_content_id = None
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Content type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems(['All Types', 'arxiv', 'github', 'youtube', 'web'])
        self.type_filter.currentTextChanged.connect(self._filter_content)
        toolbar.addWidget(QLabel('Type:'))
        toolbar.addWidget(self.type_filter)
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText('Search content...')
        self.search_box.textChanged.connect(self._filter_content)
        toolbar.addWidget(self.search_box)
        
        # Sort options
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(['Newest First', 'Oldest First', 'Type', 'Title'])
        self.sort_combo.currentTextChanged.connect(self._sort_content)
        toolbar.addWidget(QLabel('Sort:'))
        toolbar.addWidget(self.sort_combo)
        
        # Refresh button
        refresh_btn = QPushButton('Refresh')
        refresh_btn.clicked.connect(self._refresh_content)
        toolbar.addWidget(refresh_btn)
        
        layout.addLayout(toolbar)
        
        # Main content area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Content tree
        self.content_tree = QTreeWidget()
        self.content_tree.setHeaderLabels(['Title', 'Type', 'Date'])
        self.content_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.content_tree.customContextMenuRequested.connect(self._show_context_menu)
        self.content_tree.itemSelectionChanged.connect(self._handle_selection)
        splitter.addWidget(self.content_tree)
        
        # Preview panel
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        
        self.preview_title = QLabel()
        self.preview_title.setWordWrap(True)
        preview_layout.addWidget(self.preview_title)
        
        self.preview_meta = QLabel()
        self.preview_meta.setWordWrap(True)
        preview_layout.addWidget(self.preview_meta)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        preview_widget.setLayout(preview_layout)
        splitter.addWidget(preview_widget)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
        
        # Initial content load
        self._refresh_content()
    
    async def _refresh_content(self) -> None:
        """Refresh content list."""
        try:
            all_content = await self.content_manager.get_all_content()
            self._populate_tree(all_content)
        except Exception as e:
            logger.error(f"Error refreshing content: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to refresh content: {str(e)}"
            )
    
    def _populate_tree(self, content_items: List[Dict[str, Any]]) -> None:
        """Populate content tree.
        
        Args:
            content_items: List of content items
        """
        self.content_tree.clear()
        items = []
        
        for content in content_items:
            item = QTreeWidgetItem([
                content.get('url', '').split('/')[-1],
                content.get('type', ''),
                datetime.fromtimestamp(
                    content['timestamp']
                ).strftime('%Y-%m-%d %H:%M')
            ])
            item.setData(0, Qt.ItemDataRole.UserRole, content['id'])
            items.append(item)
        
        self.content_tree.addTopLevelItems(items)
        self._sort_content()
        self._filter_content()
        
        # Adjust column widths
        for i in range(3):
            self.content_tree.resizeColumnToContents(i)
    
    def _filter_content(self) -> None:
        """Filter content based on type and search text."""
        content_type = self.type_filter.currentText()
        search_text = self.search_box.text().lower()
        
        for i in range(self.content_tree.topLevelItemCount()):
            item = self.content_tree.topLevelItem(i)
            show = True
            
            # Type filter
            if content_type != 'All Types' and item.text(1) != content_type:
                show = False
            
            # Search filter
            if search_text:
                if not any(
                    search_text in item.text(col).lower()
                    for col in range(3)
                ):
                    show = False
            
            item.setHidden(not show)
    
    def _sort_content(self) -> None:
        """Sort content based on selected criteria."""
        sort_option = self.sort_combo.currentText()
        
        if sort_option == 'Newest First':
            self.content_tree.sortItems(
                2, Qt.SortOrder.DescendingOrder
            )
        elif sort_option == 'Oldest First':
            self.content_tree.sortItems(
                2, Qt.SortOrder.AscendingOrder
            )
        elif sort_option == 'Type':
            self.content_tree.sortItems(
                1, Qt.SortOrder.AscendingOrder
            )
        else:  # Title
            self.content_tree.sortItems(
                0, Qt.SortOrder.AscendingOrder
            )
    
    def _show_context_menu(self, position) -> None:
        """Show context menu for selected item."""
        item = self.content_tree.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        open_action = QAction('Open', self)
        open_action.triggered.connect(
            lambda: self._open_content(item)
        )
        menu.addAction(open_action)
        
        delete_action = QAction('Delete', self)
        delete_action.triggered.connect(
            lambda: self._delete_content(item)
        )
        menu.addAction(delete_action)
        
        find_similar_action = QAction('Find Similar', self)
        find_similar_action.triggered.connect(
            lambda: self._find_similar_content(item)
        )
        menu.addAction(find_similar_action)
        
        menu.exec(self.content_tree.viewport().mapToGlobal(position))
    
    async def _handle_selection(self) -> None:
        """Handle content selection."""
        items = self.content_tree.selectedItems()
        if not items:
            self._clear_preview()
            return
            
        content_id = items[0].data(0, Qt.ItemDataRole.UserRole)
        if content_id != self._current_content_id:
            await self._show_preview(content_id)
            self.content_selected.emit(content_id)
    
    async def _show_preview(self, content_id: str) -> None:
        """Show content preview.
        
        Args:
            content_id: ID of content to preview
        """
        try:
            content = await self.content_manager.get_content(content_id)
            if not content:
                self._clear_preview()
                return
                
            self._current_content_id = content_id
            self.preview_title.setText(content.get('url', ''))
            
            meta_text = (
                f"Type: {content.get('type', '')}\n"
                f"Date: {datetime.fromtimestamp(content['timestamp']).strftime('%Y-%m-%d %H:%M')}\n"
                f"Keywords: {', '.join(content.get('keywords', []))}"
            )
            self.preview_meta.setText(meta_text)
            
            preview_content = (
                f"{content.get('summary', '')}\n\n"
                f"{content.get('content', '')[:1000]}..."
            )
            self.preview_text.setText(preview_content)
            
        except Exception as e:
            logger.error(f"Error showing preview: {e}")
            self._clear_preview()
    
    def _clear_preview(self) -> None:
        """Clear preview panel."""
        self._current_content_id = None
        self.preview_title.setText('')
        self.preview_meta.setText('')
        self.preview_text.setText('')
    
    async def _open_content(self, item: QTreeWidgetItem) -> None:
        """Open content in separate window.
        
        Args:
            item: Selected tree item
        """
        content_id = item.data(0, Qt.ItemDataRole.UserRole)
        # TODO: Implement content viewer
    
    async def _delete_content(self, item: QTreeWidgetItem) -> None:
        """Delete selected content.
        
        Args:
            item: Selected tree item
        """
        content_id = item.data(0, Qt.ItemDataRole.UserRole)
        
        reply = QMessageBox.question(
            self,
            'Delete Content',
            'Are you sure you want to delete this content?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                await self.content_manager.delete_content(content_id)
                self.content_tree.takeTopLevelItem(
                    self.content_tree.indexOfTopLevelItem(item)
                )
                if content_id == self._current_content_id:
                    self._clear_preview()
            except Exception as e:
                logger.error(f"Error deleting content: {e}")
                QMessageBox.warning(
                    self,
                    "Error",
                    f"Failed to delete content: {str(e)}"
                )
    
    async def _find_similar_content(self, item: QTreeWidgetItem) -> None:
        """Find similar content.
        
        Args:
            item: Selected tree item
        """
        content_id = item.data(0, Qt.ItemDataRole.UserRole)
        # TODO: Implement similarity search