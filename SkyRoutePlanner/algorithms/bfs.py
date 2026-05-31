from collections import deque


def bfs(grafo, start_id):
    """Perform breadth-first search starting from a vertex identifier."""
    visited = set()
    order = []

    start = grafo.obtener_vertice(start_id)
    if start is None:
        return order

    queue = deque([start])
    visited.add(start_id)

    while queue:
        vertex = queue.popleft()
        order.append(vertex.identificador)

        for arista in vertex.adyacencias:
            destino = arista.vertice_destino
            if destino.identificador not in visited:
                visited.add(destino.identificador)
                queue.append(destino)

    return order
