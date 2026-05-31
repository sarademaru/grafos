import json
from pathlib import Path


def load_airports(json_path=None):
    """Load airport definitions from a JSON data file."""
    if json_path is None:
        json_path = Path(__file__).resolve().parents[1] / "data" / "aeropuertos.json"

    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)
