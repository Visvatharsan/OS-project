import networkx as nx
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk, filedialog
import json
import math

# --- Custom dialog classes that force focus using update_idletasks and focus_set ---

class CustomStringDialog(simpledialog.Dialog):
    def __init__(self, parent, title, prompt):
        self.prompt = prompt
        self.value = None
        super().__init__(parent, title)
    
    def body(self, master):
        label = tk.Label(master, text=self.prompt)
        label.pack(padx=10, pady=5)
        self.entry = tk.Entry(master)
        self.entry.pack(padx=10, pady=5)
        self.update_idletasks()  # update geometry
        self.entry.focus_set()   # force focus
        return self.entry  # initial focus

    def initial_focus(self):
        return self.entry

    def apply(self):
        self.value = self.entry.get()

class CustomIntegerDialog(simpledialog.Dialog):
    def __init__(self, parent, title, prompt, minvalue=1):
        self.prompt = prompt
        self.value = None
        self.minvalue = minvalue
        super().__init__(parent, title)
    
    def body(self, master):
        label = tk.Label(master, text=self.prompt)
        label.pack(padx=10, pady=5)
        self.entry = tk.Entry(master)
        self.entry.pack(padx=10, pady=5)
        self.update_idletasks()
        self.entry.focus_set()
        return self.entry
    
    def initial_focus(self):
        return self.entry

    def validate(self):
        try:
            val = int(self.entry.get())
            if val < self.minvalue:
                raise ValueError
            return True
        except ValueError:
            messagebox.showwarning("Invalid input", f"Please enter an integer ≥ {self.minvalue}", parent=self)
            return False

    def apply(self):
        self.value = int(self.entry.get())

