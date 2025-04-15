#!/usr/bin/env python3
import os
import sys
import json
import uuid
import logging
from typing import Dict, List, Any, Optional, Type, Callable, Set, Union, Tuple

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox,
    QDialog, QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem,
    QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsTextItem, QGraphicsPathItem,
    QGraphicsProxyWidget, QMenu, QAction, QInputDialog, QMessageBox,
    QFormLayout, QLineEdit, QTextEdit, QScrollArea, QFrame, QSplitter,
    QToolBar, QToolButton, QSizePolicy, QSpacerItem, QTabWidget
)
from PyQt5.QtCore import Qt, QRectF, QPointF, QSizeF, QLineF, pyqtSignal, QObject, QEvent
from PyQt5.QtGui import QPen, QBrush, QColor, QPainterPath, QFont, QCursor, QPainter

from Toolbar.core.events.event_system import (
    EventManager, Event, EventTrigger, Action, Condition, ActionParameter,
    EventType, ActionType
)

logger = logging.getLogger(__name__)

# Node types
class NodeType:
    EVENT = "event"
    CONDITION = "condition"
    ACTION = "action"
    PROJECT = "project"
    PROMPT = "prompt"

# Connection types
class ConnectionType:
    SUCCESS = "success"
    FAILURE = "failure"
    DEFAULT = "default"

class NodeGraphicsItem(QGraphicsRectItem):
    """Graphics item representing a node in the flow."""
    
    def __init__(self, node_id, node_type, title, parent=None):
        """Initialize the node graphics item."""
        super().__init__(parent)
        self.node_id = node_id
        self.node_type = node_type
        self.title = title
        self.data = {}
        self.input_ports = []
        self.output_ports = []
        
        # Set up appearance
        self.setRect(0, 0, 200, 100)
        self.setBrush(QBrush(self._get_color_for_type(node_type)))
        self.setPen(QPen(Qt.black, 2))
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemIsSelectable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        
        # Add title text
        self.title_item = QGraphicsTextItem(self)
        self.title_item.setPlainText(title)
        self.title_item.setPos(10, 5)
        self.title_item.setDefaultTextColor(Qt.black)
        
        # Create ports
        self._create_ports()
    
    def _get_color_for_type(self, node_type):
        """Get the color for a node type."""
        colors = {
            NodeType.EVENT: QColor(255, 200, 200),  # Light red
            NodeType.CONDITION: QColor(200, 255, 200),  # Light green
            NodeType.ACTION: QColor(200, 200, 255),  # Light blue
            NodeType.PROJECT: QColor(255, 255, 200),  # Light yellow
            NodeType.PROMPT: QColor(255, 200, 255),  # Light purple
        }
        return colors.get(node_type, QColor(240, 240, 240))
    
    def _create_ports(self):
        """Create input and output ports based on node type."""
        # Clear existing ports
        for port in self.input_ports + self.output_ports:
            if port.scene():
                port.scene().removeItem(port)
        self.input_ports = []
        self.output_ports = []
        
        # Create ports based on node type
        if self.node_type == NodeType.EVENT:
            # Events have only output ports
            self._add_output_port("default", 0)
        elif self.node_type == NodeType.CONDITION:
            # Conditions have one input and two outputs (success/failure)
            self._add_input_port("input", 0)
            self._add_output_port("success", 0)
            self._add_output_port("failure", 1)
        elif self.node_type == NodeType.ACTION:
            # Actions have one input and one output
            self._add_input_port("input", 0)
            self._add_output_port("next", 0)
        elif self.node_type in [NodeType.PROJECT, NodeType.PROMPT]:
            # Projects and prompts have one input
            self._add_input_port("input", 0)
    
    def _add_input_port(self, name, index):
        """Add an input port to the node."""
        port = PortGraphicsItem(self, name, is_input=True, index=index)
        port_y = 40 + (index * 20)
        port.setPos(0, port_y)
        self.input_ports.append(port)
        return port
    
    def _add_output_port(self, name, index):
        """Add an output port to the node."""
        port = PortGraphicsItem(self, name, is_input=False, index=index)
        port_y = 40 + (index * 20)
        port.setPos(self.rect().width(), port_y)
        self.output_ports.append(port)
        return port
    
    def itemChange(self, change, value):
        """Handle item changes."""
        if change == QGraphicsItem.ItemPositionHasChanged:
            # Update connections when node is moved
            for port in self.input_ports + self.output_ports:
                for connection in port.connections:
                    connection.update_path()
        
        return super().itemChange(change, value)
    
    def contextMenuEvent(self, event):
        """Show context menu on right-click."""
        menu = QMenu()
        
        # Add edit action
        edit_action = QAction("Edit", menu)
        edit_action.triggered.connect(self.edit_node)
        menu.addAction(edit_action)
        
        # Add delete action
        delete_action = QAction("Delete", menu)
        delete_action.triggered.connect(self.delete_node)
        menu.addAction(delete_action)
        
        menu.exec_(event.screenPos())
    
    def edit_node(self):
        """Edit the node properties."""
        # This will be implemented by the specific node types
        pass
    
    def delete_node(self):
        """Delete the node and its connections."""
        # Remove all connections
        for port in self.input_ports + self.output_ports:
            for connection in list(port.connections):  # Use a copy of the list
                connection.delete()
        
        # Remove the node from the scene
        if self.scene():
            self.scene().removeItem(self)

