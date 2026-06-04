import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.viajero import Viajero


class ViajeroTest(unittest.TestCase):
    """Unit tests for the Viajero class."""

    def setUp(self):
        """Create a traveler instance for testing."""
        self.viajero = Viajero(presupuesto_inicial=1000.0, tiempo_total_horas=48.0)

    def test_inicializacion(self):
        """Test that a traveler is correctly initialized."""
        self.assertEqual(self.viajero.presupuesto_inicial, 1000.0)
        self.assertEqual(self.viajero.presupuesto_actual, 1000.0)
        self.assertEqual(self.viajero.tiempo_total_horas, 48.0)
        self.assertEqual(self.viajero.tiempo_restante_horas, 48.0)
        self.assertEqual(self.viajero.gasto_total, 0.0)
        self.assertEqual(self.viajero.ingreso_total, 0.0)
        self.assertEqual(len(self.viajero.aeropuertos_visitados), 0)
        self.assertEqual(len(self.viajero.actividades_realizadas), 0)
        self.assertEqual(len(self.viajero.trabajos_realizados), 0)

    def test_inicializacion_invalida(self):
        """Test that invalid initial values raise errors."""
        with self.assertRaises(ValueError):
            Viajero(presupuesto_inicial=-100, tiempo_total_horas=48)

        with self.assertRaises(ValueError):
            Viajero(presupuesto_inicial=1000, tiempo_total_horas=-48)

        with self.assertRaises(ValueError):
            Viajero(presupuesto_inicial=0, tiempo_total_horas=48)

    def test_gastar(self):
        """Test spending money from the budget."""
        self.viajero.gastar(100)
        self.assertEqual(self.viajero.presupuesto_actual, 900.0)
        self.assertEqual(self.viajero.gasto_total, 100.0)

        self.viajero.gastar(200)
        self.assertEqual(self.viajero.presupuesto_actual, 700.0)
        self.assertEqual(self.viajero.gasto_total, 300.0)

    def test_gastar_invalido(self):
        """Test that invalid spending amounts raise errors."""
        with self.assertRaises(ValueError):
            self.viajero.gastar(-50)

        with self.assertRaises(ValueError):
            self.viajero.gastar(2000)  # More than available budget

    def test_ganar(self):
        """Test earning money."""
        self.viajero.ganar(500)
        self.assertEqual(self.viajero.presupuesto_actual, 1500.0)
        self.assertEqual(self.viajero.ingreso_total, 500.0)

        self.viajero.ganar(250)
        self.assertEqual(self.viajero.presupuesto_actual, 1750.0)
        self.assertEqual(self.viajero.ingreso_total, 750.0)

    def test_ganar_invalido(self):
        """Test that negative income raises errors."""
        with self.assertRaises(ValueError):
            self.viajero.ganar(-100)

    def test_consumir_tiempo(self):
        """Test consuming time."""
        self.viajero.consumir_tiempo(10)
        self.assertEqual(self.viajero.tiempo_restante_horas, 38.0)

        self.viajero.consumir_tiempo(8)
        self.assertEqual(self.viajero.tiempo_restante_horas, 30.0)

    def test_consumir_tiempo_invalido(self):
        """Test that invalid time consumption raises errors."""
        with self.assertRaises(ValueError):
            self.viajero.consumir_tiempo(-5)

        with self.assertRaises(ValueError):
            self.viajero.consumir_tiempo(100)  # More than available time

    def test_registrar_aeropuerto(self):
        """Test registering visited airports."""
        self.viajero.registrar_aeropuerto("BOG")
        self.assertEqual(self.viajero.aeropuertos_visitados, ["BOG"])

        self.viajero.registrar_aeropuerto("MDE")
        self.assertEqual(self.viajero.aeropuertos_visitados, ["BOG", "MDE"])

        # Avoid consecutive duplicates
        self.viajero.registrar_aeropuerto("MDE")
        self.assertEqual(self.viajero.aeropuertos_visitados, ["BOG", "MDE"])

        # But can visit again after visiting another airport
        self.viajero.registrar_aeropuerto("BOG")
        self.assertEqual(self.viajero.aeropuertos_visitados, ["BOG", "MDE", "BOG"])

    def test_registrar_aeropuerto_normalizacion(self):
        """Test that airport codes are normalized."""
        self.viajero.registrar_aeropuerto("bog")
        self.viajero.registrar_aeropuerto("  MDE  ")
        self.assertEqual(self.viajero.aeropuertos_visitados, ["BOG", "MDE"])

    def test_registrar_aeropuerto_invalido(self):
        """Test that invalid airport codes raise errors."""
        with self.assertRaises(ValueError):
            self.viajero.registrar_aeropuerto("")

        with self.assertRaises(ValueError):
            self.viajero.registrar_aeropuerto(None)

    def test_registrar_actividad(self):
        """Test recording an activity."""
        actividad = {
            "nombre": "Tour en Bogotá",
            "costo": 50.0,
            "tiempo_horas": 4,
        }
        self.viajero.registrar_actividad(actividad)

        self.assertEqual(self.viajero.presupuesto_actual, 950.0)
        self.assertEqual(self.viajero.gasto_total, 50.0)
        self.assertEqual(self.viajero.tiempo_restante_horas, 44.0)
        self.assertEqual(len(self.viajero.actividades_realizadas), 1)

    def test_registrar_actividad_con_metadata(self):
        """Test that additional activity fields are preserved."""
        actividad = {
            "nombre": "Museo",
            "costo": 15.0,
            "tiempo_horas": 2,
            "ubicacion": "Centro histórico",
            "tipo": "cultural",
        }
        self.viajero.registrar_actividad(actividad)

        registrada = self.viajero.actividades_realizadas[0]
        self.assertEqual(registrada["nombre"], "Museo")
        self.assertEqual(registrada["ubicacion"], "Centro histórico")
        self.assertEqual(registrada["tipo"], "cultural")

    def test_registrar_actividad_sin_presupuesto(self):
        """Test that insufficient budget prevents activity."""
        self.viajero.presupuesto_actual = 10.0
        actividad = {
            "nombre": "Actividad cara",
            "costo": 100.0,
            "tiempo_horas": 2,
        }
        with self.assertRaises(ValueError):
            self.viajero.registrar_actividad(actividad)

    def test_registrar_actividad_sin_tiempo(self):
        """Test that insufficient time prevents activity."""
        self.viajero.tiempo_restante_horas = 2.0
        actividad = {
            "nombre": "Actividad larga",
            "costo": 50.0,
            "tiempo_horas": 5,
        }
        with self.assertRaises(ValueError):
            self.viajero.registrar_actividad(actividad)

    def test_registrar_trabajo(self):
        """Test recording a work session."""
        trabajo = {
            "descripcion": "Consultoría de TI",
            "tarifa_hora": 25.0,
        }
        self.viajero.registrar_trabajo(trabajo, horas=8)

        self.assertEqual(self.viajero.presupuesto_actual, 1200.0)  # 1000 + 200
        self.assertEqual(self.viajero.ingreso_total, 200.0)
        self.assertEqual(self.viajero.tiempo_restante_horas, 40.0)
        self.assertEqual(len(self.viajero.trabajos_realizados), 1)

        registrado = self.viajero.trabajos_realizados[0]
        self.assertEqual(registrado["ganancia"], 200.0)
        self.assertEqual(registrado["horas_trabajadas"], 8)

    def test_registrar_trabajo_sin_tiempo(self):
        """Test that insufficient time prevents work."""
        self.viajero.tiempo_restante_horas = 5.0
        trabajo = {
            "descripcion": "Trabajo",
            "tarifa_hora": 20.0,
        }
        with self.assertRaises(ValueError):
            self.viajero.registrar_trabajo(trabajo, horas=10)

    def test_presupuesto_bajo(self):
        """Test the low budget threshold check."""
        # Initial budget is 1000, threshold is 350 (35%)
        self.assertFalse(self.viajero.presupuesto_bajo())

        # Spend down to threshold
        self.viajero.gastar(650)  # Budget becomes 350
        self.assertTrue(self.viajero.presupuesto_bajo())

        # Spend below threshold
        self.viajero.gastar(50)  # Budget becomes 300
        self.assertTrue(self.viajero.presupuesto_bajo())

        # Recover with work
        self.viajero.ganar(100)
        self.assertFalse(self.viajero.presupuesto_bajo())

    def test_obtener_resumen(self):
        """Test the summary report."""
        self.viajero.gastar(100)
        self.viajero.ganar(200)
        self.viajero.consumir_tiempo(10)
        self.viajero.registrar_aeropuerto("BOG")
        self.viajero.registrar_aeropuerto("MDE")

        actividad = {
            "nombre": "Tour",
            "costo": 50,
            "tiempo_horas": 3,
        }
        self.viajero.registrar_actividad(actividad)

        trabajo = {
            "descripcion": "Trabajo",
            "tarifa_hora": 20,
        }
        self.viajero.registrar_trabajo(trabajo, horas=5)

        resumen = self.viajero.obtener_resumen()

        self.assertEqual(resumen["presupuesto_inicial"], 1000.0)
        self.assertEqual(resumen["presupuesto_actual"], 1150.0)  # 1000 - 100 + 200 - 50 + 100 = 1150
        self.assertEqual(resumen["gasto_total"], 150.0)  # 100 (initial) + 50 (activity)
        self.assertEqual(resumen["ingreso_total"], 300.0)  # 200 (from ganar) + 100 (from work)
        self.assertEqual(resumen["tiempo_total_horas"], 48.0)
        self.assertAlmostEqual(resumen["tiempo_restante_horas"], 30.0)  # 48 - 10 - 3 - 5 = 30
        self.assertEqual(resumen["cantidad_aeropuertos_visitados"], 2)
        self.assertEqual(resumen["cantidad_actividades"], 1)
        self.assertEqual(resumen["cantidad_trabajos"], 1)

    def test_str_representation(self):
        """Test string representation."""
        self.viajero.gastar(100)
        self.viajero.consumir_tiempo(10)
        self.viajero.registrar_aeropuerto("BOG")

        str_repr = str(self.viajero)
        self.assertIn("900.00", str_repr)  # Current budget
        self.assertIn("38.0", str_repr)  # Remaining time
        self.assertIn("1", str_repr)  # Airports visited

    def test_repr_representation(self):
        """Test developer-friendly representation."""
        repr_str = repr(self.viajero)
        self.assertIn("Viajero", repr_str)
        self.assertIn("presupuesto_inicial=1000", repr_str)


if __name__ == "__main__":
    unittest.main()
