class Arista:
    """
    Representa una ruta aérea dirigida entre dos aeropuertos.
    """

    def __init__(
        self,
        vertice_destino,
        distancia_km,
        aeronaves=None,
        costo_base=0,
        estancia_minima=0,
        costo_cero=False,
    ):
        self.vertice_destino = vertice_destino
        self.distancia_km = distancia_km

        self.aeronaves = aeronaves if aeronaves else []

        self.costo_base = costo_base
        self.estancia_minima = estancia_minima
        self.costo_cero = bool(costo_cero)

    def obtener_peso(self):
        """
        Peso genérico para algoritmos.
        Inicialmente se usa la distancia.
        """
        return self.distancia_km

    def __str__(self):
        return (
            f"{self.vertice_destino.identificador} "
            f"({self.distancia_km} km)"
        )
