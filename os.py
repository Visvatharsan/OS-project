import networkx as nx
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
from PIL import Image, ImageTk

class ResourceAllocationSimulator:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.root = tk.Tk()
        self.root.title("Resource Allocation Graph Simulator")
        self.root.geometry("800x600")
        self.create_ui()
    
    def create_ui(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.frame, width=600, height=400, bg="white")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        self.control_frame = tk.Frame(self.root, bg="lightgray")
        self.control_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        buttons = [
            ("Add Process", self.add_process),
            ("Add Resource", self.add_resource),
            ("Request Resource", self.request_resource),
            ("Release Resource", self.release_resource),
            ("Detect Deadlock", self.detect_deadlock)
        ]
        
        for text, command in buttons:
            btn = ttk.Button(self.control_frame, text=text, command=command)
            btn.pack(side=tk.LEFT, padx=5, pady=5)
    
    def add_process(self):
        process = simpledialog.askstring("Input", "Enter process name:")
        if process:
            if process in self.graph.nodes:
                messagebox.showwarning("Warning", "Process already exists!")
            else:
                self.graph.add_node(process, type='process')
                self.draw_graph()
                messagebox.showinfo("Success", f"Process '{process}' added successfully!")
    
    def add_resource(self):
        resource = simpledialog.askstring("Input", "Enter resource name:")
        if resource:
            if resource in self.graph.nodes:
                messagebox.showwarning("Warning", "Resource already exists!")
            else:
                self.graph.add_node(resource, type='resource')
                self.draw_graph()
                messagebox.showinfo("Success", f"Resource '{resource}' added successfully!")
    
    def request_resource(self):
        process = simpledialog.askstring("Input", "Enter process name:")
        resource = simpledialog.askstring("Input", "Enter resource name:")
        if process in self.graph.nodes and resource in self.graph.nodes:
            self.graph.add_edge(process, resource)
            self.draw_graph()
            messagebox.showinfo("Success", f"Process '{process}' requested resource '{resource}'.")
        else:
            messagebox.showerror("Error", "Invalid process or resource name.")
    
    def release_resource(self):
        process = simpledialog.askstring("Input", "Enter process name:")
        resource = simpledialog.askstring("Input", "Enter resource name:")
        if self.graph.has_edge(process, resource):
            self.graph.remove_edge(process, resource)
            self.draw_graph()
            messagebox.showinfo("Success", f"Process '{process}' released resource '{resource}'.")
        else:
            messagebox.showerror("Error", "No such resource request found.")
    
    def detect_deadlock(self):
        try:
            cycle = nx.find_cycle(self.graph, orientation='original')
            messagebox.showwarning("Deadlock Detected", f"Deadlock cycle: {cycle}")
        except:
            messagebox.showinfo("No Deadlock", "No deadlock detected.")
    
    def draw_graph(self):
        plt.figure(figsize=(6, 4))
        pos = nx.spring_layout(self.graph)
        labels = {node: node for node in self.graph.nodes}
        nx.draw(self.graph, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=2000, font_size=10)
        plt.savefig("graph.png")
        plt.close()

        img = Image.open("graph.png")
        img = img.resize((600, 400), Image.Resampling.LANCZOS)  # Fix applied
        self.graph_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(300, 200, image=self.graph_img)
        self.canvas.update_idletasks()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    simulator = ResourceAllocationSimulator()
    simulator.run()
