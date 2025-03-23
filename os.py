import sys
import math
import json
import copy
import networkx as nx
from PyQt5 import QtWidgets, QtGui, QtCore

# --- Custom Styled Dialogs ---
class CustomInputDialog(QtWidgets.QDialog):
    def __init__(self, title, prompt, parent=None, input_type="text", min_val=1, max_val=100):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Add key event handling
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        
        theme = parent.current_theme if parent else "Default"
        bg_color = "#2C3E50" if theme == "Default" else \
                  "#1E1E1E" if theme == "Dark" else "#FFFFFF"
        text_color = "white" if theme != "Light" else "black"
        input_text_color = "black" if theme == "Default" else text_color
        accent_color = "#189AB4" if theme == "Default" else \
                      "#4CAF50" if theme == "Dark" else "#2196F3"
        accent_light = "#D4F1F4" if theme == "Default" else \
                      "#81C784" if theme == "Dark" else "#BBDEFB"
        field_bg = "#75E6DA" if theme == "Default" else \
                  "#555555" if theme == "Dark" else "#F0F0F0"

        self.setStyleSheet(f"""
            QDialog {{
                background: {bg_color};
                color: {text_color};
            }}
            QLabel {{
                color: {text_color};
                font: 12pt "Segoe UI";
                padding: 10px;
            }}
            QLineEdit, QSpinBox {{
                background: {field_bg};
                color: {input_text_color};
                border: 2px solid {accent_color};
                border-radius: 5px;
                padding: 8px;
                font: 12pt "Segoe UI";
                min-width: 200px;
            }}
            QPushButton {{
                background: {accent_color};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font: bold 12pt "Segoe UI";
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: {accent_light};
            }}
        """)

        self.label = QtWidgets.QLabel(prompt)
        self.layout.addWidget(self.label)
        
        if input_type == "text":
            self.input = QtWidgets.QLineEdit()
            # Auto-focus the input field
            self.input.setFocus()
        elif input_type == "int":
            self.input = QtWidgets.QSpinBox()
            self.input.setMinimum(min_val)
            self.input.setMaximum(max_val)
            self.input.setValue(min_val)
        
        self.layout.addWidget(self.input)
        
        self.buttonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self
        )
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.layout.addWidget(self.buttonBox)
        
        # Add Enter key to accept dialog
        if isinstance(self.input, QtWidgets.QLineEdit):
            self.input.returnPressed.connect(self.accept)

    def getText(self):
        return self.input.text() if isinstance(self.input, QtWidgets.QLineEdit) else None
    
    def getInt(self):
        return self.input.value() if isinstance(self.input, QtWidgets.QSpinBox) else None
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)

# --- Custom Graphics View with Zooming and Panning ---
class ZoomPanGraphicsView(QtWidgets.QGraphicsView):
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self._isPanning = False
        self._panStartX = 0
        self._panStartY = 0
        self.zoom_in_factor = 1.15

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            zoom_factor = self.zoom_in_factor
        else:
            zoom_factor = 1 / self.zoom_in_factor
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self._isPanning = True
            self._panStartX = event.x()
            self._panStartY = event.y()
            self.setCursor(QtCore.Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._isPanning:
            dx = event.x() - self._panStartX
            dy = event.y() - self._panStartY
            self._panStartX = event.x()
            self._panStartY = event.y()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - dx)
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - dy)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self._isPanning = False
            self.setCursor(QtCore.Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

# --- Node Items ---
class ProcessItem(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, name, radius=30):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.name = name
        self.radius = radius
        self.setBrush(QtGui.QColor("#2E8BC0"))
        self.original_pen = QtGui.QPen(QtGui.QColor("#455A64"), 2)
        self.setPen(self.original_pen)
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable |
                      QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.text = QtWidgets.QGraphicsTextItem(name, self)
        self.text.setDefaultTextColor(QtGui.QColor("white"))
        font = QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold)
        self.text.setFont(font)
        self.updateTextPosition()

    def updateTextPosition(self):
        rect = self.boundingRect()
        tRect = self.text.boundingRect()
        self.text.setPos(rect.center().x() - tRect.width() / 2,
                         rect.center().y() - tRect.height() / 2)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            if self.scene():
                main_window = self.scene().views()[0].parent()
                main_window.handleNodeMoved(self, self.pos())
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.scene():
            main_window = self.scene().views()[0].parent()
            main_window.saveState(description=f"Moved node {self.name}")

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu()
        renameAction = menu.addAction("Rename")
        removeAction = menu.addAction("Remove")
        action = menu.exec_(event.screenPos())
        main_window = self.scene().views()[0].parent()
        if action == renameAction:
            main_window.renameNode(self)
        elif action == removeAction:
            main_window.removeNode(self)

class ResourceItem(QtWidgets.QGraphicsRectItem):
    def __init__(self, name, instances, radius=30):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.name = name
        self.instances = instances
        self.available = instances
        self.radius = radius
        self.setBrush(QtGui.QColor("#FFA500"))
        self.original_pen = QtGui.QPen(QtGui.QColor("#455A64"), 2)
        self.setPen(self.original_pen)
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable |
                      QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsGeometryChanges, True)
        self.text = QtWidgets.QGraphicsTextItem(name, self)
        self.text.setDefaultTextColor(QtGui.QColor("white"))
        font = QtGui.QFont("Segoe UI", 10, QtGui.QFont.Bold)
        self.text.setFont(font)
        self.updateTextPosition()
        self.countText = QtWidgets.QGraphicsTextItem(f"{self.available}/{self.instances}", self)
        self.countText.setDefaultTextColor(QtGui.QColor("white"))
        font2 = QtGui.QFont("Segoe UI", 9)
        self.countText.setFont(font2)
        self.updateCountPosition()

    def updateTextPosition(self):
        rect = self.boundingRect()
        tRect = self.text.boundingRect()
        self.text.setPos(rect.center().x() - tRect.width() / 2,
                         rect.center().y() - tRect.height() / 2)

    def updateCountPosition(self):
        rect = self.boundingRect()
        cRect = self.countText.boundingRect()
        self.countText.setPos(rect.center().x() - cRect.width() / 2, rect.bottom() - 20)

    def updateCount(self):
        self.countText.setPlainText(f"{self.available}/{self.instances}")
        self.updateCountPosition()

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            if self.scene():
                main_window = self.scene().views()[0].parent()
                main_window.handleNodeMoved(self, self.pos())
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self.scene():
            main_window = self.scene().views()[0].parent()
            main_window.saveState(description=f"Moved node {self.name}")

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu()
        renameAction = menu.addAction("Rename")
        removeAction = menu.addAction("Remove")
        action = menu.exec_(event.screenPos())
        main_window = self.scene().views()[0].parent()
        if action == renameAction:
            main_window.renameNode(self)
        elif action == removeAction:
            main_window.removeNode(self)

