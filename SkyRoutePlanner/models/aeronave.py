class Aeronave:
    """Represents an aircraft used for itinerary planning."""

    def __init__(self, identificador, capacidad, rango_km):
        self.identificador = identificador
        self.capacidad = capacidad
        self.rango_km = rango_km
