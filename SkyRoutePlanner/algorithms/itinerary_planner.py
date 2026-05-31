def plan_itinerary(grafo, origin_id, destination_id, max_stops=None):
    """Plan an itinerary using simple backtracking between origin and destination."""
    def backtrack(current_id, target_id, visited, path):
        if max_stops is not None and len(path) - 1 > max_stops:
            return []

        if current_id == target_id:
            return [list(path)]

        routes = []
        current_vertex = grafo.obtener_vertice(current_id)
        if current_vertex is None:
            return routes

        for arista in current_vertex.adyacencias:
            neighbor_id = arista.vertice_destino.identificador
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                path.append(neighbor_id)
                routes.extend(backtrack(neighbor_id, target_id, visited, path))
                path.pop()
                visited.remove(neighbor_id)

        return routes

    if origin_id == destination_id:
        return [[origin_id]]

    return backtrack(origin_id, destination_id, {origin_id}, [origin_id])
