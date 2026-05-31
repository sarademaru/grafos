from math import inf


def bellman_ford(grafo, start_id):
    """Compute shortest paths from start_id using Bellman-Ford algorithm."""
    distances = {vertex_id: inf for vertex_id in grafo.vertices}
    previous = {vertex_id: None for vertex_id in grafo.vertices}
    distances[start_id] = 0

    for _ in range(len(grafo.vertices) - 1):
        updated = False
        for vertex in grafo.vertices.values():
            for arista in vertex.adyacencias:
                u = vertex.identificador
                v = arista.vertice_destino.identificador
                weight = arista.getPeso()
                if distances[u] + weight < distances[v]:
                    distances[v] = distances[u] + weight
                    previous[v] = u
                    updated = True
        if not updated:
            break

    for vertex in grafo.vertices.values():
        for arista in vertex.adyacencias:
            u = vertex.identificador
            v = arista.vertice_destino.identificador
            if distances[u] + arista.getPeso() < distances[v]:
                raise ValueError("Graph contains a negative-weight cycle")

    return distances, previous
