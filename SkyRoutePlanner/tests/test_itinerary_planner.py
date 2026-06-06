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

    def test_basic_alternatives_prioritize_more_destinations_over_direct_route(self):
        graph = Grafo()
        graph.configuracion["aeronaves"] = {
            "Avion Comercial": {"costoKm": 1, "tiempoKm": 1},
            "Avion Regional": {"costoKm": 1, "tiempoKm": 1},
            "Helice": {"costoKm": 1, "tiempoKm": 1},
        }

        for vertex, is_hub in (("A", True), ("B", True), ("C", False), ("D", True)):
            graph.agregar_vertice(vertex, es_hub=is_hub)

        graph.agregar_arista("A", "B", 10, aeronaves=["Avion Comercial"], costo_base=0)
        graph.agregar_arista("B", "C", 10, aeronaves=["Helice"], costo_base=0)
        graph.agregar_arista("C", "D", 10, aeronaves=["Avion Regional"], costo_base=0)
        graph.agregar_arista("A", "D", 5, aeronaves=["Avion Comercial"], costo_base=0)

        result = plan_itinerary(
            grafo=graph,
            origin_id="A",
            destination_id="D",
            budget=100,
            available_time=100,
            criteria=[CRITERION_COST],
            selected_transports=["Avion Comercial", "Avion Regional", "Helice"],
            include_secondary=True,
        )

        self.assertEqual(result["basic"]["max_destinations_by_budget"]["path"], ["A", "B", "C", "D"])
        self.assertEqual(result["basic"]["max_destinations_by_time"]["path"], ["A", "B", "C", "D"])
        self.assertEqual(
            result["basic"]["max_destinations_by_budget"]["transports_used"],
            ["Avion Comercial", "Avion Regional", "Helice"],
        )

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

    def test_basic_alternatives_maximize_destinations_before_direct_route(self):
        graph = Grafo()
        graph.configuracion["aeronaves"] = {
            "Comercial": {"costoKm": 0.30, "tiempoKm": 0.004},
            "Regional": {"costoKm": 0.15, "tiempoKm": 0.010},
            "Helice": {"costoKm": 0.04, "tiempoKm": 0.030},
        }
        for airport, is_hub in {
            "BOG": True,
            "MDE": True,
            "UIO": False,
            "LIM": True,
            "SCL": True,
            "MEX": True,
        }.items():
            graph.agregar_vertice(airport, es_hub=is_hub)

        graph.agregar_arista("BOG", "MEX", 3160, aeronaves=["Comercial"])
        graph.agregar_arista("BOG", "MDE", 250, aeronaves=["Helice"])
        graph.agregar_arista("MDE", "UIO", 430, aeronaves=["Helice"])
        graph.agregar_arista("UIO", "LIM", 1320, aeronaves=["Helice"])
        graph.agregar_arista("LIM", "SCL", 2450, aeronaves=["Helice"])
        graph.agregar_arista("SCL", "MEX", 1500, aeronaves=["Helice"])
        graph.agregar_arista("BOG", "LIM", 1880, aeronaves=["Regional"])
        graph.agregar_arista("LIM", "MEX", 4250, aeronaves=["Regional"])

        result = plan_itinerary(
            grafo=graph,
            origin_id="BOG",
            destination_id="MEX",
            budget=50000,
            available_time=500,
            criteria=[CRITERION_COST],
            selected_transports=["Avion Comercial", "Avion Regional", "Helice"],
            include_secondary=True,
        )

        expected_path = ["BOG", "MDE", "UIO", "LIM", "SCL", "MEX"]
        budget_route = result["basic"]["max_destinations_by_budget"]
        time_route = result["basic"]["max_destinations_by_time"]

        self.assertEqual(budget_route["path"], expected_path)
        self.assertEqual(time_route["path"], expected_path)
        self.assertLessEqual(budget_route["total_cost"], 50000)
        self.assertLessEqual(time_route["total_time"], 500)

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
