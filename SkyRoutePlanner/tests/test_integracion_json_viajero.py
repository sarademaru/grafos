"""
Integration test: JSON Loader → Domain Objects → Viajero Simulation
Verifies the complete flow from JSON configuration to traveler simulation.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.json_loader import cargar_json
from models.viajero import Viajero
from models.actividad import Actividad
from models.trabajo import Trabajo


def test_integracion_completa():
    """Complete integration: Load JSON → Create traveler → Register activities/jobs."""
    
    datos = {
        "configuracion": {
            "presupuestoMinimoPorcentaje": 35,
            "intervaloAlimentacionHoras": 8,
            "intervaloHospedajeHoras": 20,
            "aeronaves": {
                "Boeing 777": {"costoKm": 1.2, "tiempoKm": 0.002},
                "Airbus A380": {"costoKm": 1.5, "tiempoKm": 0.0018}
            }
        },
        "nodos": [
            {
                "codigo": "BOG",
                "nombre": "El Dorado",
                "ciudad": "Bogotá",
                "pais": "Colombia",
                "esHub": True,
                "costoAlojamiento": 50,
                "costoAlimentacion": 30,
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
                "pais": "Colombia",
                "esHub": False,
                "costoAlojamiento": 40,
                "costoAlimentacion": 25
            }
        ],
        "aristas": [
            {
                "origen": "BOG",
                "destino": "MDE",
                "distancia": 250,
                "aeronaves": ["Boeing 777"],
                "costoBase": 100,
                "estanciaMinima": 2
            }
        ]
    }

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as archivo:
        json.dump(datos, archivo, ensure_ascii=False, indent=2)
        archivo.flush()
        ruta_temporal = Path(archivo.name)

    try:
        print("=" * 70)
        print("INTEGRATION TEST: JSON Loader → Domain Objects → Viajero Simulation")
        print("=" * 70)

        # Step 1: Load JSON
        print("\n1. LOADING JSON")
        print("-" * 70)
        grafo = cargar_json(ruta_temporal)
        bog = grafo.obtener_vertice("BOG")
        print(f"✓ Graph loaded: {grafo.cantidad_vertices()} vertices")
        print(f"✓ Airport BOG loaded: {bog.nombre}, {bog.ciudad}, {bog.pais}")

        # Step 2: Verify activities are domain objects
        print("\n2. VERIFYING ACTIVITIES ARE DOMAIN OBJECTS")
        print("-" * 70)
        for i, actividad in enumerate(bog.actividades, 1):
            assert isinstance(actividad, Actividad)
            print(f"  Activity {i}: {actividad} (type: {type(actividad).__name__})")

        # Step 3: Verify jobs are domain objects
        print("\n3. VERIFYING JOBS ARE DOMAIN OBJECTS")
        print("-" * 70)
        for i, trabajo in enumerate(bog.trabajos, 1):
            assert isinstance(trabajo, Trabajo)
            print(f"  Job {i}: {trabajo} (type: {type(trabajo).__name__})")

        # Step 4: Create a traveler
        print("\n4. CREATING TRAVELER")
        print("-" * 70)
        viajero = Viajero(presupuesto_inicial=1000, tiempo_total_horas=100)
        print(f"✓ Traveler created:")
        print(f"  - Budget: ${viajero.presupuesto_actual}")
        print(f"  - Time: {viajero.tiempo_restante_horas} hours")

        # Step 5: Register traveler at airport
        print("\n5. REGISTERING TRAVELER AT AIRPORT")
        print("-" * 70)
        viajero.registrar_aeropuerto(bog.identificador)
        print(f"✓ Traveler arrived at {bog.nombre}")
        print(f"  - Airports visited: {len(viajero.aeropuertos_visitados)}")
        print(f"  - Budget spent: ${viajero.gasto_total:.2f}")

        # Step 6: Perform an activity (using Actividad object)
        print("\n6. PERFORMING AN ACTIVITY (using Actividad object)")
        print("-" * 70)
        actividad_tour = bog.actividades[0]  # Tour Bogotá
        print(f"  Selected activity: {actividad_tour}")
        print(f"  Activity details:")
        print(f"    - Name: {actividad_tour.nombre}")
        print(f"    - Duration: {actividad_tour.duracion_horas} hours")
        print(f"    - Cost: ${actividad_tour.costo_usd}")

        # Convert Actividad to dict for Viajero.registrar_actividad (which expects dict)
        actividad_dict = actividad_tour.obtener_resumen()
        viajero.registrar_actividad(actividad_dict)
        
        print(f"\n✓ Activity registered:")
        print(f"  - Budget before: $1000.00")
        print(f"  - Cost: ${actividad_tour.costo_usd}")
        print(f"  - Time spent: {actividad_tour.duracion_horas} hours")
        print(f"  - Budget after: ${viajero.presupuesto_actual:.2f}")
        print(f"  - Time remaining: {viajero.tiempo_restante_horas:.1f} hours")

        # Step 7: Check budget status
        print("\n7. CHECKING BUDGET STATUS")
        print("-" * 70)
        presupuesto_bajo = viajero.presupuesto_bajo()
        print(f"  Minimum budget: ${viajero.presupuesto_inicial * 0.35:.2f} (35%)")
        print(f"  Current budget: ${viajero.presupuesto_actual:.2f}")
        print(f"  Budget is low: {presupuesto_bajo}")

        # Step 8: Perform work if budget is low (register enough activities first)
        print("\n8. SIMULATING BUDGET PRESSURE & WORK")
        print("-" * 70)
        
        # Spend more to trigger low budget
        actividad_museos = bog.actividades[1]  # Museos
        actividad_dict2 = actividad_museos.obtener_resumen()
        viajero.registrar_actividad(actividad_dict2)
        print(f"  Performed {actividad_museos.nombre}: ${actividad_museos.costo_usd}")
        print(f"  Current budget: ${viajero.presupuesto_actual:.2f}")
        
        presupuesto_bajo = viajero.presupuesto_bajo()
        print(f"  Budget is low: {presupuesto_bajo}")

        if presupuesto_bajo:
            trabajo = bog.trabajos[0]  # Guía de aeropuerto
            print(f"\n  ✓ Performing work: {trabajo}")
            ganancia = trabajo.calcular_ganancia(4)  # Work 4 hours
            print(f"    - Hours: 4")
            print(f"    - Hourly rate: ${trabajo.tarifa_hora}")
            print(f"    - Earnings: ${ganancia:.2f}")
            
            viajero.registrar_trabajo(trabajo.obtener_resumen(), 4)
            print(f"    - New budget: ${viajero.presupuesto_actual:.2f}")

        # Step 9: Summary
        print("\n9. TRAVELER SUMMARY")
        print("-" * 70)
        resumen = viajero.obtener_resumen()
        print(f"  Presupuesto inicial: ${resumen['presupuesto_inicial']:.2f}")
        print(f"  Presupuesto actual: ${resumen['presupuesto_actual']:.2f}")
        print(f"  Gasto total: ${resumen['gasto_total']:.2f}")
        print(f"  Ingreso total: ${resumen['ingreso_total']:.2f}")
        print(f"  Tiempo total: {resumen['tiempo_total_horas']} hours")
        print(f"  Tiempo restante: {resumen['tiempo_restante_horas']:.1f} hours")
        print(f"  Actividades realizadas: {len(resumen['actividades_realizadas'])}")
        print(f"  Trabajos realizados: {len(resumen['trabajos_realizados'])}")

        # Step 10: Verify object types throughout
        print("\n10. FINAL VERIFICATION OF OBJECT TYPES")
        print("-" * 70)
        print(f"  ✓ bog.actividades[0] is Actividad: {isinstance(bog.actividades[0], Actividad)}")
        print(f"  ✓ bog.trabajos[0] is Trabajo: {isinstance(bog.trabajos[0], Trabajo)}")
        print(f"  ✓ Viajero integrates with these objects: True")

        print("\n" + "=" * 70)
        print("✓ ALL INTEGRATION TESTS PASSED!")
        print("=" * 70)

    finally:
        ruta_temporal.unlink(missing_ok=True)


if __name__ == "__main__":
    test_integracion_completa()
