# Resource Allocation Graph Simulator - Executable Version

This is the executable version of the Resource Allocation Graph Simulator, a visual tool for simulating and detecting deadlocks in operating systems resource allocation.

## Installation

No installation is required. Simply download and run the executable file.

## Running the Application

1. Navigate to the `dist` folder
2. Double-click on `Resource_Allocation_Graph_Simulator.exe` to launch the application

## Features

- **Visual Graph Editor**: Create and manipulate processes and resources with an intuitive interface
- **Resource Management**: Specify multiple instances for resources
- **Allocation Simulation**: Request and allocate resources between processes
- **Deadlock Detection**: Automatically detect and highlight deadlock situations
- **Safe Sequence Finding**: Calculate safe execution orders to avoid deadlocks
- **History Tracking**: View and track all actions performed in the simulator
- **Multiple Themes**: Choose between Default, Dark, and Light themes
- **Zoom and Pan**: Navigate complex graphs with ease
- **Undo/Redo**: Revert or reapply changes as needed
- **Save/Load**: Persist your graphs as JSON files

## Usage Guide

### Basic Operations

- **Adding Nodes**:
  - Click "Add Process" to add a process node
  - Click "Add Resource" to add a resource node with specified instances

- **Creating Edges**:
  - Click "Request" to create a resource request
  - Resources are allocated automatically if available, otherwise a request edge is created

- **Releasing Resources**:
  - Click "Release" to free previously allocated resources
  - Freed resources may be automatically allocated to pending requests

- **Auto Layout**:
  - Arrange nodes automatically for better visibility

- **Deadlock Detection**:
  - Click "Detect Deadlock" to check for deadlocks
  - If found, deadlocked nodes and edges will be highlighted in red
  - If no deadlock exists, a safe execution sequence will be displayed

### Keyboard Shortcuts

- **Ctrl+S**: Save graph
- **Ctrl+O**: Open graph
- **Ctrl+Z**: Undo
- **Ctrl+Y**: Redo
- **Ctrl+P**: Add process
- **Ctrl+R**: Add resource
- **Delete**: Remove selected items
- **Ctrl+0**: Reset zoom

### Navigation

- **Mouse Wheel**: Zoom in/out
- **Middle Mouse Button**: Pan the view

## Troubleshooting

If the application fails to start:

1. Make sure you have the Microsoft Visual C++ Redistributable installed
2. Try running the application as administrator
3. Check that your antivirus is not blocking the application

## License

This software is provided for educational purposes. 