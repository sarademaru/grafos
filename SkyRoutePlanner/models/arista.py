class Arista:
    """A directed weighted edge connecting one vertex to another."""

    def __init__(self, vertice_destino, peso=0):
        self.vertice_destino = vertice_destino
        self.peso = peso

    def getPeso(self):
        """Return the weight of the edge."""
        return self.peso
