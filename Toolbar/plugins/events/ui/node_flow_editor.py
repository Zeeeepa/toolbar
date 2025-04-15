#!/usr/bin/env python3
import os
import sys
import json
import logging
import uuid
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QTabWidget, QFormLayout, QLineEdit, QTextEdit, QCheckBox, QGroupBox,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QMessageBox, QMenu, QAction, QGraphicsView, QGraphicsScene,
    QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsLineItem,
    QGraphicsTextItem, QGraphicsPathItem, QGraphicsProxyWidget, QGraphicsSceneMouseEvent,
    QGraphicsSceneContextMenuEvent, QGraphicsSceneWheelEvent, QGraphicsSceneDragDropEvent,
    QGraphicsObject, QFrame, QSplitter, QToolBar, QToolButton, QScrollArea
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF, QLineF, QEvent, pyqtSignal, QObject
from PyQt5.QtGui import (
    QPen, QBrush, QColor, QPainterPath, QFont, QDrag, QPixmap, QPainter,
    QCursor, QTransform, QMouseEvent, QWheelEvent, QDragEnterEvent, QDropEvent
)

# Import event system
from Toolbar.plugins.events.core.event_system import (
    EventManager, Event, EventTrigger, Action, Condition, ActionParameter,
    EventType, ActionType
)

# Import node editor
from Toolbar.plugins.events.ui.node_editor import (
    NodeSocket, NodeConnection, Node, EventNode, ConditionNode, ActionNode,
    ProjectNode, PromptNode, NodeEditorScene, NodeEditorView, NodeEditorDialog
)

logger = logging.getLogger(__name__)

class EnhancedNodeSocket(NodeSocket):
    """Enhanced socket for connecting nodes with improved visual feedback."""
    
    def __init__(self, node, socket_type, name, index=0, parent=None):
        """Initialize the socket."""
        super().__init__(node, socket_type, name, index, parent)
        
        # Enhanced appearance
        self.hover_brush = QBrush(QColor(255, 255, 100))
        self.connected_brush = QBrush(QColor(100, 255, 100))
        self.setAcceptHoverEvents(True)
        
        # Add tooltip
        self.setToolTip(f"{name} ({'Input' if socket_type == NodeSocket.INPUT else 'Output'})")
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        self.setBrush(self.hover_brush)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        if self.connections:
            self.setBrush(self.connected_brush)
        else:
            if self.socket_type == NodeSocket.INPUT:
                self.setBrush(QBrush(QColor(50, 150, 250)))
            else:
                self.setBrush(QBrush(QColor(250, 150, 50)))
        super().hoverLeaveEvent(event)
    
    def add_connection(self, connection):
        """Add a connection to the socket."""
        super().add_connection(connection)
        self.setBrush(self.connected_brush)
    
    def remove_connection(self, connection):
        """Remove a connection from the socket."""
        super().remove_connection(connection)
        if not self.connections:
            if self.socket_type == NodeSocket.INPUT:
                self.setBrush(QBrush(QColor(50, 150, 250)))
            else:
                self.setBrush(QBrush(QColor(250, 150, 50)))

class EnhancedNodeConnection(NodeConnection):
    """Enhanced connection between nodes with improved visual feedback."""
    
    def __init__(self, start_socket, end_socket, scene):
        """Initialize the connection."""
        super().__init__(start_socket, end_socket, scene)
        
        # Enhanced appearance
        self.default_pen = QPen(QColor(200, 200, 200), 2)
        self.success_pen = QPen(QColor(100, 255, 100), 2)
        self.failure_pen = QPen(QColor(255, 100, 100), 2)
        self.hover_pen = QPen(QColor(255, 255, 100), 3)
        
        # Set default pen
        self.setPen(self.default_pen)
        
        # Add interactivity
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        self.setPen(self.hover_pen)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        # Determine connection type
        if hasattr(self.start_socket, 'connection_type') and self.start_socket.connection_type == 'success':
            self.setPen(self.success_pen)
        elif hasattr(self.start_socket, 'connection_type') and self.start_socket.connection_type == 'failure':
            self.setPen(self.failure_pen)
        else:
            self.setPen(self.default_pen)
        super().hoverLeaveEvent(event)

