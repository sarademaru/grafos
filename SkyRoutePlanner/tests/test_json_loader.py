import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.json_loader import cargar_json


class JsonLoaderTest(unittest.TestCase):
    def test_cargar_json_con_configuracion_y_ruta(self):
        datos = {
            "configuracion": {
                "presupuestoMinimoPorcentaje": 35,
                "intervaloAlimentacionHoras": 8,
                "intervaloHospedajeHoras": 20,
                "aeronaves": {
                    "Comercial": {"costoKm": 0.12, "tiempoKm": 0.008},
                    "Regional": {"costoKm": 0.08, "tiempoKm": 0.012},
                },
            },
            "nodos": [
                {"codigo": "BOG", "nombre": "Bogotá"},
                {"codigo": "MDE", "nombre": "Medellín"},
            ],
            "aristas": [
                {
                    "origen": "BOG",
                    "destino": "MDE",
                    "distanciaKm": 250,
                    "aeronaves": ["Comercial", "Regional"],
                    "costoBase": 0,
                    "estanciaMinima": 120,
                }
            ],
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
            archivo.flush()
            ruta_temporal = Path(archivo.name)

        try:
            grafo = cargar_json(ruta_temporal)

            configuracion = grafo.obtener_configuracion()
            self.assertEqual(configuracion["presupuestoMinimoPorcentaje"], 35)
            self.assertEqual(configuracion["intervaloAlimentacionHoras"], 8)
            self.assertEqual(configuracion["intervaloHospedajeHoras"], 20)
            self.assertEqual(set(grafo.obtener_aeronaves_disponibles()), {"Comercial", "Regional"})
            self.assertEqual(grafo.obtener_costo_por_km("Comercial"), 0.12)
            self.assertEqual(grafo.obtener_tiempo_por_km("Regional"), 0.012)

            self.assertTrue(grafo.existe_vertice("BOG"))
            arista = grafo.obtener_vertice("BOG").adyacencias[0]
            self.assertEqual(arista.distancia_km, 250)
            self.assertEqual(arista.aeronaves, ["Comercial", "Regional"])
            self.assertEqual(arista.costo_base, 0)
            self.assertEqual(arista.estancia_minima, 120)
        finally:
            ruta_temporal.unlink(missing_ok=True)
