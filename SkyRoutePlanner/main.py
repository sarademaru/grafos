from models.grafo import Grafo
from utils.json_loader import load_airports
from algorithms import bfs, dfs, dijkstra, bellman_ford, itinerary_planner


def build_sample_graph():
    """Build a sample graph using example airport codes and weights."""
    graph = Grafo()
    graph.agregar_arista("JFK", "LAX", peso=2475)
    graph.agregar_arista("LAX", "JFK", peso=2475)
    graph.agregar_arista("JFK", "ORD", peso=740)
    graph.agregar_arista("ORD", "LAX", peso=1744)
    return graph


def main():
    airports = load_airports()
    print(f"Loaded {len(airports)} airports")

    graph = build_sample_graph()
    print("Graph vertices:", [vertex.identificador for vertex in graph.obtener_vertices()])

    bfs_order = bfs.bfs(graph, "JFK")
    print("BFS order:", bfs_order)

    dfs_order = dfs.dfs(graph, "JFK")
    print("DFS order:", dfs_order)

    distances, previous = dijkstra.dijkstra(graph, "JFK")
    print("Dijkstra distances:", distances)

    bf_distances, bf_prev = bellman_ford.bellman_ford(graph, "JFK")
    print("Bellman-Ford distances:", bf_distances)

    routes = itinerary_planner.plan_itinerary(graph, "JFK", "LAX")
    print("Itineraries from JFK to LAX:", routes)


if __name__ == "__main__":
    main()
