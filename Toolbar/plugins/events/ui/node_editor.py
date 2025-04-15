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

logger = logging.getLogger(__name__)

class NodeSocket(QGraphicsEllipseItem):
    """Socket for connecting nodes."""
    
    INPUT = 0
    OUTPUT = 1
    
    def __init__(self, node, socket_type, name, index=0, parent=None):
        """Initialize the socket."""
        super().__init__(0, 0, 12, 12, parent)
        self.node = node
        self.socket_type = socket_type
        self.name = name
        self.index = index
        self.connections = []
        
        # Set appearance
        if socket_type == NodeSocket.INPUT:
            self.setBrush(QBrush(QColor(50, 150, 250)))
        else:
            self.setBrush(QBrush(QColor(250, 150, 50)))
        self.setPen(QPen(QColor(20, 20, 20), 1))
        self.setZValue(1)
        
        # Add label
        self.label = QGraphicsTextItem(name, self)
        if socket_type == NodeSocket.INPUT:
            self.label.setPos(15, -10)
        else:
            self.label.setPos(-15 - self.label.boundingRect().width(), -10)
        
        # Make socket selectable and movable with node
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        
    def get_position(self):
        """Get the center position of the socket."""
        return self.scenePos() + QPointF(6, 6)
    
    def add_connection(self, connection):
        """Add a connection to this socket."""
        self.connections.append(connection)
    
    def remove_connection(self, connection):
        """Remove a connection from this socket."""
        if connection in self.connections:
            self.connections.remove(connection)
    
    def update_connections(self):
        """Update all connections attached to this socket."""
        for connection in self.connections:
            connection.update_path()

class NodeConnection(QGraphicsPathItem):
    """Connection between node sockets."""
    
    def __init__(self, start_socket, end_socket=None, parent=None):
        """Initialize the connection."""
        super().__init__(parent)
        self.start_socket = start_socket
        self.end_socket = end_socket
        
        # Add to sockets
        if self.start_socket:
            self.start_socket.add_connection(self)
        if self.end_socket:
            self.end_socket.add_connection(self)
        
        # Set appearance
        self.setPen(QPen(QColor(200, 200, 200), 2))
        self.setZValue(0)
        
        # Update path
        self.update_path()
        
    def update_path(self):
        """Update the path between sockets."""
        if not self.start_socket:
            return
            
        path = QPainterPath()
        
        start_pos = self.start_socket.get_position()
        
        if self.end_socket:
            end_pos = self.end_socket.get_position()
        else:
            end_pos = self.mapFromScene(QCursor.pos())
        
        # Create a bezier curve
        ctrl1 = QPointF(start_pos.x() + 100, start_pos.y())
        ctrl2 = QPointF(end_pos.x() - 100, end_pos.y())
        
        path.moveTo(start_pos)
        path.cubicTo(ctrl1, ctrl2, end_pos)
        
        self.setPath(path)
    
    def remove_from_sockets(self):
        """Remove this connection from its sockets."""
        if self.start_socket:
            self.start_socket.remove_connection(self)
        if self.end_socket:
            self.end_socket.remove_connection(self)
    
    def disconnect(self):
        """Disconnect this connection and remove it from the scene."""
        self.remove_from_sockets()
        if self.scene():
            self.scene().removeItem(self)

class Node(QGraphicsObject):
    """Base class for nodes in the node editor."""
    
    def __init__(self, title="Node", parent=None):
        """Initialize the node."""
        super().__init__(parent)
        self.title = title
        self.width = 200
        self.height = 100
        self.title_height = 30
        self.input_sockets = []
        self.output_sockets = []
        
        # Set flags
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsScenePositionChanges, True)
        
        # Create node appearance
        self.init_ui()
        
    def init_ui(self):
        """Initialize the node UI."""
        # Create background rectangle
        self.background = QGraphicsRectItem(0, 0, self.width, self.height, self)
        self.background.setBrush(QBrush(QColor(60, 60, 60)))
        self.background.setPen(QPen(QColor(80, 80, 80), 1))
        
        # Create title bar
        self.title_bar = QGraphicsRectItem(0, 0, self.width, self.title_height, self)
        self.title_bar.setBrush(QBrush(QColor(80, 80, 80)))
        self.title_bar.setPen(QPen(QColor(100, 100, 100), 1))
        
        # Create title text
        self.title_text = QGraphicsTextItem(self.title, self)
        self.title_text.setDefaultTextColor(QColor(255, 255, 255))
        self.title_text.setPos(10, 5)
        
    def add_input_socket(self, name):
        """Add an input socket to the node."""
        socket = NodeSocket(self, NodeSocket.INPUT, name, len(self.input_sockets), self)
        socket.setPos(0, self.title_height + 30 + len(self.input_sockets) * 25)
        self.input_sockets.append(socket)
        self.update_size()
        return socket
    
    def add_output_socket(self, name):
        """Add an output socket to the node."""
        socket = NodeSocket(self, NodeSocket.OUTPUT, name, len(self.output_sockets), self)
        socket.setPos(self.width, self.title_height + 30 + len(self.output_sockets) * 25)
        self.output_sockets.append(socket)
        self.update_size()
        return socket
    
    def update_size(self):
        """Update the node size based on sockets."""
        num_sockets = max(len(self.input_sockets), len(self.output_sockets))
        self.height = self.title_height + 30 + num_sockets * 25 + 10
        self.background.setRect(0, 0, self.width, self.height)
    
    def boundingRect(self):
        """Return the bounding rectangle of the node."""
        return QRectF(0, 0, self.width, self.height)
    
    def paint(self, painter, option, widget):
        """Paint the node (empty implementation as we use child items)."""
        pass
    
    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Update connections when node moves
            for socket in self.input_sockets + self.output_sockets:
                socket.update_connections()
        
        return super().itemChange(change, value)

