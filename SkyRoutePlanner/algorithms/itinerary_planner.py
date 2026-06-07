from dataclasses import dataclass
from email.mime import text
from heapq import heappop, heappush
from itertools import count
""" Itinerary Planner : This module provides functions to plan travel itineraries 
based on a graph of locations and transportation options.
 It includes algorithms to find routes that maximize 
 the number of destinations visited within given budget and 
 time constraints, as well as optimized routes based on specific 
 criteria such as cost, time, or distance. The planner can handle 
 various transportation modes and allows for flexible route planning 
 with or without secondary locations. """

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
    """Normalizes text for consistent comparison (e.g., transport types)."""
    return str(value).strip().lower()


def _is_secondary(vertex):
    """Determines if a vertex is considered secondary (e.g., a hub or transit point)."""
    return not getattr(vertex, "es_hub", False)


def _transport_matches(route_transport, selected_transport):
    """Checks if a route's transport matches the selected transport, allowing for partial matches."""
    route = _normalize_text(route_transport)
    selected = _normalize_text(selected_transport)
    return route == selected or route in selected or selected in route


def _allowed_transports_for_edge(grafo, edge, selected_transports):
    """Determines which transports are allowed for a given edge based on the selected transports."""
    edge_transports = edge.aeronaves or grafo.obtener_aeronaves_disponibles()
    if not edge_transports:
        edge_transports = ["Transporte"]

    return [
        route_transport
        for route_transport in edge_transports
        if any(_transport_matches(route_transport, selected) for selected in selected_transports)
    ]


def _build_leg(grafo, origin_id, edge, transport):
    """Builds a RouteLeg object for a given edge and transport, calculating distance, cost, and time."""
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
    """Formats a list of RouteLegs into a human-readable itinerary with cumulative totals."""
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
    """Summarizes a route by calculating total cost, time, distance, and transports used."""
    return {
        "path": list(path),
        "legs": list(legs),
        "total_cost": sum(leg.cost for leg in legs),
        "total_time": sum(leg.time for leg in legs),
        "total_distance": sum(leg.distance for leg in legs),
        "transports_used": sorted({leg.transport for leg in legs}),
        "formatted_legs": _format_route(legs),
    }


def _visit_route_priority(route, tie_breaker=CRITERION_COST):
    """Determines the priority of a route for comparison, based on the number of destinations and tie-breaking criteria."""
    destinations = len(route["path"]) - 1
    if tie_breaker == CRITERION_TIME:
        return (destinations, -route["total_time"], -route["total_cost"])
    return (destinations, -route["total_cost"], -route["total_time"])


def _better_visit_route(candidate, current, tie_breaker=CRITERION_COST):
    """Determines if a candidate route is better than the current best route based on priority."""
    if current is None:
        return True

    return _visit_route_priority(candidate, tie_breaker) > _visit_route_priority(current, tie_breaker)


def _transport_requirement_met(selected_transports, used_transports):
    """Checks if all selected transports are represented in the used transports for a route."""
    for selected in selected_transports:
        if not any(_transport_matches(used, selected) for used in used_transports):
            return False
    return True


def _candidate_edges(grafo, current_id, selected_transports, include_secondary):
    """Generates candidate edges from the current vertex, filtering by selected transports and secondary status."""
    current_vertex = grafo.obtener_vertice(current_id)
    if current_vertex is None:
        return

    for edge in current_vertex.adyacencias:
        neighbor = edge.vertice_destino
        if not include_secondary and _is_secondary(neighbor):
            continue

        for transport in _allowed_transports_for_edge(grafo, edge, selected_transports):
            yield _build_leg(grafo, current_id, edge, transport)

    """Finds the route that maximizes the number of destinations visited within a given cost or time limit."""
def _find_max_destinations_route(
    grafo,
    origin_id,
    limit_value,
    limit_type,
    selected_transports,
    include_secondary=True,
    require_all_selected_transports=True,
    destination_id=None,
    max_cost=None,
    max_time=None,
):
    best = None
    tie_breaker = CRITERION_TIME if limit_type == CRITERION_TIME else CRITERION_COST
    cost_limit = limit_value if limit_type == CRITERION_COST else max_cost
    time_limit = limit_value if limit_type == CRITERION_TIME else max_time



    def backtrack(current_id, visited, path, legs, total_cost, total_time, used_transports):
        """Backtracking function to explore routes recursively, updating the best route found based on the number of destinations and tie-breaking criteria."""
        nonlocal best

        if destination_id is None or current_id == destination_id:
            if not require_all_selected_transports or _transport_requirement_met(selected_transports, used_transports):
                candidate = _route_summary(path, legs)
                if _better_visit_route(candidate, best, tie_breaker):
                    best = candidate
        """Explore candidate edges from the current vertex, recursively backtracking to find the best route."""
        for leg in _candidate_edges(grafo, current_id, selected_transports, include_secondary):
            if leg.destination in visited:
                continue

            next_cost = total_cost + leg.cost
            next_time = total_time + leg.time
            if cost_limit is not None and next_cost > cost_limit:
                continue
            if time_limit is not None and next_time > time_limit:
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

    """Start backtracking from the origin vertex, initializing the visited set, path, legs, total cost, total time, and used transports."""
    backtrack(origin_id, {origin_id}, [origin_id], [], 0, 0, set())
    return best



