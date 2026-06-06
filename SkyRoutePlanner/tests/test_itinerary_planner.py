import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from algorithms.itinerary_planner import (  # noqa: E402
    CRITERION_COST,
    CRITERION_DISTANCE,
    CRITERION_TIME,
    plan_itinerary,
)
from models.grafo import Grafo  # noqa: E402


class ItineraryPlannerTest(unittest.TestCase):
    def _build_graph(self):
        graph = Grafo()
        graph.configuracion["aeronaves"] = {
            "Avion Comercial": {"costoKm": 1, "tiempoKm": 0.03},
            "Avion Regional": {"costoKm": 0.5, "tiempoKm": 0.06},
            "Helice": {"costoKm": 0.2, "tiempoKm": 0.1},
        }

        graph.agregar_vertice("A", es_hub=True)
        graph.agregar_vertice("B", es_hub=True)
        graph.agregar_vertice("C", es_hub=False)
        graph.agregar_vertice("D", es_hub=True)

        graph.agregar_arista("A", "B", 100, aeronaves=["Avion Comercial"], costo_base=0)
        graph.agregar_arista("B", "C", 80, aeronaves=["Avion Regional"], costo_base=0)
        graph.agregar_arista("C", "D", 60, aeronaves=["Helice"], costo_base=0)
        graph.agregar_arista("A", "D", 500, aeronaves=["Avion Comercial"], costo_base=0)
        graph.agregar_arista("B", "D", 120, aeronaves=["Avion Regional"], costo_base=0)
        return graph

    def test_plan_itinerary_returns_basic_and_optimized_routes(self):
        result = plan_itinerary(
            grafo=self._build_graph(),
            origin_id="A",
            destination_id="D",
            budget=200,
            available_time=20,
            criteria=[CRITERION_DISTANCE, CRITERION_TIME, CRITERION_COST],
            selected_transports=["Avion Comercial", "Avion Regional"],
            include_secondary=True,
        )

        budget_route = result["basic"]["max_destinations_by_budget"]
        self.assertEqual(budget_route["path"], ["A", "B", "D"])
        self.assertEqual(budget_route["transports_used"], ["Avion Comercial", "Avion Regional"])

        self.assertEqual(result["optimized"][CRITERION_DISTANCE]["path"], ["A", "B", "D"])
        self.assertEqual(result["optimized"][CRITERION_TIME]["path"], ["A", "B", "D"])
        self.assertEqual(result["optimized"][CRITERION_COST]["path"], ["A", "B", "D"])

    def test_excluding_secondary_airports_removes_secondary_routes(self):
        result = plan_itinerary(
            grafo=self._build_graph(),
            origin_id="A",
            destination_id="D",
            budget=200,
            available_time=20,
            criteria=[CRITERION_COST],
            selected_transports=["Avion Comercial", "Avion Regional", "Helice"],
            include_secondary=False,
        )

        self.assertNotIn("C", result["optimized"][CRITERION_COST]["path"])

    def test_basic_alternatives_require_destination_and_all_selected_transports(self):
        result = plan_itinerary(
            grafo=self._build_graph(),
            origin_id="A",
            destination_id="D",
            budget=200,
            available_time=20,
            criteria=[CRITERION_COST],
            selected_transports=["Avion Comercial", "Avion Regional", "Helice"],
            include_secondary=True,
        )

        budget_route = result["basic"]["max_destinations_by_budget"]
        time_route = result["basic"]["max_destinations_by_time"]

        self.assertEqual(budget_route["path"], ["A", "B", "C", "D"])
        self.assertEqual(time_route["path"], ["A", "B", "C", "D"])
        self.assertEqual(
            budget_route["transports_used"],
            ["Avion Comercial", "Avion Regional", "Helice"],
        )

    def test_optimized_routes_respect_budget_and_time_limits(self):
        graph = Grafo()
        graph.configuracion["aeronaves"] = {
            "Avion Comercial": {"costoKm": 1, "tiempoKm": 1},
        }
        for vertex in ("A", "B", "D"):
            graph.agregar_vertice(vertex, es_hub=True)

        graph.agregar_arista("A", "D", 10, aeronaves=["Avion Comercial"], costo_base=1000)
        graph.agregar_arista("A", "B", 10, aeronaves=["Avion Comercial"], costo_base=0)
        graph.agregar_arista("B", "D", 10, aeronaves=["Avion Comercial"], costo_base=0)

        result = plan_itinerary(
            grafo=graph,
            origin_id="A",
            destination_id="D",
            budget=100,
            available_time=30,
            criteria=[CRITERION_DISTANCE],
            selected_transports=["Avion Comercial"],
            include_secondary=True,
        )

        self.assertEqual(result["optimized"][CRITERION_DISTANCE]["path"], ["A", "B", "D"])
        self.assertLessEqual(result["optimized"][CRITERION_DISTANCE]["total_cost"], 100)
        self.assertLessEqual(result["optimized"][CRITERION_DISTANCE]["total_time"], 30)

    def test_optimized_routes_return_none_when_no_route_is_feasible(self):
        result = plan_itinerary(
            grafo=self._build_graph(),
            origin_id="A",
            destination_id="D",
            budget=50,
            available_time=20,
            criteria=[CRITERION_COST],
            selected_transports=["Avion Comercial", "Avion Regional"],
            include_secondary=True,
        )

        self.assertIsNone(result["optimized"][CRITERION_COST])


if __name__ == "__main__":
    unittest.main()