class PortGraphicsItem(QGraphicsEllipseItem):
    """Graphics item representing a connection port on a node."""
    
    def __init__(self, parent_node, name, is_input=True, index=0):
        """Initialize the port graphics item."""
        super().__init__(parent_node)
        self.parent_node = parent_node
        self.name = name
        self.is_input = is_input
        self.index = index
        self.connections = set()
        
        # Set up appearance
        self.setRect(-6, -6, 12, 12)
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black, 1))
        
        # Add label
        self.label = QGraphicsTextItem(self)
        self.label.setPlainText(name)
        self.label.setFont(QFont("Arial", 8))
        
        # Position label based on port type
        if is_input:
            self.label.setPos(10, -10)
        else:
            # Right-align the text for output ports
            self.label.setPos(-self.label.boundingRect().width() - 10, -10)
        
        # Make port interactive
        self.setAcceptHoverEvents(True)
    
    def center(self):
        """Get the center point of the port in scene coordinates."""
        return self.mapToScene(self.rect().center())
    
    def hoverEnterEvent(self, event):
        """Handle hover enter event."""
        self.setBrush(QBrush(Qt.yellow))
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave event."""
        self.setBrush(QBrush(Qt.white))
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.LeftButton:
            # Start creating a connection
            scene = self.scene()
            if isinstance(scene, NodeGraphicsScene):
                if self.is_input and not self.connections:
                    # Can only have one connection to an input port
                    scene.start_connection(self)
                elif not self.is_input:
                    # Can have multiple connections from an output port
                    scene.start_connection(self)
        
        super().mousePressEvent(event)

class ConnectionGraphicsItem(QGraphicsPathItem):
    """Graphics item representing a connection between nodes."""
    
    def __init__(self, source_port, dest_port=None, connection_type=ConnectionType.DEFAULT):
        """Initialize the connection graphics item."""
        super().__init__()
        self.source_port = source_port
        self.dest_port = dest_port
        self.connection_type = connection_type
        self.temp_end_point = None
        
        # Set up appearance
        self.setPen(self._get_pen_for_type(connection_type))
        self.setZValue(-1)  # Draw connections behind nodes
        
        # Add to ports
        if source_port:
            source_port.connections.add(self)
        if dest_port:
            dest_port.connections.add(self)
        
        # Update the path
        self.update_path()
    
    def _get_pen_for_type(self, connection_type):
        """Get the pen for a connection type."""
        if connection_type == ConnectionType.SUCCESS:
            return QPen(QColor(0, 200, 0), 2)  # Green for success
        elif connection_type == ConnectionType.FAILURE:
            return QPen(QColor(200, 0, 0), 2)  # Red for failure
        else:
            return QPen(QColor(0, 0, 0), 2)  # Black for default
    
    def update_path(self):
        """Update the connection path."""
        path = QPainterPath()
        
        if self.source_port:
            start_point = self.source_port.center()
            
            if self.dest_port:
                # Connected to a destination port
                end_point = self.dest_port.center()
            elif self.temp_end_point:
                # Temporary end point while dragging
                end_point = self.temp_end_point
            else:
                # No destination yet
                return
            
            # Create a bezier curve path
            dx = end_point.x() - start_point.x()
            control_offset = min(abs(dx) * 0.5, 100)
            
            path.moveTo(start_point)
            path.cubicTo(
                start_point.x() + control_offset, start_point.y(),
                end_point.x() - control_offset, end_point.y(),
                end_point.x(), end_point.y()
            )
            
            self.setPath(path)
    
    def set_temp_end_point(self, point):
        """Set a temporary end point for the connection while dragging."""
        self.temp_end_point = point
        self.update_path()
    
    def set_dest_port(self, dest_port):
        """Set the destination port for the connection."""
        # Remove from old destination port if it exists
        if self.dest_port:
            self.dest_port.connections.remove(self)
        
        # Set new destination port
        self.dest_port = dest_port
        
        # Add to new destination port
        if dest_port:
            dest_port.connections.add(self)
        
        # Update the path
        self.update_path()
    
    def delete(self):
        """Delete the connection."""
        # Remove from ports
        if self.source_port:
            self.source_port.connections.remove(self)
        if self.dest_port:
            self.dest_port.connections.remove(self)
        
        # Remove from scene
        if self.scene():
            self.scene().removeItem(self)

class NodeGraphicsScene(QGraphicsScene):
    """Graphics scene for the node flow editor."""
    
    def __init__(self, parent=None):
        """Initialize the node graphics scene."""
        super().__init__(parent)
        self.active_connection = None
        self.grid_size = 20
        
        # Set scene properties
        self.setBackgroundBrush(QBrush(QColor(240, 240, 240)))
    
    def drawBackground(self, painter, rect):
        """Draw the scene background with a grid."""
        super().drawBackground(painter, rect)
        
        # Draw grid
        left = int(rect.left()) - (int(rect.left()) % self.grid_size)
        top = int(rect.top()) - (int(rect.top()) % self.grid_size)
        
        # Create grid lines
        lines = []
        
        # Vertical lines
        for x in range(left, int(rect.right()), self.grid_size):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        
        # Horizontal lines
        for y in range(top, int(rect.bottom()), self.grid_size):
            lines.append(QLineF(rect.left(), y, rect.right(), y))
        
        # Draw the lines
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawLines(lines)
    
    def start_connection(self, port):
        """Start creating a connection from a port."""
        # Determine connection type based on port name
        connection_type = ConnectionType.DEFAULT
        if port.name == "success":
            connection_type = ConnectionType.SUCCESS
        elif port.name == "failure":
            connection_type = ConnectionType.FAILURE
        
        # Create a new connection
        self.active_connection = ConnectionGraphicsItem(port, connection_type=connection_type)
        self.addItem(self.active_connection)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move event."""
        if self.active_connection:
            # Update the temporary end point of the active connection
            self.active_connection.set_temp_end_point(event.scenePos())
        
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if self.active_connection:
            # Check if we're over a port
            items = self.items(event.scenePos())
            valid_port = None
            
            for item in items:
                if isinstance(item, PortGraphicsItem):
                    # Check if this is a valid connection
                    if self._can_connect(self.active_connection.source_port, item):
                        valid_port = item
                        break
            
            if valid_port:
                # Complete the connection
                self.active_connection.set_dest_port(valid_port)
            else:
                # Remove the invalid connection
                self.removeItem(self.active_connection)
                self.active_connection.source_port.connections.remove(self.active_connection)
            
            self.active_connection = None
        
        super().mouseReleaseEvent(event)
    
    def _can_connect(self, source_port, dest_port):
        """Check if two ports can be connected."""
        # Can't connect to self
        if source_port.parent_node == dest_port.parent_node:
            return False
        
        # Can only connect output to input
        if source_port.is_input or not dest_port.is_input:
            return False
        
        # Input ports can only have one connection
        if dest_port.connections:
            return False
        
        return True
    
    def add_node(self, node_type, title, pos=None):
        """Add a new node to the scene."""
        node_id = str(uuid.uuid4())
        node = NodeGraphicsItem(node_id, node_type, title)
        
        if pos:
            node.setPos(pos)
        else:
            # Center in view if no position specified
            view = self.views()[0] if self.views() else None
            if view:
                view_center = view.mapToScene(view.viewport().rect().center())
                node.setPos(view_center - QPointF(node.rect().width() / 2, node.rect().height() / 2))
        
        self.addItem(node)
        return node
    
    def clear_all(self):
        """Clear all items from the scene."""
        self.clear()
        self.active_connection = None

