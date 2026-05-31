class Vertice:
    """A graph vertex with a list of outgoing adjacency edges."""

    def __init__(self, identificador):
        self.identificador = identificador
        self.adyacencias = []

    def agregar_adyacencia(self, arista):
        """Add an adjacency edge to this vertex."""
        self.adyacencias.append(arista)
