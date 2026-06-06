from .vertice import Vertice
from .arista import Arista


DEFAULT_AERONAVES = {
    "Avion Comercial": {"costoKm": 0.18, "tiempoKm": 0.7 / 60},
    "Avion Regional": {"costoKm": 0.25, "tiempoKm": 1.1 / 60},
    "Helice": {"costoKm": 0.12, "tiempoKm": 2.5 / 60},
}


class Grafo:
    """
    Grafo dirigido implementado mediante lista de adyacencia.
    """

    def __init__(self):
        self.vertices = {}
        self.configuracion = {
            "presupuestoMinimoPorcentaje": 35,
            "intervaloAlimentacionHoras": 8,
            "intervaloHospedajeHoras": 20,
            "aeronaves": dict(DEFAULT_AERONAVES),
        }

    def obtener_configuracion(self):
        """Devuelve la configuración global del grafo."""
        return {
            "presupuestoMinimoPorcentaje": self.configuracion.get("presupuestoMinimoPorcentaje", 35),
            "intervaloAlimentacionHoras": self.configuracion.get("intervaloAlimentacionHoras", 8),
            "intervaloHospedajeHoras": self.configuracion.get("intervaloHospedajeHoras", 20),
            "aeronaves": dict(self.configuracion.get("aeronaves", {})),
        }

    def obtener_aeronaves_disponibles(self):
        """Devuelve los tipos de aeronaves definidos en la configuración."""
        return list(self.configuracion.get("aeronaves", {}).keys())

    def obtener_costo_por_km(self, tipo_aeronave):
        """Devuelve el costo por kilómetro para un tipo de aeronave."""
        aeronave = self.configuracion.get("aeronaves", {}).get(tipo_aeronave, {})
        return aeronave.get("costoKm", 0)

    def obtener_tiempo_por_km(self, tipo_aeronave):
        """Devuelve el tiempo por kilómetro para un tipo de aeronave."""
        aeronave = self.configuracion.get("aeronaves", {}).get(tipo_aeronave, {})
        return aeronave.get("tiempoKm", 0)

    def agregar_vertice(
        self,
        identificador,
        nombre="",
        ciudad="",
        pais="",
        zona_horaria="",
        es_hub=False,
        costo_alojamiento=0,
        costo_alimentacion=0,
        actividades=None,
        trabajos=None,
    ):
        if identificador not in self.vertices:

            self.vertices[identificador] = Vertice(
                identificador=identificador,
                nombre=nombre,
                ciudad=ciudad,
                pais=pais,
                zona_horaria=zona_horaria,
                es_hub=es_hub,
                costo_alojamiento=costo_alojamiento,
                costo_alimentacion=costo_alimentacion,
                actividades=actividades,
                trabajos=trabajos,
            )

        return self.vertices[identificador]

    def agregar_arista(
        self,
        origen,
        destino,
        distancia_km,
        aeronaves=None,
        costo_base=0,
        estancia_minima=0,
        costo_cero=False,
    ):
        if origen not in self.vertices:
            raise ValueError(f"El aeropuerto {origen} no existe")

        if destino not in self.vertices:
            raise ValueError(f"El aeropuerto {destino} no existe")

        arista = Arista(
            vertice_destino=self.vertices[destino],
            distancia_km=distancia_km,
            aeronaves=aeronaves,
            costo_base=costo_base,
            estancia_minima=estancia_minima,
            costo_cero=costo_cero,
        )

        self.vertices[origen].agregar_adyacencia(arista)

    def obtener_vertice(self, identificador):
        return self.vertices.get(identificador)

    def obtener_vertices(self):
        return list(self.vertices.values())

    def existe_vertice(self, identificador):
        return identificador in self.vertices

    def cantidad_vertices(self):
        return len(self.vertices)
    
    def bloquear_arista(self, origen, destino):
        """Bloquea la ruta entre origen y destino."""
        vertice_origen = self.obtener_vertice(origen)
        if vertice_origen:
            for arista in vertice_origen.adyacencias:
                if arista.vertice_destino.identificador == destino:
                    arista.bloquear()
                    return True
        return False
    
    def desbloquear_arista(self, origen, destino):
        """Desbloquea la ruta entre origen y destino."""
        vertice_origen = self.obtener_vertice(origen)
        if vertice_origen:
            for arista in vertice_origen.adyacencias:
                if arista.vertice_destino.identificador == destino:
                    arista.desbloquear()
                    return True
        return False
    
    def obtener_aristas_activas(self, origen):
        """Devuelve las aristas activas desde el aeropuerto de origen."""
        vertice_origen = self.obtener_vertice(origen)
        if vertice_origen:
            return [arista for arista in vertice_origen.adyacencias if arista.esta_activa()]
        return []

    def __str__(self):
        return f"Grafo con {len(self.vertices)} aeropuertos"
