from dataclasses import dataclass
from heapq import heappop, heappush
from math import inf


CRITERION_DISTANCE = "distancia"
CRITERION_TIME = "tiempo"
CRITERION_COST = "costo"


@dataclass(frozen=True)
class RouteLeg:
    origin: str
    destination: str
    transport: str
    distance: float
    cost: float
    time: float


def _normalize_text(value):
    return str(value).strip().lower()


def _is_secondary(vertex):
    return not getattr(vertex, "es_hub", False)


def _transport_matches(route_transport, selected_transport):
    route = _normalize_text(route_transport)
    selected = _normalize_text(selected_transport)
    return route == selected or route in selected or selected in route


def _allowed_transports_for_edge(grafo, edge, selected_transports):
    edge_transports = edge.aeronaves or grafo.obtener_aeronaves_disponibles()
    if not edge_transports:
        edge_transports = ["Transporte"]

    return [
        route_transport
        for route_transport in edge_transports
        if any(_transport_matches(route_transport, selected) for selected in selected_transports)
    ]


def _build_leg(grafo, origin_id, edge, transport):
    distance = float(edge.distancia_km or 0)
    cost_per_km = float(grafo.obtener_costo_por_km(transport) or 0)
    time_per_km = float(grafo.obtener_tiempo_por_km(transport) or 0)
    cost = float(edge.costo_base or 0) + distance * cost_per_km
    time = distance * time_per_km

    return RouteLeg(
        origin=origin_id,
        destination=edge.vertice_destino.identificador,
        transport=transport,
        distance=distance,
        cost=cost,
        time=time,
    )


def _format_route(legs):
    lines = []
    total_cost = 0
    total_time = 0
    total_distance = 0

    for index, leg in enumerate(legs, start=1):
        total_cost += leg.cost
        total_time += leg.time
        total_distance += leg.distance
        lines.append(
            f"{index}. {leg.origin} -> {leg.destination} | {leg.transport} | "
            f"{leg.distance:.2f} km (acum. {total_distance:.2f} km) | "
            f"${leg.cost:.2f} (acum. ${total_cost:.2f}) | "
            f"{leg.time:.2f} h (acum. {total_time:.2f} h)"
        )

    return lines


def _route_summary(path, legs):
    return {
        "path": list(path),
        "legs": list(legs),
        "total_cost": sum(leg.cost for leg in legs),
        "total_time": sum(leg.time for leg in legs),
        "total_distance": sum(leg.distance for leg in legs),
        "transports_used": sorted({leg.transport for leg in legs}),
        "formatted_legs": _format_route(legs),
    }


def _better_visit_route(candidate, current, tie_breaker=CRITERION_COST):
    if current is None:
        return True

    candidate_destinations = len(candidate["path"]) - 1
    current_destinations = len(current["path"]) - 1
    if candidate_destinations != current_destinations:
        return candidate_destinations > current_destinations

    if tie_breaker == CRITERION_TIME:
        if candidate["total_time"] != current["total_time"]:
            return candidate["total_time"] < current["total_time"]
        return candidate["total_cost"] < current["total_cost"]

    if candidate["total_cost"] != current["total_cost"]:
        return candidate["total_cost"] < current["total_cost"]
    return candidate["total_time"] < current["total_time"]


def _transport_requirement_met(selected_transports, used_transports):
    for selected in selected_transports:
        if not any(_transport_matches(used, selected) for used in used_transports):
            return False
    return True


def _candidate_edges(grafo, current_id, selected_transports, include_secondary):
    current_vertex = grafo.obtener_vertice(current_id)
    if current_vertex is None:
        return

    for edge in current_vertex.adyacencias:
        neighbor = edge.vertice_destino
        if not include_secondary and _is_secondary(neighbor):
            continue

        for transport in _allowed_transports_for_edge(grafo, edge, selected_transports):
            yield _build_leg(grafo, current_id, edge, transport)


