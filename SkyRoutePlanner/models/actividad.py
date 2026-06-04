from typing import Dict, Any


class Actividad:
    """
    Represents a tourist activity available at an airport.

    An activity has a name, duration in hours, and cost in USD.
    It can be performed by a traveler to spend time and money while
    gaining memorable experiences during their journey.

    Attributes:
        nombre (str): Name of the activity (e.g., 'City Tour', 'Museum Visit').
        duracion_horas (float): Duration of the activity in hours (must be > 0).
        costo_usd (float): Cost of the activity in USD (must be >= 0).
    """

    def __init__(
        self,
        nombre: str,
        duracion_horas: float,
        costo_usd: float,
    ) -> None:
        """
        Initialize a new activity with name, duration, and cost.

        Args:
            nombre: Activity name (must be a non-empty string).
            duracion_horas: Duration in hours (must be positive).
            costo_usd: Cost in USD (must be non-negative).

        Raises:
            ValueError: If nombre is empty, duracion_horas is not positive,
                       or costo_usd is negative.
        """
        if not nombre or not isinstance(nombre, str):
            raise ValueError("nombre must be a non-empty string")
        
        nombre_normalizado = nombre.strip() if isinstance(nombre, str) else ""
        if not nombre_normalizado:
            raise ValueError("nombre must be a non-empty string")
        
        if duracion_horas <= 0:
            raise ValueError("duracion_horas must be positive")
        if costo_usd < 0:
            raise ValueError("costo_usd must be non-negative")

        self.nombre: str = nombre_normalizado
        self.duracion_horas: float = duracion_horas
        self.costo_usd: float = costo_usd

    def obtener_resumen(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the activity.

        Returns:
            Dictionary containing:
                - nombre: Activity name
                - duracion_horas: Duration in hours
                - costo_usd: Cost in USD
        """
        return {
            "nombre": self.nombre,
            "duracion_horas": self.duracion_horas,
            "costo_usd": self.costo_usd,
        }

    def __str__(self) -> str:
        """Return a human-readable string representation of the activity."""
        return (
            f"{self.nombre} ({self.duracion_horas}h, ${self.costo_usd:.2f})"
        )

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return (
            f"Actividad(nombre={self.nombre!r}, "
            f"duracion_horas={self.duracion_horas}, "
            f"costo_usd={self.costo_usd})"
        )

    def __eq__(self, other: Any) -> bool:
        """Check equality based on all attributes."""
        if not isinstance(other, Actividad):
            return False
        return (
            self.nombre == other.nombre
            and self.duracion_horas == other.duracion_horas
            and self.costo_usd == other.costo_usd
        )

    def __hash__(self) -> int:
        """Make activities hashable for use in sets and dictionaries."""
        return hash((self.nombre, self.duracion_horas, self.costo_usd))