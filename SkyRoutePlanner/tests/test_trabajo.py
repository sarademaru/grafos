import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.trabajo import Trabajo


class TrabajoTest(unittest.TestCase):
    """Unit tests for the Trabajo class."""

    def test_inicializacion_valida(self):
        """Test that a work opportunity is correctly initialized."""
        trabajo = Trabajo(
            nombre="Tour Guide",
            tarifa_hora=15.0,
            max_horas=8.0,
        )
        self.assertEqual(trabajo.nombre, "Tour Guide")
        self.assertEqual(trabajo.tarifa_hora, 15.0)
        self.assertEqual(trabajo.max_horas, 8.0)

    def test_inicializacion_con_espacios(self):
        """Test that work names are trimmed."""
        trabajo = Trabajo(
            nombre="  Airport Assistant  ",
            tarifa_hora=12.0,
            max_horas=10.0,
        )
        self.assertEqual(trabajo.nombre, "Airport Assistant")

    def test_inicializacion_nombre_invalido(self):
        """Test that invalid names raise errors."""
        with self.assertRaises(ValueError):
            Trabajo(nombre="", tarifa_hora=15.0, max_horas=8.0)

        with self.assertRaises(ValueError):
            Trabajo(nombre="  ", tarifa_hora=15.0, max_horas=8.0)

        with self.assertRaises(ValueError):
            Trabajo(nombre=None, tarifa_hora=15.0, max_horas=8.0)

    def test_inicializacion_tarifa_invalida(self):
        """Test that invalid hourly rates raise errors."""
        with self.assertRaises(ValueError):
            Trabajo(nombre="Work", tarifa_hora=0, max_horas=8.0)

        with self.assertRaises(ValueError):
            Trabajo(nombre="Work", tarifa_hora=-10, max_horas=8.0)

    def test_inicializacion_max_horas_invalida(self):
        """Test that invalid max hours raise errors."""
        with self.assertRaises(ValueError):
            Trabajo(nombre="Work", tarifa_hora=15.0, max_horas=0)

        with self.assertRaises(ValueError):
            Trabajo(nombre="Work", tarifa_hora=15.0, max_horas=-5)

    def test_calcular_ganancia_valida(self):
        """Test calculating earnings for valid hours."""
        trabajo = Trabajo(nombre="Consultant", tarifa_hora=25.0, max_horas=10.0)

        ganancia = trabajo.calcular_ganancia(5.0)
        self.assertEqual(ganancia, 125.0)

        ganancia = trabajo.calcular_ganancia(10.0)
        self.assertEqual(ganancia, 250.0)

    def test_calcular_ganancia_fraccionada(self):
        """Test calculating earnings with fractional hours."""
        trabajo = Trabajo(nombre="Writer", tarifa_hora=20.0, max_horas=20.0)

        ganancia = trabajo.calcular_ganancia(2.5)
        self.assertEqual(ganancia, 50.0)

        ganancia = trabajo.calcular_ganancia(0.5)
        self.assertEqual(ganancia, 10.0)

    def test_calcular_ganancia_horas_invalidas(self):
        """Test that invalid hours raise errors."""
        trabajo = Trabajo(nombre="Job", tarifa_hora=15.0, max_horas=8.0)

        with self.assertRaises(ValueError):
            trabajo.calcular_ganancia(0)

        with self.assertRaises(ValueError):
            trabajo.calcular_ganancia(-5)

        with self.assertRaises(ValueError):
            trabajo.calcular_ganancia(10.0)  # Exceeds max_horas

    def test_obtener_resumen(self):
        """Test the summary report."""
        trabajo = Trabajo(
            nombre="Chef",
            tarifa_hora=18.0,
            max_horas=12.0,
        )
        resumen = trabajo.obtener_resumen()

        self.assertIsInstance(resumen, dict)
        self.assertEqual(resumen["nombre"], "Chef")
        self.assertEqual(resumen["tarifa_hora"], 18.0)
        self.assertEqual(resumen["max_horas"], 12.0)

    def test_str_representation(self):
        """Test string representation."""
        trabajo = Trabajo(
            nombre="Guide",
            tarifa_hora=15.0,
            max_horas=8.0,
        )
        str_repr = str(trabajo)

        self.assertIn("Guide", str_repr)
        self.assertIn("15", str_repr)
        self.assertIn("USD/hour", str_repr)
        self.assertIn("8", str_repr)

    def test_repr_representation(self):
        """Test developer-friendly representation."""
        trabajo = Trabajo(
            nombre="Cleaner",
            tarifa_hora=10.0,
            max_horas=6.0,
        )
        repr_str = repr(trabajo)

        self.assertIn("Trabajo", repr_str)
        self.assertIn("Cleaner", repr_str)
        self.assertIn("10", repr_str)

    def test_equality(self):
        """Test that identical work opportunities are equal."""
        trabajo1 = Trabajo("Translator", 20.0, 15.0)
        trabajo2 = Trabajo("Translator", 20.0, 15.0)
        trabajo3 = Trabajo("Translator", 21.0, 15.0)

        self.assertEqual(trabajo1, trabajo2)
        self.assertNotEqual(trabajo1, trabajo3)
        self.assertNotEqual(trabajo1, "not a work")

    def test_hashability(self):
        """Test that work opportunities can be used in sets and dicts."""
        trabajo1 = Trabajo("Teacher", 18.0, 10.0)
        trabajo2 = Trabajo("Teacher", 18.0, 10.0)
        trabajo3 = Trabajo("Tutor", 22.0, 8.0)

        trabajo_set = {trabajo1, trabajo2, trabajo3}
        # trabajo1 and trabajo2 are equal, so set should have 2 elements
        self.assertEqual(len(trabajo_set), 2)

        trabajo_dict = {trabajo1: "available"}
        self.assertEqual(trabajo_dict[trabajo2], "available")

    def test_large_values(self):
        """Test that large values are handled correctly."""
        trabajo = Trabajo(
            nombre="Executive Consultant",
            tarifa_hora=500.0,
            max_horas=100.0,
        )
        self.assertEqual(trabajo.tarifa_hora, 500.0)
        self.assertEqual(trabajo.max_horas, 100.0)
        self.assertEqual(trabajo.calcular_ganancia(50.0), 25000.0)


if __name__ == "__main__":
    unittest.main()