class NodeFlowView(QGraphicsView):
    """Graphics view for the node flow editor."""
    
    def __init__(self, parent=None):
        """Initialize the node flow view."""
        super().__init__(parent)
        
        # Set up the view
        self.setRenderHint(QPainter.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Set up zooming and panning
        self.setDragMode(QGraphicsView.RubberBandDrag)
        self.zoom_factor = 1.15
        self.current_zoom = 1.0
        
        # Create the scene
        self.node_scene = NodeGraphicsScene(self)
        self.setScene(self.node_scene)
    
    def wheelEvent(self, event):
        """Handle wheel event for zooming."""
        if event.modifiers() & Qt.ControlModifier:
            # Zoom in/out with Ctrl+Wheel
            zoom_in = event.angleDelta().y() > 0
            
            if zoom_in:
                self.scale(self.zoom_factor, self.zoom_factor)
                self.current_zoom *= self.zoom_factor
            else:
                self.scale(1 / self.zoom_factor, 1 / self.zoom_factor)
                self.current_zoom /= self.zoom_factor
            
            event.accept()
        else:
            super().wheelEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press event."""
        if event.button() == Qt.MiddleButton:
            # Enable panning with middle mouse button
            self.setDragMode(QGraphicsView.ScrollHandDrag)
            # Create a fake mouse press event with left button
            fake_event = event
            super().mousePressEvent(fake_event)
        elif event.button() == Qt.RightButton:
            # Show context menu for adding nodes
            if not self.itemAt(event.pos()):
                self.show_context_menu(event)
        else:
            super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release event."""
        if event.button() == Qt.MiddleButton:
            # Restore drag mode after panning
            self.setDragMode(QGraphicsView.RubberBandDrag)
        
        super().mouseReleaseEvent(event)
    
    def show_context_menu(self, event):
        """Show context menu for adding nodes."""
        menu = QMenu(self)
        
        # Add node type submenus
        event_menu = menu.addMenu("Add Event")
        condition_menu = menu.addMenu("Add Condition")
        action_menu = menu.addMenu("Add Action")
        project_menu = menu.addMenu("Add Project")
        prompt_menu = menu.addMenu("Add Prompt")
        
        # Add event node types
        for event_type in EventType:
            action = event_menu.addAction(event_type.value)
            action.triggered.connect(lambda checked, et=event_type: 
                self.add_node(NodeType.EVENT, et.value, self.mapToScene(event.pos())))
        
        # Add condition node types
        condition_types = ["Field Equals", "Field Contains", "Field Starts With", "Field Ends With", "Regex Match"]
        for condition_type in condition_types:
            action = condition_menu.addAction(condition_type)
            action.triggered.connect(lambda checked, ct=condition_type: 
                self.add_node(NodeType.CONDITION, ct, self.mapToScene(event.pos())))
        
        # Add action node types
        for action_type in ActionType:
            action = action_menu.addAction(action_type.value)
            action.triggered.connect(lambda checked, at=action_type: 
                self.add_node(NodeType.ACTION, at.value, self.mapToScene(event.pos())))
        
        # Add project node types (placeholder)
        action = project_menu.addAction("GitHub Project")
        action.triggered.connect(lambda: 
            self.add_node(NodeType.PROJECT, "GitHub Project", self.mapToScene(event.pos())))
        
        # Add prompt node types (placeholder)
        action = prompt_menu.addAction("Template Prompt")
        action.triggered.connect(lambda: 
            self.add_node(NodeType.PROMPT, "Template Prompt", self.mapToScene(event.pos())))
        
        # Show the menu
        menu.exec_(event.globalPos())
    
    def add_node(self, node_type, title, pos=None):
        """Add a new node to the scene."""
        return self.node_scene.add_node(node_type, title, pos)
    
    def clear_all(self):
        """Clear all nodes and connections."""
        self.node_scene.clear_all()
    
    def reset_zoom(self):
        """Reset the zoom level to 100%."""
        self.resetTransform()
        self.current_zoom = 1.0

class NodeFlowEditor(QWidget):
    """Widget for editing node flows."""
    
    def __init__(self, event_manager, parent=None):
        """Initialize the node flow editor."""
        super().__init__(parent)
        self.event_manager = event_manager
        self.current_event = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create toolbar
        toolbar = QToolBar()
        main_layout.addWidget(toolbar)
        
        # Add toolbar actions
        new_action = toolbar.addAction("New")
        new_action.triggered.connect(self.new_flow)
        
        save_action = toolbar.addAction("Save")
        save_action.triggered.connect(self.save_flow)
        
        load_action = toolbar.addAction("Load")
        load_action.triggered.connect(self.load_flow)
        
        toolbar.addSeparator()
        
        reset_zoom_action = toolbar.addAction("Reset Zoom")
        reset_zoom_action.triggered.connect(self.reset_zoom)
        
        clear_action = toolbar.addAction("Clear All")
        clear_action.triggered.connect(self.clear_all)
        
        # Create splitter for node view and properties
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)
        
        # Create node flow view
        self.node_view = NodeFlowView()
        splitter.addWidget(self.node_view)
        
        # Create properties panel
        properties_widget = QWidget()
        properties_layout = QVBoxLayout(properties_widget)
        
        properties_label = QLabel("Properties")
        properties_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        properties_layout.addWidget(properties_label)
        
        # Event name and description
        form_layout = QFormLayout()
        properties_layout.addLayout(form_layout)
        
        self.event_name_edit = QLineEdit()
        form_layout.addRow("Event Name:", self.event_name_edit)
        
        self.event_description_edit = QTextEdit()
        self.event_description_edit.setMaximumHeight(100)
        form_layout.addRow("Description:", self.event_description_edit)
        
        self.event_enabled_checkbox = QCheckBox("Enabled")
        self.event_enabled_checkbox.setChecked(True)
        form_layout.addRow("", self.event_enabled_checkbox)
        
        # Add properties widget to splitter
        splitter.addWidget(properties_widget)
        
        # Set splitter sizes
        splitter.setSizes([700, 300])
    
    def new_flow(self):
        """Create a new flow."""
        # Clear the current flow
        self.clear_all()
        
        # Create a new event
        self.current_event = None
        self.event_name_edit.setText("New Event")
        self.event_description_edit.setText("")
        self.event_enabled_checkbox.setChecked(True)
    
    def save_flow(self):
        """Save the current flow as an event."""
        if not self.event_name_edit.text():
            QMessageBox.warning(self, "Save Error", "Event name cannot be empty.")
            return
        
        try:
            # Create or update event
            event_id = str(uuid.uuid4()) if not self.current_event else self.current_event.id
            trigger_id = str(uuid.uuid4())
            
            # Create trigger
            trigger = EventTrigger(
                id=trigger_id,
                name=f"Trigger for {self.event_name_edit.text()}",
                event_type=EventType.CUSTOM,
                conditions=[],
                enabled=self.event_enabled_checkbox.isChecked()
            )
            
            # Create event
            event = Event(
                id=event_id,
                name=self.event_name_edit.text(),
                description=self.event_description_edit.toPlainText(),
                trigger=trigger,
                actions=[],
                enabled=self.event_enabled_checkbox.isChecked()
            )
            
            # TODO: Convert node graph to conditions and actions
            
            # Save the event
            if self.current_event:
                self.event_manager.update_event(event_id, event)
            else:
                self.event_manager.add_event(event)
            
            self.current_event = event
            
            QMessageBox.information(self, "Save Successful", f"Event '{event.name}' saved successfully.")
        
        except Exception as e:
            logger.error(f"Error saving flow: {e}", exc_info=True)
            QMessageBox.critical(self, "Save Error", f"Error saving flow: {str(e)}")
    
    def load_flow(self):
        """Load an existing event as a flow."""
        # Get all events
        events = self.event_manager.get_all_events()
        
        if not events:
            QMessageBox.information(self, "No Events", "No events found to load.")
            return
        
        # Show event selection dialog
        event_names = [event.name for event in events]
        selected_name, ok = QInputDialog.getItem(
            self, "Load Event", "Select an event to load:", event_names, 0, False
        )
        
        if ok and selected_name:
            # Find the selected event
            selected_event = next((event for event in events if event.name == selected_name), None)
            
            if selected_event:
                # Load the event
                self.current_event = selected_event
                self.event_name_edit.setText(selected_event.name)
                self.event_description_edit.setText(selected_event.description)
                self.event_enabled_checkbox.setChecked(selected_event.enabled)
                
                # Clear the current flow
                self.clear_all()
                
                # TODO: Convert conditions and actions to node graph
                
                QMessageBox.information(self, "Load Successful", f"Event '{selected_event.name}' loaded successfully.")
    
    def reset_zoom(self):
        """Reset the zoom level of the node view."""
        self.node_view.reset_zoom()
    
    def clear_all(self):
        """Clear all nodes and connections."""
        # Confirm with user
        if self.node_view.node_scene.items():
            reply = QMessageBox.question(
                self, "Clear All", "Are you sure you want to clear all nodes and connections?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
        
        self.node_view.clear_all()

class NodeFlowEditorDialog(QDialog):
    """Dialog for the node flow editor."""
    
    def __init__(self, event_manager, parent=None):
        """Initialize the dialog."""
        super().__init__(parent)
        self.event_manager = event_manager
        
        self.setWindowTitle("Event Flow Editor")
        self.setMinimumSize(1000, 700)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Create node flow editor
        self.editor = NodeFlowEditor(event_manager)
        layout.addWidget(self.editor, 1)
        
        # Add close button
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
