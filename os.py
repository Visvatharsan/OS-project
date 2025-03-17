import networkx as nx
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from PIL import Image, ImageTk

class EnhancedResourceAllocationSimulator:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.node_positions = {}
        self.selected_node = None
        self.undo_stack = []
        self.redo_stack = []
        
        # Grid positioning settings
        self.grid_x = 100
        self.grid_y = 100
        self.grid_spacing = 150
        
        self.root = tk.Tk()
        self.root.title("Enhanced Resource Allocation Graph Simulator")
        self.root.geometry("1000x800")
        self.create_enhanced_ui()
    
    def create_enhanced_ui(self):
        # Configure main window style
        self.root.configure(bg="#f0f0f0")
        style = ttk.Style()
        style.theme_use("clam")
        
        # Create main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(main_frame, bg="white", width=900, height=600)
        hscroll = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        vscroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hscroll.set, yscrollcommand=vscroll.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Create control panel
        control_frame = ttk.LabelFrame(self.root, text="Controls")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        controls = [
            ("Add Process", self.add_process),
            ("Add Resource", self.add_resource),
            ("Request", self.request_resource),
            ("Allocate", self.allocate_resource),
            ("Release", self.release_resource),
            ("Detect Deadlock", self.detect_deadlock),
            ("Undo", self.undo_action),
            ("Redo", self.redo_action),
            ("Save", self.save_graph),
            ("Load", self.load_graph)
        ]
        
        for text, cmd in controls:
            btn = ttk.Button(control_frame, text=text, command=cmd)
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Status bar
        self.status = ttk.Label(self.root, text="Ready", anchor=tk.W)
        self.status.pack(fill=tk.X, padx=10, pady=2)
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_node_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_release)
    
    def calculate_grid_position(self):
        # Get current number of nodes
        num_nodes = len(self.graph.nodes)
        
        # Calculate grid position
        cols_per_row = (self.canvas.winfo_width() - 200) // self.grid_spacing or 4
        col = num_nodes % cols_per_row
        row = num_nodes // cols_per_row
        
        x = self.grid_x + col * self.grid_spacing
        y = self.grid_y + row * self.grid_spacing
        
        # Reset column and move to next row if exceeding canvas width
        if x + 100 > self.canvas.winfo_width():
            x = self.grid_x
            y += self.grid_spacing
        
        return x, y
    
    def add_process(self):
        process = simpledialog.askstring("Add Process", "Enter process name:")
        if process:
            if process in self.graph.nodes:
                self.show_status("Process already exists!", "red")
            else:
                self.graph.add_node(process, type='process', instances=1)
                # Assign grid position
                x, y = self.calculate_grid_position()
                self.node_positions[process] = (x, y)
                self.update_graph()
                self.show_status(f"Process '{process}' added", "green")
    
    def add_resource(self):
        resource = simpledialog.askstring("Add Resource", "Enter resource name:")
        instances = simpledialog.askinteger("Resource Instances", "Enter number of instances:", minvalue=1)
        if resource and instances:
            if resource in self.graph.nodes:
                self.show_status("Resource already exists!", "red")
            else:
                self.graph.add_node(resource, type='resource', instances=instances, available=instances)
                # Assign grid position
                x, y = self.calculate_grid_position()
                self.node_positions[resource] = (x, y)
                self.update_graph()
                self.show_status(f"Resource '{resource}' ({instances} instances) added", "green")
    
    def request_resource(self):
        process = simpledialog.askstring("Request Resource", "Enter process name:")
        resource = simpledialog.askstring("Request Resource", "Enter resource name:")
        instances = simpledialog.askinteger("Instances", "Request amount:", minvalue=1)
        
        if all([process, resource, instances]):
            if self.graph.has_edge(process, resource):
                self.show_status("Request already exists!", "red")
                return
            
            if self.graph.nodes[resource]['available'] >= instances:
                self.graph.nodes[resource]['available'] -= instances
                self.graph.add_edge(resource, process, instances=instances, type='allocation')
                self.show_status(f"Allocated {instances} of {resource} to {process}", "green")
            else:
                self.graph.add_edge(process, resource, instances=instances, type='request')
                self.show_status(f"Requested {instances} of {resource} from {process}", "blue")
            self.update_graph()
    
    def allocate_resource(self):
        # Similar to request but inverse logic
        pass  # Implementation left for exercise
    
    def release_resource(self):
        process = simpledialog.askstring("Release Resource", "Enter process name:")
        resource = simpledialog.askstring("Release Resource", "Enter resource name:")
        instances = simpledialog.askinteger("Instances", "Release amount:", minvalue=1)
        
        if self.graph.has_edge(resource, process):
            current = self.graph[resource][process]['instances']
            if instances > current:
                self.show_status(f"Cannot release more than allocated ({current})", "red")
                return
            
            self.graph[resource][process]['instances'] -= instances
            self.graph.nodes[resource]['available'] += instances
            if self.graph[resource][process]['instances'] == 0:
                self.graph.remove_edge(resource, process)
            self.update_graph()
            self.show_status(f"Released {instances} of {resource} from {process}", "green")
    
    def detect_deadlock(self):
        try:
            cycle = nx.find_cycle(self.graph, orientation='original')
            self.highlight_cycle(cycle)
            self.show_status("Deadlock detected! Cycle highlighted.", "red")
        except nx.NetworkXNoCycle:
            self.show_status("No deadlock detected", "green")
    
    def highlight_cycle(self, cycle):
        for u, v in cycle:
            self.canvas.itemconfig(f"edge_{u}_{v}", fill="red", width=2)
    
    def update_graph(self):
        self.canvas.delete("all")
        self.draw_nodes()
        self.draw_edges()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def draw_nodes(self):
        for node in self.graph.nodes:
            node_type = self.graph.nodes[node]['type']
            x, y = self.node_positions.get(node, (100, 100))
            
            color = "#FFB3BA" if node_type == 'process' else "#BAFFC9"
            self.canvas.create_oval(x-30, y-30, x+30, y+30, fill=color, tags=("node", node))
            self.canvas.create_text(x, y, text=node, tags=("label", node))
            
            if node_type == 'resource':
                instances = self.graph.nodes[node]['instances']
                available = self.graph.nodes[node]['available']
                self.canvas.create_text(x, y+20, text=f"{available}/{instances}", tags=("count", node))
    
    def draw_edges(self):
        for u, v, data in self.graph.edges(data=True):
            x1, y1 = self.node_positions.get(u, (100, 100))
            x2, y2 = self.node_positions.get(v, (150, 150))
            
            arrow = "last" if data['type'] == 'allocation' else "first"
            color = "green" if data['type'] == 'allocation' else "blue"
            self.canvas.create_line(x1, y1, x2, y2, arrow=arrow, fill=color, width=2,
                                   tags=(f"edge_{u}_{v}", "edge"))
            if data['instances'] > 1:
                self.canvas.create_text((x1+x2)/2, (y1+y2)/2, text=data['instances'],
                                        fill=color, tags=("edge_label", f"edge_{u}_{v}"))
    
    def on_canvas_click(self, event):
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)
        if item and "node" in tags:
            self.selected_node = tags[-1]
    
    def on_node_drag(self, event):
        if self.selected_node:
            self.canvas.move(self.selected_node, event.x - self.node_positions[self.selected_node][0], 
                            event.y - self.node_positions[self.selected_node][1])
            self.node_positions[self.selected_node] = (event.x, event.y)
            self.update_graph()
    
    def on_drag_release(self, event):
        self.selected_node = None
    
    def undo_action(self):
        if self.undo_stack:
            state = self.undo_stack.pop()
            self.redo_stack.append((self.graph.copy(), self.node_positions.copy()))
            self.graph = state[0]
            self.node_positions = state[1]
            self.update_graph()
    
    def redo_action(self):
        if self.redo_stack:
            state = self.redo_stack.pop()
            self.undo_stack.append((self.graph.copy(), self.node_positions.copy()))
            self.graph = state[0]
            self.node_positions = state[1]
            self.update_graph()
    
    def save_graph(self):
        # Implement using pickle or json
        pass
    
    def load_graph(self):
        # Implement loading logic
        pass
    
    def show_status(self, message, color="black"):
        self.status.config(text=message, foreground=color)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    simulator = EnhancedResourceAllocationSimulator()
    simulator.run() 
