"""
Visualization interface component.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
    QLabel, QPushButton, QSpinBox, QTabWidget,
    QGraphicsScene, QGraphicsView, QMessageBox,
    QScrollArea, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QColor
import networkx as nx
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..core.content_manager import ContentManager
from ..core.analytics import AnalyticsService
from ..utils.logger import get_logger

logger = get_logger(__name__)

class KnowledgeGraphWidget(QWidget):
    """Interactive knowledge graph visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self.graph = nx.Graph()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Controls
        controls = QHBoxLayout()
        
        self.layout_combo = QComboBox()
        self.layout_combo.addItems([
            "Force Directed",
            "Circular",
            "Hierarchical"
        ])
        self.layout_combo.currentTextChanged.connect(self._update_layout)
        controls.addWidget(QLabel("Layout:"))
        controls.addWidget(self.layout_combo)
        
        self.min_similarity = QSpinBox()
        self.min_similarity.setRange(0, 100)
        self.min_similarity.setValue(70)
        self.min_similarity.setSuffix("%")
        self.min_similarity.valueChanged.connect(self._update_graph)
        controls.addWidget(QLabel("Min Similarity:"))
        controls.addWidget(self.min_similarity)
        
        layout.addLayout(controls)
        
        # Graph view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)
        
        self.setLayout(layout)
    
    def update_graph(self, content: List[Dict[str, Any]]) -> None:
        """Update graph with new content.
        
        Args:
            content: List of content items
        """
        self.graph.clear()
        
        # Add nodes
        for item in content:
            self.graph.add_node(
                item['id'],
                title=item['url'].split('/')[-1],
                type=item['type']
            )
        
        # Add edges based on similarity
        threshold = self.min_similarity.value() / 100
        for i, item1 in enumerate(content):
            for item2 in content[i+1:]:
                if 'embedding' in item1 and 'embedding' in item2:
                    similarity = self._compute_similarity(
                        item1['embedding'],
                        item2['embedding']
                    )
                    if similarity >= threshold:
                        self.graph.add_edge(
                            item1['id'],
                            item2['id'],
                            weight=similarity
                        )
        
        self._update_layout()
    
    def _update_layout(self) -> None:
        """Update graph layout."""
        self.scene.clear()
        
        if not self.graph:
            return
        
        layout_type = self.layout_combo.currentText()
        
        if layout_type == "Force Directed":
            pos = nx.spring_layout(self.graph)
        elif layout_type == "Circular":
            pos = nx.circular_layout(self.graph)
        else:  # Hierarchical
            pos = nx.kamada_kawai_layout(self.graph)
        
        # Scale and center positions
        scale = 300
        for node, (x, y) in pos.items():
            pos[node] = (x * scale, y * scale)
        
        # Draw edges
        for u, v, data in self.graph.edges(data=True):
            weight = data.get('weight', 0.5)
            color = QColor(
                int(255 * (1 - weight)),
                int(255 * weight),
                0,
                int(255 * weight)
            )
            pen = QPen(color)
            pen.setWidthF(max(1, 3 * weight))
            self.scene.addLine(
                pos[u][0], pos[u][1],
                pos[v][0], pos[v][1],
                pen
            )
        
        # Draw nodes
        for node, (x, y) in pos.items():
            node_data = self.graph.nodes[node]
            color = {
                'arxiv': QColor(255, 100, 100),
                'github': QColor(100, 255, 100),
                'youtube': QColor(255, 100, 255),
                'web': QColor(100, 100, 255)
            }.get(node_data.get('type', ''), QColor(200, 200, 200))
            
            self.scene.addEllipse(
                x - 5, y - 5, 10, 10,
                QPen(Qt.PenStyle.NoPen),
                color
            )
            
            self.scene.addText(
                node_data.get('title', '')
            ).setPos(x + 10, y - 10)
        
        self.view.setScene(self.scene)
        self.view.fitInView(
            self.scene.sceneRect(),
            Qt.AspectRatioMode.KeepAspectRatio
        )

class TimelineWidget(QWidget):
    """Content timeline visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Controls
        controls = QHBoxLayout()
        
        self.interval_combo = QComboBox()
        self.interval_combo.addItems([
            "Day",
            "Week",
            "Month",
            "Year"
        ])
        self.interval_combo.currentTextChanged.connect(self._update_timeline)
        controls.addWidget(QLabel("Interval:"))
        controls.addWidget(self.interval_combo)
        
        self.stack_check = QComboBox()
        self.stack_check.addItems([
            "No Stacking",
            "Stack by Type"
        ])
        self.stack_check.currentTextChanged.connect(self._update_timeline)
        controls.addWidget(QLabel("Stacking:"))
        controls.addWidget(self.stack_check)
        
        layout.addLayout(controls)
        
        # Timeline view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)
        
        self.setLayout(layout)

class TopicClusterWidget(QWidget):
    """Topic cluster visualization."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Controls
        controls = QHBoxLayout()
        
        self.min_cluster = QSpinBox()
        self.min_cluster.setRange(2, 20)
        self.min_cluster.setValue(5)
        self.min_cluster.valueChanged.connect(self._update_clusters)
        controls.addWidget(QLabel("Min Cluster Size:"))
        controls.addWidget(self.min_cluster)
        
        self.max_clusters = QSpinBox()
        self.max_clusters.setRange(2, 50)
        self.max_clusters.setValue(10)
        self.max_clusters.valueChanged.connect(self._update_clusters)
        controls.addWidget(QLabel("Max Clusters:"))
        controls.addWidget(self.max_clusters)
        
        layout.addLayout(controls)
        
        # Cluster view
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        layout.addWidget(self.view)
        
        self.setLayout(layout)

class VisualizationWidget(QWidget):
    """Main visualization widget."""
    
    def __init__(
        self,
        content_manager: ContentManager,
        parent: Optional[QWidget] = None
    ):
        """Initialize visualization widget.
        
        Args:
            content_manager: Content manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.content_manager = content_manager
        self.analytics_service = AnalyticsService(content_manager)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout()
        
        # Controls
        controls = QHBoxLayout()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_visualizations)
        controls.addWidget(refresh_btn)
        
        layout.addLayout(controls)
        
        # Tabs
        tabs = QTabWidget()
        
        # Knowledge graph
        self.graph_widget = KnowledgeGraphWidget()
        tabs.addTab(self.graph_widget, "Knowledge Graph")
        
        # Timeline
        self.timeline_widget = TimelineWidget()
        tabs.addTab(self.timeline_widget, "Timeline")
        
        # Topic clusters
        self.cluster_widget = TopicClusterWidget()
        tabs.addTab(self.cluster_widget, "Topic Clusters")
        
        layout.addWidget(tabs)
        self.setLayout(layout)
    
    async def _refresh_visualizations(self) -> None:
        """Refresh all visualizations."""
        try:
            content = await self.content_manager.get_all_content()
            self.graph_widget.update_graph(content)
            # Update other visualizations...
        except Exception as e:
            logger.error(f"Error refreshing visualizations: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to refresh visualizations: {str(e)}"
            )