# --- Edge Item ---
class EdgeItem(QtWidgets.QGraphicsPathItem):
    def __init__(self, source, dest, instances, edge_type, color):
        super().__init__()
        self.source = source
        self.dest = dest
        self.instances = instances
        self.edge_type = edge_type
        self.arrowSize = 15
        self.color = QtGui.QColor(color)
        self.original_pen = QtGui.QPen(self.color, 4)  # Store original pen
        self.mainPen = self.original_pen  # Use mainPen for drawing
        self.setPen(self.mainPen)
        self.setZValue(-1)
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.adjust()

    def adjust(self):
        if not self.source or not self.dest:
            return
            
        path = QtGui.QPainterPath()
        path.moveTo(self.source.scenePos())
        path.lineTo(self.dest.scenePos())
        self.setPath(path)

    def paint(self, painter, option, widget=None):
        if not self.source or not self.dest:
            return
            
        self.adjust()
        if self.isSelected():
            highlight_pen = QtGui.QPen(QtGui.QColor("#00FFFF"),
                                        self.mainPen.width() + 4,
                                        QtCore.Qt.SolidLine,
                                        QtCore.Qt.RoundCap,
                                        QtCore.Qt.RoundJoin)
            painter.setPen(highlight_pen)
            painter.drawPath(self.path())

        path = self.path()
        border_pen = QtGui.QPen(QtGui.QColor("black"), self.mainPen.width() + 2)
        painter.setPen(border_pen)
        painter.drawPath(path)
        painter.setPen(self.mainPen)
        painter.drawPath(path)

        line = QtCore.QLineF(self.source.scenePos(), self.dest.scenePos())
        if line.length() == 0:
            return
        dx = line.dx() / line.length()
        dy = line.dy() / line.length()
        dest_center = self.dest.scenePos()
        tip = dest_center
        if self.edge_type == "allocation" and isinstance(self.dest, ProcessItem):
            tip = dest_center - QtCore.QPointF(dx * self.dest.radius, dy * self.dest.radius)
        elif self.edge_type == "request" and isinstance(self.dest, ResourceItem):
            half_width = self.dest.boundingRect().width() / 2
            half_height = self.dest.boundingRect().height() / 2
            factor = min(half_width / abs(dx) if dx != 0 else 1e9,
                         half_height / abs(dy) if dy != 0 else 1e9)
            tip = dest_center - QtCore.QPointF(dx * factor, dy * factor)

        angle = math.atan2(dy, dx)
        arrowP1 = tip - QtCore.QPointF(math.cos(angle - math.pi/6) * self.arrowSize,
                                       math.sin(angle - math.pi/6) * self.arrowSize)
        arrowP2 = tip - QtCore.QPointF(math.cos(angle + math.pi/6) * self.arrowSize,
                                       math.sin(angle + math.pi/6) * self.arrowSize)
        arrowHead = QtGui.QPolygonF([tip, arrowP1, arrowP2])

        arrow_border_pen = QtGui.QPen(QtGui.QColor("black"), self.mainPen.width() + 2)
        painter.setPen(arrow_border_pen)
        painter.setBrush(QtGui.QColor("black"))
        painter.drawPolygon(arrowHead)
        painter.setPen(self.mainPen)
        painter.setBrush(self.color)
        painter.drawPolygon(arrowHead)

        if self.instances > 1:
            mid = (self.source.scenePos() + self.dest.scenePos()) / 2
            text_bg = QtCore.QRectF(mid.x() - 12, mid.y() - 12, 24, 24)
            painter.setBrush(QtGui.QColor(255, 255, 255, 200))
            painter.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 150), 1))
            painter.drawEllipse(text_bg)
            
            font = QtGui.QFont("Segoe UI", 9, QtGui.QFont.Bold)
            painter.setFont(font)
            painter.setPen(QtGui.QColor(0, 0, 0))
            painter.drawText(text_bg, QtCore.Qt.AlignCenter, str(self.instances))

