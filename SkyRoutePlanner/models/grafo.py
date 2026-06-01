from .vertice import Vertice
from .arista import Arista


class Grafo:
    """
    Grafo dirigido implementado mediante lista de adyacencia.
    """

    def __init__(self):
        self.vertices = {}

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

    def __str__(self):
        return f"Grafo con {len(self.vertices)} aeropuertos"