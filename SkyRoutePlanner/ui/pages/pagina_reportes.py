from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
)


class PaginaReportes(QtWidgets.QWidget):
    """Vista de consulta para datos ya generados por el planificador y el viaje."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.planificacion = None
        self.viaje_dinamico = None
        self.alternativas_aeronaves = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Reportes")
        title.setObjectName("pageTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.scroll = QtWidgets.QScrollArea()
        self.scroll.setObjectName("reportsScroll")
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(14)
        self.scroll.setWidget(self.content)

        layout.addWidget(self.scroll, stretch=1)
        self.refresh_report()

    def clear_report(self):
        self.planificacion = None
        self.viaje_dinamico = None
        self.alternativas_aeronaves = []
        self.refresh_report()

    def set_report(self, payload):
        self.set_planning_report(payload)

    def set_planning_report(self, payload):
        self.planificacion = payload
        self.refresh_report()

    def set_dynamic_report(self, estado=None, alternativas=None):
        self.viaje_dinamico = estado
        self.alternativas_aeronaves = list(alternativas or [])
        self.refresh_report()

    def refresh_report(self):
        self._clear_content()
        self.content_layout.addWidget(self._build_planning_group())
        self.content_layout.addWidget(self._build_aircraft_comparison_group())
        self.content_layout.addWidget(self._build_visited_destinations_group())
        self.content_layout.addWidget(self._build_flight_legs_group())
        self.content_layout.addWidget(self._build_activities_group())
        self.content_layout.addWidget(self._build_jobs_group())
        self.content_layout.addWidget(self._build_free_time_group())
        self.content_layout.addWidget(self._build_statistics_group())
        self.content_layout.addStretch()

    def _clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _build_planning_group(self):
        group, layout = self._new_group("Planificación de Ruta")

        if not self.planificacion:
            layout.addWidget(self._message("No hay una planificación calculada."))
            return group

        context = self.planificacion.get("context", {})
        rows = [
            ("Origen", context.get("origin", "-")),
            ("Destino", context.get("destination", "-")),
            ("Presupuesto inicial", self._money(context.get("budget", 0))),
            ("Tiempo disponible", self._hours(context.get("available_time", 0))),
            ("Criterios seleccionados", ", ".join(context.get("criteria_labels", [])) or "-"),
        ]
        layout.addLayout(self._details_grid(rows))

        # Use basic plan alternatives; if missing, fallback to primary_route provided by planner
        primary_route = self.planificacion.get("primary_route") if self.planificacion else None

        alt_a = self._get_basic_route("max_destinations_by_budget") or primary_route
        alt_b = self._get_basic_route("max_destinations_by_time") or primary_route

        layout.addWidget(
            self._route_summary_box(
                "Alternativa A",
                alt_a,
                "No existe una ruta factible que llegue al destino, respete el presupuesto y use los transportes requeridos.",
            )
        )
        layout.addWidget(
            self._route_summary_box(
                "Alternativa B",
                alt_b,
                "No existe una ruta factible que llegue al destino, respete el tiempo disponible y use los transportes requeridos.",
            )
        )
        return group

    def _build_aircraft_comparison_group(self):
        rows = [
            [
                alt.get("destino", "-"),
                alt.get("transporte", "-"),
                self._km(alt.get("distancia_km", 0)),
                self._money(alt.get("costo_vuelo", 0)),
                self._hours(alt.get("tiempo_vuelo_horas", 0)),
                "Sí" if alt.get("es_subsidiada", False) else "No",
            ]
            for alt in self.alternativas_aeronaves
        ]

        table = self._new_table(
            ["Destino", "Aeronave", "Distancia", "Costo", "Tiempo", "Subsidiada"],
            rows,
            "No hay alternativas evaluadas para comparar aeronaves.",
        )

        if self.alternativas_aeronaves:
            costos = [float(alt.get("costo_vuelo", 0) or 0) for alt in self.alternativas_aeronaves]
            tiempos = [float(alt.get("tiempo_vuelo_horas", 0) or 0) for alt in self.alternativas_aeronaves]
            menor_costo = min(costos)
            menor_tiempo = min(tiempos)
            for row, alt in enumerate(self.alternativas_aeronaves):
                if alt.get("es_subsidiada", False):
                    self._paint_row(table, row, "#713f12")
                if float(alt.get("costo_vuelo", 0) or 0) == menor_costo:
                    self._paint_cell(table, row, 3, "#14532d")
                if float(alt.get("tiempo_vuelo_horas", 0) or 0) == menor_tiempo:
                    self._paint_cell(table, row, 4, "#1e3a8a")

        group, layout = self._new_group("Comparación de Aeronaves")
        layout.addWidget(table)
        return group

    def _build_visited_destinations_group(self):
        group, layout = self._new_group("Destinos Visitados")
        viajero = (self.viaje_dinamico or {}).get("viajero", {})
        visitados = viajero.get("aeropuertos_visitados", [])
        if not visitados:
            layout.addWidget(self._message("No hay destinos registrados."))
            return group

        rows = [[index, aeropuerto] for index, aeropuerto in enumerate(visitados, start=1)]
        layout.addWidget(
            self._new_table(
                ["Orden", "Aeropuerto"],
                rows,
                "No hay destinos registrados.",
            )
        )
        return group

    def _build_flight_legs_group(self):
        decisiones = list((self.viaje_dinamico or {}).get("decisiones", []))
        rows = [
            [
                decision.get("origen", "-"),
                decision.get("destino", "-"),
                decision.get("transporte", "-"),
                self._km(decision.get("distancia_km", 0)),
                self._hours(decision.get("tiempo_vuelo_horas", 0)),
                self._money(decision.get("costo_vuelo", 0)),
            ]
            for decision in decisiones
            if decision.get("tipo") == "vuelo"
        ]

        group, layout = self._new_group("Tramos Volados")
        layout.addWidget(
            self._new_table(
                ["Origen", "Destino", "Aeronave", "Distancia", "Tiempo", "Costo"],
                rows,
                "No hay tramos volados registrados.",
            )
        )
        return group

    def _build_pending_group(self, title):
        group, layout = self._new_group(title)
        layout.addWidget(self._message("Pendiente de implementación."))
        return group

    def _build_activities_group(self):
        actividades = list((self.viaje_dinamico or {}).get("actividades_realizadas", []))
        rows = [
            [
                actividad.get("aeropuerto", "-"),
                actividad.get("nombre", "-"),
                f"{float(actividad.get('tiempo_horas', 0) or 0) * 60:.0f} min",
                self._money(actividad.get("costo", 0)),
            ]
            for actividad in actividades
        ]

        group, layout = self._new_group("Actividades Realizadas")
        layout.addWidget(
            self._new_table(
                ["Aeropuerto", "Actividad", "Duracion", "Costo"],
                rows,
                "No hay actividades realizadas registradas.",
            )
        )
        return group

    def _build_jobs_group(self):
        trabajos = list((self.viaje_dinamico or {}).get("trabajos_realizados", []))
        rows = [
            [
                trabajo.get("aeropuerto", "-"),
                trabajo.get("descripcion", trabajo.get("nombre", "-")),
                self._hours(trabajo.get("horas_trabajadas", 0)),
                f"{self._money(trabajo.get('tarifa_hora', 0))}/h",
                self._money(trabajo.get("ganancia", 0)),
            ]
            for trabajo in trabajos
        ]

        group, layout = self._new_group("Trabajos Realizados")
        layout.addWidget(
            self._new_table(
                ["Aeropuerto", "Trabajo", "Horas", "Tarifa", "Ingreso Total"],
                rows,
                "No hay trabajos realizados registrados.",
            )
        )
        return group

    def _build_free_time_group(self):
        tiempos_libres = list((self.viaje_dinamico or {}).get("tiempo_libre_registrado", []))
        rows = [
            [
                evento.get("aeropuerto", "-"),
                self._hours(evento.get("duracion_horas", 0)),
            ]
            for evento in tiempos_libres
        ]

        group, layout = self._new_group("Tiempo Libre Registrado")
        layout.addWidget(
            self._new_table(
                ["Aeropuerto", "Horas libres"],
                rows,
                "No hay tiempo libre registrado.",
            )
        )
        return group

    def _build_statistics_group(self):
        estado = self.viaje_dinamico or {}
        viajero = estado.get("viajero", {})
        decisiones = list(estado.get("decisiones", []))
        vuelos = [decision for decision in decisiones if decision.get("tipo") == "vuelo"]
        actividades = list(estado.get("actividades_realizadas", []))
        trabajos = list(estado.get("trabajos_realizados", []))
        tiempos_libres = list(estado.get("tiempo_libre_registrado", []))
        distancia = float(estado.get("distancia_volada_km", 0) or 0)
        distancia_subsidiada = float(estado.get("distancia_subsidiada_km", 0) or 0)
        porcentaje = (distancia_subsidiada / distancia * 100) if distancia > 0 else 0.0
        total_gastado_actividades = sum(float(item.get("costo", 0) or 0) for item in actividades)
        total_ganado_trabajos = sum(float(item.get("ganancia", 0) or 0) for item in trabajos)
        tiempo_actividades = sum(float(item.get("tiempo_horas", 0) or 0) for item in actividades)
        tiempo_trabajos = sum(float(item.get("horas_trabajadas", 0) or 0) for item in trabajos)
        tiempo_libre = sum(float(item.get("duracion_horas", 0) or 0) for item in tiempos_libres)

        rows = [
            ("Distancia recorrida", self._km(distancia)),
            ("Tiempo acumulado", self._hours(estado.get("tiempo_transcurrido_horas", 0))),
            ("Costo acumulado", self._money(viajero.get("gasto_total", 0))),
            ("Cantidad de vuelos", str(len(vuelos))),
            ("Cantidad de aeropuertos visitados", str(viajero.get("cantidad_aeropuertos_visitados", 0))),
            ("Distancia subsidiada utilizada", self._km(distancia_subsidiada)),
            ("Porcentaje subsidiado utilizado", f"{porcentaje:.2f}%"),
            ("Total gastado en actividades", self._money(total_gastado_actividades)),
            ("Total ganado en trabajos", self._money(total_ganado_trabajos)),
            ("Tiempo total invertido en actividades", self._hours(tiempo_actividades)),
            ("Tiempo total invertido en trabajos", self._hours(tiempo_trabajos)),
            ("Tiempo total libre", self._hours(tiempo_libre)),
            ("Presupuesto inicial", self._money(viajero.get("presupuesto_inicial", 0))),
            ("Presupuesto final", self._money(viajero.get("presupuesto_actual", 0))),
        ]

        group, layout = self._new_group("Estadísticas")
        layout.addLayout(self._details_grid(rows))
        return group

    def _get_basic_route(self, key):
        result = self.planificacion.get("result", {}) if self.planificacion else {}
        basic = result.get("basic", {}) if isinstance(result, dict) else {}
        route = basic.get(key) if isinstance(basic, dict) else None
        if self._has_route_data(route):
            return route

        criteria_results = self.planificacion.get("criteria_results", []) if self.planificacion else []
        for item in criteria_results:
            item_result = item.get("result", {}) if isinstance(item, dict) else {}
            item_basic = item_result.get("basic", {}) if isinstance(item_result, dict) else {}
            route = item_basic.get(key) if isinstance(item_basic, dict) else None
            if self._has_route_data(route):
                return route

        return route

    def _has_route_data(self, route):
        if not isinstance(route, dict):
            return False
        return bool(route.get("legs")) or len(route.get("path", [])) > 1

    def _route_summary_box(self, title, route, empty_message="No hay una planificacion calculada."):
        box, layout = self._new_group(title)
        if not self._has_route_data(route):
            layout.addWidget(self._message(empty_message))
            return box

        stops = route.get("path", [])[1:-1]
        rows = [
            ("Secuencia completa", " -> ".join(route.get("path", [])) or "-"),
            ("Escalas intermedias", ", ".join(stops) if stops else "Sin escalas"),
            ("Transportes utilizados", ", ".join(route.get("transports_used", [])) or "-"),
            ("Distancia total", self._km(route.get("total_distance", 0))),
            ("Costo total", self._money(route.get("total_cost", 0))),
            ("Tiempo total", self._hours(route.get("total_time", 0))),
        ]
        layout.addLayout(self._details_grid(rows))
        layout.addWidget(
            self._new_table(
                ["Origen", "Destino", "Aeronave", "Distancia", "Costo", "Tiempo"],
                self._route_leg_rows(route),
                "No hay tramos registrados para esta alternativa.",
            )
        )
        return box

    def _route_leg_rows(self, route):
        rows = []
        for leg in route.get("legs", []):
            rows.append(
                [
                    self._leg_value(leg, "origin", "-"),
                    self._leg_value(leg, "destination", "-"),
                    self._leg_value(leg, "transport", "-"),
                    self._km(self._leg_value(leg, "distance", 0)),
                    self._money(self._leg_value(leg, "cost", 0)),
                    self._hours(self._leg_value(leg, "time", 0)),
                ]
            )
        return rows

    def _leg_value(self, leg, key, default=None):
        if isinstance(leg, dict):
            return leg.get(key, default)
        return getattr(leg, key, default)

    def _details_grid(self, rows):
        grid = QtWidgets.QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(8)
        for row, (label, value) in enumerate(rows):
            label_widget = QLabel(str(label))
            label_widget.setObjectName("infoLabel")
            value_widget = QLabel(str(value))
            value_widget.setObjectName("infoValue")
            value_widget.setWordWrap(True)
            grid.addWidget(label_widget, row, 0)
            grid.addWidget(value_widget, row, 1)
        return grid

    def _new_group(self, title):
        group = QGroupBox(title)
        group.setObjectName("reportGroup")
        layout = QtWidgets.QVBoxLayout(group)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(10)
        return group, layout

    def _new_table(self, headers, rows, empty_message):
        row_count = len(rows) if rows else 1
        table = QTableWidget(row_count, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setMinimumHeight(120)

        if rows:
            for row_index, values in enumerate(rows):
                for column_index, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                    table.setItem(row_index, column_index, item)
        else:
            table.setSpan(0, 0, 1, len(headers))
            item = QTableWidgetItem(empty_message)
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            table.setItem(0, 0, item)

        table.resizeRowsToContents()
        return table

    def _message(self, text):
        label = QLabel(text)
        label.setObjectName("infoLabel")
        label.setWordWrap(True)
        return label

    def _paint_cell(self, table, row, column, color):
        item = table.item(row, column)
        if item:
            item.setBackground(QtGui.QBrush(QtGui.QColor(color)))

    def _paint_row(self, table, row, color):
        for column in range(table.columnCount()):
            self._paint_cell(table, row, column, color)

    def _money(self, value):
        return f"${float(value or 0):.2f}"

    def _hours(self, value):
        return f"{float(value or 0):.2f} h"

    def _km(self, value):
        return f"{float(value or 0):.2f} km"
