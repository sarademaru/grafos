from typing import Dict, List, Optional, Any


class Viajero:
    """
    Represents a traveler in the flight network simulation.

    A traveler has a budget, time available, and can perform activities
    and work to manage their finances during their journey through airports.

    Attributes:
        presupuesto_inicial (float): Initial budget amount in currency units.
        presupuesto_actual (float): Current budget available.
        tiempo_total_horas (float): Total time available for the journey in hours.
        tiempo_restante_horas (float): Remaining time available in hours.
        gasto_total (float): Total amount spent during the journey.
        ingreso_total (float): Total amount earned through work during the journey.
        aeropuertos_visitados (list): List of airport codes visited in order.
        actividades_realizadas (list): List of activities performed.
        trabajos_realizados (list): List of work sessions completed.
    """

    def __init__(
        self,
        presupuesto_inicial: float,
        tiempo_total_horas: float,
    ) -> None:
        """
        Initialize a new traveler with initial budget and available time.

        Args:
            presupuesto_inicial: Starting budget amount (must be positive).
            tiempo_total_horas: Total time available in hours (must be positive).

        Raises:
            ValueError: If presupuesto_inicial or tiempo_total_horas are not positive.
        """
        if presupuesto_inicial <= 0:
            raise ValueError("presupuesto_inicial must be positive")
        if tiempo_total_horas <= 0:
            raise ValueError("tiempo_total_horas must be positive")

        self.presupuesto_inicial: float = presupuesto_inicial
        self.presupuesto_actual: float = presupuesto_inicial
        self.tiempo_total_horas: float = tiempo_total_horas
        self.tiempo_restante_horas: float = tiempo_total_horas
        self.gasto_total: float = 0.0
        self.ingreso_total: float = 0.0

        self.aeropuertos_visitados: List[str] = []
        self.actividades_realizadas: List[Dict[str, Any]] = []
        self.trabajos_realizados: List[Dict[str, Any]] = []
        self.tiempo_libre_registrado: List[Dict[str, Any]] = []

    def gastar(self, cantidad: float) -> None:
        """
        Deduct money from the current budget.

        Updates the total spending counter. Does not allow spending
        more than the current available budget.

        Args:
            cantidad: Amount to spend (must be positive and not exceed current budget).

        Raises:
            ValueError: If cantidad is not positive or exceeds available budget.
        """
        if cantidad < 0:
            raise ValueError("Spending amount must be non-negative")
        if cantidad > self.presupuesto_actual:
            raise ValueError(
                f"Cannot spend {cantidad}: only {self.presupuesto_actual} available"
            )

        self.presupuesto_actual -= cantidad
        self.gasto_total += cantidad

    def ganar(self, cantidad: float) -> None:
        """
        Add money to the current budget.

        Updates the total income counter. Typically used when completing
        work or other income-generating activities.

        Args:
            cantidad: Amount to add (must be non-negative).

        Raises:
            ValueError: If cantidad is negative.
        """
        if cantidad < 0:
            raise ValueError("Income amount must be non-negative")

        self.presupuesto_actual += cantidad
        self.ingreso_total += cantidad

    def consumir_tiempo(self, horas: float) -> None:
        """
        Reduce the remaining available time.

        Args:
            horas: Hours to consume (must be positive and not exceed remaining time).

        Raises:
            ValueError: If horas is not positive or exceeds remaining time.
        """
        if horas < 0:
            raise ValueError("Time consumption must be non-negative")
        if horas > self.tiempo_restante_horas:
            raise ValueError(
                f"Cannot consume {horas} hours: only {self.tiempo_restante_horas} available"
            )

        self.tiempo_restante_horas -= horas

    def registrar_aeropuerto(self, codigo_aeropuerto: str) -> None:
        """
        Record a visited airport.

        Prevents consecutive duplicates (same airport visited twice in a row).

        Args:
            codigo_aeropuerto: Airport IATA code (e.g., 'BOG', 'MDE').

        Raises:
            ValueError: If codigo_aeropuerto is empty or None.
        """
        if not codigo_aeropuerto or not isinstance(codigo_aeropuerto, str):
            raise ValueError("Airport code must be a non-empty string")

        codigo_normalizado = codigo_aeropuerto.upper().strip()

        # Avoid consecutive duplicates
        if (
            self.aeropuertos_visitados
            and self.aeropuertos_visitados[-1] == codigo_normalizado
        ):
            return

        self.aeropuertos_visitados.append(codigo_normalizado)

    def registrar_actividad(
        self,
        actividad: Dict[str, Any],
    ) -> None:
        """
        Record and execute an activity.

        Automatically deducts the associated cost and time from the traveler's
        budget and available time.

        Args:
            actividad: Dictionary containing at least:
                - 'nombre': Activity name
                - 'costo': Cost in currency units (non-negative)
                - 'tiempo_horas': Time required in hours (non-negative)

        Raises:
            ValueError: If actividad is invalid or resources are insufficient.
        """
        if not isinstance(actividad, dict):
            raise ValueError("Activity must be a dictionary")

        nombre = actividad.get("nombre")
        costo = actividad.get("costo", 0)
        tiempo_horas = actividad.get("tiempo_horas", 0)

        if not nombre or not isinstance(nombre, str):
            raise ValueError("Activity must have a valid 'nombre' field")
        if costo < 0:
            raise ValueError("Activity cost cannot be negative")
        if tiempo_horas < 0:
            raise ValueError("Activity time cannot be negative")

        # Check resources before deducting
        if costo > self.presupuesto_actual:
            raise ValueError(
                f"Insufficient budget for activity '{nombre}': "
                f"need {costo}, have {self.presupuesto_actual}"
            )
        if tiempo_horas > self.tiempo_restante_horas:
            raise ValueError(
                f"Insufficient time for activity '{nombre}': "
                f"need {tiempo_horas} hours, have {self.tiempo_restante_horas} hours"
            )

        # Deduct cost and time
        self.gastar(costo)
        self.consumir_tiempo(tiempo_horas)

        # Record activity with metadata
        actividad_registrada = {
            "nombre": nombre,
            "costo": costo,
            "tiempo_horas": tiempo_horas,
            **{k: v for k, v in actividad.items() if k not in ["nombre", "costo", "tiempo_horas"]},
        }
        self.actividades_realizadas.append(actividad_registrada)

    def registrar_trabajo(
        self,
        trabajo: Dict[str, Any],
        horas: float,
    ) -> None:
        """
        Record and execute a work session.

        Calculates earnings based on hourly rate × hours worked.
        Updates budget and deducts time consumed.

        Args:
            trabajo: Dictionary containing at least:
                - 'descripcion': Work description
                - 'tarifa_hora': Hourly rate (non-negative)
            horas: Number of hours worked (must be positive and not exceed available time).

        Raises:
            ValueError: If trabajo is invalid, horas is invalid, or insufficient time available.
        """
        if not isinstance(trabajo, dict):
            raise ValueError("Work must be a dictionary")

        descripcion = trabajo.get("descripcion")
        tarifa_hora = trabajo.get("tarifa_hora", 0)

        if not descripcion or not isinstance(descripcion, str):
            raise ValueError("Work must have a valid 'descripcion' field")
        if tarifa_hora < 0:
            raise ValueError("Hourly rate cannot be negative")
        if horas <= 0:
            raise ValueError("Work hours must be positive")
        if horas > self.tiempo_restante_horas:
            raise ValueError(
                f"Insufficient time for work: need {horas} hours, "
                f"have {self.tiempo_restante_horas} hours"
            )

        # Calculate earnings and update budget
        ganancia = tarifa_hora * horas
        self.ganar(ganancia)
        self.consumir_tiempo(horas)

        # Record work session
        trabajo_registrado = {
            "descripcion": descripcion,
            "tarifa_hora": tarifa_hora,
            "horas_trabajadas": horas,
            "ganancia": ganancia,
            **{k: v for k, v in trabajo.items() if k not in ["descripcion", "tarifa_hora"]},
        }
        self.trabajos_realizados.append(trabajo_registrado)

    def registrar_tiempo_libre(self, evento: Dict[str, Any]) -> None:
        """Record free time spent at an airport."""
        if not isinstance(evento, dict):
            raise ValueError("Free time event must be a dictionary")

        aeropuerto = evento.get("aeropuerto")
        duracion_horas = float(evento.get("duracion_horas", 0) or 0)
        if not aeropuerto or not isinstance(aeropuerto, str):
            raise ValueError("Free time event must have a valid airport")
        if duracion_horas <= 0:
            raise ValueError("Free time duration must be positive")

        self.consumir_tiempo(duracion_horas)
        self.tiempo_libre_registrado.append(
            {
                "aeropuerto": aeropuerto.upper().strip(),
                "duracion_horas": duracion_horas,
                **{k: v for k, v in evento.items() if k not in ["aeropuerto", "duracion_horas"]},
            }
        )

    def presupuesto_bajo(self, porcentaje_minimo: float = 35) -> bool:
        """
        Check if the current budget is below the minimum threshold.

        The threshold percentage is supplied by configuration and defaults
        to 35 for backwards compatibility.

        Returns:
            True if current budget <= configured percentage of initial budget.
        """
        umbral_minimo = self.presupuesto_inicial * (float(porcentaje_minimo) / 100)
        return self.presupuesto_actual <= umbral_minimo

    def obtener_resumen(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the traveler's journey state.

        Returns:
            Dictionary containing:
                - presupuesto_inicial: Initial budget amount
                - presupuesto_actual: Current budget
                - gasto_total: Total spent
                - ingreso_total: Total earned
                - tiempo_total_horas: Total time available
                - tiempo_restante_horas: Remaining time
                - cantidad_aeropuertos_visitados: Number of airports visited
                - cantidad_actividades: Number of activities completed
                - cantidad_trabajos: Number of work sessions completed
        """
        return {
            "presupuesto_inicial": self.presupuesto_inicial,
            "presupuesto_actual": self.presupuesto_actual,
            "gasto_total": self.gasto_total,
            "ingreso_total": self.ingreso_total,
            "tiempo_total_horas": self.tiempo_total_horas,
            "tiempo_restante_horas": self.tiempo_restante_horas,
            "cantidad_aeropuertos_visitados": len(self.aeropuertos_visitados),
            "cantidad_actividades": len(self.actividades_realizadas),
            "cantidad_trabajos": len(self.trabajos_realizados),
            "aeropuertos_visitados": list(self.aeropuertos_visitados),
            "actividades_realizadas": list(self.actividades_realizadas),
            "trabajos_realizados": list(self.trabajos_realizados),
            "tiempo_libre_registrado": list(self.tiempo_libre_registrado),
        }

    def __str__(self) -> str:
        """Return a human-readable string representation of the traveler's status."""
        return (
            f"Traveler(Budget: ${self.presupuesto_actual:.2f}|"
            f"Time: {self.tiempo_restante_horas:.1f}h|"
            f"Airports: {len(self.aeropuertos_visitados)})"
        )

    def __repr__(self) -> str:
        """Return a developer-friendly string representation."""
        return (
            f"Viajero(presupuesto_inicial={self.presupuesto_inicial}, "
            f"presupuesto_actual={self.presupuesto_actual}, "
            f"tiempo_total_horas={self.tiempo_total_horas}, "
            f"tiempo_restante_horas={self.tiempo_restante_horas})"
        )
