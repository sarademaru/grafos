import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.actividad import Actividad


class ActividadTest(unittest.TestCase):
    """Unit tests for the Actividad class."""

    def test_inicializacion_valida(self):
        """Test that an activity is correctly initialized."""
        actividad = Actividad(
            nombre="City Tour",
            duracion_horas=3.5,
            costo_usd=50.0,
        )
        self.assertEqual(actividad.nombre, "City Tour")
        self.assertEqual(actividad.duracion_horas, 3.5)
        self.assertEqual(actividad.costo_usd, 50.0)

    def test_inicializacion_con_espacios(self):
        """Test that activity names are trimmed."""
        actividad = Actividad(
            nombre="  Museum Visit  ",
            duracion_horas=2.0,
            costo_usd=15.0,
        )
        self.assertEqual(actividad.nombre, "Museum Visit")

    def test_inicializacion_costo_cero(self):
        """Test that zero cost is allowed."""
        actividad = Actividad(
            nombre="Free Event",
            duracion_horas=1.0,
            costo_usd=0.0,
        )
        self.assertEqual(actividad.costo_usd, 0.0)

    def test_inicializacion_nombre_invalido(self):
        """Test that invalid names raise errors."""
        with self.assertRaises(ValueError):
            Actividad(nombre="", duracion_horas=1.0, costo_usd=10.0)

        with self.assertRaises(ValueError):
            Actividad(nombre="  ", duracion_horas=1.0, costo_usd=10.0)

        with self.assertRaises(ValueError):
            Actividad(nombre=None, duracion_horas=1.0, costo_usd=10.0)

        with self.assertRaises(ValueError):
            Actividad(nombre=123, duracion_horas=1.0, costo_usd=10.0)

    def test_inicializacion_duracion_invalida(self):
        """Test that invalid duration raises errors."""
        with self.assertRaises(ValueError):
            Actividad(nombre="Activity", duracion_horas=0, costo_usd=10.0)

        with self.assertRaises(ValueError):
            Actividad(nombre="Activity", duracion_horas=-5, costo_usd=10.0)

    def test_inicializacion_costo_invalido(self):
        """Test that negative cost raises errors."""
        with self.assertRaises(ValueError):
            Actividad(nombre="Activity", duracion_horas=1.0, costo_usd=-10.0)

    def test_obtener_resumen(self):
        """Test the summary report."""
        actividad = Actividad(
            nombre="Beach Day",
            duracion_horas=4.0,
            costo_usd=35.50,
        )
        resumen = actividad.obtener_resumen()

        self.assertIsInstance(resumen, dict)
        self.assertEqual(resumen["nombre"], "Beach Day")
        self.assertEqual(resumen["duracion_horas"], 4.0)
        self.assertEqual(resumen["costo_usd"], 35.50)

    def test_str_representation(self):
        """Test string representation."""
        actividad = Actividad(
            nombre="Historical Tour",
            duracion_horas=2.5,
            costo_usd=25.00,
        )
        str_repr = str(actividad)

        self.assertIn("Historical Tour", str_repr)
        self.assertIn("2.5h", str_repr)
        self.assertIn("$25.00", str_repr)

    def test_repr_representation(self):
        """Test developer-friendly representation."""
        actividad = Actividad(
            nombre="Concert",
            duracion_horas=3.0,
            costo_usd=80.0,
        )
        repr_str = repr(actividad)

        self.assertIn("Actividad", repr_str)
        self.assertIn("Concert", repr_str)
        self.assertIn("3.0", repr_str)
        self.assertIn("80", repr_str)

    def test_equality(self):
        """Test that identical activities are equal."""
        act1 = Actividad("Hiking", 6.0, 0.0)
        act2 = Actividad("Hiking", 6.0, 0.0)
        act3 = Actividad("Hiking", 5.0, 0.0)

        self.assertEqual(act1, act2)
        self.assertNotEqual(act1, act3)
        self.assertNotEqual(act1, "not an activity")

    def test_hashability(self):
        """Test that activities can be used in sets and dicts."""
        act1 = Actividad("Dancing", 2.0, 20.0)
        act2 = Actividad("Dancing", 2.0, 20.0)
        act3 = Actividad("Singing", 1.5, 15.0)

        activity_set = {act1, act2, act3}
        # act1 and act2 are equal, so set should have 2 elements
        self.assertEqual(len(activity_set), 2)

        activity_dict = {act1: "enjoyed"}
        self.assertEqual(activity_dict[act2], "enjoyed")

    def test_fractional_hours(self):
        """Test that fractional hours are supported."""
        actividad = Actividad(
            nombre="Quick Tour",
            duracion_horas=0.5,
            costo_usd=5.0,
        )
        self.assertEqual(actividad.duracion_horas, 0.5)

    def test_large_values(self):
        """Test that large values are handled correctly."""
        actividad = Actividad(
            nombre="Expedition",
            duracion_horas=100.0,
            costo_usd=9999.99,
        )
        self.assertEqual(actividad.duracion_horas, 100.0)
        self.assertEqual(actividad.costo_usd, 9999.99)


if __name__ == "__main__":
    unittest.main()
