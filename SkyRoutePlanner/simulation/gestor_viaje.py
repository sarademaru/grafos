from typing import List, Optional, Dict, Any

from models.grafo import Grafo
from models.viajero import Viajero
from models.actividad import Actividad
from models.trabajo import Trabajo


class GestorViaje:
    """Orquesta un viaje: registra llegadas, actividades y trabajos.

    Attributes:
        grafo: Grafo en el que se opera.
        viajero: Viajero que realiza el viaje.
        ruta_actual: Lista de códigos de aeropuertos en la ruta planificada.
        indice_actual: Índice del aeropuerto actual en `ruta_actual` o None.
    """

    def __init__(self, grafo: Grafo, viajero: Viajero) -> None:
        self.grafo = grafo
        self.viajero = viajero
        self.ruta_actual: List[str] = []
        self.indice_actual: Optional[int] = None

    def iniciar_viaje(self, ruta: List[str]) -> None:
        """Inicia el viaje con una ruta (lista de códigos de aeropuerto).

        Registra la llegada al primer aeropuerto automáticamente.
        """
        if not ruta:
            raise ValueError("La ruta no puede estar vacía")
        self.ruta_actual = [c.upper().strip() for c in ruta]
        self.indice_actual = 0
        codigo = self.ruta_actual[0]
        self.registrar_llegada(codigo)

    def registrar_llegada(self, codigo_aeropuerto: str) -> None:
        """Registrar llegada del viajero a un aeropuerto dado por código.

        Actualiza el estado interno y notifica al `Viajero`.
        """
        if not codigo_aeropuerto:
            raise ValueError("Código de aeropuerto inválido")
        codigo = codigo_aeropuerto.upper().strip()
        # Actualizar índice si forma parte de la ruta
        if self.ruta_actual and codigo in self.ruta_actual:
            self.indice_actual = self.ruta_actual.index(codigo)
        else:
            # si no está en la ruta, añadimos al final y posicionamos allí
            self.ruta_actual.append(codigo)
            self.indice_actual = len(self.ruta_actual) - 1

        # Notificar al viajero
        self.viajero.registrar_aeropuerto(codigo)

    def _actividad_a_dict(self, actividad: Actividad) -> Dict[str, Any]:
        return {
            "nombre": actividad.nombre,
            "costo": actividad.costo_usd,
            "tiempo_horas": actividad.duracion_horas,
        }

    def _trabajo_a_dict(self, trabajo: Trabajo) -> Dict[str, Any]:
        return {
            "descripcion": trabajo.nombre,
            "tarifa_hora": trabajo.tarifa_hora,
        }

    def realizar_actividad(self, actividad: Any) -> None:
        """Realiza una actividad: acepta `Actividad` o diccionario compatible.

        Convierte objetos de dominio a la forma esperada por `Viajero`.
        """
        if isinstance(actividad, Actividad):
            actividad_dict = self._actividad_a_dict(actividad)
        elif isinstance(actividad, dict):
            actividad_dict = actividad
        else:
            raise ValueError("Actividad debe ser Actividad o dict compatible")

        # Delegar la ejecución al viajero (podrá lanzar ValueError si insuficientes recursos)
        self.viajero.registrar_actividad(actividad_dict)

    def realizar_trabajo(self, trabajo: Any, horas: float) -> None:
        """Realiza un trabajo: acepta `Trabajo` o dict compatible y horas a trabajar.

        Convierte objetos de dominio a la forma esperada por `Viajero`.
        """
        if isinstance(trabajo, Trabajo):
            trabajo_dict = self._trabajo_a_dict(trabajo)
        elif isinstance(trabajo, dict):
            trabajo_dict = trabajo
        else:
            raise ValueError("Trabajo debe ser Trabajo o dict compatible")

        # Delegar la ejecución al viajero
        self.viajero.registrar_trabajo(trabajo_dict, horas)

    def obtener_estado(self) -> Dict[str, Any]:
        """Devuelve el estado actual del gestor y del viajero.

        Incluye resumen del `Viajero`, código del aeropuerto actual y la ruta.
        """
        estado_viajero = self.viajero.obtener_resumen()
        aeropuerto_actual = None
        if self.indice_actual is not None and self.ruta_actual:
            aeropuerto_actual = self.ruta_actual[self.indice_actual]

        return {
            "viajero": estado_viajero,
            "aeropuerto_actual": aeropuerto_actual,
            "ruta_actual": list(self.ruta_actual),
            "indice_actual": self.indice_actual,
        }