# --- Action History Status Bar ---
class ActionHistoryStatusBar(QtWidgets.QStatusBar):
    def __init__(self, parent=None, max_actions=20):
        super().__init__(parent)
        self.max_actions = max_actions
        self.action_history = []
        
        # Create layout for status bar
        self.layout = QtWidgets.QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(10)
        
        # Current status label (left)
        self.currentStatusLabel = QtWidgets.QLabel("Ready")
        self.currentStatusLabel.setMinimumWidth(200)
        
        # History button (middle)
        self.historyButton = QtWidgets.QPushButton("Show Action History")
        self.historyButton.setMaximumHeight(20)
        self.historyButton.setCursor(QtCore.Qt.PointingHandCursor)
        self.historyButton.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                text-decoration: underline;
                color: inherit;
            }
        """)
        self.historyButton.clicked.connect(self.showHistoryDialog)
        
        # Spacer to push elements to the left and right
        spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        
        # Last action label (right)
        self.lastActionLabel = QtWidgets.QLabel("")
        self.lastActionLabel.setAlignment(QtCore.Qt.AlignRight)
        
        # Add widgets to layout
        self.layout.addWidget(self.currentStatusLabel)
        self.layout.addWidget(self.historyButton)
        self.layout.addItem(spacer)
        self.layout.addWidget(self.lastActionLabel)
        
        # Create a widget to hold the layout
        container = QtWidgets.QWidget()
        container.setLayout(self.layout)
        
        # Add container to status bar
        self.addWidget(container, 1)

    def logAction(self, action_text, is_current_action=False):
        """Add an action to the history log"""
        timestamp = QtCore.QTime.currentTime().toString("hh:mm:ss")
        action_entry = f"{timestamp}: {action_text}"
        
        # Add to history
        self.action_history.append(action_entry)
        
        # Limit history size
        if len(self.action_history) > self.max_actions:
            self.action_history.pop(0)  # Remove oldest entry
        
        # Update labels
        if is_current_action:
            self.currentStatusLabel.setText(action_text)
        self.lastActionLabel.setText(f"Last action: {action_text}")
        
        return action_entry
    
    def clearCurrentAction(self):
        """Clear the current action label"""
        self.currentStatusLabel.setText("Ready")
    
    def showHistoryDialog(self):
        """Show a dialog with the action history"""
        dialog = QtWidgets.QDialog(self.parent())
        dialog.setWindowTitle("Action History")
        dialog.setMinimumWidth(400)
        dialog.setMinimumHeight(300)
        
        # Dialog layout
        layout = QtWidgets.QVBoxLayout(dialog)
        
        # History list
        historyList = QtWidgets.QListWidget()
        for action in reversed(self.action_history):  # Show newest first
            historyList.addItem(action)
        
        # Style the list according to the theme
        theme = self.parent().current_theme if hasattr(self.parent(), 'current_theme') else "Default"
        if theme == "Default" or theme == "Dark":
            historyList.setStyleSheet("""
                QListWidget {
                    background-color: #333;
                    color: white;
                    border: 1px solid #555;
                }
                QListWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #555;
                }
                QListWidget::item:selected {
                    background-color: #189ab4;
                }
            """)
        else:  # Light theme
            historyList.setStyleSheet("""
                QListWidget {
                    background-color: white;
                    color: black;
                    border: 1px solid #ccc;
                }
                QListWidget::item {
                    padding: 5px;
                    border-bottom: 1px solid #eee;
                }
                QListWidget::item:selected {
                    background-color: #2196F3;
                    color: white;
                }
            """)
        
        # Add to layout
        layout.addWidget(historyList)
        
        # Close button
        closeButton = QtWidgets.QPushButton("Close")
        closeButton.clicked.connect(dialog.accept)
        layout.addWidget(closeButton)
        
        # Show dialog
        dialog.exec_()

# --- Main Window ---
class MainWindow(QtWidgets.QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Resource Allocation Graph Simulator")
        self.resize(1000, 800)

        self.themes = {
            "Default": """
                QMainWindow { background-color: #2C3E50; }
                QToolBar { background: #05445e; }
                QToolButton { 
                    background: #189ab4; 
                    color: white; 
                    border: none; 
                    padding: 4px 8px; 
                    border-radius: 4px; 
                    min-width: 100px; 
                    min-height: 30px;
                    margin-bottom: 8px;
                }
                QToolButton:hover { background: #d4f1f4; color: black; }
                QToolButton:pressed { background: #75e6da; }
                QGraphicsView { background-color: #75e6da; border: none; }
                QStatusBar { 
                    background-color: #05445e; 
                    color: white; 
                    font: 10pt "Segoe UI";
                    padding: 3px;
                }
                QStatusBar QLabel { color: white; }
                QStatusBar::item { border: none; }
            """,
            "Dark": """
                QMainWindow { background-color: #1E1E1E; }
                QToolBar { background: #333333; }
                QToolButton { 
                    background: #555555; 
                    color: #FFFFFF; 
                    border: none; 
                    padding: 4px 8px; 
                    border-radius: 4px; 
                    min-width: 100px; 
                    min-height: 30px;
                    margin-bottom: 8px;
                }
                QToolButton:hover { background: #777777; color: #FFFFFF; }
                QToolButton:pressed { background: #999999; }
                QGraphicsView { background-color: #3C3C3C; border: none; }
                QStatusBar { 
                    background-color: #333333; 
                    color: white; 
                    font: 10pt "Segoe UI";
                    padding: 3px;
                }
                QStatusBar QLabel { color: white; }
                QStatusBar::item { border: none; }
            """,
            "Light": """
                QMainWindow { background-color: #FFFFFF; }
                QToolBar { background: #E0E0E0; }
                QToolButton { 
                    background: #F0F0F0; 
                    color: #000000; 
                    border: none; 
                    padding: 4px 8px; 
                    border-radius: 4px; 
                    min-width: 100px; 
                    min-height: 30px;
                    margin-bottom: 8px;
                }
                QToolButton:hover { background: #D0D0D0; color: #000000; }
                QToolButton:pressed { background: #B0B0B0; }
                QGraphicsView { background-color: #FFFFFF; border: none; }
                QStatusBar { 
                    background-color: #E0E0E0; 
                    color: black; 
                    font: 10pt "Segoe UI";
                    padding: 3px;
                }
                QStatusBar QLabel { color: black; }
                QStatusBar::item { border: none; }
            """
        }

        self.current_theme = "Default"
        self.setStyleSheet(self.themes[self.current_theme])

        self.createMenuBar()
        self.createToolBar()

        self.scene = QtWidgets.QGraphicsScene()
        self.view = ZoomPanGraphicsView(self.scene)
        self.setCentralWidget(self.view)

        self.graph = nx.DiGraph()
        self.nodeItems = {}
        self.edgeItems = {}
        self.undo_stack = []
        self.redo_stack = []
        self.current_positions = {}
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.resizeEvent = self.onViewResize
        
        # Create enhanced status bar
        self.statusBar = ActionHistoryStatusBar(self, max_actions=30)
        self.setStatusBar(self.statusBar)
        self.statusBar.logAction("Application started", is_current_action=True)

    def restoreState(self, state):
        self.graph = nx.node_link_graph(state['graph'])
        self.current_positions = state['positions'].copy()
        
        for name, (x, y) in self.current_positions.items():
            if name in self.nodeItems:
                self.nodeItems[name].setPos(x, y)
        
        self.view.setTransform(QtGui.QTransform(*state['transform']))
        
        # Rebuild edges
        for edge in list(self.edgeItems.values()):
            self.scene.removeItem(edge)
        self.edgeItems.clear()
        
        for u, v, data in self.graph.edges(data=True):
            self.createOrUpdateEdge(u, v)
        
        self.updateEdges()

    def clearGraph(self):
        self.saveState(description="Clear graph")
        self.graph.clear()
        self.current_positions.clear()
        for item in list(self.nodeItems.values()):
            self.scene.removeItem(item)
        for item in list(self.edgeItems.values()):
            self.scene.removeItem(item)
        self.nodeItems.clear()
        self.edgeItems.clear()
        self.view.viewport().update()

    def saveGraph(self):
        if not self.graph.nodes:
            QtWidgets.QMessageBox.warning(self, "Warning", "Nothing to save! The graph is empty.")
            return
            
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Graph", "", "JSON Files (*.json)"
        )
        if not path:
            return
            
        # Make sure the file has .json extension
        if not path.lower().endswith('.json'):
            path += '.json'
            
        try:
            data = {
                "graph": nx.node_link_data(self.graph, edges="links"),
                "positions": self.current_positions,
                "version": "1.0"  # Add version for future compatibility
            }
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            QtWidgets.QMessageBox.information(self, "Save", "Graph saved successfully.")
            self.statusBar.logAction(f"Graph saved to {path}", True)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save graph: {str(e)}")
            print(f"Save error: {str(e)}")

    def loadGraph(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Load Graph", "", "JSON Files (*.json)"
        )
        if not path:
            return
            
        try:
            with open(path, "r") as f:
                data = json.load(f)
                
            # Validate the graph data structure
            if not isinstance(data, dict) or "graph" not in data or "positions" not in data:
                raise ValueError("Invalid graph file format")
                
            self.saveState(description="Load graph")
            
            # Clear current graph
            self.clearGraph()
            
            # Load the graph
            self.graph = nx.node_link_graph(data["graph"])
            self.current_positions = {
                str(k): (float(x), float(y)) 
                for k, (x, y) in data["positions"].items()
            }
            
            # Create visual nodes
            for n, attr in self.graph.nodes(data=True):
                if attr.get("type") == "process":
                    item = ProcessItem(n)
                elif attr.get("type") == "resource":
                    instances = attr.get("instances", 1)
                    item = ResourceItem(n, instances)
                    item.available = attr.get("available", instances)
                    item.updateCount()
                else:
                    print(f"Unknown node type for {n}: {attr}")
                    continue
                    
                self.scene.addItem(item)
                self.nodeItems[n] = item
                
                # Position the node
                if n in self.current_positions:
                    x, y = self.current_positions[n]
                    item.setPos(x, y)
            
            # Create edges
            for u, v, data in self.graph.edges(data=True):
                self.createOrUpdateEdge(u, v)
            
            self.updateEdges()
            QtWidgets.QMessageBox.information(self, "Load", "Graph loaded successfully.")
            self.statusBar.logAction(f"Graph loaded from {path}", True)
            
        except json.JSONDecodeError:
            QtWidgets.QMessageBox.critical(self, "Error", "Invalid JSON file!")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load graph: {str(e)}")
            print(f"Load error: {str(e)}")
            # Reset to a clean state
            self.clearGraph()

    def renameNode(self, node_item):
        old_name = node_item.name
        dialog = CustomInputDialog("Rename Node", "New name:", self, "text")
        dialog.input.setText(old_name)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_name = dialog.getText()
            
            # Check for empty name
            if not new_name:
                QtWidgets.QMessageBox.warning(self, "Error", "Node name cannot be empty!")
                return
                
            # Check if name is unchanged
            if new_name == old_name:
                return
                
            # Check for duplicate name
            if new_name in self.graph.nodes:
                QtWidgets.QMessageBox.warning(self, "Error", "Name already exists!")
                return
                
            try:
                self.saveState(description=f"Rename {old_name} to {new_name}")
                
                # Temporarily store edges connected to the node
                connected_edges = []
                for u, v, data in list(self.graph.edges(data=True)):
                    if u == old_name or v == old_name:
                        source = new_name if u == old_name else u
                        target = new_name if v == old_name else v
                        connected_edges.append((source, target, data))
                        # Remove existing edges that will be replaced
                        if (u, v) in self.edgeItems:
                            self.scene.removeItem(self.edgeItems[(u, v)])
                            del self.edgeItems[(u, v)]
                
                # Relabel the node in the graph
                mapping = {old_name: new_name}
                self.graph = nx.relabel_nodes(self.graph, mapping)
                
                # Update the node item
                self.nodeItems[new_name] = self.nodeItems.pop(old_name)
                self.current_positions[new_name] = self.current_positions.pop(old_name)
                node_item.name = new_name
                node_item.text.setPlainText(new_name)
                node_item.updateTextPosition()
                
                # Recreate edges with the new node name
                for source, target, data in connected_edges:
                    if source in self.graph.nodes and target in self.graph.nodes:
                        self.graph.add_edge(source, target, **data)
                        self.createOrUpdateEdge(source, target)
                
                self.updateEdges()
                QtWidgets.QMessageBox.information(self, "Success", f"Node renamed from '{old_name}' to '{new_name}'")
                
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to rename node: {str(e)}")
                print(f"Rename error: {str(e)}")
                # Try to restore the previous state
                if len(self.undo_stack) > 1:
                    self.undoAction()

    def removeNode(self, node_item):
        node_name = node_item.name
        node_type = "process" if isinstance(node_item, ProcessItem) else "resource"
        
        # Confirm node removal
        reply = QtWidgets.QMessageBox.question(
            self, 
            "Confirm Removal",
            f"Are you sure you want to remove {node_type} '{node_name}'?\nThis will also remove all connected edges.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.No:
            return
            
        try:
            self.saveState(description=f"Remove node {node_name}")
            
            # Find all connected edges
            connected_edges = []
            for u, v in list(self.edgeItems.keys()):
                if u == node_name or v == node_name:
                    connected_edges.append((u, v))
            
            # Remove connected edges from scene and data structures
            for u, v in connected_edges:
                if (u, v) in self.edgeItems:
                    self.scene.removeItem(self.edgeItems[(u, v)])
                    del self.edgeItems[(u, v)]
            
            # Remove node from graph
            self.graph.remove_node(node_name)
            
            # Remove node from scene
            self.scene.removeItem(node_item)
            
            # Remove node from data structures
            del self.nodeItems[node_name]
            if node_name in self.current_positions:
                del self.current_positions[node_name]
            
            self.updateEdges()
            # Update status bar with action message
            self.statusBar.logAction(f"{node_type.capitalize()} '{node_name}' removed", True)
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to remove node: {str(e)}")
            print(f"Remove node error: {str(e)}")
            
    def resetZoom(self):
        """Reset zoom level to 1:1"""
        self.view.resetTransform()
        self.updateEdges()
        self.statusBar.logAction("Zoom reset to 100%", True)
        
    def zoomIn(self):
        """Zoom in view"""
        self.view.scale(self.view.zoom_in_factor, self.view.zoom_in_factor)
        self.updateEdges()
        self.statusBar.logAction("Zoomed in", False)
        
    def zoomOut(self):
        """Zoom out view"""
        self.view.scale(1 / self.view.zoom_in_factor, 1 / self.view.zoom_in_factor)
        self.updateEdges()
        self.statusBar.logAction("Zoomed out", False)
        
    def showAbout(self):
        """Show information about the application"""
        QtWidgets.QMessageBox.about(self, 
            "About Resource Allocation Graph Simulator",
            """<h2>Enhanced Resource Allocation Graph Simulator</h2>
            <p>Version 1.0</p>
            <p>A tool for simulating and detecting deadlocks in operating systems
            resource allocation.</p>
            <p>Features:</p>
            <ul>
                <li>Visual representation of processes and resources</li>
                <li>Resource request and allocation simulation</li>
                <li>Deadlock detection with cycle highlighting</li>
                <li>Save and load graphs</li>
                <li>Undo/redo functionality</li>
            </ul>
            """)
            
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts"""
        # Delete key to remove selected items
        if event.key() == QtCore.Qt.Key_Delete:
            selected_items = self.scene.selectedItems()
            if selected_items:
                for item in selected_items:
                    if isinstance(item, (ProcessItem, ResourceItem)):
                        self.removeNode(item)
                    elif isinstance(item, EdgeItem):
                        # Find the edge key in edgeItems
                        edge_key = None
                        for key, edge in self.edgeItems.items():
                            if edge == item:
                                edge_key = key
                                break
                        if edge_key:
                            u, v = edge_key
                            self.saveState(description=f"Remove edge {u}->{v}")
                            self.graph.remove_edge(u, v)
                            self.scene.removeItem(item)
                            del self.edgeItems[edge_key]
                            self.updateEdges()
        else:
            super().keyPressEvent(event)

    def applyTheme(self, theme):
        if theme in self.themes:
            self.current_theme = theme
            self.setStyleSheet(self.themes[theme])
            for widget in QtWidgets.QApplication.topLevelWidgets():
                if isinstance(widget, CustomInputDialog):
                    widget.setStyleSheet(widget.styleSheet())
            self.update()
            self.statusBar.logAction(f"Applied {theme} theme", True)

    def saveState(self, description=None):
        state = {
            'graph': nx.node_link_data(self.graph, edges="links"),
            'positions': copy.copy(self.current_positions),
            'transform': (
                self.view.transform().m11(),
                self.view.transform().m12(),
                self.view.transform().m21(),
                self.view.transform().m22(),
                self.view.transform().dx(),
                self.view.transform().dy()
            ),
            'description': description or "State change"
        }
        
        if not self.undo_stack or state != self.undo_stack[-1]:
            self.undo_stack.append(state)
            self.redo_stack.clear()
            
            # Log the action to status bar
            if description:
                self.statusBar.logAction(description)
    
    def undoAction(self):
        if len(self.undo_stack) > 1:
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            previous_state = self.undo_stack[-1]
            self.restoreState(previous_state)
            
            # Log the action
            description = previous_state.get('description', 'Unknown state')
            self.statusBar.logAction(f"Undo: Reverted to {description}", True)
    
    def redoAction(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            self.restoreState(state)
            
            # Log the action
            description = state.get('description', 'Unknown state')
            self.statusBar.logAction(f"Redo: Applied {description}", True)

    def createMenuBar(self):
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu("&File")
        saveAction = QtWidgets.QAction("&Save Graph", self)
        saveAction.setShortcut("Ctrl+S")
        saveAction.setStatusTip("Save the current graph to a file")
        saveAction.triggered.connect(self.saveGraph)
        fileMenu.addAction(saveAction)
        
        openAction = QtWidgets.QAction("&Open Graph", self)
        openAction.setShortcut("Ctrl+O")
        openAction.setStatusTip("Load a graph from a file")
        openAction.triggered.connect(self.loadGraph)
        fileMenu.addAction(openAction)
        
        fileMenu.addSeparator()
        
        exitAction = QtWidgets.QAction("E&xit", self)
        exitAction.setShortcut("Ctrl+Q")
        exitAction.setStatusTip("Exit the application")
        exitAction.triggered.connect(self.close)
        fileMenu.addAction(exitAction)

        editMenu = menuBar.addMenu("&Edit")
        undoAction = QtWidgets.QAction("&Undo", self)
        undoAction.setShortcut("Ctrl+Z")
        undoAction.setStatusTip("Undo the last action")
        undoAction.triggered.connect(self.undoAction)
        editMenu.addAction(undoAction)
        
        redoAction = QtWidgets.QAction("&Redo", self)
        redoAction.setShortcut("Ctrl+Y")
        redoAction.setStatusTip("Redo the last undone action")
        redoAction.triggered.connect(self.redoAction)
        editMenu.addAction(redoAction)
        
        editMenu.addSeparator()
        
        clearAction = QtWidgets.QAction("&Clear", self)
        clearAction.setShortcut("Ctrl+Shift+C")
        clearAction.setStatusTip("Clear the entire graph")
        clearAction.triggered.connect(self.clearGraph)
        editMenu.addAction(clearAction)
        
        nodesMenu = editMenu.addMenu("&Nodes")
        
        addProcessAction = QtWidgets.QAction("Add &Process", self)
        addProcessAction.setShortcut("Ctrl+P")
        addProcessAction.setStatusTip("Add a new process node")
        addProcessAction.triggered.connect(self.addProcess)
        nodesMenu.addAction(addProcessAction)
        
        addResourceAction = QtWidgets.QAction("Add &Resource", self)
        addResourceAction.setShortcut("Ctrl+R")
        addResourceAction.setStatusTip("Add a new resource node")
        addResourceAction.triggered.connect(self.addResource)
        nodesMenu.addAction(addResourceAction)

        optionMenu = menuBar.addMenu("&Option")
        themeMenu = optionMenu.addMenu("&Theme")
        defaultAction = QtWidgets.QAction("&Default", self)
        defaultAction.triggered.connect(lambda: self.applyTheme("Default"))
        themeMenu.addAction(defaultAction)
        darkAction = QtWidgets.QAction("&Dark", self)
        darkAction.triggered.connect(lambda: self.applyTheme("Dark"))
        themeMenu.addAction(darkAction)
        lightAction = QtWidgets.QAction("&Light", self)
        lightAction.triggered.connect(lambda: self.applyTheme("Light"))
        themeMenu.addAction(lightAction)

        zoomMenu = optionMenu.addMenu("&Zoom")
        zoomInAction = QtWidgets.QAction("Zoom &In", self)
        zoomInAction.setShortcut(QtGui.QKeySequence.ZoomIn)
        zoomInAction.triggered.connect(self.zoomIn)
        zoomMenu.addAction(zoomInAction)
        zoomOutAction = QtWidgets.QAction("Zoom &Out", self)
        zoomOutAction.setShortcut(QtGui.QKeySequence.ZoomOut)
        zoomOutAction.triggered.connect(self.zoomOut)
        zoomMenu.addAction(zoomOutAction)
        
        resetZoomAction = QtWidgets.QAction("&Reset Zoom", self)
        resetZoomAction.setShortcut("Ctrl+0")
        resetZoomAction.triggered.connect(self.resetZoom)
        zoomMenu.addAction(resetZoomAction)
        
        # Add help menu
        helpMenu = menuBar.addMenu("&Help")
        aboutAction = QtWidgets.QAction("&About", self)
        aboutAction.triggered.connect(self.showAbout)
        helpMenu.addAction(aboutAction)

    def createToolBar(self):
        toolbar = QtWidgets.QToolBar()
        self.addToolBar(QtCore.Qt.LeftToolBarArea, toolbar)
        toolbar.setFixedWidth(140)
        actions = [
            ("Add Process", self.addProcess, 
             "Add a new process node to the graph"),
            ("Add Resource", self.addResource, 
             "Add a new resource node with specified instances"),
            ("Request", self.requestResource, 
             "Create a resource request or allocation edge"),
            ("Release", self.releaseResource, 
             "Release previously allocated resources"),
            ("Auto Layout", self.autoLayout, 
             "Automatically arrange nodes for better visibility"),
            ("Detect Deadlock", self.detectDeadlock, 
             "Check and highlight deadlock cycles in the graph")
        ]
        for text, slot, tooltip in actions:
            action = QtWidgets.QAction(text, self)
            action.triggered.connect(slot)
            action.setToolTip(tooltip)
            toolbar.addAction(action)

    def onViewResize(self, event):
        self.updateEdges()
        QtWidgets.QGraphicsView.resizeEvent(self.view, event)

    def updateEdges(self):
        for edge in self.edgeItems.values():
            edge.adjust()
            edge.update()

    def addProcess(self):
        dialog = CustomInputDialog("Add Process", "Enter process name:", self, "text")
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            name = dialog.getText()
            if name and name not in self.graph.nodes:
                self.saveState(description=f"Added process {name}")
                self.graph.add_node(name, type="process", instances=1)
                procItem = ProcessItem(name)
                self.scene.addItem(procItem)
                self.nodeItems[name] = procItem
                self.current_positions[name] = (procItem.x(), procItem.y())
                self.autoLayout()
                self.statusBar.logAction(f"Added process {name}", True)

    def addResource(self):
        dialog = CustomInputDialog("Add Resource", "Enter resource name:", self, "text")
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            name = dialog.getText()
            if name and name not in self.graph.nodes:
                inst_dialog = CustomInputDialog("Resource Instances", "Number of instances:", 
                                               self, "int", 1, 100)
                if inst_dialog.exec_() == QtWidgets.QDialog.Accepted:
                    inst = inst_dialog.getInt()
                    self.saveState(description=f"Added resource {name}")
                    self.graph.add_node(name, type="resource", instances=inst, available=inst)
                    resItem = ResourceItem(name, inst)
                    self.scene.addItem(resItem)
                    self.nodeItems[name] = resItem
                    self.current_positions[name] = (resItem.x(), resItem.y())
                    self.autoLayout()
                    self.statusBar.logAction(f"Added resource {name} with {inst} instances", True)

    def requestResource(self):
        if not any(self.graph.nodes[n].get("type") == "process" for n in self.graph.nodes if n in self.nodeItems):
            QtWidgets.QMessageBox.warning(self, "Error", "Please add at least one process first!")
            return
            
        if not any(self.graph.nodes[n].get("type") == "resource" for n in self.graph.nodes if n in self.nodeItems):
            QtWidgets.QMessageBox.warning(self, "Error", "Please add at least one resource first!")
            return
    
        proc_nodes = [n for n in self.graph.nodes if self.graph.nodes[n].get("type") == "process"]
        res_nodes = [n for n in self.graph.nodes if self.graph.nodes[n].get("type") == "resource"]
        
        proc_dialog = CustomInputDialog("Request Resource", "Process name:", self, "text")
        if proc_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        proc = proc_dialog.getText()
        
        # Validate process name
        if not proc:
            QtWidgets.QMessageBox.warning(self, "Error", "Process name cannot be empty!")
            return
            
        if proc not in proc_nodes:
            QtWidgets.QMessageBox.warning(self, "Error", f"Process '{proc}' does not exist!")
            return
        
        res_dialog = CustomInputDialog("Request Resource", "Resource name:", self, "text")
        if res_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        res = res_dialog.getText()
        
        # Validate resource name
        if not res:
            QtWidgets.QMessageBox.warning(self, "Error", "Resource name cannot be empty!")
            return
            
        if res not in res_nodes:
            QtWidgets.QMessageBox.warning(self, "Error", f"Resource '{res}' does not exist!")
            return
        
        # Check for existing request edge
        if self.graph.has_edge(proc, res):
            current_req = self.graph[proc][res].get("instances", 0)
            QtWidgets.QMessageBox.warning(self, "Error", 
                f"Process '{proc}' already has a request for {current_req} instance(s) of resource '{res}'.\n"
                "Please release the existing request before making a new one.")
            return
        
        amt_dialog = CustomInputDialog("Request Amount", "Instances to request:", 
                                      self, "int", 1, self.graph.nodes[res]["instances"])
        if amt_dialog.exec_() == QtWidgets.QDialog.Accepted:
            amt = amt_dialog.getInt()
            
            # Validate request amount
            if amt <= 0:
                QtWidgets.QMessageBox.warning(self, "Error", "Request amount must be positive!")
                return
                
            if amt > self.graph.nodes[res]["instances"]:
                QtWidgets.QMessageBox.warning(self, "Error", 
                    f"Cannot request more than total instances ({self.graph.nodes[res]['instances']})!")
                return
            
            self.saveState(description=f"Request {amt} {res} by {proc}")
            
            if self.graph.nodes[res]["available"] >= amt:
                # Sufficient resources are available, allocate directly
                self.graph.nodes[res]["available"] -= amt
                self.graph.add_edge(res, proc, instances=amt, type="allocation")
                self.createOrUpdateEdge(res, proc)
                QtWidgets.QMessageBox.information(self, "Success", 
                    f"Resource '{res}' allocated to process '{proc}'.")
                self.statusBar.logAction(f"Allocated {amt} {res} to {proc}", True)
            else:
                # Not enough resources, create a request edge
                self.graph.add_edge(proc, res, instances=amt, type="request")
                self.createOrUpdateEdge(proc, res)
                QtWidgets.QMessageBox.information(self, "Pending", 
                    f"Request for resource '{res}' is pending due to insufficient availability.")
                self.statusBar.logAction(f"Request {amt} {res} by {proc} (pending)", True)
                
            self.updateEdges()
            if res in self.nodeItems and isinstance(self.nodeItems[res], ResourceItem):
                self.nodeItems[res].available = self.graph.nodes[res]["available"]
                self.nodeItems[res].updateCount()
                
    def releaseResource(self):
        # Get all allocation edges
        allocation_edges = [(u, v) for u, v, d in self.graph.edges(data=True) 
                           if d.get("type") == "allocation"]
        
        if not allocation_edges:
            QtWidgets.QMessageBox.warning(self, "Error", "No resources are currently allocated!")
            return
            
        proc_nodes = [v for u, v in allocation_edges]
        res_nodes = [u for u, v in allocation_edges]
        
        proc_dialog = CustomInputDialog("Release Resource", "Process name:", self, "text")
        if proc_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        proc = proc_dialog.getText()
        
        # Validate process name
        if not proc:
            QtWidgets.QMessageBox.warning(self, "Error", "Process name cannot be empty!")
            return
            
        if proc not in proc_nodes:
            QtWidgets.QMessageBox.warning(self, "Error", f"Process '{proc}' does not have any allocated resources!")
            return
        
        # Find resources allocated to this process
        allocated_resources = [u for u, v in allocation_edges if v == proc]
        
        if not allocated_resources:
            QtWidgets.QMessageBox.warning(self, "Error", f"Process '{proc}' has no allocated resources!")
            return
        
        res_dialog = CustomInputDialog("Release Resource", "Resource name:", self, "text")
        if res_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        res = res_dialog.getText()
        
        # Validate resource name
        if not res:
            QtWidgets.QMessageBox.warning(self, "Error", "Resource name cannot be empty!")
            return
            
        if res not in allocated_resources:
            QtWidgets.QMessageBox.warning(self, "Error", 
                f"Resource '{res}' is not allocated to process '{proc}'!")
            return
        
        # Get current allocation amount
        current = self.graph[res][proc]["instances"]
        
        amt_dialog = CustomInputDialog("Release Amount", "Instances to release:", 
                                      self, "int", 1, current)
        if amt_dialog.exec_() == QtWidgets.QDialog.Accepted:
            amt = amt_dialog.getInt()
            
            # Validate release amount
            if amt <= 0:
                QtWidgets.QMessageBox.warning(self, "Error", "Release amount must be positive!")
                return
                
            if amt > current:
                QtWidgets.QMessageBox.warning(self, "Error", 
                    f"Cannot release more than allocated ({current})!")
                return
            
            self.saveState(description=f"Release {amt} {res} by {proc}")
            
            # Update allocation edge
            self.graph[res][proc]["instances"] -= amt
            self.graph.nodes[res]["available"] += amt
            
            # Remove edge if all instances are released
            if self.graph[res][proc]["instances"] == 0:
                self.graph.remove_edge(res, proc)
                if (res, proc) in self.edgeItems:
                    self.scene.removeItem(self.edgeItems[(res, proc)])
                    del self.edgeItems[(res, proc)]
            else:
                # Update edge label if some instances remain
                if (res, proc) in self.edgeItems:
                    self.edgeItems[(res, proc)].instances = self.graph[res][proc]["instances"]
                    self.edgeItems[(res, proc)].update()
            
            # Try to satisfy pending requests
            pending_requests = [(u, v, d) for u, v, d in self.graph.edges(data=True) 
                               if v == res and d.get("type") == "request"]
            
            # Sort requests by amount (smaller first for fairness)
            pending_requests.sort(key=lambda x: x[2].get("instances", 0))
            
            for u, v, data in pending_requests:
                request_amt = data.get("instances", 0)
                
                # If we can satisfy this request
                if self.graph.nodes[res]["available"] >= request_amt:
                    self.graph.nodes[res]["available"] -= request_amt
                    
                    # Remove request edge
                    self.graph.remove_edge(u, v)
                    if (u, v) in self.edgeItems:
                        self.scene.removeItem(self.edgeItems[(u, v)])
                        del self.edgeItems[(u, v)]
                    
                    # Create allocation edge
                    self.graph.add_edge(res, u, instances=request_amt, type="allocation")
                    self.createOrUpdateEdge(res, u)
                    
                    QtWidgets.QMessageBox.information(self, "Success", 
                        f"Resource '{res}' allocated to process '{u}' after release.")
                    self.statusBar.logAction(f"Released {amt} {res} from {proc} and allocated to {u}", True)
                    break
                else:
                    self.statusBar.logAction(f"Released {amt} {res} from {proc}", True)
            
            self.updateEdges()
            if res in self.nodeItems and isinstance(self.nodeItems[res], ResourceItem):
                self.nodeItems[res].available = self.graph.nodes[res]["available"]
                self.nodeItems[res].updateCount()

    def createOrUpdateEdge(self, u, v):
        if (u, v) in self.edgeItems:
            self.scene.removeItem(self.edgeItems[(u, v)])
            del self.edgeItems[(u, v)]
        if self.graph.has_edge(u, v):
            data = self.graph[u][v]
            edge_color = "#4CAF50" if data.get("type") == "allocation" else "#FFEB3B"
            srcItem = self.nodeItems.get(u)
            destItem = self.nodeItems.get(v)
            if srcItem and destItem:
                edge = EdgeItem(srcItem, destItem, data.get("instances", 1), data.get("type"), edge_color)
                self.scene.addItem(edge)
                self.edgeItems[(u, v)] = edge

    def autoLayout(self):
        if len(self.graph.nodes) == 0:
            return

        self.saveState(description="Auto layout")
        pos = nx.spring_layout(self.graph, seed=42)
        
        view_rect = self.view.viewport().rect()
        margin = 50
        width = view_rect.width() - 2 * margin
        height = view_rect.height() - 2 * margin
        
        for node, (x, y) in pos.items():
            scaled_x = margin + (x + 1) * width / 2
            scaled_y = margin + (y + 1) * height / 2
            self.nodeItems[node].setPos(scaled_x, scaled_y)
            self.current_positions[node] = (scaled_x, scaled_y)
        
        self.updateEdges()
        self.statusBar.logAction("Auto layout applied", True)

    def handleNodeMoved(self, node_item, new_pos):
        self.current_positions[node_item.name] = (new_pos.x(), new_pos.y())

    def detectDeadlock(self):
        # Reset edges and nodes to original appearance
        for edge in self.edgeItems.values():
            edge.mainPen = edge.original_pen  # Restore original pen
            edge.update()
        for node in self.nodeItems.values():
            if isinstance(node, (ProcessItem, ResourceItem)):
                node.setPen(node.original_pen)
        
        # Create a wait-for graph for deadlock detection
        # In a resource allocation system, a process can be in deadlock if it's waiting for
        # resources held by other processes that are also waiting, forming a cycle
        wait_for_graph = nx.DiGraph()
        
        # Get all currently waiting processes (those with request edges)
        waiting_processes = {}  # process -> (resource, amount)
        for u, v, data in self.graph.edges(data=True):
            if data.get("type") == "request":
                # Process u is waiting for resource v
                waiting_processes[u] = (v, data.get("instances", 1))
        
        # For each waiting process, find which processes hold the resources it needs
        for waiting_process, (needed_resource, needed_amount) in waiting_processes.items():
            # Find all processes that have this resource allocated to them
            for resource, holder, data in self.graph.edges(data=True):
                if (data.get("type") == "allocation" and 
                    resource == needed_resource and
                    holder != waiting_process):  # Don't consider self-allocations
                    # Process 'waiting_process' is waiting for process 'holder'
                    wait_for_graph.add_edge(waiting_process, holder)
        
        try:
            cycles = list(nx.simple_cycles(wait_for_graph))
            
            if not cycles:
                # No cycles means no deadlock
                execution_result = self.calculateSafeExecutionOrder()
                execution_order, execution_flow = execution_result
                
                if execution_order:
                    order_str = " → ".join([f"({p})" for p in execution_order])
                    
                    # Generate the flow string if available
                    flow_str = ""
                    if execution_flow:
                        flow_pairs = []
                        for i in range(len(execution_flow) - 1):
                            curr_p, curr_r = execution_flow[i]
                            next_p, next_r = execution_flow[i+1]
                            flow_pairs.append(f"({curr_p}, {curr_r})->({next_p}, {next_r})")
                        flow_str = "\n\nExecution Flow:\n" + "\n".join(flow_pairs)
                    
                    QtWidgets.QMessageBox.information(self, "No Deadlock", 
                        f"No deadlock detected.\n\nSafe execution order:\n{order_str}{flow_str}")
                    
                    # Show execution order in a box at the bottom right
                    self.showExecutionOrderBox(execution_result)
                else:
                    QtWidgets.QMessageBox.information(self, "No Deadlock", 
                        "No deadlock detected, but couldn't determine a safe execution order.")
                
                self.statusBar.logAction("Deadlock detection: No deadlock found", True)
                return
            
            # Having cycles doesn't necessarily mean there's a deadlock
            # Check if there's a safe execution sequence despite cycles
            execution_result = self.calculateSafeExecutionOrder()
            execution_order, execution_flow = execution_result
            
            if execution_order:
                # There is a safe execution sequence, so no deadlock
                order_str = " → ".join([f"({p})" for p in execution_order])
                
                # Generate the flow string if available
                flow_str = ""
                if execution_flow:
                    flow_pairs = []
                    for i in range(len(execution_flow) - 1):
                        curr_p, curr_r = execution_flow[i]
                        next_p, next_r = execution_flow[i+1]
                        flow_pairs.append(f"({curr_p}, {curr_r})->({next_p}, {next_r})")
                    flow_str = "\n\nExecution Flow:\n" + "\n".join(flow_pairs)
                
                QtWidgets.QMessageBox.information(self, "No Deadlock", 
                    f"Cycles found but no deadlock detected.\n\n"
                    f"Although there are {len(cycles)} cycle(s) in the wait-for graph,\n"
                    f"multiple instances of resources allow all processes to complete.\n\n"
                    f"Safe execution order:\n{order_str}{flow_str}")
                
                # Show execution order in a box at the bottom right
                self.showExecutionOrderBox(execution_result)
                
                self.statusBar.logAction("Deadlock detection: Cycles found but no deadlock", True)
                return
            
            # If we reached here, there are cycles and no safe execution sequence, so there is a deadlock
            # Collect all nodes and edges involved in deadlock
            deadlocked_processes = set()
            deadlocked_resources = set()
            deadlocked_edges = set()
            
            for cycle in cycles:
                # Add all processes in the cycle
                for process in cycle:
                    deadlocked_processes.add(process)
                    # Find the resource this process is waiting for
                    if process in waiting_processes:
                        resource, _ = waiting_processes[process]
                        deadlocked_resources.add(resource)
                
                # Find all edges involved in the deadlock
                for i in range(len(cycle)):
                    waiting_proc = cycle[i]
                    holding_proc = cycle[(i + 1) % len(cycle)]
                    
                    # The resource that waiting_proc needs
                    if waiting_proc in waiting_processes:
                        needed_resource, _ = waiting_processes[waiting_proc]
                        
                        # Add the request edge
                        if self.graph.has_edge(waiting_proc, needed_resource):
                            deadlocked_edges.add((waiting_proc, needed_resource))
                        
                        # Add allocation edges from the resource to holding_proc
                        if self.graph.has_edge(needed_resource, holding_proc):
                            deadlocked_edges.add((needed_resource, holding_proc))
            
            # Highlight all edges involved in deadlock
            for u, v in deadlocked_edges:
                edge = self.edgeItems.get((u, v))
                if edge:
                    edge.mainPen = QtGui.QPen(QtGui.QColor("#F44336"), 4)
                    edge.update()
            
            # Highlight all nodes in deadlock
            highlight_pen = QtGui.QPen(QtGui.QColor("#F44336"), 3)
            
            for node_name in deadlocked_processes.union(deadlocked_resources):
                node = self.nodeItems.get(node_name)
                if node:
                    node.setPen(highlight_pen)
            
            processes_str = ", ".join(deadlocked_processes)
            resources_str = ", ".join(deadlocked_resources)
            QtWidgets.QMessageBox.information(self, "Deadlock", 
                f"Deadlock detected!\nCycles found: {len(cycles)}\n\n"
                f"Processes involved: {processes_str}\n"
                f"Resources involved: {resources_str}")
            
            self.statusBar.logAction(f"Deadlock detected between processes: {processes_str}", True)
            
            # If there's a deadlock, remove any execution order box if it exists
            self.removeExecutionOrderBox()
            
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Error", f"Error during deadlock detection: {str(e)}")
            print(f"Deadlock detection error: {str(e)}")
            self.statusBar.logAction(f"Deadlock detection error: {str(e)}", True)

    def calculateSafeExecutionOrder(self):
        """Calculate a safe execution order using a simplified Banker's algorithm approach"""
        # Get all processes (only consider those with allocation or request)
        processes = set()
        for u, v, data in self.graph.edges(data=True):
            if data.get("type") == "request" and self.graph.nodes.get(u, {}).get("type") == "process":
                processes.add(u)
            elif data.get("type") == "allocation" and self.graph.nodes.get(v, {}).get("type") == "process":
                processes.add(v)
        
        if not processes:
            return []
        
        # Get all resources
        resources = {n for n in self.graph.nodes if self.graph.nodes[n].get("type") == "resource"}
        
        # Create allocation and request matrices
        allocation = {p: {r: 0 for r in resources} for p in processes}
        requests = {p: {r: 0 for r in resources} for p in processes}
        
        # Fill allocation matrix
        for r, p, data in self.graph.edges(data=True):
            if data.get("type") == "allocation" and r in resources and p in processes:
                allocation[p][r] = data.get("instances", 1)
        
        # Fill request matrix
        for p, r, data in self.graph.edges(data=True):
            if data.get("type") == "request" and p in processes and r in resources:
                requests[p][r] = data.get("instances", 1)
        
        # Current available resources
        available = {r: self.graph.nodes[r].get("available", 0) for r in resources}
        
        # Execution order
        execution_order = []
        execution_flow = []  # Will store (process, resource) pairs
        
        # Map of resources held by each process (for producing the flow)
        held_resources = {}
        for p in processes:
            held_resources[p] = [r for r in resources if allocation[p][r] > 0]
            
        # Map of processes waiting for resources (for producing the flow)
        waiting_resources = {}
        for p in processes:
            waiting_resources[p] = [r for r in resources if requests[p][r] > 0]
        
        work = available.copy()
        finish = {p: False for p in processes}
        
        while True:
            found = False
            for p in processes:
                if not finish[p]:
                    # Check if all resource requests can be satisfied
                    can_execute = True
                    for r in resources:
                        if requests[p][r] > work[r]:
                            can_execute = False
                            break
                    
                    if can_execute:
                        # Process p can be executed
                        execution_order.append(p)
                        
                        # Add entry to flow for each resource being allocated
                        for r in waiting_resources[p]:
                            if requests[p][r] > 0:
                                execution_flow.append((p, r))
                        
                        # Add entry to flow for each resource being released
                        for r in held_resources[p]:
                            if allocation[p][r] > 0:
                                execution_flow.append((p, r))
                        
                        finish[p] = True
                        found = True
                        
                        # Release allocated resources
                        for r in resources:
                            work[r] += allocation[p][r]
            
            if not found:
                break
        
        # If all processes can finish, return the execution order and flow
        if all(finish.values()):
            return execution_order, execution_flow
        
        return None, None

    def showExecutionOrderBox(self, execution_order_data):
        """Show a box with the execution order at the bottom right of the view"""
        # Remove existing box if any
        self.removeExecutionOrderBox()
        
        # Unpack the execution order data
        if isinstance(execution_order_data, tuple):
            execution_order, execution_flow = execution_order_data
        else:
            execution_order, execution_flow = execution_order_data, None
        
        # Create text for execution order
        if execution_flow:
            # Format flow as (process, resource)->(process, resource)
            flow_pairs = []
            for i in range(len(execution_flow) - 1):
                curr_p, curr_r = execution_flow[i]
                next_p, next_r = execution_flow[i+1]
                flow_pairs.append(f"({curr_p}, {curr_r})->({next_p}, {next_r})")
            
            order_text = "Safe Execution Order:\n" + " → ".join([f"({p})" for p in execution_order])
            order_text += "\n\nExecution Flow:\n" + "\n".join(flow_pairs)
        else:
            order_text = "Safe Execution Order:\n" + " → ".join([f"({p})" for p in execution_order])
        
        # Create text item
        text_item = QtWidgets.QGraphicsTextItem(order_text)
        text_item.setZValue(100)  # Ensure it's on top
        
        # Style the text item
        font = QtGui.QFont("Segoe UI", 10)
        text_item.setFont(font)
        text_item.setDefaultTextColor(QtGui.QColor("black"))
        
        # Create background rectangle
        text_rect = text_item.boundingRect()
        rect_item = QtWidgets.QGraphicsRectItem(text_rect)
        rect_item.setBrush(QtGui.QColor(255, 255, 255, 220))
        rect_item.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0, 150)))
        rect_item.setZValue(99)  # Just below the text
        
        # Position at bottom right with padding
        view_rect = self.view.viewport().rect()
        padding = 20
        x = view_rect.width() - text_rect.width() - padding
        y = view_rect.height() - text_rect.height() - padding
        
        # Convert to scene coordinates - fix by converting floats to integers
        bottom_right = self.view.mapToScene(int(x), int(y))
        rect_item.setPos(bottom_right)
        text_item.setPos(bottom_right)
        
        # Add to scene with a tag to find them later
        rect_item.setData(0, "execution_order_box")
        text_item.setData(0, "execution_order_text")
        self.scene.addItem(rect_item)
        self.scene.addItem(text_item)

    def removeExecutionOrderBox(self):
        """Remove the execution order box from the scene if it exists"""
        # Find and remove existing execution order items
        for item in self.scene.items():
            if (item.data(0) == "execution_order_box" or
                item.data(0) == "execution_order_text"):
                self.scene.removeItem(item)

def main():
    try:
        # Apply a more compatible rendering backend BEFORE creating QApplication
        QtGui.QGuiApplication.setAttribute(QtCore.Qt.AA_UseSoftwareOpenGL)
        
        app = QtWidgets.QApplication(sys.argv)
        
        # Set application metadata
        app.setApplicationName("Resource Allocation Graph Simulator")
        app.setApplicationVersion("1.0")
        app.setOrganizationName("Operating Systems Simulator")
        
        # Create and show the main window
        window = MainWindow()
        window.show()
        
        # Run the application
        sys.exit(app.exec_())
        
    except Exception as e:
        # Show error dialog for unhandled exceptions
        error_msg = f"Fatal error: {str(e)}\n\nPlease report this issue."
        print(error_msg)
        
        # Try to show a message box if possible
        try:
            if QtWidgets.QApplication.instance():
                QtWidgets.QMessageBox.critical(None, "Fatal Error", error_msg)
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()