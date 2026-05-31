import heapq
from math import inf


def dijkstra(grafo, start_id):
    """Compute shortest path distances from start_id using Dijkstra's algorithm."""
    distances = {vertex_id: inf for vertex_id in grafo.vertices}
    previous = {vertex_id: None for vertex_id in grafo.vertices}
    distances[start_id] = 0

    heap = [(0, start_id)]
    while heap:
        current_distance, current_id = heapq.heappop(heap)
        if current_distance > distances[current_id]:
            continue

        current_vertex = grafo.obtener_vertice(current_id)
        if current_vertex is None:
            continue

        for arista in current_vertex.adyacencias:
            neighbor = arista.vertice_destino
            alt = current_distance + arista.getPeso()
            if alt < distances[neighbor.identificador]:
                distances[neighbor.identificador] = alt
                previous[neighbor.identificador] = current_id
                heapq.heappush(heap, (alt, neighbor.identificador))

    return distances, previous
