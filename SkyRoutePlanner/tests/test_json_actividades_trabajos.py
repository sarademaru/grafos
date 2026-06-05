import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.json_loader import cargar_json
from models.actividad import Actividad
from models.trabajo import Trabajo


def test_actividades_y_trabajos_como_objetos():
    """Verify that activities and jobs are converted to domain objects, not dicts."""
    
    datos = {
        "nodos": [
            {
                "codigo": "BOG",
                "nombre": "El Dorado",
                "ciudad": "Bogotá",
                "pais": "Colombia",
                "actividades": [
                    {
                        "nombre": "Tour Bogotá",
                        "duracionMin": 180,
                        "costoUSD": 25
                    },
                    {
                        "nombre": "Museos",
                        "duracion_horas": 4,
                        "costo_usd": 15
                    }
                ],
                "trabajos": [
                    {
                        "nombre": "Guía de aeropuerto",
                        "tarifaHora": 12,
                        "maxHoras": 8
                    },
                    {
                        "nombre": "Asistente turístico",
                        "tarifa_hora": 15,
                        "max_horas": 10
                    }
                ]
            },
            {
                "codigo": "MDE",
                "nombre": "Rionegro",
                "ciudad": "Medellín",
                "pais": "Colombia"
            }
        ],
        "aristas": []
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
        archivo.flush()
        ruta_temporal = Path(archivo.name)

    try:
        grafo = cargar_json(ruta_temporal)
        bog = grafo.obtener_vertice("BOG")
        mde = grafo.obtener_vertice("MDE")

        # Test 1: Activities are Actividad objects
        print("=" * 60)
        print("TEST: Activities as Objects")
        print("=" * 60)
        
        assert len(bog.actividades) == 2, f"Expected 2 activities, got {len(bog.actividades)}"
        
        actividad1 = bog.actividades[0]
        actividad2 = bog.actividades[1]
        
        print(f"Type of bog.actividades[0]: {type(actividad1).__name__}")
        print(f"Type of bog.actividades[1]: {type(actividad2).__name__}")
        
        assert isinstance(actividad1, Actividad), f"Expected Actividad, got {type(actividad1)}"
        assert isinstance(actividad2, Actividad), f"Expected Actividad, got {type(actividad2)}"
        
        print(f"✓ Both activities are Actividad objects")
        print(f"  - Activity 1: {actividad1}")
        print(f"  - Activity 2: {actividad2}")

        # Test 2: Jobs are Trabajo objects
        print("\n" + "=" * 60)
        print("TEST: Jobs as Objects")
        print("=" * 60)
        
        assert len(bog.trabajos) == 2, f"Expected 2 jobs, got {len(bog.trabajos)}"
        
        trabajo1 = bog.trabajos[0]
        trabajo2 = bog.trabajos[1]
        
        print(f"Type of bog.trabajos[0]: {type(trabajo1).__name__}")
        print(f"Type of bog.trabajos[1]: {type(trabajo2).__name__}")
        
        assert isinstance(trabajo1, Trabajo), f"Expected Trabajo, got {type(trabajo1)}"
        assert isinstance(trabajo2, Trabajo), f"Expected Trabajo, got {type(trabajo2)}"
        
        print(f"✓ Both jobs are Trabajo objects")
        print(f"  - Job 1: {trabajo1}")
        print(f"  - Job 2: {trabajo2}")

        # Test 3: Activity values are correct
        print("\n" + "=" * 60)
        print("TEST: Activity Values")
        print("=" * 60)
        
        assert actividad1.nombre == "Tour Bogotá"
        assert actividad1.duracion_horas == 3.0  # 180 minutes / 60
        assert actividad1.costo_usd == 25
        
        assert actividad2.nombre == "Museos"
        assert actividad2.duracion_horas == 4
        assert actividad2.costo_usd == 15
        
        print(f"✓ Activity 1 values correct: {actividad1.obtener_resumen()}")
        print(f"✓ Activity 2 values correct: {actividad2.obtener_resumen()}")

        # Test 4: Job values are correct
        print("\n" + "=" * 60)
        print("TEST: Job Values")
        print("=" * 60)
        
        assert trabajo1.nombre == "Guía de aeropuerto"
        assert trabajo1.tarifa_hora == 12
        assert trabajo1.max_horas == 8
        
        assert trabajo2.nombre == "Asistente turístico"
        assert trabajo2.tarifa_hora == 15
        assert trabajo2.max_horas == 10
        
        print(f"✓ Job 1 values correct: {trabajo1.obtener_resumen()}")
        print(f"✓ Job 2 values correct: {trabajo2.obtener_resumen()}")

        # Test 5: Empty activities/jobs when not specified
        print("\n" + "=" * 60)
        print("TEST: Empty Activities/Jobs")
        print("=" * 60)
        
        assert len(mde.actividades) == 0, "MDE should have no activities"
        assert len(mde.trabajos) == 0, "MDE should have no jobs"
        
        print("✓ Airports without activities/jobs have empty lists")

        # Test 6: Using airport methods
        print("\n" + "=" * 60)
        print("TEST: Airport Methods")
        print("=" * 60)
        
        resumen = bog.obtener_resumen()
        print(f"Airport summary:")
        print(f"  - Cantidad de actividades: {resumen['cantidad_actividades']}")
        print(f"  - Cantidad de trabajos: {resumen['cantidad_trabajos']}")
        print(f"✓ Airport.obtener_resumen() includes activity and job counts")

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    finally:
        ruta_temporal.unlink(missing_ok=True)


if __name__ == "__main__":
    test_actividades_y_trabajos_como_objetos()
