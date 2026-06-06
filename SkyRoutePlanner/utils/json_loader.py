import json
from pathlib import Path

from models.grafo import Grafo
from models.grafo import DEFAULT_AERONAVES
from models.actividad import Actividad
from models.trabajo import Trabajo


def _get_value(dct, keys, default=None):
    for k in keys:
        if k in dct:
            return dct[k]
    return default


def _normalize_aeronaves_config(aeronaves_config):
    # Do not merge with DEFAULT_AERONAVES here; return only provided types
    normalized = {}
    if not isinstance(aeronaves_config, dict):
        return normalized

    for tipo, datos in aeronaves_config.items():
        if not isinstance(datos, dict):
            continue
        tiempo_horas_km = _get_value(datos, ["tiempoKm", "timePerKm", "time_per_km"], None)
        tiempo_min_km = _get_value(datos, ["tiempoMinKm", "tiempo_min_km", "timeMinPerKm"], None)
        if tiempo_min_km is not None:
            tiempo_horas_km = float(tiempo_min_km) / 60

        normalized[tipo] = {
            "costoKm": _get_value(datos, ["costoKm", "costPerKm", "cost_per_km"], 0),
            "tiempoKm": tiempo_horas_km or 0,
        }
    return normalized


def _parse_configuracion(datos):
    configuracion = _get_value(datos, ["configuracion", "configuration"], {})
    if not isinstance(configuracion, dict):
        return {
            "presupuestoMinimoPorcentaje": 35,
            "intervaloAlimentacionHoras": 8,
            "intervaloHospedajeHoras": 20,
            "aeronaves": dict(DEFAULT_AERONAVES),
        }

    return {
        "presupuestoMinimoPorcentaje": _get_value(
            configuracion,
            ["presupuestoMinimoPorcentaje", "minimumBudgetPercentage"],
            35,
        ),
        "intervaloAlimentacionHoras": _get_value(
            configuracion,
            ["intervaloAlimentacionHoras", "feedingIntervalHours"],
            8,
        ),
        "intervaloHospedajeHoras": _get_value(
            configuracion,
            ["intervaloHospedajeHoras", "lodgingIntervalHours"],
            20,
        ),
        "aeronaves": _normalize_aeronaves_config(
            _get_value(configuracion, ["aeronaves", "aircraft"], {}),
        ),
    }


def _crear_actividades(actividades_data):
    """Convert activity dictionaries from JSON to Actividad objects."""
    if not isinstance(actividades_data, list):
        return []

    actividades = []
    for actividad_data in actividades_data:
        if not isinstance(actividad_data, dict):
            continue

        try:
            nombre = _get_value(
                actividad_data,
                ["nombre", "name", "title"],
                None
            )
            if not nombre:
                continue

            # Duration: support multiple field names
            duracion_horas = _get_value(
                actividad_data,
                ["duracion_horas", "duracionHoras", "duracionMin", "duration_hours", "duration"],
                0
            )
            # Convert minutes to hours if needed
            if "duracionMin" in actividad_data or "duracion_min" in actividad_data:
                duracion_horas = actividad_data.get("duracionMin") or actividad_data.get("duracion_min", 0)
                duracion_horas = duracion_horas / 60.0  # Convert minutes to hours

            # Cost: support multiple field names
            costo_usd = _get_value(
                actividad_data,
                ["costo_usd", "costoUSD", "costo", "cost", "price"],
                0
            )

            actividad = Actividad(
                nombre=nombre,
                duracion_horas=duracion_horas,
                costo_usd=costo_usd
            )
            actividades.append(actividad)
        except (ValueError, TypeError) as e:
            # Skip invalid activities with warning message in logs
            continue

    return actividades


def _crear_trabajos(trabajos_data):
    """Convert job dictionaries from JSON to Trabajo objects."""
    if not isinstance(trabajos_data, list):
        return []

    trabajos = []
    for trabajo_data in trabajos_data:
        if not isinstance(trabajo_data, dict):
            continue

        try:
            nombre = _get_value(
                trabajo_data,
                ["nombre", "name", "title"],
                None
            )
            if not nombre:
                continue

            # Hourly rate: support multiple field names
            tarifa_hora = _get_value(
                trabajo_data,
                ["tarifa_hora", "tarifaHora", "hourly_rate", "salary"],
                0
            )

            # Max hours: support multiple field names
            max_horas = _get_value(
                trabajo_data,
                ["max_horas", "maxHoras", "maximum_hours", "max_hours"],
                8
            )

            trabajo = Trabajo(
                nombre=nombre,
                tarifa_hora=tarifa_hora,
                max_horas=max_horas
            )
            trabajos.append(trabajo)
        except (ValueError, TypeError) as e:
            # Skip invalid jobs with warning message in logs
            continue

    return trabajos


