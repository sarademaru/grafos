from typing import List, Optional, Dict, Any

from models.grafo import Grafo
from models.viajero import Viajero
from models.actividad import Actividad
from models.trabajo import Trabajo


class GestorViaje:
    """Orchestras a trip: registers arrivals, activities, and jobs.

    Attributes:
        grafo: Graph in which the operations are performed.
        viajero: Traveler who is taking the trip.
        ruta_actual: List of airport codes in the planned route.
        indice_actual: Index of the current airport in `ruta_actual` or None.
    """

    def __init__(self, grafo: Grafo, viajero: Viajero) -> None:
        self.grafo = grafo
        self.viajero = viajero
        self.ruta_actual: List[str] = []
        self.indice_actual: Optional[int] = None

        # Estado adicional para viaje dinamico paso a paso.
        self.tiempo_transcurrido_horas: float = 0.0
        self.horas_desde_ultima_alimentacion: float = 0.0
        self.horas_desde_ultimo_hospedaje: float = 0.0
        self.distancia_volada_km: float = 0.0
        self.distancia_subsidiada_km: float = 0.0
        self.ultimo_aeropuerto_visitado: Optional[str] = None
        self.estancia_minima_actual_horas: float = 0.0
        self.tiempo_estancia_actual_horas: float = 0.0
        self.decisiones: List[Dict[str, Any]] = []
        self.estado_movimiento: str = "en_aeropuerto"
        self.vuelo_actual: Optional[Dict[str, Any]] = None

    def iniciar_viaje(self, ruta: List[str]) -> None:
        """Initiates the trip with a route (list of airport codes).

        Automatically registers the arrival at the first airport.
        """
        if not ruta:
            raise ValueError("The route cannot be empty")
        self.ruta_actual = [c.upper().strip() for c in ruta]
        self.indice_actual = 0
        self.estado_movimiento = "en_aeropuerto"
        self.vuelo_actual = None
        codigo = self.ruta_actual[0]
        self.registrar_llegada(codigo)

    def registrar_llegada(self, codigo_aeropuerto: str) -> None:
        """Registers the traveler's arrival at an airport given by code.

        Updates the internal state and notifies the `Viajero`.
        """
        if not codigo_aeropuerto:
            raise ValueError("Codigo de aeropuerto invalido")
        codigo = codigo_aeropuerto.upper().strip()
        # Actualizar indice si forma parte de la ruta
        if self.ruta_actual and codigo in self.ruta_actual:
            self.indice_actual = self.ruta_actual.index(codigo)
        else:
            # si no esta en la ruta, anadimos al final y posicionamos alli
            self.ruta_actual.append(codigo)
            self.indice_actual = len(self.ruta_actual) - 1

        # Notificar al viajero
        self.viajero.registrar_aeropuerto(codigo)
        self.ultimo_aeropuerto_visitado = codigo

    """Auxiliary methods for converting activities and jobs to dictionaries compatible with Viajero, normalizing records, and checking if they have already been performed."""
    def _actividad_a_dict(self, actividad: Actividad) -> Dict[str, Any]:
        return {
            "nombre": actividad.nombre,
            "costo": actividad.costo_usd,
            "tiempo_horas": actividad.duracion_horas,
        }

    """Auxiliary methods for converting activities and jobs to dictionaries compatible with Viajero, normalizing records, and checking if they have already been performed."""
    def _trabajo_a_dict(self, trabajo: Trabajo) -> Dict[str, Any]:
        return {
            "descripcion": trabajo.nombre,
            "tarifa_hora": trabajo.tarifa_hora,
            "max_horas": trabajo.max_horas,
        }
    
    """Auxiliary method to normalize the minimum stay time in hours, ensuring it is non-negative."""
    def _normalizar_texto_registro(self, valor: Any) -> str:
        return str(valor or "").strip().lower()
    
    """Auxiliary method to normalize numeric values in records, converting them to floats and treating None or empty as 0. """
    def _normalizar_numero_registro(self, valor: Any) -> float:
        return float(valor or 0)
    
    """Auxiliary method to normalize the minimum stay time in hours, ensuring it is non-negative."""

    def _actividad_ya_realizada(self, actividad_dict: Dict[str, Any], aeropuerto_actual: str) -> bool:
        nombre = self._normalizar_texto_registro(actividad_dict.get("nombre"))
        aeropuerto = self._normalizar_texto_registro(aeropuerto_actual)
        costo = self._normalizar_numero_registro(actividad_dict.get("costo"))
        tiempo_horas = self._normalizar_numero_registro(actividad_dict.get("tiempo_horas"))
        return any(
            self._normalizar_texto_registro(registro.get("nombre")) == nombre
            and self._normalizar_texto_registro(registro.get("aeropuerto")) == aeropuerto
            and self._normalizar_numero_registro(registro.get("costo")) == costo
            and self._normalizar_numero_registro(registro.get("tiempo_horas")) == tiempo_horas
            for registro in self.viajero.actividades_realizadas
        )
    
    """Auxiliary method to check if a job has already been performed at the current airport, based on its description, hourly rate, and maximum hours."""
    def _trabajo_ya_realizado(self, trabajo_dict: Dict[str, Any], aeropuerto_actual: str) -> bool:
        descripcion = self._normalizar_texto_registro(trabajo_dict.get("descripcion"))
        aeropuerto = self._normalizar_texto_registro(aeropuerto_actual)
        tarifa_hora = self._normalizar_numero_registro(trabajo_dict.get("tarifa_hora"))
        max_horas = self._normalizar_numero_registro(trabajo_dict.get("max_horas"))
        return any(
            self._normalizar_texto_registro(registro.get("descripcion")) == descripcion
            and self._normalizar_texto_registro(registro.get("aeropuerto")) == aeropuerto
            and self._normalizar_numero_registro(registro.get("tarifa_hora")) == tarifa_hora
            and self._normalizar_numero_registro(registro.get("max_horas")) == max_horas
            for registro in self.viajero.trabajos_realizados
        )

    """Registers the performance of an activity, accepting either an `Actividad` object or a compatible dictionary. Converts domain objects to the expected form for `Viajero` and updates the internal state accordingly."""
    def realizar_actividad(self, actividad: Any) -> Dict[str, Any]:
      
        if isinstance(actividad, Actividad):
            actividad_dict = self._actividad_a_dict(actividad)
        elif isinstance(actividad, dict):
            actividad_dict = dict(actividad)
        else:
            raise ValueError("Actividad debe ser Actividad o dict compatible")

        tiempo_actividad = float(actividad_dict.get("tiempo_horas", 0) or 0)
        costo_actividad = float(actividad_dict.get("costo", 0) or 0)
        aeropuerto_actual = self._obtener_codigo_actual()
        if self._actividad_ya_realizada(actividad_dict, aeropuerto_actual):
            raise ValueError("La actividad ya fue realizada en este aeropuerto")
        actividad_dict.setdefault("aeropuerto", aeropuerto_actual)
        actividad_dict.setdefault("instante_simulacion", self.tiempo_transcurrido_horas)

        # Delegar la ejecucion al viajero (podra lanzar ValueError si insuficientes recursos)
        self.viajero.registrar_actividad(actividad_dict)
        self._registrar_tiempo_operacion(tiempo_actividad)

        decision = {
            "tipo": "actividad",
            "actividad": actividad_dict.get("nombre", "Actividad"),
            "aeropuerto": aeropuerto_actual,
            "duracion_horas": tiempo_actividad,
            "costo": costo_actividad,
            "tiempo": self.tiempo_transcurrido_horas,
            "presupuesto_restante": self.viajero.presupuesto_actual,
            "tiempo_restante_horas": self.viajero.tiempo_restante_horas,
        }
        self.decisiones.append(decision)
        return decision


    """Registers the omission of an activity, accepting either an `Actividad` object or a compatible dictionary. Converts domain objects to the expected form for `Viajero` and updates the internal state accordingly."""
    def omitir_actividad(self, actividad: Any) -> Dict[str, Any]:
        nombre = getattr(actividad, "nombre", None)
        if isinstance(actividad, dict):
            nombre = actividad.get("nombre", nombre)
        decision = {
            "tipo": "actividad_omitida",
            "actividad": nombre or "Actividad",
            "aeropuerto": self._obtener_codigo_actual(),
            "tiempo": self.tiempo_transcurrido_horas,
            "presupuesto_restante": self.viajero.presupuesto_actual,
            "tiempo_restante_horas": self.viajero.tiempo_restante_horas,
        }
        self.decisiones.append(decision)
        return decision

    """Registers the performance of a job, accepting either a `Trabajo` object or a compatible dictionary. Converts domain objects to the expected form for `Viajero` and updates the internal state accordingly."""
    def realizar_trabajo(self, trabajo: Any, horas: float) -> Dict[str, Any]:
        
        if isinstance(trabajo, Trabajo):
            trabajo_dict = self._trabajo_a_dict(trabajo)
        elif isinstance(trabajo, dict):
            trabajo_dict = dict(trabajo)
            if "descripcion" not in trabajo_dict and "nombre" in trabajo_dict:
                trabajo_dict["descripcion"] = trabajo_dict["nombre"]
        else:
            raise ValueError("Trabajo debe ser Trabajo o dict compatible")

        if not self.puede_trabajar():
            raise ValueError("Solo se puede trabajar cuando el presupuesto esta por debajo del minimo configurado")

        horas_trabajadas = float(horas)
        tarifa_hora = float(trabajo_dict.get("tarifa_hora", 0) or 0)
        max_horas = trabajo_dict.get("max_horas")
        if max_horas is not None and horas_trabajadas > float(max_horas):
            raise ValueError(f"No se pueden trabajar {horas_trabajadas:g} horas: maximo {float(max_horas):g}")
        aeropuerto_actual = self._obtener_codigo_actual()
        if self._trabajo_ya_realizado(trabajo_dict, aeropuerto_actual):
            raise ValueError("El trabajo ya fue realizado en este aeropuerto")
        trabajo_dict.setdefault("aeropuerto", aeropuerto_actual)
        trabajo_dict.setdefault("instante_simulacion", self.tiempo_transcurrido_horas)

        # Delegar la ejecucion al viajero
        self.viajero.registrar_trabajo(trabajo_dict, horas)
        self._registrar_tiempo_operacion(horas_trabajadas)

        decision = {
            "tipo": "trabajo",
            "trabajo": trabajo_dict.get("descripcion", "Trabajo"),
            "aeropuerto": aeropuerto_actual,
            "horas": horas_trabajadas,
            "tarifa_hora": tarifa_hora,
            "ingreso": tarifa_hora * horas_trabajadas,
            "tiempo": self.tiempo_transcurrido_horas,
            "presupuesto_restante": self.viajero.presupuesto_actual,
            "tiempo_restante_horas": self.viajero.tiempo_restante_horas,
        }
        self.decisiones.append(decision)
        return decision


    """Registers the omission of a job, accepting either a `Trabajo` object or a compatible dictionary. Converts domain objects to the expected form for `Viajero` and updates the internal state accordingly."""
    def rechazar_trabajo(self, trabajo: Any) -> Dict[str, Any]:
        nombre = getattr(trabajo, "nombre", None)
        if isinstance(trabajo, dict):
            nombre = trabajo.get("descripcion", trabajo.get("nombre", nombre))
        decision = {
            "tipo": "trabajo_rechazado",
            "trabajo": nombre or "Trabajo",
            "aeropuerto": self._obtener_codigo_actual(),
            "tiempo": self.tiempo_transcurrido_horas,
            "presupuesto_restante": self.viajero.presupuesto_actual,
            "tiempo_restante_horas": self.viajero.tiempo_restante_horas,
        }
        self.decisiones.append(decision)
        return decision
    """Auxiliary method to check if the traveler can work based on their current budget and the minimum percentage configured for working."""
    def puede_trabajar(self) -> bool:
        configuracion = self.grafo.obtener_configuracion()
        porcentaje = configuracion.get("presupuestoMinimoPorcentaje", 35)
        return self.viajero.presupuesto_bajo(porcentaje)
    
    """Auxiliary method to obtain the current airport code based on the route and index, or None if not available."""
    def registrar_tiempo_libre_pendiente(self) -> Optional[Dict[str, Any]]:
        tiempo_libre = self.estancia_minima_actual_horas - self.tiempo_estancia_actual_horas
        if tiempo_libre <= 1e-9:
            return None

        aeropuerto_actual = self._obtener_codigo_actual()
        evento = {
            "tipo": "tiempo_libre",
            "aeropuerto": aeropuerto_actual,
            "duracion_horas": tiempo_libre,
            "tiempo": self.tiempo_transcurrido_horas + tiempo_libre,
        }
        self.viajero.registrar_tiempo_libre(evento)
        self._registrar_tiempo_operacion(tiempo_libre)
        evento["presupuesto_restante"] = self.viajero.presupuesto_actual
        evento["tiempo_restante_horas"] = self.viajero.tiempo_restante_horas
        self.decisiones.append(evento)
        return evento


    """Auxiliary method to obtain the current airport code based on the route and index, or None if not available."""
    def obtener_estado(self) -> Dict[str, Any]:
       
        estado_viajero = self.viajero.obtener_resumen()
        aeropuerto_actual = None
        if self.indice_actual is not None and self.ruta_actual:
            aeropuerto_actual = self.ruta_actual[self.indice_actual]

        return {
            "viajero": estado_viajero,
            "aeropuerto_actual": aeropuerto_actual,
            "ruta_actual": list(self.ruta_actual),
            "indice_actual": self.indice_actual,
            "tiempo_transcurrido_horas": self.tiempo_transcurrido_horas,
            "horas_desde_ultima_alimentacion": self.horas_desde_ultima_alimentacion,
            "horas_desde_ultimo_hospedaje": self.horas_desde_ultimo_hospedaje,
            "distancia_volada_km": self.distancia_volada_km,
            "distancia_subsidiada_km": self.distancia_subsidiada_km,
            "estancia_minima_actual_horas": self.estancia_minima_actual_horas,
            "tiempo_estancia_actual_horas": self.tiempo_estancia_actual_horas,
            "actividades_realizadas": list(self.viajero.actividades_realizadas),
            "trabajos_realizados": list(self.viajero.trabajos_realizados),
            "tiempo_libre_registrado": list(self.viajero.tiempo_libre_registrado),
            "decisiones": list(self.decisiones),
            "estado_movimiento": self.estado_movimiento,
            "vuelo_actual": dict(self.vuelo_actual) if self.vuelo_actual else None,
        }

    # ------------------------------------------------------------------
    # COMPLEMENTOS PARA SIMULACION DINAMICA PASO A PASO
    # ------------------------------------------------------------------

    """starts a dynamic simulation from an origin airport, initializing the internal state for step-by-step progression and registering the initial arrival."""
    def iniciar_viaje_dinamico(self, aeropuerto_origen: str) -> None:
        """Inicia una simulacion dinamica desde un aeropuerto de origen."""
        if not self.grafo.existe_vertice(aeropuerto_origen):
            raise ValueError(f"El aeropuerto {aeropuerto_origen} no existe")

        self.ruta_actual = []
        self.indice_actual = None
        self.tiempo_transcurrido_horas = 0.0
        self.horas_desde_ultima_alimentacion = 0.0
        self.horas_desde_ultimo_hospedaje = 0.0
        self.distancia_volada_km = 0.0
        self.distancia_subsidiada_km = 0.0
        self.ultimo_aeropuerto_visitado = None
        self.estancia_minima_actual_horas = 0.0
        self.tiempo_estancia_actual_horas = 0.0
        self.decisiones = []
        self.estado_movimiento = "en_aeropuerto"
        self.vuelo_actual = None
        self.registrar_llegada(aeropuerto_origen)
        self._registrar_decision("inicio", f"Viaje dinamico iniciado en {aeropuerto_origen}")

    """Returns the available flight alternatives from the current airport, considering the traveler's preferences and the state of the graph. Each alternative includes details such as destination, transport options, costs, and whether it can be paid with the current budget."""
    def obtener_alternativas_disponibles(self, transportes_preferidos: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Devuelve los vuelos posibles desde el aeropuerto actual."""
        if self.estado_movimiento == "en_vuelo":
            return []

        aeropuerto_actual = self._obtener_codigo_actual()
        vertice = self.grafo.obtener_vertice(aeropuerto_actual)
        if vertice is None:
            return []

        alternativas = []
        for arista in vertice.adyacencias:
            if arista.esta_bloqueada():
                continue
            for transporte in self._transportes_para_arista(arista, transportes_preferidos):
                costo = self._calcular_costo_tramo(arista, transporte)
                tiempo = self._calcular_tiempo_tramo(arista, transporte)
                puede_usar_subsidio = self._puede_usar_subsidio(arista)
                alternativas.append(
                    {
                        "origen": aeropuerto_actual,
                        "destino": arista.vertice_destino.identificador,
                        "transporte": transporte,
                        "distancia_km": arista.distancia_km,
                        "costo_vuelo": costo,
                        "tiempo_vuelo_horas": tiempo,
                        "tiempo_vuelo_min": tiempo * 60,
                        "costo_por_km": float(self.grafo.obtener_costo_por_km(transporte) or 0),
                        "tiempo_min_por_km": float(self.grafo.obtener_tiempo_por_km(transporte) or 0) * 60,
                        "es_subsidiada": bool(getattr(arista, "costo_cero", False)),
                        "puede_usar_subsidio": puede_usar_subsidio,
                        "limite_subsidio_km": self._limite_subsidio_despues_de(arista),
                        "distancia_subsidiada_usada_km": self.distancia_subsidiada_km,
                        "puede_pagarse": costo <= self.viajero.presupuesto_actual and puede_usar_subsidio,
                    }
                )

        alternativas.sort(key=lambda item: (item["costo_vuelo"], item["tiempo_vuelo_horas"]))
        return alternativas

    """Suggests the next cheapest movement towards an unvisited destination, considering the traveler's preferences and the available alternatives. If there are no unvisited destinations, it suggests the cheapest available alternative."""
    def sugerir_siguiente_alternativa(self, transportes_preferidos: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """Sugiere el siguiente movimiento mas barato hacia un destino no visitado."""
        visitados = set(self.viajero.aeropuertos_visitados)
        alternativas = self.obtener_alternativas_disponibles(transportes_preferidos)
        no_visitadas = [
            alternativa
            for alternativa in alternativas
            if alternativa["destino"] not in visitados and alternativa["puede_pagarse"]
        ]
        if no_visitadas:
            return no_visitadas[0]

        pagables = [alternativa for alternativa in alternativas if alternativa["puede_pagarse"]]
        return pagables[0] if pagables else None

    """Initiates a flight towards an adjacent destination without immediately registering the arrival. Validates the movement, updates the internal state for the ongoing flight, and registers the pending free time if applicable."""
    def avanzar_a_destino(self, destino: str, transporte: Optional[str] = None) -> Dict[str, Any]:
        """Inicia un vuelo hacia un destino adyacente sin registrar llegada inmediata."""
        if self.estado_movimiento == "en_vuelo":
            raise ValueError("Ya hay un vuelo en curso")

        aeropuerto_actual = self._obtener_codigo_actual()
        arista = self._buscar_arista(aeropuerto_actual, destino)
        if arista is None:
            raise ValueError(f"No existe ruta directa de {aeropuerto_actual} a {destino}")
        if arista.esta_bloqueada():
            raise ValueError(f"La ruta {aeropuerto_actual} -> {destino} esta bloqueada")

        transporte_elegido = transporte or self._elegir_transporte_mas_barato(arista)
        if transporte_elegido not in self._transportes_para_arista(arista, None):
            raise ValueError(f"El transporte {transporte_elegido} no esta disponible para esta ruta")
        if not self._puede_usar_subsidio(arista):
            raise ValueError("La ruta subsidiada supera el limite del 20% de distancia del viaje")

        evento_tiempo_libre = self.registrar_tiempo_libre_pendiente()
        costo_vuelo = self._calcular_costo_tramo(arista, transporte_elegido)
        tiempo_vuelo = self._calcular_tiempo_tramo(arista, transporte_elegido)

        self.viajero.gastar(costo_vuelo)
        self.estado_movimiento = "en_vuelo"
        self.vuelo_actual = {
            "origen": aeropuerto_actual,
            "destino": arista.vertice_destino.identificador,
            "arista": arista,
            "transporte": transporte_elegido,
            "tiempo_total_horas": tiempo_vuelo,
            "tiempo_transcurrido_horas": 0.0,
            "costo_vuelo": costo_vuelo,
            "tiempo_libre_origen": evento_tiempo_libre,
        }
        self._registrar_decision("vuelo_iniciado", f"Vuelo iniciado {aeropuerto_actual} -> {self.vuelo_actual['destino']}")
        return dict(self.vuelo_actual)


    """Returns the progress of the current flight as a float between 0.0 and 1.0, representing the percentage of the flight completed based on the time elapsed and the total flight time."""
    def obtener_progreso_vuelo(self) -> float:
        if not self.vuelo_actual:
            return 0.0
        total = float(self.vuelo_actual.get("tiempo_total_horas", 0) or 0)
        if total <= 0:
            return 1.0
        transcurrido = float(self.vuelo_actual.get("tiempo_transcurrido_horas", 0) or 0)
        return max(0.0, min(1.0, transcurrido / total))

    """Advances the current flight by a given number of hours, updating the internal state accordingly. If the flight is completed during this advancement, it registers the arrival and returns the details of the completed flight. If the route becomes blocked during the flight, it cancels the flight and returns the cancellation details."""
    def avanzar_vuelo(self, horas: float) -> Optional[Dict[str, Any]]:
        if self.estado_movimiento != "en_vuelo" or not self.vuelo_actual:
            return None

        arista = self.vuelo_actual["arista"]
        if arista.esta_bloqueada():
            return self.cancelar_vuelo("Ruta bloqueada durante el vuelo")

        total = float(self.vuelo_actual.get("tiempo_total_horas", 0) or 0)
        transcurrido = float(self.vuelo_actual.get("tiempo_transcurrido_horas", 0) or 0)
        delta = max(0.0, min(float(horas), total - transcurrido))
        if delta > 0:
            self._consumir_tiempo_con_obligatorias(delta)
            self.vuelo_actual["tiempo_transcurrido_horas"] = transcurrido + delta

        if self.obtener_progreso_vuelo() >= 1.0:
            return self.completar_vuelo()
        return None

    """Completes the current flight, registering the arrival at the destination and applying any mandatory events upon arrival. Updates the internal state to reflect the completed flight and returns the details of the completed flight."""
    def completar_vuelo(self) -> Dict[str, Any]:
        if self.estado_movimiento != "en_vuelo" or not self.vuelo_actual:
            raise ValueError("No hay un vuelo en curso")

        vuelo = self.vuelo_actual
        arista = vuelo["arista"]
        distancia_vuelo = float(arista.distancia_km or 0)

        self.distancia_volada_km += distancia_vuelo
        if getattr(arista, "costo_cero", False):
            self.distancia_subsidiada_km += distancia_vuelo
        self.registrar_llegada(vuelo["destino"])
        self.estancia_minima_actual_horas = self._normalizar_estancia_minima_horas(
            getattr(arista, "estancia_minima", 0) or 0
        )
        self.tiempo_estancia_actual_horas = 0.0
        eventos_llegada = self._aplicar_obligatorias_en_destino()

        decision = {
            "tipo": "vuelo",
            "origen": vuelo["origen"],
            "destino": vuelo["destino"],
            "transporte": vuelo["transporte"],
            "distancia_km": distancia_vuelo,
            "es_subsidiada": bool(getattr(arista, "costo_cero", False)),
            "costo_vuelo": vuelo["costo_vuelo"],
            "tiempo_vuelo_horas": vuelo["tiempo_total_horas"],
            "eventos_obligatorios": eventos_llegada,
            "tiempo_libre_origen": vuelo.get("tiempo_libre_origen"),
            "presupuesto_restante": self.viajero.presupuesto_actual,
            "tiempo_restante_horas": self.viajero.tiempo_restante_horas,
        }
        self.decisiones.append(decision)
        self.vuelo_actual = None
        self.estado_movimiento = "en_aeropuerto"
        return decision

    """Cancels the current flight, registering the cancellation and updating the internal state accordingly. Returns the details of the cancelled flight."""
    def cancelar_vuelo(self, motivo: str = "Vuelo cancelado") -> Dict[str, Any]:
        if self.estado_movimiento != "en_vuelo" or not self.vuelo_actual:
            raise ValueError("No hay un vuelo en curso")

        vuelo = self.vuelo_actual
        costo_vuelo = float(vuelo.get("costo_vuelo", 0) or 0)
        self.viajero.presupuesto_actual += costo_vuelo
        self.viajero.gasto_total = max(0.0, self.viajero.gasto_total - costo_vuelo)
        decision = {
            "tipo": "vuelo_cancelado",
            "origen": vuelo["origen"],
            "destino": vuelo["destino"],
            "motivo": motivo,
            "tiempo_vuelo_horas": vuelo.get("tiempo_transcurrido_horas", 0.0),
            "presupuesto_restante": self.viajero.presupuesto_actual,
            "tiempo_restante_horas": self.viajero.tiempo_restante_horas,
        }
        self.decisiones.append(decision)
        self.vuelo_actual = None
        self.estado_movimiento = "en_aeropuerto"
        return decision


    """Applies mandatory events upon arrival at a destination, such as required activities or jobs. Returns a list of the applied mandatory events."""
    def obtener_actividades_y_trabajos_actuales(self) -> Dict[str, Any]:
        """Lista actividades opcionales y trabajos en el aeropuerto actual."""
        if self.estado_movimiento == "en_vuelo":
            return {"actividades": [], "trabajos": []}

        vertice = self.grafo.obtener_vertice(self._obtener_codigo_actual())
        if vertice is None:
            return {"actividades": [], "trabajos": []}
        return {
            "actividades": list(vertice.actividades),
            "trabajos": list(vertice.trabajos),
        }

    """Auxiliary method to apply mandatory events upon arrival at a destination, such as required activities or jobs. Returns a list of the applied mandatory events."""
    def _obtener_codigo_actual(self) -> str:
        if self.indice_actual is None or not self.ruta_actual:
            raise ValueError("El viaje no ha sido iniciado")
        return self.ruta_actual[self.indice_actual]

    """Auxiliary method to find the edge (arista) between the current airport and a given destination. Returns the edge if found, or None if there is no direct route."""
    def _buscar_arista(self, origen: str, destino: str):
        vertice = self.grafo.obtener_vertice(origen)
        if vertice is None:
            return None
        destino_normalizado = destino.upper().strip()
        for arista in vertice.adyacencias:
            if arista.vertice_destino.identificador == destino_normalizado:
                return arista
        return None

    """Auxiliary method to determine the available transport options for a given edge (arista), considering the traveler's preferred transport modes. Returns a list of available transport options that match the preferences, or all available options if no preferences are specified."""
    def _transportes_para_arista(self, arista, transportes_preferidos: Optional[List[str]]) -> List[str]:
        transportes = arista.aeronaves or self.grafo.obtener_aeronaves_disponibles()
        if not transportes:
            return ["Transporte"]
        if not transportes_preferidos:
            return list(transportes)

        preferidos = {transporte.strip().lower() for transporte in transportes_preferidos}
        return [transporte for transporte in transportes if transporte.strip().lower() in preferidos]
    
    """Auxiliary method to choose the cheapest transport option for a given edge (arista), based on the calculated cost of the segment for each available transport. Returns the transport option with the lowest cost."""
    def _elegir_transporte_mas_barato(self, arista) -> str:
        transportes = self._transportes_para_arista(arista, None)
        return min(transportes, key=lambda transporte: self._calcular_costo_tramo(arista, transporte))

    """Auxiliary method to calculate the cost of a flight segment (tramo) based on the edge (arista) and the chosen transport mode. Considers factors such as distance, base cost, cost per kilometer, and whether the segment is subsidized. Returns the total calculated cost for the segment."""
    def _calcular_costo_tramo(self, arista, transporte: str) -> float:
        if getattr(arista, "costo_cero", False):
            return 0.0

        distancia = float(arista.distancia_km or 0)
        costo_km = float(self.grafo.obtener_costo_por_km(transporte) or 0)
        return float(arista.costo_base or 0) + distancia * costo_km

    """Auxiliary method to calculate the time required for a flight segment (tramo) based on the edge (arista) and the chosen transport mode. Considers factors such as distance and time per kilometer for the transport mode. Returns the total calculated time in hours for the segment."""
    def _calcular_tiempo_tramo(self, arista, transporte: str) -> float:
        distancia = float(arista.distancia_km or 0)
        tiempo_km = float(self.grafo.obtener_tiempo_por_km(transporte) or 0)
        return distancia * tiempo_km
    """Auxiliary method to determine the limit of subsidized distance after a given edge (arista), based on the total distance flown so far and the distance of the current segment. The limit is calculated as 20% of the total distance flown including the current segment. Returns the calculated limit for subsidized distance in kilometers."""
    def _limite_subsidio_despues_de(self, arista) -> float:
        distancia = float(getattr(arista, "distancia_km", 0) or 0)
        return (self.distancia_volada_km + distancia) * 0.20
    """Auxiliary method to check if a subsidized segment (arista) can be used based on the current distance flown and the limit for subsidized distance. If the segment is not subsidized, it can always be used. If it is subsidized, it checks if adding the distance of the segment would exceed the calculated limit for subsidized distance. Returns True if the subsidized segment can be used, or False if it would exceed the limit."""
    def _puede_usar_subsidio(self, arista) -> bool:
        if not getattr(arista, "costo_cero", False):
            return True

        distancia = float(getattr(arista, "distancia_km", 0) or 0)
        return self.distancia_subsidiada_km + distancia <= self._limite_subsidio_despues_de(arista)

    """Auxiliary method to consume flight time while applying mandatory events such as required meals or accommodations. Advances the internal clock by the given number of hours, and if during this time the traveler reaches the threshold for mandatory meals or accommodations, it applies those events accordingly. Raises a ValueError if the provided hours are negative."""
    def _consumir_tiempo_con_obligatorias(self, horas: float) -> None:
        if horas < 0:
            raise ValueError("El tiempo de vuelo no puede ser negativo")

        horas_restantes = horas
        while horas_restantes > 0:
            faltante_alimentacion = 8 - self.horas_desde_ultima_alimentacion
            if faltante_alimentacion <= 0:
                self._aplicar_alimentacion(self.ultimo_aeropuerto_visitado)
                continue
            if faltante_alimentacion <= horas_restantes:
                self._avanzar_reloj(faltante_alimentacion)
                horas_restantes -= faltante_alimentacion
                self._aplicar_alimentacion(self.ultimo_aeropuerto_visitado)
            else:
                self._avanzar_reloj(horas_restantes)
                horas_restantes = 0
    """Auxiliary method to advance the internal clock of the simulation by a given number of hours, updating the traveler's consumed time and the internal counters for time since last meal and accommodation. Raises a ValueError if the provided hours are negative."""
    def _avanzar_reloj(self, horas: float) -> None:
        self.viajero.consumir_tiempo(horas)
        self.tiempo_transcurrido_horas += horas
        self.horas_desde_ultima_alimentacion += horas
        self.horas_desde_ultimo_hospedaje += horas
    """Auxiliary method to register the passage of time for operations such as flights, activities, or jobs. Advances the internal clock by the given number of hours and updates the counters for time since last meal and accommodation accordingly. Raises a ValueError if the provided hours are negative."""
    def _registrar_tiempo_operacion(self, horas: float) -> None:
        self.tiempo_transcurrido_horas += horas
        self.horas_desde_ultima_alimentacion += horas
        self.horas_desde_ultimo_hospedaje += horas
        self.tiempo_estancia_actual_horas += horas
    """Auxiliary method to normalize the minimum stay time in hours, ensuring it is non-negative. If the provided minimum stay time is greater than 24 hours, it is assumed to be in minutes and converted to hours. Returns the normalized minimum stay time in hours."""
    def _normalizar_estancia_minima_horas(self, estancia_minima: float) -> float:
        estancia = float(estancia_minima or 0)
        if estancia > 24:
            return estancia / 60
        return estancia
    """Auxiliary method to apply mandatory meal events when the traveler has reached the threshold for time since the last meal. If there is a previous airport to charge for the meal, it retrieves the cost of the meal from the vertex of that airport, charges the traveler, resets the counter for time since last meal, and registers the meal event in the decisions list. Raises a ValueError if there is no previous airport to charge for the meal."""
    def _aplicar_alimentacion(self, codigo_aeropuerto: Optional[str]) -> Dict[str, Any]:
        if not codigo_aeropuerto:
            raise ValueError("No hay aeropuerto previo para cobrar alimentacion")
        vertice = self.grafo.obtener_vertice(codigo_aeropuerto)
        costo = float(getattr(vertice, "costo_alimentacion", 0) or 0)
        self.viajero.gastar(costo)
        self.horas_desde_ultima_alimentacion = 0.0
        evento = {
            "tipo": "alimentacion",
            "aeropuerto": codigo_aeropuerto,
            "costo": costo,
            "tiempo": self.tiempo_transcurrido_horas,
        }
        self.decisiones.append(evento)
        return evento
    """Auxiliary method to apply mandatory accommodation events when the traveler has reached the threshold for time since the last accommodation. If there is a current airport to charge for the accommodation, it retrieves the cost of the accommodation from the vertex of that airport, charges the traveler, resets the counter for time since last accommodation, and registers the accommodation event in the decisions list. Raises a ValueError if there is no current airport to charge for the accommodation."""
    def _aplicar_obligatorias_en_destino(self) -> List[Dict[str, Any]]:
        eventos = []
        if self.horas_desde_ultimo_hospedaje >= 20:
            eventos.append(self._aplicar_hospedaje(self._obtener_codigo_actual()))
        return eventos
    """Auxiliary method to apply mandatory accommodation events when the traveler has reached the threshold for time since the last accommodation. If there is a current airport to charge for the accommodation, it retrieves the cost of the accommodation from the vertex of that airport, charges the traveler, resets the counter for time since last accommodation, and registers the accommodation event in the decisions list. Raises a ValueError if there is no current airport to charge for the accommodation."""
    def _aplicar_hospedaje(self, codigo_aeropuerto: str) -> Dict[str, Any]:
        vertice = self.grafo.obtener_vertice(codigo_aeropuerto)
        costo = float(getattr(vertice, "costo_alojamiento", 0) or 0)
        self.viajero.gastar(costo)
        self.horas_desde_ultimo_hospedaje = 0.0
        evento = {
            "tipo": "hospedaje",
            "aeropuerto": codigo_aeropuerto,
            "costo": costo,
            "tiempo": self.tiempo_transcurrido_horas,
        }
        self.decisiones.append(evento)
        return evento
    """Auxiliary method to register a decision in the decisions list, including the type of decision, a description, the current simulation time, and the traveler's remaining budget. This method is used to log significant events such as starting a flight, completing a flight, or encountering a blocked route."""
    def _registrar_decision(self, tipo: str, descripcion: str) -> None:
        self.decisiones.append(
            {
                "tipo": tipo,
                "descripcion": descripcion,
                "tiempo": self.tiempo_transcurrido_horas,
                "presupuesto": self.viajero.presupuesto_actual,
            }
        )
    """Auxiliary method to block a direct route between two airports. This method updates the state of the edge (arista) between the specified origin and destination to indicate that it is blocked. If there is an ongoing flight on that route when it becomes blocked, the flight is cancelled and a cancellation event is registered."""
    def bloquear_ruta(self, origen: str, destino: str) -> None:
        """Bloquea una ruta directa entre origen y destino."""
        origen = origen.upper().strip()
        destino = destino.upper().strip()
        arista = self._buscar_arista(origen, destino)
        if arista is None:
            raise ValueError(f"No existe ruta directa de {origen} a {destino}")
        arista.bloquear()
        if (
            self.estado_movimiento == "en_vuelo"
            and self.vuelo_actual
            and self.vuelo_actual["origen"] == origen
            and self.vuelo_actual["destino"] == destino
        ):
            self.cancelar_vuelo("Ruta bloqueada durante el vuelo")
