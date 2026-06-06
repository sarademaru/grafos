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
        ruta_actual: Lista de codigos de aeropuertos en la ruta planificada.
        indice_actual: Indice del aeropuerto actual en `ruta_actual` o None.
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
        """Inicia el viaje con una ruta (lista de codigos de aeropuerto).

        Registra la llegada al primer aeropuerto automaticamente.
        """
        if not ruta:
            raise ValueError("La ruta no puede estar vacia")
        self.ruta_actual = [c.upper().strip() for c in ruta]
        self.indice_actual = 0
        self.estado_movimiento = "en_aeropuerto"
        self.vuelo_actual = None
        codigo = self.ruta_actual[0]
        self.registrar_llegada(codigo)

    def registrar_llegada(self, codigo_aeropuerto: str) -> None:
        """Registrar llegada del viajero a un aeropuerto dado por codigo.

        Actualiza el estado interno y notifica al `Viajero`.
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
            "max_horas": trabajo.max_horas,
        }

    def realizar_actividad(self, actividad: Any) -> Dict[str, Any]:
        """Realiza una actividad: acepta `Actividad` o diccionario compatible.

        Convierte objetos de dominio a la forma esperada por `Viajero`.
        """
        if isinstance(actividad, Actividad):
            actividad_dict = self._actividad_a_dict(actividad)
        elif isinstance(actividad, dict):
            actividad_dict = dict(actividad)
        else:
            raise ValueError("Actividad debe ser Actividad o dict compatible")

        tiempo_actividad = float(actividad_dict.get("tiempo_horas", 0) or 0)
        costo_actividad = float(actividad_dict.get("costo", 0) or 0)
        aeropuerto_actual = self._obtener_codigo_actual()
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

    def realizar_trabajo(self, trabajo: Any, horas: float) -> Dict[str, Any]:
        """Realiza un trabajo: acepta `Trabajo` o dict compatible y horas a trabajar.

        Convierte objetos de dominio a la forma esperada por `Viajero`.
        """
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

    def puede_trabajar(self) -> bool:
        configuracion = self.grafo.obtener_configuracion()
        porcentaje = configuracion.get("presupuestoMinimoPorcentaje", 35)
        return self.viajero.presupuesto_bajo(porcentaje)

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

    def obtener_estado(self) -> Dict[str, Any]:
        """Devuelve el estado actual del gestor y del viajero.

        Incluye resumen del `Viajero`, codigo del aeropuerto actual y la ruta.
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
    # Funcionalidad adicional para el viaje dinamico paso a paso.
    # No reemplaza los metodos existentes; los complementa.
    # ------------------------------------------------------------------

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

    def obtener_progreso_vuelo(self) -> float:
        if not self.vuelo_actual:
            return 0.0
        total = float(self.vuelo_actual.get("tiempo_total_horas", 0) or 0)
        if total <= 0:
            return 1.0
        transcurrido = float(self.vuelo_actual.get("tiempo_transcurrido_horas", 0) or 0)
        return max(0.0, min(1.0, transcurrido / total))

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

    def _obtener_codigo_actual(self) -> str:
        if self.indice_actual is None or not self.ruta_actual:
            raise ValueError("El viaje no ha sido iniciado")
        return self.ruta_actual[self.indice_actual]

    def _buscar_arista(self, origen: str, destino: str):
        vertice = self.grafo.obtener_vertice(origen)
        if vertice is None:
            return None
        destino_normalizado = destino.upper().strip()
        for arista in vertice.adyacencias:
            if arista.vertice_destino.identificador == destino_normalizado:
                return arista
        return None

    def _transportes_para_arista(self, arista, transportes_preferidos: Optional[List[str]]) -> List[str]:
        transportes = arista.aeronaves or self.grafo.obtener_aeronaves_disponibles()
        if not transportes:
            return ["Transporte"]
        if not transportes_preferidos:
            return list(transportes)

        preferidos = {transporte.strip().lower() for transporte in transportes_preferidos}
        return [transporte for transporte in transportes if transporte.strip().lower() in preferidos]

    def _elegir_transporte_mas_barato(self, arista) -> str:
        transportes = self._transportes_para_arista(arista, None)
        return min(transportes, key=lambda transporte: self._calcular_costo_tramo(arista, transporte))

    def _calcular_costo_tramo(self, arista, transporte: str) -> float:
        if getattr(arista, "costo_cero", False):
            return 0.0

        distancia = float(arista.distancia_km or 0)
        costo_km = float(self.grafo.obtener_costo_por_km(transporte) or 0)
        return float(arista.costo_base or 0) + distancia * costo_km

    def _calcular_tiempo_tramo(self, arista, transporte: str) -> float:
        distancia = float(arista.distancia_km or 0)
        tiempo_km = float(self.grafo.obtener_tiempo_por_km(transporte) or 0)
        return distancia * tiempo_km

    def _limite_subsidio_despues_de(self, arista) -> float:
        distancia = float(getattr(arista, "distancia_km", 0) or 0)
        return (self.distancia_volada_km + distancia) * 0.20

    def _puede_usar_subsidio(self, arista) -> bool:
        if not getattr(arista, "costo_cero", False):
            return True

        distancia = float(getattr(arista, "distancia_km", 0) or 0)
        return self.distancia_subsidiada_km + distancia <= self._limite_subsidio_despues_de(arista)

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

    def _avanzar_reloj(self, horas: float) -> None:
        self.viajero.consumir_tiempo(horas)
        self.tiempo_transcurrido_horas += horas
        self.horas_desde_ultima_alimentacion += horas
        self.horas_desde_ultimo_hospedaje += horas

    def _registrar_tiempo_operacion(self, horas: float) -> None:
        self.tiempo_transcurrido_horas += horas
        self.horas_desde_ultima_alimentacion += horas
        self.horas_desde_ultimo_hospedaje += horas
        self.tiempo_estancia_actual_horas += horas

    def _normalizar_estancia_minima_horas(self, estancia_minima: float) -> float:
        estancia = float(estancia_minima or 0)
        if estancia > 24:
            return estancia / 60
        return estancia

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

    def _aplicar_obligatorias_en_destino(self) -> List[Dict[str, Any]]:
        eventos = []
        if self.horas_desde_ultimo_hospedaje >= 20:
            eventos.append(self._aplicar_hospedaje(self._obtener_codigo_actual()))
        return eventos

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

    def _registrar_decision(self, tipo: str, descripcion: str) -> None:
        self.decisiones.append(
            {
                "tipo": tipo,
                "descripcion": descripcion,
                "tiempo": self.tiempo_transcurrido_horas,
                "presupuesto": self.viajero.presupuesto_actual,
            }
        )
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
