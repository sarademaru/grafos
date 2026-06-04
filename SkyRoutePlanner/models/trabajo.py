from typing import Dict, Any


class Trabajo:
    """
    Represents a temporary work opportunity available to a traveler.

    A work opportunity has a name, hourly rate, and maximum hours that can be worked.
    It allows travelers to earn money when their budget is running low.

    Attributes:
        nombre (str): Name of the work (e.g., 'Tour Guide', 'Airport Assistant').
        tarifa_hora (float): Hourly rate in USD (must be > 0).
        max_horas (float): Maximum hours allowed for this work (must be > 0).
    """

    def __init__(
        self,
        nombre: str,
        tarifa_hora: float,
        max_horas: float,
    ) -> None:
        """
        Initialize a new work opportunity with name, hourly rate, and maximum hours.

        Args:
            nombre: Work name (must be a non-empty string).
            tarifa_hora: Hourly rate in USD (must be positive).
            max_horas: Maximum hours allowed (must be positive).

        Raises:
            ValueError: If nombre is empty, tarifa_hora is not positive,
                       or max_horas is not positive.
        """
        if not nombre or not isinstance(nombre, str):
            raise ValueError("nombre must be a non-empty string")
        
        nombre_normalizado = nombre.strip() if isinstance(nombre, str) else ""
        if not nombre_normalizado:
            raise ValueError("nombre must be a non-empty string")
        
        if tarifa_hora <= 0:
            raise ValueError("tarifa_hora must be positive")
        if max_horas <= 0:
            raise ValueError("max_horas must be positive")

        self.nombre: str = nombre_normalizado
        self.tarifa_hora: float = tarifa_hora
        self.max_horas: float = max_horas

    def calcular_ganancia(self, horas: float) -> float:
        """
        Calculate total earnings for a given number of work hours.

        Validates that the requested hours do not exceed the maximum allowed.

        Args:
            horas: Number of hours worked (must be positive and <= max_horas).

        Returns:
            Total earnings calculated as tarifa_hora × horas.

        Raises:
            ValueError: If horas is negative, zero, or exceeds max_horas.
        """
        if horas <= 0:
            raise ValueError("horas must be positive")
        if horas > self.max_horas:
            raise ValueError(
                f"Cannot work {horas} hours: maximum is {self.max_horas} hours"
            )

        return self.tarifa_hora * horas

    def obtener_resumen(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the work opportunity.

        Returns:
            Dictionary containing:
                - nombre: Work name
                - tarifa_hora: Hourly rate in USD
                - max_horas: Maximum hours allowed
        """
        return {
            "nombre": self.nombre,
            "tarifa_hora": self.tarifa_hora,
            "max_horas": self.max_horas,
        }

    def __str__(self) -> str:
        """Return a human-readable string representation of the work opportunity."""
        return (
            f"{self.nombre} - {self.tarifa_hora} USD/hour - Max. {self.max_horas} hours"
        )

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return (
            f"Trabajo(nombre={self.nombre!r}, "
            f"tarifa_hora={self.tarifa_hora}, "
            f"max_horas={self.max_horas})"
        )

    def __eq__(self, other: Any) -> bool:
        """Check equality based on all attributes."""
        if not isinstance(other, Trabajo):
            return False
        return (
            self.nombre == other.nombre
            and self.tarifa_hora == other.tarifa_hora
            and self.max_horas == other.max_horas
        )

    def __hash__(self) -> int:
        """Make work opportunities hashable for use in sets and dictionaries."""
        return hash((self.nombre, self.tarifa_hora, self.max_horas))