# --- Main Simulator Class ---

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
    
    # Custom wrappers to use our dialogs
    def ask_string(self, title, prompt):
        d = CustomStringDialog(self.root, title, prompt)
        return d.value

    def ask_integer(self, title, prompt, minvalue=1):
        d = CustomIntegerDialog(self.root, title, prompt, minvalue)
        return d.value

    def create_enhanced_ui(self):
        self.root.configure(bg="#f0f0f0")
        style = ttk.Style()
        style.theme_use("clam")
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(main_frame, bg="white", width=900, height=600)
        hscroll = ttk.Scrollbar(main_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        vscroll = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=hscroll.set, yscrollcommand=vscroll.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vscroll.grid(row=0, column=1, sticky="ns")
        hscroll.grid(row=1, column=0, sticky="ew")
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Control buttons (including Save/Load)
        control_frame = ttk.LabelFrame(self.root, text="Controls")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        controls = [
            ("Add Process", self.add_process),
            ("Add Resource", self.add_resource),
            ("Request", self.request_resource),
            ("Release", self.release_resource),
            ("Detect Deadlock", self.detect_deadlock),
            ("Undo", self.undo_action),
            ("Redo", self.redo_action),
            ("Save Graph", self.save_graph),
            ("Load Graph", self.load_graph)
        ]
        for text, cmd in controls:
            btn = ttk.Button(control_frame, text=text, command=cmd)
            btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        self.status = ttk.Label(self.root, text="Ready", anchor=tk.W)
        self.status.pack(fill=tk.X, padx=10, pady=2)
        
        # Bind left click (for selection/drag) and right-click (for context menu)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_node_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_drag_release)
        self.canvas.bind("<Button-3>", self.on_right_click)
    
    def calculate_grid_position(self):
        num_nodes = len(self.graph.nodes)
        cols_per_row = (self.canvas.winfo_width() - 200) // self.grid_spacing or 4
        col = num_nodes % cols_per_row
        row = num_nodes // cols_per_row
        x = self.grid_x + col * self.grid_spacing
        y = self.grid_y + row * self.grid_spacing
        if x + 100 > self.canvas.winfo_width():
            x = self.grid_x
            y += self.grid_spacing
        return x, y

    def save_state(self):
        self.undo_stack.append((self.graph.copy(), self.node_positions.copy()))
        self.redo_stack.clear()
    
    def add_process(self):
        process = self.ask_string("Add Process", "Enter process name:")
        if process:
            if process in self.graph.nodes:
                self.show_status("Process already exists!", "red")
            else:
                self.save_state()
                self.graph.add_node(process, type='process', instances=1)
                x, y = self.calculate_grid_position()
                self.node_positions[process] = (x, y)
                self.update_graph()
                self.show_status(f"Process '{process}' added", "green")
    
    def add_resource(self):
        resource = self.ask_string("Add Resource", "Enter resource name:")
        if not resource:
            return
        instances = self.ask_integer("Resource Instances", "Enter number of instances:")
        if not instances:
            return
        if resource in self.graph.nodes:
            self.show_status("Resource already exists!", "red")
            return
        self.save_state()
        self.graph.add_node(resource, type='resource', instances=instances, available=instances)
        x, y = self.calculate_grid_position()
        self.node_positions[resource] = (x, y)
        self.update_graph()
        self.show_status(f"Resource '{resource}' ({instances} instances) added", "green")
    
    def request_resource(self):
        process = self.ask_string("Request Resource", "Enter process name:")
        resource = self.ask_string("Request Resource", "Enter resource name:")
        instances = self.ask_integer("Instances", "Request amount:")
        if not all([process, resource, instances]):
            return
        if resource not in self.graph.nodes or self.graph.nodes[resource].get('type') != 'resource':
            self.show_status("Invalid resource!", "red")
            return
        self.save_state()
        if self.graph.nodes[resource]['available'] >= instances:
            self.graph.nodes[resource]['available'] -= instances
            self.graph.add_edge(resource, process, instances=instances, type='allocation')
            self.show_status(f"Allocated {instances} of {resource} to {process}", "green")
        else:
            self.graph.add_edge(process, resource, instances=instances, type='request')
            self.show_status(f"Requested {instances} of {resource} from {process}", "blue")
        self.update_graph()
    
    def release_resource(self):
        process = self.ask_string("Release Resource", "Enter process name:")
        resource = self.ask_string("Release Resource", "Enter resource name:")
        instances = self.ask_integer("Instances", "Release amount:")
        if not self.graph.has_edge(resource, process):
            self.show_status("No allocation found!", "red")
            return
        self.save_state()
        current = self.graph[resource][process]['instances']
        if instances > current:
            self.show_status(f"Cannot release more than allocated ({current})", "red")
            return
        self.graph[resource][process]['instances'] -= instances
        self.graph.nodes[resource]['available'] += instances
        if self.graph[resource][process]['instances'] == 0:
            self.graph.remove_edge(resource, process)
        waiting_edges = [
            (u, v, d) for u, v, d in self.graph.edges(data=True)
            if v == resource and d.get('type') == 'request'
        ]
        if waiting_edges and self.graph.nodes[resource]['available'] > 0:
            waiting_process, _, waiting_data = waiting_edges[0]
            self.graph.nodes[resource]['available'] -= 1
            self.graph.remove_edge(waiting_process, resource)
            self.graph.add_edge(resource, waiting_process, instances=waiting_data['instances'], type='allocation', color='green')
            self.show_status(f"Released {instances} of {resource} from {process} and allocated to {waiting_process}", "green")
        else:
            self.show_status(f"Released {instances} of {resource} from {process}", "green")
        self.update_graph()
    
    def detect_deadlock(self):
        try:
            # Unpack the third element (direction) returned by find_cycle
            cycle = nx.find_cycle(self.graph, orientation='original')
            self.highlight_cycle(cycle)
            self.show_status("Deadlock detected! Cycle highlighted.", "red")
        except nx.NetworkXNoCycle:
            self.show_status("No deadlock detected", "green")
    
    def highlight_cycle(self, cycle):
        for u, v, _ in cycle:
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
            if node_type == 'resource':
                color = "#BAFFC9"
                self.canvas.create_rectangle(x-30, y-30, x+30, y+30, fill=color, tags=("node", node))
                self.canvas.create_text(x, y, text=node, tags=("label", node))
                instances = self.graph.nodes[node]['instances']
                available = self.graph.nodes[node]['available']
                self.canvas.create_text(x, y+20, text=f"{available}/{instances}", tags=("count", node))
            else:
                color = "#FFB3BA"
                self.canvas.create_oval(x-30, y-30, x+30, y+30, fill=color, tags=("node", node))
                self.canvas.create_text(x, y, text=node, tags=("label", node))
    
    def draw_edges(self):
        for u, v, data in self.graph.edges(data=True):
            x1, y1 = self.node_positions.get(u, (100, 100))
            x2, y2 = self.node_positions.get(v, (150, 150))
            arrow = "last" if data.get('type') == 'allocation' else "first"
            edge_color = data.get('color', "green" if data.get('type') == 'allocation' else "blue")
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2
            dx = x2 - x1
            dy = y2 - y1
            length = math.sqrt(dx*dx + dy*dy)
            offset = 30
            if length != 0:
                offset_x = mid_x - (dy / length) * offset
                offset_y = mid_y + (dx / length) * offset
            else:
                offset_x, offset_y = mid_x, mid_y
            self.canvas.create_line(x1, y1, offset_x, offset_y, x2, y2, smooth=True, arrow=arrow,
                                    fill=edge_color, width=2, tags=(f"edge_{u}_{v}", "edge"))
            if data.get('instances', 0) > 1:
                self.canvas.create_text(offset_x, offset_y, text=data['instances'],
                                        fill=edge_color, tags=("edge_label", f"edge_{u}_{v}"))
    
    def on_canvas_click(self, event):
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)
        if item and "node" in tags:
            self.selected_node = tags[-1]
    
    def on_node_drag(self, event):
        if self.selected_node:
            dx = event.x - self.node_positions[self.selected_node][0]
            dy = event.y - self.node_positions[self.selected_node][1]
            self.canvas.move(self.selected_node, dx, dy)
            self.node_positions[self.selected_node] = (event.x, event.y)
            self.update_graph()
    
    def on_drag_release(self, event):
        self.selected_node = None
        self.save_state()
    
    def on_right_click(self, event):
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)
        if item and "node" in tags:
            node = tags[-1]
            self.selected_node = node
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Show Details", command=lambda: self.show_node_details(node))
            if self.graph.nodes[node]['type'] == 'resource':
                menu.add_command(label="Edit Resource", command=lambda: self.edit_resource(node))
            menu.add_command(label="Delete Node", command=lambda: self.delete_node(node))
            menu.post(event.x_root, event.y_root)
    
    def show_node_details(self, node):
        details = f"Node: {node}\nType: {self.graph.nodes[node]['type']}"
        if self.graph.nodes[node]['type'] == 'resource':
            details += f"\nInstances: {self.graph.nodes[node]['instances']}\nAvailable: {self.graph.nodes[node]['available']}"
        messagebox.showinfo("Node Details", details, parent=self.root)
    
    def edit_resource(self, node):
        if self.graph.nodes[node]['type'] != 'resource':
            return
        new_instances = self.ask_integer("Edit Resource", "Enter new total instances:")
        if new_instances is not None:
            current_instances = self.graph.nodes[node]['instances']
            current_available = self.graph.nodes[node]['available']
            if new_instances < current_instances:
                new_available = min(current_available, new_instances)
            else:
                new_available = current_available + (new_instances - current_instances)
            self.save_state()
            self.graph.nodes[node]['instances'] = new_instances
            self.graph.nodes[node]['available'] = new_available
            self.update_graph()
            self.show_status(f"Resource '{node}' updated", "green")
    
    def delete_node(self, node):
        self.save_state()
        self.graph.remove_node(node)
        if node in self.node_positions:
            del self.node_positions[node]
        self.update_graph()
        self.show_status(f"Node '{node}' deleted", "blue")
    
    def undo_action(self):
        if self.undo_stack:
            self.redo_stack.append((self.graph.copy(), self.node_positions.copy()))
            state = self.undo_stack.pop()
            self.graph = state[0]
            self.node_positions = state[1]
            self.update_graph()
            self.show_status("Undo performed", "blue")
        else:
            self.show_status("Nothing to undo", "red")
    
    def redo_action(self):
        if self.redo_stack:
            self.undo_stack.append((self.graph.copy(), self.node_positions.copy()))
            state = self.redo_stack.pop()
            self.graph = state[0]
            self.node_positions = state[1]
            self.update_graph()
            self.show_status("Redo performed", "blue")
        else:
            self.show_status("Nothing to redo", "red")
    
    def save_graph(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")], parent=self.root)
        if file_path:
            data = {
                "graph": nx.node_link_data(self.graph),
                "node_positions": self.node_positions
            }
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
            self.show_status("Graph saved successfully", "green")
    
    def load_graph(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")], parent=self.root)
        if file_path:
            with open(file_path, "r") as f:
                data = json.load(f)
            self.save_state()
            self.graph = nx.node_link_graph(data["graph"])
            self.node_positions = data["node_positions"]
            self.update_graph()
            self.show_status("Graph loaded successfully", "green")
    
    def show_status(self, message, color="black"):
        self.status.config(text=message, foreground=color)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    simulator = EnhancedResourceAllocationSimulator()
    simulator.run()
