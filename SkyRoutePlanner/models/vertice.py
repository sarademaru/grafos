class Vertice:
    """
    Representa un aeropuerto dentro del grafo.
    Cada vértice almacena su información y las rutas salientes.
    """

    def __init__(
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
        self.identificador = identificador
        self.nombre = nombre
        self.ciudad = ciudad
        self.pais = pais
        self.zona_horaria = zona_horaria
        self.es_hub = es_hub

        self.costo_alojamiento = costo_alojamiento
        self.costo_alimentacion = costo_alimentacion

        self.actividades = actividades if actividades else []
        self.trabajos = trabajos if trabajos else []

        self.adyacencias = []

    def agregar_adyacencia(self, arista):
        """Agrega una ruta saliente."""
        self.adyacencias.append(arista)

    def __str__(self):
        return f"{self.identificador} - {self.ciudad}, {self.pais}"