def _find_max_destinations_route(
    grafo,
    origin_id,
    limit_value,
    limit_type,
    selected_transports,
    include_secondary=True,
    require_all_selected_transports=True,
    destination_id=None,
):
    best = None
    tie_breaker = CRITERION_TIME if limit_type == CRITERION_TIME else CRITERION_COST

    def backtrack(current_id, visited, path, legs, total_cost, total_time, used_transports):
        nonlocal best

        if destination_id is None or current_id == destination_id:
            if not require_all_selected_transports or _transport_requirement_met(selected_transports, used_transports):
                candidate = _route_summary(path, legs)
                if _better_visit_route(candidate, best, tie_breaker):
                    best = candidate

        for leg in _candidate_edges(grafo, current_id, selected_transports, include_secondary):
            if leg.destination in visited:
                continue

            next_cost = total_cost + leg.cost
            next_time = total_time + leg.time
            if limit_type == CRITERION_COST and next_cost > limit_value:
                continue
            if limit_type == CRITERION_TIME and next_time > limit_value:
                continue

            visited.add(leg.destination)
            path.append(leg.destination)
            legs.append(leg)
            backtrack(
                leg.destination,
                visited,
                path,
                legs,
                next_cost,
                next_time,
                used_transports | {leg.transport},
            )
            legs.pop()
            path.pop()
            visited.remove(leg.destination)

    if not grafo.obtener_vertice(origin_id):
        return None

    backtrack(origin_id, {origin_id}, [origin_id], [], 0, 0, set())
    return best


def _criterion_weight(leg, criterion):
    if criterion == CRITERION_TIME:
        return leg.time
    if criterion == CRITERION_COST:
        return leg.cost
    return leg.distance


def find_best_route_by_criterion(
    grafo,
    origin_id,
    destination_id,
    criterion,
    selected_transports,
    include_secondary=True,
):
    if not grafo.obtener_vertice(origin_id) or not grafo.obtener_vertice(destination_id):
        return None

    distances = {vertex.identificador: inf for vertex in grafo.obtener_vertices()}
    previous = {}
    distances[origin_id] = 0
    heap = [(0, origin_id)]

    while heap:
        current_weight, current_id = heappop(heap)
        if current_weight > distances[current_id]:
            continue
        if current_id == destination_id:
            break

        for leg in _candidate_edges(grafo, current_id, selected_transports, include_secondary):
            next_weight = current_weight + _criterion_weight(leg, criterion)
            if next_weight < distances.get(leg.destination, inf):
                distances[leg.destination] = next_weight
                previous[leg.destination] = (current_id, leg)
                heappush(heap, (next_weight, leg.destination))

    if destination_id not in previous and origin_id != destination_id:
        return None

    legs = []
    current_id = destination_id
    while current_id != origin_id:
        previous_id, leg = previous[current_id]
        legs.append(leg)
        current_id = previous_id

    legs.reverse()
    return _route_summary([origin_id] + [leg.destination for leg in legs], legs)


def plan_basic_itineraries(
    grafo,
    origin_id,
    budget,
    available_time,
    selected_transports,
    include_secondary=True,
    destination_id=None,
):
    return {
        "max_destinations_by_budget": _find_max_destinations_route(
            grafo=grafo,
            origin_id=origin_id,
            limit_value=budget,
            limit_type=CRITERION_COST,
            selected_transports=selected_transports,
            include_secondary=include_secondary,
            destination_id=destination_id,
        ),
        "max_destinations_by_time": _find_max_destinations_route(
            grafo=grafo,
            origin_id=origin_id,
            limit_value=available_time,
            limit_type=CRITERION_TIME,
            selected_transports=selected_transports,
            include_secondary=include_secondary,
            destination_id=destination_id,
        ),
    }


def plan_routes_by_criteria(
    grafo,
    origin_id,
    destination_id,
    criteria,
    selected_transports,
    include_secondary=True,
):
    return {
        criterion: find_best_route_by_criterion(
            grafo=grafo,
            origin_id=origin_id,
            destination_id=destination_id,
            criterion=criterion,
            selected_transports=selected_transports,
            include_secondary=include_secondary,
        )
        for criterion in criteria
    }


def plan_itinerary(
    grafo,
    origin_id,
    destination_id,
    budget,
    available_time,
    criteria,
    selected_transports,
    include_secondary=True,
):
    basic = plan_basic_itineraries(
        grafo=grafo,
        origin_id=origin_id,
        budget=budget,
        available_time=available_time,
        selected_transports=selected_transports,
        include_secondary=include_secondary,
        destination_id=destination_id,
    )
    optimized = plan_routes_by_criteria(
        grafo=grafo,
        origin_id=origin_id,
        destination_id=destination_id,
        criteria=criteria,
        selected_transports=selected_transports,
        include_secondary=include_secondary,
    )

    return {
        "basic": basic,
        "optimized": optimized,
    }
