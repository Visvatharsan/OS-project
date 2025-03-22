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

    def getText(self):
        return self.input.text() if isinstance(self.input, QtWidgets.QLineEdit) else None
    
    def getInt(self):
        return self.input.value() if isinstance(self.input, QtWidgets.QSpinBox) else None

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
        path = QtGui.QPainterPath()
        path.moveTo(self.source.scenePos())
        path.lineTo(self.dest.scenePos())
        self.setPath(path)

    def paint(self, painter, option, widget=None):
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
            font = QtGui.QFont("Segoe UI", 9)
            painter.setFont(font)
            painter.drawText(mid, str(self.instances))

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

    def createMenuBar(self):
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu("File")
        saveAction = QtWidgets.QAction("Save Graph", self)
        saveAction.setShortcut("Ctrl+S")
        saveAction.triggered.connect(self.saveGraph)
        fileMenu.addAction(saveAction)
        openAction = QtWidgets.QAction("Open Graph", self)
        openAction.setShortcut("Ctrl+O")
        openAction.triggered.connect(self.loadGraph)
        fileMenu.addAction(openAction)

        editMenu = menuBar.addMenu("Edit")
        undoAction = QtWidgets.QAction("Undo", self)
        undoAction.setShortcut("Ctrl+Z")
        undoAction.triggered.connect(self.undoAction)
        editMenu.addAction(undoAction)
        redoAction = QtWidgets.QAction("Redo", self)
        redoAction.setShortcut("Ctrl+Y")
        redoAction.triggered.connect(self.redoAction)
        editMenu.addAction(redoAction)
        clearAction = QtWidgets.QAction("Clear", self)
        clearAction.setShortcut("Ctrl+Shift+C")
        clearAction.triggered.connect(self.clearGraph)
        editMenu.addAction(clearAction)

        optionMenu = menuBar.addMenu("Option")
        themeMenu = optionMenu.addMenu("Theme")
        defaultAction = QtWidgets.QAction("Default", self)
        defaultAction.triggered.connect(lambda: self.applyTheme("Default"))
        themeMenu.addAction(defaultAction)
        darkAction = QtWidgets.QAction("Dark", self)
        darkAction.triggered.connect(lambda: self.applyTheme("Dark"))
        themeMenu.addAction(darkAction)
        lightAction = QtWidgets.QAction("Light", self)
        lightAction.triggered.connect(lambda: self.applyTheme("Light"))
        themeMenu.addAction(lightAction)

        zoomMenu = optionMenu.addMenu("Zoom")
        zoomInAction = QtWidgets.QAction("Zoom In", self)
        zoomInAction.setShortcut(QtGui.QKeySequence.ZoomIn)
        zoomInAction.triggered.connect(self.zoomIn)
        zoomMenu.addAction(zoomInAction)
        zoomOutAction = QtWidgets.QAction("Zoom Out", self)
        zoomOutAction.setShortcut(QtGui.QKeySequence.ZoomOut)
        zoomOutAction.triggered.connect(self.zoomOut)
        zoomMenu.addAction(zoomOutAction)

    def applyTheme(self, theme):
        if theme in self.themes:
            self.current_theme = theme
            self.setStyleSheet(self.themes[theme])
            for widget in QtWidgets.QApplication.topLevelWidgets():
                if isinstance(widget, CustomInputDialog):
                    widget.setStyleSheet(widget.styleSheet())
            self.update()

    def createToolBar(self):
        toolbar = QtWidgets.QToolBar()
        self.addToolBar(QtCore.Qt.LeftToolBarArea, toolbar)
        toolbar.setFixedWidth(140)
        actions = [
            ("Add Process", self.addProcess),
            ("Add Resource", self.addResource),
            ("Request", self.requestResource),
            ("Release", self.releaseResource),
            ("Auto Layout", self.autoLayout),
            ("Detect Deadlock", self.detectDeadlock)
        ]
        for text, slot in actions:
            action = QtWidgets.QAction(text, self)
            action.triggered.connect(slot)
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

    def requestResource(self):
        proc_dialog = CustomInputDialog("Request Resource", "Process name:", self, "text")
        if proc_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        proc = proc_dialog.getText()
        
        res_dialog = CustomInputDialog("Request Resource", "Resource name:", self, "text")
        if res_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        res = res_dialog.getText()
        
        amt_dialog = CustomInputDialog("Request Amount", "Instances to request:", 
                                      self, "int", 1, 100)
        if amt_dialog.exec_() == QtWidgets.QDialog.Accepted:
            amt = amt_dialog.getInt()
            if res not in self.graph.nodes or self.graph.nodes[res].get("type") != "resource":
                QtWidgets.QMessageBox.warning(self, "Error", "Invalid resource!")
                return
            self.saveState(description=f"Request {amt} {res} by {proc}")
            if self.graph.nodes[res]["available"] >= amt:
                self.graph.nodes[res]["available"] -= amt
                self.graph.add_edge(res, proc, instances=amt, type="allocation")
                self.createOrUpdateEdge(res, proc)
            else:
                self.graph.add_edge(proc, res, instances=amt, type="request")
                self.createOrUpdateEdge(proc, res)
            self.updateEdges()
            if res in self.nodeItems and isinstance(self.nodeItems[res], ResourceItem):
                self.nodeItems[res].available = self.graph.nodes[res]["available"]
                self.nodeItems[res].updateCount()

    def releaseResource(self):
        proc_dialog = CustomInputDialog("Release Resource", "Process name:", self, "text")
        if proc_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        proc = proc_dialog.getText()
        
        res_dialog = CustomInputDialog("Release Resource", "Resource name:", self, "text")
        if res_dialog.exec_() != QtWidgets.QDialog.Accepted:
            return
        res = res_dialog.getText()
        
        amt_dialog = CustomInputDialog("Release Amount", "Instances to release:", 
                                      self, "int", 1, 100)
        if amt_dialog.exec_() == QtWidgets.QDialog.Accepted:
            amt = amt_dialog.getInt()
            if not self.graph.has_edge(res, proc):
                QtWidgets.QMessageBox.warning(self, "Error", "No allocation found!")
                return
            self.saveState(description=f"Release {amt} {res} by {proc}")
            current = self.graph[res][proc]["instances"]
            if amt > current:
                QtWidgets.QMessageBox.warning(self, "Error", f"Cannot release more than allocated ({current})")
                return
            self.graph[res][proc]["instances"] -= amt
            self.graph.nodes[res]["available"] += amt
            if self.graph[res][proc]["instances"] == 0:
                self.graph.remove_edge(res, proc)
                if (res, proc) in self.edgeItems:
                    self.scene.removeItem(self.edgeItems[(res, proc)])
                    del self.edgeItems[(res, proc)]
            for u, v, data in list(self.graph.edges(data=True)):
                if v == res and data.get("type") == "request":
                    if self.graph.nodes[res]["available"] > 0:
                        self.graph.nodes[res]["available"] -= 1
                        if (u, v) in self.edgeItems:
                            self.scene.removeItem(self.edgeItems[(u, v)])
                            del self.edgeItems[(u, v)]
                        self.graph.remove_edge(u, v)
                        self.graph.add_edge(res, u, instances=data["instances"], type="allocation")
                        self.createOrUpdateEdge(res, u)
                        break
            self.updateEdges()
            if res in self.nodeItems and isinstance(self.nodeItems[res], ResourceItem):
                self.nodeItems[res].available = self.graph.nodes[res]["available"]
                self.nodeItems[res].updateCount()

    def detectDeadlock(self):
        # Reset edges and nodes to original appearance
        for edge in self.edgeItems.values():
            edge.mainPen = edge.original_pen  # Restore original pen
            edge.update()
        for node in self.nodeItems.values():
            if isinstance(node, (ProcessItem, ResourceItem)):
                node.setPen(node.original_pen)
        
        try:
            cycle = nx.find_cycle(self.graph, orientation="original")
            cycle_edges = [(u, v) for u, v, _ in cycle]
            cycle_nodes = set()
            for u, v in cycle_edges:
                cycle_nodes.add(u)
                cycle_nodes.add(v)
            
            # Highlight edges in the cycle
            for u, v in cycle_edges:
                edge = self.edgeItems.get((u, v))
                if edge:
                    edge.mainPen = QtGui.QPen(QtGui.QColor("#F44336"), 4)
                    edge.update()
            
            # Highlight nodes in the cycle
            highlight_pen = QtGui.QPen(QtGui.QColor("#F44336"), 3)
            for node_name in cycle_nodes:
                node = self.nodeItems.get(node_name)
                if node:
                    node.setPen(highlight_pen)
            
            QtWidgets.QMessageBox.information(self, "Deadlock", "Deadlock detected! Cycle highlighted.")
        except nx.NetworkXNoCycle:
            QtWidgets.QMessageBox.information(self, "Deadlock", "No deadlock detected.")

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

    def handleNodeMoved(self, node_item, new_pos):
        self.current_positions[node_item.name] = (new_pos.x(), new_pos.y())

    def saveState(self, description=None):
        state = {
            'graph': nx.node_link_data(self.graph),
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

    def undoAction(self):
        if len(self.undo_stack) > 1:
            current_state = self.undo_stack.pop()
            self.redo_stack.append(current_state)
            self.restoreState(self.undo_stack[-1])

    def redoAction(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append(state)
            self.restoreState(state)

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
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Graph", "", "JSON Files (*.json)")
        if path:
            data = {
                "graph": nx.node_link_data(self.graph),
                "positions": self.current_positions
            }
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            QtWidgets.QMessageBox.information(self, "Save", "Graph saved successfully.")

    def loadGraph(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Graph", "", "JSON Files (*.json)")
        if path:
            with open(path, "r") as f:
                data = json.load(f)
            self.saveState(description="Load graph")
            self.graph = nx.node_link_graph(data["graph"])
            self.current_positions = data["positions"]
            
            for item in list(self.nodeItems.values()):
                self.scene.removeItem(item)
            for item in list(self.edgeItems.values()):
                self.scene.removeItem(item)
            self.nodeItems.clear()
            self.edgeItems.clear()
            
            for n, attr in self.graph.nodes(data=True):
                if attr.get("type") == "process":
                    item = ProcessItem(n)
                else:
                    item = ResourceItem(n, attr.get("instances", 1))
                    item.available = attr.get("available", attr.get("instances", 1))
                    item.updateCount()
                self.scene.addItem(item)
                self.nodeItems[n] = item
                if n in self.current_positions:
                    x, y = self.current_positions[n]
                    item.setPos(x, y)
            
            for u, v, data in self.graph.edges(data=True):
                self.createOrUpdateEdge(u, v)
            
            self.updateEdges()
            QtWidgets.QMessageBox.information(self, "Load", "Graph loaded successfully.")

    def renameNode(self, node_item):
        dialog = CustomInputDialog("Rename Node", "New name:", self, "text")
        dialog.input.setText(node_item.name)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            new_name = dialog.getText()
            if new_name and new_name != node_item.name:
                if new_name in self.graph.nodes:
                    QtWidgets.QMessageBox.warning(self, "Error", "Name already exists!")
                    return
                self.saveState(description=f"Rename {node_item.name} to {new_name}")
                old_name = node_item.name
                self.graph = nx.relabel_nodes(self.graph, {old_name: new_name})
                self.nodeItems[new_name] = self.nodeItems.pop(old_name)
                self.current_positions[new_name] = self.current_positions.pop(old_name)
                node_item.name = new_name
                node_item.text.setPlainText(new_name)
                node_item.updateTextPosition()
                self.updateEdges()

    def removeNode(self, node_item):
        node_name = node_item.name
        self.saveState(description=f"Remove node {node_name}")
        self.graph.remove_node(node_name)
        self.scene.removeItem(node_item)
        del self.nodeItems[node_name]
        del self.current_positions[node_name]
        for key in list(self.edgeItems.keys()):
            if node_name in key:
                self.scene.removeItem(self.edgeItems[key])
                del self.edgeItems[key]
        self.updateEdges()

    def zoomIn(self):
        self.view.scale(self.view.zoom_in_factor, self.view.zoom_in_factor)
        self.updateEdges()

    def zoomOut(self):
        self.view.scale(1 / self.view.zoom_in_factor, 1 / self.view.zoom_in_factor)
        self.updateEdges()

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
