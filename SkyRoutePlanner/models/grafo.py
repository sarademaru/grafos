from .vertice import Vertice
from .arista import Arista


class Grafo:
    """Directed weighted graph implemented with adjacency lists."""

    def __init__(self):
        self.vertices = {}

    def agregar_vertice(self, identificador):
        """Add a vertex by identifier if it does not already exist."""
        if identificador not in self.vertices:
            self.vertices[identificador] = Vertice(identificador)
        return self.vertices[identificador]

    def agregar_arista(self, origen, destino, peso=0):
        """Add a directed edge from origen to destino with an optional weight."""
        if origen not in self.vertices:
            self.agregar_vertice(origen)
        if destino not in self.vertices:
            self.agregar_vertice(destino)

        arista = Arista(self.vertices[destino], peso)
        self.vertices[origen].agregar_adyacencia(arista)

    def obtener_vertice(self, identificador):
        """Return the vertex object for a given identifier."""
        return self.vertices.get(identificador)

    def obtener_vertices(self):
        """Return a list of all vertices in the graph."""
        return list(self.vertices.values())