def cargar_json(ruta_archivo):
    """Load a graph from a JSON file.

    Supports multiple simple schemas:
    - A list of airports (each with 'code'/'id' and 'name')
    - A dict with 'nodos' and 'aristas' (Spanish schema)
    - A dict with 'airports' and 'routes' (alternate schema)

    The loader will create missing vertices when edges reference them.
    Global configuration values can be read from a top-level
    'configuracion' section and are stored in the returned Grafo.
    """
    ruta = Path(ruta_archivo)
    if not ruta.exists():
        raise FileNotFoundError(ruta_archivo)

    with open(ruta, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    grafo = Grafo()
    if isinstance(datos, dict):
        grafo.configuracion = _parse_configuracion(datos)

    # Helper to add an airport dict to the graph
    def _add_airport(a):
        identificador = _get_value(a, ["id", "code", "codigo", "iata"])
        if identificador is None:
            return
        nombre = _get_value(a, ["name", "nombre"], "")
        ciudad = _get_value(a, ["city", "ciudad"], "")
        pais = _get_value(a, ["country", "pais"], "")
        zona = _get_value(a, ["timezone", "zonaHoraria"], "")
        es_hub = _get_value(a, ["isHub", "esHub"], False)
        costo_alojamiento = _get_value(a, ["costoAlojamiento"], 0)
        costo_alimentacion = _get_value(a, ["costoAlimentacion"], 0)
        
        # Convert activity and job dictionaries to domain objects
        actividades_data = _get_value(a, ["actividades"], [])
        actividades = _crear_actividades(actividades_data)
        
        trabajos_data = _get_value(a, ["trabajos"], [])
        trabajos = _crear_trabajos(trabajos_data)

        grafo.agregar_vertice(
            identificador=identificador,
            nombre=nombre,
            ciudad=ciudad,
            pais=pais,
            zona_horaria=zona,
            es_hub=es_hub,
            costo_alojamiento=costo_alojamiento,
            costo_alimentacion=costo_alimentacion,
            actividades=actividades,
            trabajos=trabajos,
        )

    # Case 1: list of airports
    if isinstance(datos, list):
        for a in datos:
            _add_airport(a)

        return grafo

    # Case 2: object with 'nodos' / 'aristas' (Spanish schema)
    if isinstance(datos, dict) and "nodos" in datos:
        for a in datos.get("nodos", []):
            _add_airport(a)

        for ruta in datos.get("aristas", []):
            origen = _get_value(ruta, ["origen", "origin", "from"])
            destino = _get_value(ruta, ["destino", "destination", "to"])
            distancia = _get_value(ruta, ["distanciaKm", "distance_km", "distance"], 0)
            aeronaves = _get_value(ruta, ["aeronaves", "aircraft"], [])
            costo_base = _get_value(ruta, ["costoBase", "costBase"], 0)
            estancia_minima = _get_value(ruta, ["estanciaMinima", "minStay"], 0)
            costo_cero = _get_value(
                ruta,
                ["costoCero", "costoDesplazamientoCero", "rutaSubsidiada", "subsidized", "zeroCost"],
                False,
            )

            if origen and not grafo.existe_vertice(origen):
                grafo.agregar_vertice(identificador=origen)
            if destino and not grafo.existe_vertice(destino):
                grafo.agregar_vertice(identificador=destino)

            if origen and destino:
                grafo.agregar_arista(
                    origen=origen,
                    destino=destino,
                    distancia_km=distancia,
                    aeronaves=aeronaves,
                    costo_base=costo_base,
                    estancia_minima=estancia_minima,
                    costo_cero=costo_cero,
                )

        return grafo

    # Case 3: object with 'airports' / 'routes' (alternate schema)
    if isinstance(datos, dict) and "airports" in datos:
        for a in datos.get("airports", []):
            _add_airport(a)

        for ruta in datos.get("routes", []):
            origen = _get_value(ruta, ["origin", "from"])
            destino = _get_value(ruta, ["destination", "to"])
            distancia = _get_value(ruta, ["distance_km", "distance"], 0)
            aeronaves = _get_value(ruta, ["aeronaves", "aircraft"], [])
            costo_base = _get_value(ruta, ["costoBase", "costBase"], 0)
            estancia_minima = _get_value(ruta, ["estanciaMinima", "minStay"], 0)
            costo_cero = _get_value(
                ruta,
                ["costoCero", "costoDesplazamientoCero", "rutaSubsidiada", "subsidized", "zeroCost"],
                False,
            )

            if origen and not grafo.existe_vertice(origen):
                grafo.agregar_vertice(identificador=origen)
            if destino and not grafo.existe_vertice(destino):
                grafo.agregar_vertice(identificador=destino)

            if origen and destino:
                grafo.agregar_arista(
                    origen=origen,
                    destino=destino,
                    distancia_km=distancia,
                    aeronaves=aeronaves,
                    costo_base=costo_base,
                    estancia_minima=estancia_minima,
                    costo_cero=costo_cero,
                )

        return grafo

    raise ValueError("Unsupported JSON schema for graph data")