class EnhancedNode(Node):
    """Enhanced node with improved visual feedback and functionality."""
    
    def __init__(self, scene, title="Node", inputs=None, outputs=None):
        """Initialize the node."""
        super().__init__(scene, title, inputs, outputs)
        
        # Enhanced appearance
        self.default_brush = QBrush(QColor(80, 80, 80))
        self.hover_brush = QBrush(QColor(100, 100, 100))
        self.selected_brush = QBrush(QColor(120, 120, 120))
        
        # Set default brush
        self.background.setBrush(self.default_brush)
        
        # Add interactivity
        self.setAcceptHoverEvents(True)
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        if not self.isSelected():
            self.background.setBrush(self.hover_brush)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        if not self.isSelected():
            self.background.setBrush(self.default_brush)
        super().hoverLeaveEvent(event)
    
    def itemChange(self, change, value):
        """Handle item change event."""
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.background.setBrush(self.selected_brush)
            else:
                self.background.setBrush(self.default_brush)
        return super().itemChange(change, value)

class EnhancedEventNode(EventNode, EnhancedNode):
    """Enhanced event node with improved visual feedback."""
    
    def __init__(self, scene, event_type=EventType.GITHUB_PR_CREATED):
        """Initialize the event node."""
        EnhancedNode.__init__(self, scene, f"Event: {event_type.value}", [], ["output"])
        
        # Set event type
        self.event_type = event_type
        
        # Enhanced appearance
        self.default_brush = QBrush(QColor(50, 100, 150))
        self.hover_brush = QBrush(QColor(70, 120, 170))
        self.selected_brush = QBrush(QColor(90, 140, 190))
        
        # Set default brush
        self.background.setBrush(self.default_brush)
        
        # Add event type label
        self.event_type_label = QGraphicsTextItem(self)
        self.event_type_label.setPlainText(f"Type: {event_type.value}")
        self.event_type_label.setPos(10, self.title_height + 10)
        self.event_type_label.setDefaultTextColor(Qt.white)
        
        # Update height
        self.height = self.title_height + 60

class EnhancedConditionNode(ConditionNode, EnhancedNode):
    """Enhanced condition node with improved visual feedback."""
    
    def __init__(self, scene, field="", operator="equals", value=""):
        """Initialize the condition node."""
        EnhancedNode.__init__(self, scene, "Condition", ["input"], ["success", "failure"])
        
        # Set condition properties
        self.field = field
        self.operator = operator
        self.value = value
        
        # Enhanced appearance
        self.default_brush = QBrush(QColor(150, 100, 50))
        self.hover_brush = QBrush(QColor(170, 120, 70))
        self.selected_brush = QBrush(QColor(190, 140, 90))
        
        # Set default brush
        self.background.setBrush(self.default_brush)
        
        # Add condition label
        self.condition_label = QGraphicsTextItem(self)
        self.condition_label.setPlainText(f"{field} {operator} {value}")
        self.condition_label.setPos(10, self.title_height + 10)
        self.condition_label.setDefaultTextColor(Qt.white)
        
        # Update height
        self.height = self.title_height + 60
        
        # Set connection types
        self.output_sockets[0].connection_type = "success"
        self.output_sockets[1].connection_type = "failure"

class EnhancedActionNode(ActionNode, EnhancedNode):
    """Enhanced action node with improved visual feedback."""
    
    def __init__(self, scene, action_type=ActionType.SEND_PROMPT):
        """Initialize the action node."""
        EnhancedNode.__init__(self, scene, f"Action: {action_type.value}", ["input"], ["output"])
        
        # Set action type
        self.action_type = action_type
        
        # Enhanced appearance
        self.default_brush = QBrush(QColor(150, 50, 100))
        self.hover_brush = QBrush(QColor(170, 70, 120))
        self.selected_brush = QBrush(QColor(190, 90, 140))
        
        # Set default brush
        self.background.setBrush(self.default_brush)
        
        # Add action type label
        self.action_type_label = QGraphicsTextItem(self)
        self.action_type_label.setPlainText(f"Type: {action_type.value}")
        self.action_type_label.setPos(10, self.title_height + 10)
        self.action_type_label.setDefaultTextColor(Qt.white)
        
        # Update height
        self.height = self.title_height + 60

