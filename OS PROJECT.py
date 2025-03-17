import sys
import math
import json
import copy
import networkx as nx
from PyQt5 import QtWidgets, QtGui, QtCore

# --- Node Items ---

class ProcessItem(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, name, radius=30):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.name = name
        self.radius = radius
        # Sea blue for process nodes
        self.setBrush(QtGui.QColor("#2E8BC0"))
        self.setPen(QtGui.QPen(QtGui.QColor("#455A64"), 2))
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable | 
                      QtWidgets.QGraphicsItem.ItemIsSelectable)
        # Add text label
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

class ResourceItem(QtWidgets.QGraphicsRectItem):
    def __init__(self, name, instances, radius=30):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.name = name
        self.instances = instances
        self.available = instances
        self.radius = radius
        # Orange for resource nodes
        self.setBrush(QtGui.QColor("#FFA500"))
        self.setPen(QtGui.QPen(QtGui.QColor("#455A64"), 2))
        self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable | 
                      QtWidgets.QGraphicsItem.ItemIsSelectable)
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

# --- Edge Item ---

class EdgeItem(QtWidgets.QGraphicsPathItem):
    def __init__(self, source, dest, instances, edge_type, color):
        super().__init__()
        self.source = source
        self.dest = dest
        self.instances = instances
        self.edge_type = edge_type  # "allocation" or "request"
        self.arrowSize = 10
        self.color = QtGui.QColor(color)
        pen = QtGui.QPen(self.color, 2)
        self.setPen(pen)
        self.setZValue(-1)
        self.adjust()
    
    def adjust(self):
        path = QtGui.QPainterPath()
        path.moveTo(self.source.scenePos())
        path.lineTo(self.dest.scenePos())
        self.setPath(path)
    
    def paint(self, painter, option, widget=None):
        self.adjust()
        painter.setPen(self.pen())
        painter.drawPath(self.path())
        # Draw arrowhead at destination.
        line = QtCore.QLineF(self.source.scenePos(), self.dest.scenePos())
        if line.length() == 0:
            return
        angle = math.acos(line.dx() / line.length())
        if line.dy() >= 0:
            angle = (2 * math.pi) - angle
        arrowP1 = self.dest.scenePos() + QtCore.QPointF(math.sin(angle - math.pi/3) * self.arrowSize,
                                                         math.cos(angle - math.pi/3) * self.arrowSize)
        arrowP2 = self.dest.scenePos() + QtCore.QPointF(math.sin(angle - math.pi + math.pi/3) * self.arrowSize,
                                                         math.cos(angle - math.pi + math.pi/3) * self.arrowSize)
        arrowHead = QtGui.QPolygonF([self.dest.scenePos(), arrowP1, arrowP2])
        painter.setBrush(self.color)
        painter.drawPolygon(arrowHead)
        # Draw instance count if more than one.
        if self.instances > 1:
            mid = (self.source.scenePos() + self.dest.scenePos()) / 2
            painter.setFont(QtGui.QFont("Segoe UI", 9))
            painter.drawText(mid, str(self.instances))

