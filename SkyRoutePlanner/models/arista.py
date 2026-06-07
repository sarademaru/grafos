class Arista:
    """
    Represents a directed edge in the graph, connecting a source vertex to a destination vertex with attributes such as distance, cost, and availability.
    """

    def __init__(
        self,
        vertice_destino,
        distancia_km,
        aeronaves=None,
        costo_base=0,
        estancia_minima=0,
        costo_cero=False,
        activa=True,
    ):
        self.vertice_destino = vertice_destino
        self.distancia_km = distancia_km
        self.activa = activa
        self.aeronaves = aeronaves if aeronaves else []

        self.costo_base = costo_base
        self.estancia_minima = estancia_minima
        self.costo_cero = bool(costo_cero)

    def obtener_peso(self):
        """
        Calculates the weight of the edge based on its distance and cost attributes, which can be used in pathfinding algorithms to determine the optimal route.
        """
        return self.distancia_km

    def __str__(self):
        return (
            f"{self.vertice_destino.identificador} "
            f"({self.distancia_km} km)"
        )
    def bloquear(self):
        """Blocks the route, preventing its use in the planner."""
        self.activa = False
    def desbloquear(self):
        """Unblocks the route, allowing its use in the planner."""
        self.activa = True  
    def esta_activa(self):
        """Indicates if the route is active and available for planning."""
        return self.activa
    def esta_bloqueada(self):
        """Indicates if the route is blocked and not available for planning."""
        return not self.activa