class EnhancedNodeEditorScene(NodeEditorScene):
    """Enhanced node editor scene with improved functionality."""
    
    def __init__(self, parent=None):
        """Initialize the scene."""
        super().__init__(parent)
        
        # Add grid
        self.grid_size = 20
        self.grid_color = QColor(50, 50, 50)
        self.setBackgroundBrush(QBrush(QColor(30, 30, 30)))
    
    def drawBackground(self, painter, rect):
        """Draw the background grid."""
        super().drawBackground(painter, rect)
        
        # Draw grid
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        
        # Draw grid lines
        painter.setPen(QPen(self.grid_color, 1))
        
        # Draw vertical lines
        for x in range(left, int(rect.right()), self.grid_size):
            painter.drawLine(x, rect.top(), x, rect.bottom())
        
        # Draw horizontal lines
        for y in range(top, int(rect.bottom()), self.grid_size):
            painter.drawLine(rect.left(), y, rect.right(), y)

class EnhancedNodeEditorView(NodeEditorView):
    """Enhanced node editor view with improved functionality."""
    
    def __init__(self, scene, parent=None):
        """Initialize the view."""
        super().__init__(scene, parent)
        
        # Enhanced appearance
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.TextAntialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        
        # Add zoom controls
        self.zoom_level = 1.0
        self.zoom_step = 0.1
        self.zoom_min = 0.1
        self.zoom_max = 2.0
    
    def wheelEvent(self, event):
        """Handle wheel event for zooming."""
        # Get zoom direction
        zoom_in = event.angleDelta().y() > 0
        
        # Calculate new zoom level
        if zoom_in:
            self.zoom_level = min(self.zoom_level + self.zoom_step, self.zoom_max)
        else:
            self.zoom_level = max(self.zoom_level - self.zoom_step, self.zoom_min)
        
        # Apply zoom
        self.setTransform(QTransform().scale(self.zoom_level, self.zoom_level))

class EnhancedNodeEditorDialog(NodeEditorDialog):
    """Enhanced node editor dialog with improved functionality."""
    
    def __init__(self, event_manager, parent=None):
        """Initialize the dialog."""
        super().__init__(event_manager, parent)
        
        # Replace scene and view with enhanced versions
        self.scene = EnhancedNodeEditorScene()
        self.view = EnhancedNodeEditorView(self.scene)
        
        # Replace layout
        self.layout().removeWidget(self.view)
        self.layout().addWidget(self.view)
        
        # Add node palette
        self.add_node_palette()
    
    def add_node_palette(self):
        """Add a node palette for easy node creation."""
        # Create palette widget
        palette = QWidget()
        palette_layout = QVBoxLayout()
        palette.setLayout(palette_layout)
        
        # Add title
        title = QLabel("Node Palette")
        title.setAlignment(Qt.AlignCenter)
        palette_layout.addWidget(title)
        
        # Add node buttons
        # Event nodes
        event_group = QGroupBox("Event Nodes")
        event_layout = QVBoxLayout()
        event_group.setLayout(event_layout)
        
        for event_type in EventType:
            button = QPushButton(event_type.value)
            button.clicked.connect(lambda checked, et=event_type: self.add_event_node(et))
            event_layout.addWidget(button)
        
        palette_layout.addWidget(event_group)
        
        # Condition nodes
        condition_group = QGroupBox("Condition Nodes")
        condition_layout = QVBoxLayout()
        condition_group.setLayout(condition_layout)
        
        condition_button = QPushButton("Add Condition")
        condition_button.clicked.connect(self.add_condition_node)
        condition_layout.addWidget(condition_button)
        
        palette_layout.addWidget(condition_group)
        
        # Action nodes
        action_group = QGroupBox("Action Nodes")
        action_layout = QVBoxLayout()
        action_group.setLayout(action_layout)
        
        for action_type in ActionType:
            button = QPushButton(action_type.value)
            button.clicked.connect(lambda checked, at=action_type: self.add_action_node(at))
            action_layout.addWidget(button)
        
        palette_layout.addWidget(action_group)
        
        # Add palette to layout
        self.layout().addWidget(palette)
    
    def add_event_node(self, event_type):
        """Add an event node to the scene."""
        node = EnhancedEventNode(self.scene, event_type)
        node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
        self.scene.addItem(node)
    
    def add_condition_node(self):
        """Add a condition node to the scene."""
        node = EnhancedConditionNode(self.scene)
        node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
        self.scene.addItem(node)
    
    def add_action_node(self, action_type):
        """Add an action node to the scene."""
        node = EnhancedActionNode(self.scene, action_type)
        node.setPos(self.view.mapToScene(self.view.viewport().rect().center()))
        self.scene.addItem(node)