class EventNode(Node):
    """Node representing an event trigger."""
    
    def __init__(self, event_type=EventType.CUSTOM, title="Event", parent=None):
        """Initialize the event node."""
        super().__init__(title, parent)
        self.event_type = event_type
        self.conditions = []
        
        # Set node color
        self.title_bar.setBrush(QBrush(QColor(80, 150, 80)))
        
        # Add output socket
        self.add_output_socket("Event")
        
        # Add event type text
        self.event_type_text = QGraphicsTextItem(f"Type: {event_type.value}", self)
        self.event_type_text.setDefaultTextColor(QColor(200, 200, 200))
        self.event_type_text.setPos(10, self.title_height + 5)
    
    def set_event_type(self, event_type):
        """Set the event type."""
        self.event_type = event_type
        self.event_type_text.setPlainText(f"Type: {event_type.value}")
    
    def add_condition(self, condition):
        """Add a condition to the event node."""
        self.conditions.append(condition)
        
        # Update node height
        self.height += 20
        self.background.setRect(0, 0, self.width, self.height)
        
        # Add condition text
        condition_text = QGraphicsTextItem(
            f"{condition.field} {condition.operator} {condition.value}", 
            self
        )
        condition_text.setDefaultTextColor(QColor(200, 200, 200))
        condition_text.setPos(10, self.title_height + 30 + len(self.conditions) * 20)

class ActionNode(Node):
    """Node representing an action."""
    
    def __init__(self, action_type=ActionType.CUSTOM, title="Action", parent=None):
        """Initialize the action node."""
        super().__init__(title, parent)
        self.action_type = action_type
        self.parameters = []
        
        # Set node color
        self.title_bar.setBrush(QBrush(QColor(150, 80, 80)))
        
        # Add input socket
        self.add_input_socket("Trigger")
        
        # Add action type text
        self.action_type_text = QGraphicsTextItem(f"Type: {action_type.value}", self)
        self.action_type_text.setDefaultTextColor(QColor(200, 200, 200))
        self.action_type_text.setPos(10, self.title_height + 5)
    
    def set_action_type(self, action_type):
        """Set the action type."""
        self.action_type = action_type
        self.action_type_text.setPlainText(f"Type: {action_type.value}")
    
    def add_parameter(self, parameter):
        """Add a parameter to the action node."""
        self.parameters.append(parameter)
        
        # Update node height
        self.height += 20
        self.background.setRect(0, 0, self.width, self.height)
        
        # Add parameter text
        parameter_text = QGraphicsTextItem(
            f"{parameter.name}: {parameter.value}", 
            self
        )
        parameter_text.setDefaultTextColor(QColor(200, 200, 200))
        parameter_text.setPos(10, self.title_height + 30 + len(self.parameters) * 20)

class NodeScene(QGraphicsScene):
    """Scene for the node editor."""
    
    def __init__(self, parent=None):
        """Initialize the node scene."""
        super().__init__(parent)
        self.setSceneRect(-1000, -1000, 2000, 2000)
        
        # Set background
        self.setBackgroundBrush(QBrush(QColor(40, 40, 40)))
        
        # Track current connection being created
        self.current_connection = None
        self.start_socket = None
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton:
            # Check if we clicked on a socket
            item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item, NodeSocket):
                # Start creating a connection
                if item.socket_type == NodeSocket.OUTPUT:
                    self.start_socket = item
                    self.current_connection = NodeConnection(self.start_socket)
                    self.addItem(self.current_connection)
                    return
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.current_connection:
            # Update the current connection path
            self.current_connection.update_path()
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.LeftButton and self.current_connection:
            # Check if we released on a socket
            item = self.itemAt(event.scenePos(), QTransform())
            if isinstance(item, NodeSocket) and item.socket_type == NodeSocket.INPUT:
                # Connect to this socket
                self.current_connection.end_socket = item
                item.add_connection(self.current_connection)
                self.current_connection.update_path()
            else:
                # Remove the temporary connection
                self.removeItem(self.current_connection)
                self.start_socket.remove_connection(self.current_connection)
            
            self.current_connection = None
            self.start_socket = None
        
        super().mouseReleaseEvent(event)
    
    def contextMenuEvent(self, event):
        """Handle context menu events."""
        # Create context menu
        menu = QMenu()
        
        # Add actions
        add_event_action = menu.addAction("Add Event Node")
        add_action_action = menu.addAction("Add Action Node")
        menu.addSeparator()
        delete_action = menu.addAction("Delete Selected Items")
        
        # Show menu and get selected action
        action = menu.exec_(event.screenPos())
        
        # Handle action
        if action == add_event_action:
            node = EventNode()
            node.setPos(event.scenePos())
            self.addItem(node)
        elif action == add_action_action:
            node = ActionNode()
            node.setPos(event.scenePos())
            self.addItem(node)
        elif action == delete_action:
            self.delete_selected_items()
    
    def delete_selected_items(self):
        """Delete all selected items."""
        for item in self.selectedItems():
            if isinstance(item, Node):
                # Remove all connections
                for socket in item.input_sockets + item.output_sockets:
                    for connection in socket.connections[:]:  # Use a copy of the list
                        connection.disconnect()
                
                # Remove the node
                self.removeItem(item)
            elif isinstance(item, NodeConnection):
                # Disconnect and remove the connection
                item.disconnect()

