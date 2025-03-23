# Resource Allocation Graph Simulator

A visual tool for simulating and detecting deadlocks in operating systems resource allocation.

![Resource Allocation Graph Simulator](https://github.com/Visvatharsan/OS-project/raw/main/screenshot.png)

## Overview

This application provides a graphical environment for creating and analyzing Resource Allocation Graphs (RAGs), which are used in operating systems to detect and prevent deadlocks among competing processes.

## Download Options

### Option 1: Source Code
Clone this repository and run the application using Python:

```bash
git clone https://github.com/Visvatharsan/OS-project.git
cd OS-project
pip install -r requirements.txt
python os.py
```

### Option 2: Executable File
Download the executable file from the [Releases](https://github.com/Visvatharsan/OS-project/releases) section. No installation required.

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

## Requirements (Source Code)

- Python 3.6+
- PyQt5
- NetworkX

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

## Understanding Resource Allocation Graphs

Resource Allocation Graphs (RAGs) are directed graphs used to detect deadlocks in operating systems:

- **Processes**: Represented as circular nodes
- **Resources**: Represented as square nodes with instance counts
- **Allocation Edges**: Directed edges from resources to processes (green)
- **Request Edges**: Directed edges from processes to resources (yellow)

Deadlocks occur when there is a circular wait - a cycle in the graph where processes are waiting for resources held by other processes in the cycle.

## Example Workflow

1. Add multiple processes (P1, P2, P3)
2. Add resources with instances (R1 with 2 instances, R2 with 1 instance)
3. Allocate one R1 to P1
4. Let P2 request R2
5. Allocate R2 to P2
6. Let P2 request remaining R1
7. Let P1 request R2
8. Run deadlock detection to identify the circular wait

## License

This software is provided for educational purposes.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 
