from pathlib import Path

PROJECT_ROOT = Path.cwd() / "SkyRoutePlanner"
PROJECT_STRUCTURE = {
    "data": ["aeropuertos.json"],
    "models": ["vertice.py", "arista.py", "aeropuerto.py", "aeronave.py", "grafo.py"],
    "algorithms": ["bfs.py", "dfs.py", "dijkstra.py", "bellman_ford.py", "itinerary_planner.py"],
    "ui": ["main_window.py", "graph_view.py", "dialogs.py"],
    "utils": ["json_loader.py", "constants.py"],
    "tests": ["test_graph.py"],
}

ROOT_FILES = ["main.py", "requirements.txt", "README.md"]


def create_files():
    PROJECT_ROOT.mkdir(exist_ok=True)

    for folder, files in PROJECT_STRUCTURE.items():
        folder_path = PROJECT_ROOT / folder
        folder_path.mkdir(exist_ok=True)
        for file_name in files:
            file_path = folder_path / file_name
            if not file_path.exists():
                file_path.write_text("")

    for file_name in ROOT_FILES:
        file_path = PROJECT_ROOT / file_name
        if not file_path.exists():
            file_path.write_text("")

    print(f"Project structure created under: {PROJECT_ROOT}")


if __name__ == "__main__":
    create_files()