class NodeView(QGraphicsView):
    """View for the node editor."""
    
    def __init__(self, parent=None):
        """Initialize the node view."""
        super().__init__(parent)
        
        # Set view properties
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Set scene
        self.setScene(NodeScene(self))
        
        # Track middle mouse button for panning
        self.middle_mouse_button_pressed = False
        self.last_mouse_pos = QPointF(0, 0)
        
        # Set initial scale
        self.scale(0.8, 0.8)
    
    def wheelEvent(self, event):
        """Handle wheel events for zooming."""
        zoom_factor = 1.1
        
        if event.angleDelta().y() > 0:
            # Zoom in
            self.scale(zoom_factor, zoom_factor)
        else:
            # Zoom out
            self.scale(1 / zoom_factor, 1 / zoom_factor)
    
    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.MiddleButton:
            # Start panning
            self.middle_mouse_button_pressed = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if self.middle_mouse_button_pressed:
            # Pan the view
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x()
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y()
            )
            
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        if event.button() == Qt.MiddleButton:
            # Stop panning
            self.middle_mouse_button_pressed = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == Qt.Key_Delete:
            # Delete selected items
            self.scene().delete_selected_items()
            event.accept()
        else:
            super().keyPressEvent(event)

class NodeEditorWidget(QWidget):
    """Widget for the node editor."""
    
    def __init__(self, parent=None):
        """Initialize the node editor widget."""
        super().__init__(parent)
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        toolbar = QToolBar()
        layout.addWidget(toolbar)
        
        # Add toolbar actions
        add_event_action = toolbar.addAction("Add Event")
        add_event_action.triggered.connect(self.add_event_node)
        
        add_action_action = toolbar.addAction("Add Action")
        add_action_action.triggered.connect(self.add_action_node)
        
        toolbar.addSeparator()
        
        clear_action = toolbar.addAction("Clear")
        clear_action.triggered.connect(self.clear_scene)
        
        save_action = toolbar.addAction("Save")
        save_action.triggered.connect(self.save_flow)
        
        # Create node view
        self.node_view = NodeView()
        layout.addWidget(self.node_view)
    
    def add_event_node(self):
        """Add an event node to the scene."""
        node = EventNode()
        node.setPos(0, 0)
        self.node_view.scene().addItem(node)
    
    def add_action_node(self):
        """Add an action node to the scene."""
        node = ActionNode()
        node.setPos(200, 0)
        self.node_view.scene().addItem(node)
    
    def clear_scene(self):
        """Clear the scene."""
        self.node_view.scene().clear()
    
    def save_flow(self):
        """Save the current flow."""
        # TODO: Implement saving the flow to an event configuration
        QMessageBox.information(self, "Save Flow", "Flow saving not implemented yet.")
    
    def load_flow(self, event):
        """Load a flow from an event configuration."""
        # TODO: Implement loading a flow from an event configuration
        pass

class NodeEditorDialog(QDialog):
    """Dialog for the node editor."""
    
    def __init__(self, event_manager, event=None, parent=None):
        """Initialize the node editor dialog."""
        super().__init__(parent)
        self.event_manager = event_manager
        self.event = event
        
        self.setWindowTitle("Node Flow Editor")
        self.setMinimumSize(800, 600)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create node editor
        self.node_editor = NodeEditorWidget()
        layout.addWidget(self.node_editor)
        
        # Add buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_event)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        # Load event if provided
        if self.event:
            self.load_event()
    
    def load_event(self):
        """Load the event into the node editor."""
        # TODO: Implement loading the event into the node editor
        pass
    
    def save_event(self):
        """Save the event from the node editor."""
        # TODO: Implement saving the event from the node editor
        QMessageBox.information(self, "Save Event", "Event saving not implemented yet.")
        self.accept()