def _criterion_weight(leg, criterion):
    """Calculates the weight of a route leg based on the specified criterion (distance, time, or cost)."""
    if criterion == CRITERION_TIME:
        return leg.time
    if criterion == CRITERION_COST:
        return leg.cost
    return leg.distance


"""Finds the best route from origin to destination 
based on a specific criterion (distance, time, or cost) 
using a modified Dijkstra's algorithm that considers multiple
 labels for each vertex to handle different combinations of cost and time."""
def find_best_route_by_criterion(
    grafo,
    origin_id,
    destination_id,
    criterion,
    selected_transports,
    include_secondary=True,
    budget=None,
    available_time=None,
):
    if not grafo.obtener_vertice(origin_id) or not grafo.obtener_vertice(destination_id):
        return None
  
  
    labels_by_vertex = {vertex.identificador: [] for vertex in grafo.obtener_vertices()}
    origin_label = {
        "weight": 0,
        "cost": 0,
        "time": 0,
        "path": (origin_id,),
        "legs": (),
    }
    labels_by_vertex[origin_id].append(origin_label)
    sequence = count()
    heap = [(0, 0, 0, next(sequence), origin_id, origin_label)]



    def is_dominated(candidate, labels):
        """Checks if a candidate label is dominated by any existing labels for the same vertex, meaning it is worse in terms of weight, cost, and time."""
        for label in labels:
            if (
                label["weight"] <= candidate["weight"]
                and label["cost"] <= candidate["cost"]
                and label["time"] <= candidate["time"]
            ):
                return True
        return False

    while heap:
        current_weight, current_cost, current_time, _, current_id, current_label = heappop(heap)
        if current_label not in labels_by_vertex[current_id]:
            continue
        if current_id == destination_id:
            return _route_summary(current_label["path"], current_label["legs"])

        for leg in _candidate_edges(grafo, current_id, selected_transports, include_secondary):
            if leg.destination in current_label["path"]:
                continue

            next_cost = current_cost + leg.cost
            next_time = current_time + leg.time
            if budget is not None and next_cost > budget:
                continue
            if available_time is not None and next_time > available_time:
                continue

            next_weight = current_weight + _criterion_weight(leg, criterion)
            candidate = {
                "weight": next_weight,
                "cost": next_cost,
                "time": next_time,
                "path": current_label["path"] + (leg.destination,),
                "legs": current_label["legs"] + (leg,),
            }
            destination_labels = labels_by_vertex.get(leg.destination, [])
            if is_dominated(candidate, destination_labels):
                continue

            labels_by_vertex[leg.destination] = [
                label
                for label in destination_labels
                if not (
                    candidate["weight"] <= label["weight"]
                    and candidate["cost"] <= label["cost"]
                    and candidate["time"] <= label["time"]
                )
            ]
            labels_by_vertex[leg.destination].append(candidate)
            heappush(heap, (next_weight, next_cost, next_time, next(sequence), leg.destination, candidate))

    if origin_id == destination_id:
        return _route_summary([origin_id], [])
    return None


"""Public functions to plan itineraries based on the graph, including basic itineraries that maximize destinations within budget and time constraints, and optimized routes based on specific criteria."""
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
            require_all_selected_transports=False,
            destination_id=destination_id,
            max_time=available_time,
        ),
        "max_destinations_by_time": _find_max_destinations_route(
            grafo=grafo,
            origin_id=origin_id,
            limit_value=available_time,
            limit_type=CRITERION_TIME,
            selected_transports=selected_transports,
            include_secondary=include_secondary,
            require_all_selected_transports=False,
            destination_id=destination_id,
            max_cost=budget,
        ),
    }


"""Finds the best routes from origin to destination based on multiple criteria (distance, time, cost) and returns a dictionary of optimized routes for each criterion."""
def plan_routes_by_criteria(
    grafo,
    origin_id,
    destination_id,
    criteria,
    selected_transports,
    include_secondary=True,
    budget=None,
    available_time=None,
):
    return {
        criterion: find_best_route_by_criterion(
            grafo=grafo,
            origin_id=origin_id,
            destination_id=destination_id,
            criterion=criterion,
            selected_transports=selected_transports,
            include_secondary=include_secondary,
            budget=budget,
            available_time=available_time,
        )
        for criterion in criteria
    }

"""Main function to plan itineraries, combining basic itineraries that maximize destinations with optimized routes based on specific criteria, and returning a comprehensive itinerary plan."""
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
        budget=budget,
        available_time=available_time,
    )

    return {
        "basic": basic,
        "optimized": optimized,
    }
