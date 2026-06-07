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
    """Page for displaying reports."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.planificacion = None
        self.viaje_dinamico = None
        self.alternativas_aeronaves = []
        self._setup_ui()
    """Auxiliary method to initialize the user interface components of the reports page. This method sets up the layout, title, and scrollable content area for displaying various report sections such as route planning details, aircraft comparisons, visited destinations, flight legs, activities, jobs, free time, and overall statistics. It organizes the structure of the reports page and prepares it for dynamic content updates based on the provided report data."""
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
    """Clears the current report data and refreshes the displayed content to show an empty state. This method resets the planning report, dynamic travel state, and aircraft alternatives to their initial empty values, and then calls the refresh_report method to update the user interface accordingly. It is typically used when loading a new graph or resetting the current report data."""
    def clear_report(self):
        self.planificacion = None
        self.viaje_dinamico = None
        self.alternativas_aeronaves = []
        self.refresh_report()

    """Sets the overall report data and refreshes the displayed content. This method is a convenience wrapper that calls the appropriate report setting methods based on the provided payload."""
    def set_report(self, payload):
        self.set_planning_report(payload)

    """Sets the planning report data and refreshes the displayed content. This method updates the internal planning report attribute and triggers a UI refresh to display the new information."""
    def set_planning_report(self, payload):
        self.planificacion = payload
        self.refresh_report()
    """Sets the dynamic travel report data and refreshes the displayed content. This method updates the internal dynamic travel state and aircraft alternatives attributes, then triggers a UI refresh to display the new information."""
    def set_dynamic_report(self, estado=None, alternativas=None):
        self.viaje_dinamico = estado
        self.alternativas_aeronaves = list(alternativas or [])
        self.refresh_report()
    """Refreshes the displayed report content based on the current planning report, dynamic travel state, and aircraft alternatives. This method clears the existing content and rebuilds the report sections to reflect the latest data. It ensures that all displayed information is up-to-date and accurately represents the current state of the reports."""
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
    """Auxiliary method to clear the current content displayed in the reports page. This method removes all existing widgets from the content layout and deletes them to free up resources. It is typically called before rebuilding the report sections to ensure that the displayed information is current and relevant to the latest report data."""

    def _clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
    """Auxiliary method to build the planning report section of the reports page. This method creates a group box containing details about the route planning, including the origin, destination, budget, available time, selected criteria, and summaries of the calculated routes based on different criteria. It organizes the information in a structured layout and provides a clear overview of the planning results."""
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

    """Auxiliary method to build the aircraft comparison section of the reports page. This method creates a group box containing a table that compares different aircraft alternatives for the planned route, showing details such as destination, type of aircraft, distance, cost, time, and whether the flight is subsidized. It highlights the best options based on cost and time, and provides a clear overview of the available aircraft choices for the route."""
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
    """Auxiliary method to build the visited destinations section of the reports page. This method creates a group box containing a table that lists the airports visited during the planned route, showing the order of visits and the corresponding airport codes. It provides a clear overview of the travel path taken through the various destinations."""
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

    """Auxiliary method to build the flight legs section of the reports page. This method creates a group box containing a table that lists the flight segments of the planned route, showing details such as origin, destination, aircraft type, distance, time, and cost. It provides a clear overview of the travel path taken through the various destinations."""      
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
    """Auxiliary method to build a new group box with a title and a vertical layout. This method creates a QGroupBox with the specified title and sets up a QVBoxLayout for its content. It returns both the group box and the layout, allowing for easy addition of widgets to the group box in other methods."""
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
    """Auxiliary method to build the jobs section of the reports page. This method creates a group box containing a table that lists the jobs performed during the planned route, showing details such as the airport where the job was done, a description of the job, hours worked, hourly rate, and total earnings. It provides a clear overview of the work activities undertaken during the travel."""
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
    """Auxiliary method to build the free time section of the reports page. This method creates a group box containing a table that lists the registered free time during the planned route, showing details such as the airport where the free time was recorded and the duration of that free time. It provides a clear overview of the leisure periods available during the travel."""
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
    """Auxiliary method to build the overall statistics section of the reports page. This method creates a group box containing a grid layout that displays various aggregated statistics about the planned route and the traveler's activities, such as total distance traveled, accumulated time and cost, number of flights, visited airports, subsidized distance used, total spent on activities, total earned from jobs, and initial and final budget. It provides a comprehensive overview of the travel experience based on the dynamic travel state."""
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
    """Auxiliary method to retrieve the basic route information for a given key from the planning report. This method checks the primary result for the specified key and, if not found or if it lacks route data, iterates through the criteria results to find a valid route. It returns the first valid route found or None if no valid route is available."""
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
    """Auxiliary method to check if a given route contains valid data. This method verifies that the route is a dictionary and that it has either legs or a path with more than one stop. It returns True if the route has valid data and False otherwise."""
    def _has_route_data(self, route):
        if not isinstance(route, dict):
            return False
        return bool(route.get("legs")) or len(route.get("path", [])) > 1
    """Auxiliary method to build a summary box for a given route. This method creates a group box with the specified title and populates it with details about the route, such as the complete sequence of stops, intermediate stops, transports used, total distance, cost, and time. It also includes a table of the route legs if available. If the route does not contain valid data, it displays an appropriate message instead."""
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
    """Auxiliary method to build the rows for the route legs table. This method iterates through the legs of the given route and extracts relevant information such as origin, destination, transport used, distance, cost, and time for each leg. It returns a list of rows that can be used to populate the legs table in the route summary box."""
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
    """Auxiliary method to safely retrieve a value from a leg dictionary or object. This method checks if the leg is a dictionary and retrieves the value using the get method; otherwise, it uses getattr to access the attribute. It returns the retrieved value or a default value if the key or attribute is not found."""
    def _leg_value(self, leg, key, default=None):
        if isinstance(leg, dict):
            return leg.get(key, default)
        return getattr(leg, key, default)
    """Auxiliary method to build a grid layout for displaying label-value pairs. This method takes a list of tuples containing labels and their corresponding values, creates QLabel widgets for each pair, and organizes them in a QGridLayout with appropriate spacing. The resulting layout can be used to display detailed information in a structured format within the report sections."""
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
    """Auxiliary method to create a new group box with a specified title and a vertical layout. This method initializes a QGroupBox, sets its object name for styling, and creates a QVBoxLayout for its content. It configures the layout's margins and spacing to ensure proper formatting of the contained widgets. The method returns both the created group box and its associated layout for further use in building the report sections."""
    def _new_group(self, title):
        group = QGroupBox(title)
        group.setObjectName("reportGroup")
        layout = QtWidgets.QVBoxLayout(group)
        layout.setContentsMargins(14, 18, 14, 14)
        layout.setSpacing(10)
        return group, layout
    """Auxiliary method to create a new table widget with specified headers, rows, and an empty message. This method initializes a QTableWidget, sets its properties for editing and selection behavior, and populates it with the provided data. If no rows are provided, it displays a single cell spanning all columns with the given empty message. The method also configures the appearance of the table, such as alternating row colors and header resizing."""
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

    """Auxiliary method to create a label widget with a specified text. This method initializes a QLabel, sets its object name for styling, and configures it to wrap text. The resulting label can be used to display information in the report sections."""
    def _message(self, text):
        label = QLabel(text)
        label.setObjectName("infoLabel")
        label.setWordWrap(True)
        return label
    """Auxiliary method to set the background color of a specific cell in a table. This method retrieves the item at the specified row and column, and if it exists, it applies a background color using a QBrush with the given color. This can be used to highlight specific cells based on certain conditions or criteria.  """
    def _paint_cell(self, table, row, column, color):
        item = table.item(row, column)
        if item:
            item.setBackground(QtGui.QBrush(QtGui.QColor(color)))
    """Auxiliary method to set the background color of an entire row in a table. This method iterates through all columns in the specified row and applies a background color to each cell using the _paint_cell method. This can be used to highlight an entire row based on certain conditions or criteria."""
    def _paint_row(self, table, row, color):
        for column in range(table.columnCount()):
            self._paint_cell(table, row, column, color)
    """Auxiliary method to format a value as a monetary amount. This method takes a value, converts it to a float, and formats it as a string with a dollar sign and two decimal places. If the value is None or cannot be converted to a float, it defaults to 0.00. This method is used to consistently display monetary values in the report sections."""
    def _money(self, value):
        return f"${float(value or 0):.2f}"
    """Auxiliary method to format a value as a duration in hours. This method takes a value, converts it to a float, and formats it as a string with two decimal places followed by "h". If the value is None or cannot be converted to a float, it defaults to 0.00 h. This method is used to consistently display time durations in the report sections."""
    def _hours(self, value):
        return f"{float(value or 0):.2f} h"
    """Auxiliary method to format a value as a distance in kilometers. This method takes a value, converts it to a float, and formats it as a string with two decimal places followed by "km". If the value is None or cannot be converted to a float, it defaults to 0.00 km. This method is used to consistently display distance values in the report sections."""
    def _km(self, value):
        return f"{float(value or 0):.2f} km"
