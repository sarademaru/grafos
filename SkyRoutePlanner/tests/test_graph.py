from models.grafo import Grafo


def test_graph_add_vertices_and_edges():
    graph = Grafo()
    graph.agregar_arista("A", "B", peso=5)
    assert graph.obtener_vertice("A") is not None
    assert graph.obtener_vertice("B") is not None
    assert len(graph.obtener_vertice("A").adyacencias) == 1
    assert graph.obtener_vertice("A").adyacencias[0].getPeso() == 5


if __name__ == "__main__":
    test_graph_add_vertices_and_edges()
    print("All graph tests passed.")
