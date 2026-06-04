import json
from pathlib import Path

from models.grafo import Grafo


def _get_value(dct, keys, default=None):
    for k in keys:
        if k in dct:
            return dct[k]
    return default


def _normalize_aeronaves_config(aeronaves_config):
    normalized = {}
    if not isinstance(aeronaves_config, dict):
        return normalized

    for tipo, datos in aeronaves_config.items():
        if not isinstance(datos, dict):
            continue
        normalized[tipo] = {
            "costoKm": _get_value(datos, ["costoKm", "costPerKm", "cost_per_km"], 0),
            "tiempoKm": _get_value(datos, ["tiempoKm", "timePerKm", "time_per_km"], 0),
        }
    return normalized


def _parse_configuracion(datos):
    configuracion = _get_value(datos, ["configuracion", "configuration"], {})
    if not isinstance(configuracion, dict):
        return {
            "presupuestoMinimoPorcentaje": 35,
            "intervaloAlimentacionHoras": 8,
            "intervaloHospedajeHoras": 20,
            "aeronaves": {},
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
        actividades = _get_value(a, ["actividades"], [])
        trabajos = _get_value(a, ["trabajos"], [])

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

            if origen and not grafo.existe_vertice(origen):
                grafo.agregar_vertice(identificador=origen)
            if destino and not grafo.existe_vertice(destino):
                grafo.agregar_vertice(identificador=destino)

            if origen and destino:
                grafo.agregar_arista(
                    origen=origen,
                    destino=destino,
                    distancia_km=distancia,
                )

        return grafo

    raise ValueError("Unsupported JSON schema for graph data")