# --- Main Window ---

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Resource Allocation Graph Simulator")
        self.resize(1000, 800)
        # Sleek light/dark color palette
        self.setStyleSheet("""
            QMainWindow { background-color: #2C3E50; }
            QToolBar { background: #34495E; spacing: 10px; }
            QToolButton { background: #4A90E2; color: white; border: none; padding: 6px 12px; border-radius: 6px; }
            QToolButton:hover { background: #357ABD; }
            QGraphicsView { background-color: #ECEFF1; border: none; }
            QScrollBar:vertical { background: #2C3E50; width: 14px; margin: 0px; border-radius: 7px; }
            QScrollBar::handle:vertical { background: #4A90E2; min-height: 20px; border-radius: 7px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { background: none; }
            QScrollBar:horizontal { background: #2C3E50; height: 14px; margin: 0px; border-radius: 7px; }
            QScrollBar::handle:horizontal { background: #4A90E2; min-width: 20px; border-radius: 7px; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { background: none; }
        """)
        self.scene = QtWidgets.QGraphicsScene()
        self.view = QtWidgets.QGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        self.createToolBar()
        self.graph = nx.DiGraph()
        self.nodeItems = {}  # node name -> NodeItem
        self.edgeItems = {}  # (u, v) -> EdgeItem
        self.undo_stack = []
        self.redo_stack = []
        self.autoNodes = {}  # node name -> True/False
        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.resizeEvent = self.onViewResize

    def createToolBar(self):
        toolbar = QtWidgets.QToolBar()
        # Place toolbar on the right side.
        self.addToolBar(QtCore.Qt.RightToolBarArea, toolbar)
        actions = [
            ("Add Process", self.addProcess),
            ("Add Resource", self.addResource),
            ("Request", self.requestResource),
            ("Release", self.releaseResource),
            ("Detect Deadlock", self.detectDeadlock),
            ("Undo", self.undoAction),
            ("Redo", self.redoAction),
            ("Save Graph", self.saveGraph),
            ("Load Graph", self.loadGraph)
        ]
        for text, slot in actions:
            action = QtWidgets.QAction(text, self)
            action.triggered.connect(slot)
            toolbar.addAction(action)

    def onViewResize(self, event):
        self.updateLayout()
        QtWidgets.QGraphicsView.resizeEvent(self.view, event)

    def updateLayout(self):
        """
        Automatically reposition nodes:
          - Resources in the top region,
          - Processes in the bottom region,
          - Waiting processes (with a request edge) under their requested resource.
        """
        viewRect = self.view.viewport().rect()
        width = viewRect.width()
        height = viewRect.height()
        margin_x = 50
        margin_y = 50

        # Resources: top 30%
        resourceY = margin_y + (height * 0.3 - margin_y) / 2
        resources = sorted([n for n, attr in self.graph.nodes(data=True) if attr.get("type") == "resource"])
        rcount = len(resources)
        for i, node in enumerate(resources):
            if self.autoNodes.get(node, True):
                x = margin_x + (width - 2 * margin_x) * (i + 1) / (rcount + 1)
                self.nodeItems[node].setPos(x, resourceY)
        # Waiting processes: those with a request edge.
        waiting = {}
        for node in self.graph.nodes:
            if self.graph.nodes[node]["type"] == "process":
                for u, v, data in self.graph.edges(node, data=True):
                    if data.get("type") == "request":
                        waiting.setdefault(v, []).append(node)
                        break
        waitingOffset = 60
        for resource, procList in waiting.items():
            procList.sort()
            rpos = self.nodeItems[resource].pos() if resource in self.nodeItems else QtCore.QPointF(margin_x, margin_y)
            for i, proc in enumerate(procList):
                x = rpos.x() + (i - (len(procList) - 1) / 2) * 40
                y = rpos.y() + waitingOffset
                self.nodeItems[proc].setPos(x, y)
                self.autoNodes[proc] = True
        # Non-waiting processes: grid in bottom region.
        nonWaiting = [n for n in self.graph.nodes if self.graph.nodes[n]["type"] == "process" and
                      not any(data.get("type") == "request" for u, v, data in self.graph.edges(n, data=True))]
        pcount = len(nonWaiting)
        if pcount > 0:
            startY = height * 0.4
            endY = height - margin_y
            availHeight = endY - startY
            desiredSpacing = 100
            columns = max(1, int((width - 2 * margin_x) // desiredSpacing))
            rows = (pcount + columns - 1) // columns
            rowSpacing = availHeight / rows if rows > 0 else availHeight
            for idx, node in enumerate(nonWaiting):
                if self.autoNodes.get(node, True):
                    col = idx % columns
                    row = idx // columns
                    x = margin_x + (width - 2 * margin_x) * (col + 0.5) / columns
                    y = startY + rowSpacing * (row + 0.5)
                    self.nodeItems[node].setPos(x, y)
        self.updateEdges()

    def updateEdges(self):
        for edge in self.edgeItems.values():
            edge.adjust()
            edge.update()

    def updateGraphView(self):
        self.scene.update()

    def addProcess(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Add Process", "Enter process name:")
        if ok and name:
            if name in self.graph.nodes:
                QtWidgets.QMessageBox.warning(self, "Error", "Process already exists!")
                return
            self.saveState()
            self.graph.add_node(name, type="process", instances=1)
            procItem = ProcessItem(name)
            self.scene.addItem(procItem)
            self.autoNodes[name] = True
            self.nodeItems[name] = procItem
            self.updateLayout()

    def addResource(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Add Resource", "Enter resource name:")
        if ok and name:
            if name in self.graph.nodes:
                QtWidgets.QMessageBox.warning(self, "Error", "Resource already exists!")
                return
            inst, ok2 = QtWidgets.QInputDialog.getInt(self, "Resource Instances", "Enter number of instances:", min=1)
            if not ok2:
                return
            self.saveState()
            self.graph.add_node(name, type="resource", instances=inst, available=inst)
            resItem = ResourceItem(name, inst)
            self.scene.addItem(resItem)
            self.autoNodes[name] = True
            self.nodeItems[name] = resItem
            self.updateLayout()

    def requestResource(self):
        proc, ok = QtWidgets.QInputDialog.getText(self, "Request Resource", "Enter process name:")
        if not (ok and proc):
            return
        res, ok2 = QtWidgets.QInputDialog.getText(self, "Request Resource", "Enter resource name:")
        if not (ok2 and res):
            return
        amt, ok3 = QtWidgets.QInputDialog.getInt(self, "Instances", "Request amount:", min=1)
        if not ok3:
            return
        if res not in self.graph.nodes or self.graph.nodes[res].get("type") != "resource":
            QtWidgets.QMessageBox.warning(self, "Error", "Invalid resource!")
            return
        self.saveState()
        if self.graph.nodes[res]["available"] >= amt:
            self.graph.nodes[res]["available"] -= amt
            self.graph.add_edge(res, proc, instances=amt, type="allocation")
        else:
            self.graph.add_edge(proc, res, instances=amt, type="request")
        self.createOrUpdateEdge(res, proc)
        self.updateLayout()
        if res in self.nodeItems and isinstance(self.nodeItems[res], ResourceItem):
            self.nodeItems[res].available = self.graph.nodes[res]["available"]
            self.nodeItems[res].updateCount()

    def releaseResource(self):
        proc, ok = QtWidgets.QInputDialog.getText(self, "Release Resource", "Enter process name:")
        if not (ok and proc):
            return
        res, ok2 = QtWidgets.QInputDialog.getText(self, "Release Resource", "Enter resource name:")
        if not (ok2 and res):
            return
        amt, ok3 = QtWidgets.QInputDialog.getInt(self, "Instances", "Release amount:", min=1)
        if not ok3:
            return
        if not self.graph.has_edge(res, proc):
            QtWidgets.QMessageBox.warning(self, "Error", "No allocation found!")
            return
        self.saveState()
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
                    self.graph.remove_edge(u, v)
                    self.graph.add_edge(res, u, instances=data["instances"], type="allocation")
                    self.createOrUpdateEdge(res, u)
                    break
        self.updateLayout()
        if res in self.nodeItems and isinstance(self.nodeItems[res], ResourceItem):
            self.nodeItems[res].available = self.graph.nodes[res]["available"]
            self.nodeItems[res].updateCount()

    def detectDeadlock(self):
        try:
            cycle = nx.find_cycle(self.graph, orientation="original")
            for u, v, d in cycle:
                if (u, v) in self.edgeItems:
                    # Highlight deadlock edges in red.
                    self.edgeItems[(u, v)].setPen(QtGui.QPen(QtGui.QColor("#F44336"), 3))
            QtWidgets.QMessageBox.information(self, "Deadlock", "Deadlock detected! Cycle highlighted.")
        except nx.NetworkXNoCycle:
            QtWidgets.QMessageBox.information(self, "Deadlock", "No deadlock detected.")

    def createOrUpdateEdge(self, u, v):
        if (u, v) in self.edgeItems:
            self.scene.removeItem(self.edgeItems[(u, v)])
            del self.edgeItems[(u, v)]
        if self.graph.has_edge(u, v):
            data = self.graph[u][v]
            # For allocation edges use green; for request edges use yellowish-orange.
            if data.get("type") == "allocation":
                edge_color = "#4CAF50"
            elif data.get("type") == "request":
                edge_color = "#FFC107"
            else:
                edge_color = "#FFFFFF"
            srcItem = self.nodeItems.get(u)
            destItem = self.nodeItems.get(v)
            if srcItem and destItem:
                edge = EdgeItem(srcItem, destItem, data.get("instances", 1), data.get("type"), edge_color)
                self.scene.addItem(edge)
                self.edgeItems[(u, v)] = edge

    def saveState(self):
        state = (copy.deepcopy(nx.node_link_data(self.graph)),
                 {n: [self.nodeItems[n].scenePos().x(), self.nodeItems[n].scenePos().y()] for n in self.nodeItems})
        self.undo_stack.append(state)
        self.redo_stack.clear()

    def undoAction(self):
        if self.undo_stack:
            current = (copy.deepcopy(nx.node_link_data(self.graph)),
                       {n: [self.nodeItems[n].scenePos().x(), self.nodeItems[n].scenePos().y()] for n in self.nodeItems})
            state = self.undo_stack.pop()
            self.redo_stack.append(current)
            self.restoreState(state)
        else:
            QtWidgets.QMessageBox.information(self, "Undo", "Nothing to undo.")

    def redoAction(self):
        if self.redo_stack:
            current = (copy.deepcopy(nx.node_link_data(self.graph)),
                       {n: [self.nodeItems[n].scenePos().x(), self.nodeItems[n].scenePos().y()] for n in self.nodeItems})
            state = self.redo_stack.pop()
            self.undo_stack.append(current)
            self.restoreState(state)
        else:
            QtWidgets.QMessageBox.information(self, "Redo", "Nothing to redo.")

    def restoreState(self, state):
        graph_data, positions = state
        self.graph = nx.node_link_graph(graph_data)
        for n, pos in positions.items():
            if n in self.nodeItems:
                self.nodeItems[n].setPos(QtCore.QPointF(pos[0], pos[1]))
        self.updateEdges()
        self.view.viewport().update()

    def saveGraph(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Graph", "", "JSON Files (*.json)")
        if path:
            data = {
                "graph": nx.node_link_data(self.graph),
                "positions": {n: [self.nodeItems[n].scenePos().x(), self.nodeItems[n].scenePos().y()] for n in self.nodeItems}
            }
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            QtWidgets.QMessageBox.information(self, "Save", "Graph saved successfully.")

    def loadGraph(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Load Graph", "", "JSON Files (*.json)")
        if path:
            with open(path, "r") as f:
                data = json.load(f)
            self.saveState()
            self.graph = nx.node_link_graph(data["graph"])
            pos_data = data["positions"]
            for item in self.nodeItems.values():
                self.scene.removeItem(item)
            for item in self.edgeItems.values():
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
                if n in pos_data:
                    x, y = pos_data[n]
                    item.setPos(x, y)
                else:
                    item.setPos(100, 100)
                self.autoNodes[n] = True
            self.updateEdges()
            self.view.viewport().update()
            QtWidgets.QMessageBox.information(self, "Load", "Graph loaded successfully.")

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
