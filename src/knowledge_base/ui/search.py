"""
Search interface component.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem,
    QComboBox, QSpinBox, QCheckBox,
    QTextEdit, QSplitter, QMenu
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.content_manager import ContentManager
from ..utils.logger import get_logger

logger = get_logger(__name__)

class SearchWidget(QWidget):
    """Advanced search interface widget."""
    
    result_selected = pyqtSignal(str)  # Emits content ID when selected
    
    def __init__(
        self,
        content_manager: ContentManager,
        parent: Optional[QWidget] = None
    ):
        """Initialize search widget.
        
        Args:
            content_manager: Content manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.content_manager = content_manager
        self.current_results = []
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Search controls
        controls = QHBoxLayout()
        
        # Search box
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Enter search query...")
        self.search_box.returnPressed.connect(self._perform_search)
        controls.addWidget(self.search_box)
        
        # Search type
        self.search_type = QComboBox()
        self.search_type.addItems([
            "Semantic Search",
            "Keyword Search",
            "Combined Search"
        ])
        controls.addWidget(self.search_type)
        
        # Content type filter
        self.type_filter = QComboBox()
        self.type_filter.addItems([
            "All Types",
            "arxiv",
            "github",
            "youtube",
            "web"
        ])
        controls.addWidget(self.type_filter)
        
        # Results limit
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 100)
        self.limit_spin.setValue(20)
        controls.addWidget(QLabel("Limit:"))
        controls.addWidget(self.limit_spin)
        
        # Search button
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._perform_search)
        controls.addWidget(search_btn)
        
        layout.addLayout(controls)
        
        # Advanced options
        advanced_controls = QHBoxLayout()
        
        # Date range
        self.date_filter = QCheckBox("Date Range")
        advanced_controls.addWidget(self.date_filter)
        
        self.start_date = QLineEdit()
        self.start_date.setPlaceholderText("Start (YYYY-MM-DD)")
        advanced_controls.addWidget(self.start_date)
        
        self.end_date = QLineEdit()
        self.end_date.setPlaceholderText("End (YYYY-MM-DD)")
        advanced_controls.addWidget(self.end_date)
        
        # Similarity threshold
        advanced_controls.addWidget(QLabel("Similarity:"))
        self.similarity_threshold = QSpinBox()
        self.similarity_threshold.setRange(1, 100)
        self.similarity_threshold.setValue(70)
        self.similarity_threshold.setSuffix("%")
        advanced_controls.addWidget(self.similarity_threshold)
        
        advanced_controls.addStretch()
        layout.addLayout(advanced_controls)
        
        # Results area
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels([
            "Title",
            "Type",
            "Date",
            "Score",
            "Keywords"
        ])
        self.results_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self._show_context_menu)
        self.results_table.itemSelectionChanged.connect(self._handle_selection)
        splitter.addWidget(self.results_table)
        
        # Preview area
        preview_widget = QWidget()
        preview_layout = QVBoxLayout()
        
        self.preview_title = QLabel()
        self.preview_title.setWordWrap(True)
        preview_layout.addWidget(self.preview_title)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        preview_layout.addWidget(self.preview_text)
        
        preview_widget.setLayout(preview_layout)
        splitter.addWidget(preview_widget)
        
        layout.addWidget(splitter)
        self.setLayout(layout)
    
    async def _perform_search(self) -> None:
        """Perform search based on current settings."""
        try:
            # Build search parameters
            params = {
                'query': self.search_box.text(),
                'limit': self.limit_spin.value()
            }
            
            # Add content type filter
            content_type = self.type_filter.currentText()
            if content_type != 'All Types':
                params['type'] = content_type.lower()
            
            # Add date filter
            if self.date_filter.isChecked():
                try:
                    start = datetime.strptime(
                        self.start_date.text(),
                        '%Y-%m-%d'
                    ).timestamp()
                    end = datetime.strptime(
                        self.end_date.text(),
                        '%Y-%m-%d'
                    ).timestamp()
                    params['date_range'] = {'start': start, 'end': end}
                except ValueError:
                    pass
            
            # Add similarity threshold
            params['similarity_threshold'] = self.similarity_threshold.value() / 100
            
            # Perform search based on type
            search_type = self.search_type.currentText()
            if search_type == "Semantic Search":
                self.current_results = await self.content_manager.search(
                    query=params['query'],
                    use_embeddings=True,
                    **params
                )
            elif search_type == "Keyword Search":
                self.current_results = await self.content_manager.search(
                    query=params['query'],
                    use_embeddings=False,
                    **params
                )
            else:  # Combined Search
                self.current_results = await self.content_manager.search(
                    query=params['query'],
                    use_embeddings=True,
                    combine_results=True,
                    **params
                )
            
            self._display_results()
            
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            self.results_table.setRowCount(0)
            self.preview_title.setText("Search Error")
            self.preview_text.setText(str(e))
    
    def _display_results(self) -> None:
        """Display search results in table."""
        self.results_table.setRowCount(len(self.current_results))
        
        for row, result in enumerate(self.current_results):
            # Title/URL
            title_item = QTableWidgetItem(
                result.get('url', '').split('/')[-1]
            )
            title_item.setData(Qt.ItemDataRole.UserRole, result['id'])
            self.results_table.setItem(row, 0, title_item)
            
            # Type
            self.results_table.setItem(
                row,
                1,
                QTableWidgetItem(result.get('type', ''))
            )
            
            # Date
            date_str = datetime.fromtimestamp(
                result['timestamp']
            ).strftime('%Y-%m-%d %H:%M')
            self.results_table.setItem(row, 2, QTableWidgetItem(date_str))
            
            # Score
            score = result.get('similarity', 0.0)
            score_item = QTableWidgetItem(f"{score:.2%}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignRight)
            self.results_table.setItem(row, 3, score_item)
            
            # Keywords
            keywords = ', '.join(result.get('keywords', []))
            self.results_table.setItem(row, 4, QTableWidgetItem(keywords))
        
        # Adjust column widths
        self.results_table.resizeColumnsToContents()
    
    def _show_context_menu(self, position) -> None:
        """Show context menu for selected result."""
        item = self.results_table.itemAt(position)
        if not item:
            return
            
        menu = QMenu()
        
        open_action = QAction('Open', self)
        open_action.triggered.connect(
            lambda: self._open_result(item)
        )
        menu.addAction(open_action)
        
        find_similar_action = QAction('Find Similar', self)
        find_similar_action.triggered.connect(
            lambda: self._find_similar(item)
        )
        menu.addAction(find_similar_action)
        
        menu.exec(self.results_table.viewport().mapToGlobal(position))
    
    def _handle_selection(self) -> None:
        """Handle result selection."""
        items = self.results_table.selectedItems()
        if not items:
            self._clear_preview()
            return
        
        # Get selected result
        row = items[0].row()
        result = self.current_results[row]
        
        # Update preview
        self.preview_title.setText(result.get('url', ''))
        preview_text = (
            f"Type: {result.get('type', '')}\n"
            f"Date: {datetime.fromtimestamp(result['timestamp']).strftime('%Y-%m-%d %H:%M')}\n"
            f"Keywords: {', '.join(result.get('keywords', []))}\n\n"
            f"Summary:\n{result.get('summary', '')}\n\n"
            f"Content:\n{result.get('content', '')[:1000]}..."
        )
        self.preview_text.setText(preview_text)
        
        # Emit selected content ID
        self.result_selected.emit(result['id'])
    
    def _clear_preview(self) -> None:
        """Clear preview area."""
        self.preview_title.setText('')
        self.preview_text.setText('')
    
    async def _open_result(self, item: QTableWidgetItem) -> None:
        """Open selected result.
        
        Args:
            item: Selected table item
        """
        content_id = item.data(Qt.ItemDataRole.UserRole)
        # TODO: Implement result viewer
    
    async def _find_similar(self, item: QTableWidgetItem) -> None:
        """Find similar content to selected result.
        
        Args:
            item: Selected table item
        """
        content_id = item.data(Qt.ItemDataRole.UserRole)
        try:
            self.current_results = await self.content_manager.find_similar(
                content_id,
                limit=self.limit_spin.value()
            )
            self._display_results()
        except Exception as e:
            logger.error(f"Error finding similar content: {e}")
            self.results_table.setRowCount(0)
            self.preview_title.setText("Error")
            self.preview_text.setText(str(e))