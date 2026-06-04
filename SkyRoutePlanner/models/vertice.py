from typing import Any, Dict, List, Optional


class Vertice:
    """
    Represents an airport node in the graph.

    The airport model stores basic location details, economic cost data,
    tourism activities, available jobs, and outgoing route adjacencies.
    """

    def __init__(
        self,
        identificador: str,
        nombre: str = "",
        ciudad: str = "",
        pais: str = "",
        zona_horaria: str = "",
        es_hub: bool = False,
        costo_alojamiento: float = 0,
        costo_alimentacion: float = 0,
        actividades: Optional[List[Any]] = None,
        trabajos: Optional[List[Any]] = None,
    ) -> None:
        if not identificador or not isinstance(identificador, str):
            raise ValueError("identificador must be a non-empty string")
        if costo_alojamiento < 0:
            raise ValueError("costo_alojamiento must be non-negative")
        if costo_alimentacion < 0:
            raise ValueError("costo_alimentacion must be non-negative")

        self.identificador: str = identificador.strip()
        self.nombre: str = nombre
        self.ciudad: str = ciudad
        self.pais: str = pais
        self.zona_horaria: str = zona_horaria
        self.es_hub: bool = es_hub

        self.costo_alojamiento: float = costo_alojamiento
        self.costo_alimentacion: float = costo_alimentacion

        self.actividades: List[Any] = list(actividades) if actividades else []
        self.trabajos: List[Any] = list(trabajos) if trabajos else []

        self.adyacencias: List[Any] = []

    @property
    def codigo(self) -> str:
        """Return the airport code alias for the vertex identifier."""
        return self.identificador

    @codigo.setter
    def codigo(self, value: str) -> None:
        if not value or not isinstance(value, str) or not value.strip():
            raise ValueError("codigo must be a non-empty string")
        self.identificador = value.strip()

    def agregar_actividad(self, actividad: Any) -> None:
        """Add an available activity to this airport."""
        if actividad is None:
            raise ValueError("actividad must not be None")
        self.actividades.append(actividad)

    def agregar_trabajo(self, trabajo: Any) -> None:
        """Add an available job to this airport."""
        if trabajo is None:
            raise ValueError("trabajo must not be None")
        self.trabajos.append(trabajo)

    def obtener_actividades(self) -> List[Any]:
        """Return a copy of the activities available at this airport."""
        return list(self.actividades)

    def obtener_trabajos(self) -> List[Any]:
        """Return a copy of the jobs available at this airport."""
        return list(self.trabajos)

    def obtener_resumen(self) -> Dict[str, Any]:
        """Return a summary dictionary with airport and simulation-related data."""
        actividades = [
            actividad.obtener_resumen()
            if hasattr(actividad, "obtener_resumen")
            else actividad
            for actividad in self.actividades
        ]
        trabajos = [
            trabajo.obtener_resumen()
            if hasattr(trabajo, "obtener_resumen")
            else trabajo
            for trabajo in self.trabajos
        ]

        return {
            "identificador": self.identificador,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "ciudad": self.ciudad,
            "pais": self.pais,
            "zona_horaria": self.zona_horaria,
            "es_hub": self.es_hub,
            "costo_alojamiento": self.costo_alojamiento,
            "costo_alimentacion": self.costo_alimentacion,
            "actividades": actividades,
            "trabajos": trabajos,
            "cantidad_actividades": len(self.actividades),
            "cantidad_trabajos": len(self.trabajos),
            "cantidad_adyacencias": len(self.adyacencias),
        }

    def agregar_adyacencia(self, arista: Any) -> None:
        """Add an outgoing edge from this airport to a destination vertex."""
        self.adyacencias.append(arista)

    def __str__(self) -> str:
        return f"{self.identificador} - {self.ciudad}, {self.pais}"
