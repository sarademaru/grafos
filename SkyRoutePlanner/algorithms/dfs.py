def dfs(grafo, start_id):
    """Perform depth-first search starting from a vertex identifier."""
    visited = set()
    order = []

    def visit(vertex):
        visited.add(vertex.identificador)
        order.append(vertex.identificador)

        for arista in vertex.adyacencias:
            destino = arista.vertice_destino
            if destino.identificador not in visited:
                visit(destino)

    start = grafo.obtener_vertice(start_id)
    if start is None:
        return order

    visit(start)
    return order
