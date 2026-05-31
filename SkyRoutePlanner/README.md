# SkyRoute Planner

SkyRoute Planner is a university project for route analysis and airport itinerary planning using a custom graph implementation in Python. The repository is designed to support graph algorithms, itinerary backtracking, and a future PyQt6 visualization interface.

## Requirements

- Python 3.10+
- PyQt6
- pyqtgraph
- numpy
- pandas

## Installation

1. Create a virtual environment:

```bash
python -m venv .venv
```

2. Activate the environment:

Windows:
```powershell
.venv\Scripts\activate
```

Linux / macOS:
```bash
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Execution

Run the main entry point from the project root:

```bash
python main.py
```

## Project Structure

SkyRoutePlanner/
├── data/
│   └── aeropuertos.json
├── models/
│   ├── vertice.py
│   ├── arista.py
│   ├── aeropuerto.py
│   ├── aeronave.py
│   └── grafo.py
├── algorithms/
│   ├── bfs.py
│   ├── dfs.py
│   ├── dijkstra.py
│   ├── bellman_ford.py
│   └── itinerary_planner.py
├── ui/
│   ├── main_window.py
│   ├── graph_view.py
│   └── dialogs.py
├── utils/
│   ├── json_loader.py
│   └── constants.py
├── tests/
├── main.py
└── README.md

## Technologies Used

- Python 3
- PyQt6
- pyqtgraph
- NumPy
- pandas

## Notes

The graph is implemented from scratch without NetworkX or other graph frameworks to keep the core algorithmic logic explicit and educational.
