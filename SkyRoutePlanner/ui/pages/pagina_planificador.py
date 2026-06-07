from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
)

from algorithms.itinerary_planner import (
    CRITERION_COST,
    CRITERION_DISTANCE,
    CRITERION_TIME,
    plan_itinerary,
)
from ui.graph_view import GraphView


class PaginaPlanificador(QtWidgets.QWidget):
    """Page for planning routes between airports based on user-selected criteria, budget, and available time. This page allows users to select origin and destination airports, specify optimization criteria (distance, time, cost), choose preferred transport types, and calculate the optimal route using the underlying graph data. The results are displayed in an executive summary format, and the selected route is highlighted in the graph view for easy visualization."""

    route_calculated = QtCore.pyqtSignal(dict)

    """Initializes the user interface components of the route planner page, including the layout, title, control panel for selecting origin, destination, criteria, and transport preferences, as well as the graph view for visualizing the air network. This method sets up the structure and styling of the route planner page."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.grafo = None
        self.graph_view = GraphView()
        self.graph_view.node_selected.connect(self.on_node_selected)
        self._setup_ui()
    """Returns a dictionary containing the types of aircraft defined in the configuration, which can be used to determine available transport options and their associated costs and times in the route planning process."""
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        title = QLabel("Planificador de Rutas")
        title.setObjectName("pageTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        control_panel = QFrame()
        control_panel.setObjectName("controlPanel")
        control_panel.setMinimumWidth(360)
        control_panel.setMaximumWidth(460)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(16, 16, 16, 16)
        control_layout.setSpacing(16)

        section_label = QLabel("Selecciona origen y destino")
        section_label.setObjectName("sectionTitle")

        self.origin_combo = QComboBox()
        self.dest_combo = QComboBox()

        self.budget_spin = QDoubleSpinBox()
        self.budget_spin.setPrefix("$")
        self.budget_spin.setMaximum(1e9)
        self.budget_spin.setDecimals(2)
        self.budget_spin.setSingleStep(10.0)
        self.budget_spin.setValue(100.0)

        self.time_spin = QSpinBox()
        self.time_spin.setMinimum(1)
        self.time_spin.setMaximum(10_000)
        self.time_spin.setSuffix(" h")
        self.time_spin.setValue(1)

        criteria_box = QGroupBox()
        criteria_box.setObjectName("criteriaBox")
        criteria_layout = QVBoxLayout(criteria_box)
        criteria_layout.setContentsMargins(6, 6, 6, 6)
        self.crit_dist = QCheckBox("Distancia")
        self.crit_time = QCheckBox("Tiempo")
        self.crit_cost = QCheckBox("Costo")
        criteria_layout.addWidget(self.crit_dist)
        criteria_layout.addWidget(self.crit_time)
        criteria_layout.addWidget(self.crit_cost)

        secondary_box = QGroupBox()
        secondary_box.setObjectName("secondaryBox")
        secondary_layout = QVBoxLayout(secondary_box)
        secondary_layout.setContentsMargins(6, 6, 6, 6)
        self.sec_include = QRadioButton("Incluir")
        self.sec_exclude = QRadioButton("Excluir")
        self.sec_group = QButtonGroup(self)
        self.sec_group.addButton(self.sec_include)
        self.sec_group.addButton(self.sec_exclude)
        self.sec_include.setChecked(True)
        secondary_layout.addWidget(self.sec_include)
        secondary_layout.addWidget(self.sec_exclude)

        transport_box = QGroupBox()
        transport_box.setObjectName("transportBox")
        transport_layout = QVBoxLayout(transport_box)
        transport_layout.setContentsMargins(6, 6, 6, 6)
        self.tr_commercial = QCheckBox("Avion Comercial")
        self.tr_regional = QCheckBox("Avion Regional")
        self.tr_prop = QCheckBox("Helice")
        for checkbox in (self.tr_commercial, self.tr_regional, self.tr_prop):
            checkbox.setChecked(True)
            transport_layout.addWidget(checkbox)

        form_layout = QFormLayout()
        form_layout.addRow("Origen", self.origin_combo)
        form_layout.addRow("Destino", self.dest_combo)
        form_layout.addRow("Presupuesto inicial (USD)", self.budget_spin)
        form_layout.addRow("Tiempo disponible (horas)", self.time_spin)
        form_layout.addRow("Criterios de optimizacion", criteria_box)
        form_layout.addRow("Aeropuertos secundarios", secondary_box)
        form_layout.addRow("Tipos de transporte preferidos", transport_box)

        self.calculate_button = QPushButton("Calcular Ruta")
        self.calculate_button.setObjectName("primaryButton")
        self.calculate_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.calculate_button.clicked.connect(self.on_calculate_route)

        self.selected_info = QLabel("Seleccione un aeropuerto para ver mas informacion.")
        self.selected_info.setWordWrap(True)
        self.selected_info.setObjectName("infoLabel")

        self.summary_panel = QFrame()
        self.summary_panel.setObjectName("summaryPanel")
        summary_layout = QVBoxLayout(self.summary_panel)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_layout.setSpacing(8)

        summary_title = QLabel("Resumen ejecutivo")
        summary_title.setObjectName("sectionTitle")

        summary_layout.addWidget(summary_title)
        self.summary_results_layout = QVBoxLayout()
        self.summary_results_layout.setContentsMargins(0, 0, 0, 0)
        self.summary_results_layout.setSpacing(10)
        summary_layout.addLayout(self.summary_results_layout)
        self._clear_summary()

        legend_label = QLabel("Leyenda")
        legend_label.setObjectName("sectionTitle")

        legend = QtWidgets.QWidget()
        legend_layout = QVBoxLayout(legend)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(8)
        legend_layout.addWidget(QLabel("🟠 Hub"))
        legend_layout.addWidget(QLabel("🔵 Aeropuerto Secundario"))

        info_box = QFrame()
        info_box.setObjectName("infoFrame")
        info_box_layout = QVBoxLayout(info_box)
        info_box_layout.setContentsMargins(12, 12, 12, 12)
        info_box_layout.setSpacing(10)
        info_box_layout.addWidget(QLabel("Aeropuerto seleccionado"))

        self.selected_code = QLabel("Codigo: -")
        self.selected_name = QLabel("Nombre: -")
        self.selected_city = QLabel("Ciudad: -")
        self.selected_country = QLabel("Pais: -")
        self.selected_timezone = QLabel("Zona Horaria: -")

        for widget in [
            self.selected_code,
            self.selected_name,
            self.selected_city,
            self.selected_country,
            self.selected_timezone,
        ]:
            widget.setObjectName("infoValue")
            info_box_layout.addWidget(widget)

        control_layout.addWidget(section_label)
        control_layout.addLayout(form_layout)
        control_layout.addWidget(self.calculate_button)
        control_layout.addWidget(self.selected_info)
        control_layout.addWidget(self.summary_panel)
        control_layout.addWidget(legend_label)
        control_layout.addWidget(legend)
        control_layout.addWidget(info_box)
        control_layout.addStretch()

        control_scroll = QScrollArea()
        control_scroll.setObjectName("plannerScroll")
        control_scroll.setWidgetResizable(True)
        control_scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        control_scroll.setWidget(control_panel)

        graph_layout = QVBoxLayout()
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.addWidget(self.graph_view)

        content_layout.addWidget(control_scroll)
        content_layout.addLayout(graph_layout, stretch=1)
        main_layout.addLayout(content_layout)
    """Sets the graph data for the dashboard and updates the graph view and statistics accordingly. This method is called when a new graph is loaded or updated, allowing the dashboard to reflect the current state of the air network. It also triggers a refresh of the displayed statistics based on the new graph data."""
    def set_graph(self, grafo):
        self.grafo = grafo
        self.graph_view.set_graph(grafo)
        self._refresh_airports()
    """Clears the current graph data from the dashboard, resetting the graph view and statistics to their default state. This method is useful when the user wants to start fresh with a new graph or when the existing graph data is no longer relevant. It ensures that all displayed information is cleared and ready for new input."""
    def clear_graph(self):
        self.grafo = None
        self.graph_view.clear_graph()
        self.origin_combo.clear()
        self.dest_combo.clear()
        self._clear_summary()
        self._clear_selected_info()
    """ Sets the last calculated route information for the dashboard, updating the displayed last route statistic and highlighting the route in the graph view. This method is called after a route calculation is performed, allowing the dashboard to show the most recent route found by the planner. It also triggers a refresh of the displayed statistics to reflect the new route information."""
    def _refresh_airports(self):
        self.origin_combo.clear()
        self.dest_combo.clear()
        if self.grafo:
            codes = [vertice.identificador for vertice in self.grafo.obtener_vertices()]
            self.origin_combo.addItems(codes)
            self.dest_combo.addItems(codes)
    """Auxiliary method to clear the selected airport information displayed in the control panel. This method resets all displayed fields related to the selected airport (such as code, name, city, country, and timezone) to their default placeholder values. It is typically called when the graph is cleared or when no airport is currently selected, ensuring that the displayed information is accurate and does not show outdated data."""
    def _clear_selected_info(self):
        self.selected_code.setText("Codigo: -")
        self.selected_name.setText("Nombre: -")
        self.selected_city.setText("Ciudad: -")
        self.selected_country.setText("Pais: -")
        self.selected_timezone.setText("Zona Horaria: -")
    """Event handler for when a node (airport) is selected in the graph view. This method updates the displayed information about the selected airport in the control panel, showing details such as the airport code, name, city, country, and timezone. It is connected to the node_selected signal of the graph view, allowing it to respond dynamically to user interactions with the graph visualization."""
    def on_node_selected(self, vertice):
        self.selected_code.setText(f"Codigo: {vertice.identificador}")
        self.selected_name.setText(f"Nombre: {vertice.nombre}")
        self.selected_city.setText(f"Ciudad: {vertice.ciudad}")
        self.selected_country.setText(f"Pais: {vertice.pais}")
        self.selected_timezone.setText(f"Zona Horaria: {vertice.zona_horaria}")
    """Event handler for when the "Calcular Ruta" button is clicked. This method validates the user input for origin, destination, selected criteria, transport preferences, budget, and available time. If the input is valid, it calls the plan_itinerary function to calculate the optimal route based on the selected options and updates the dashboard with the results. It also emits a signal with the calculated route information for further processing or display in other parts of the application."""
    def on_calculate_route(self):
        if not self.grafo:
            self.selected_info.setText("Carga un archivo JSON antes de calcular la ruta.")
            return

        origen = self.origin_combo.currentText()
        destino = self.dest_combo.currentText()

        if origen == destino:
            msg = "Origen y destino no pueden ser iguales."
            QMessageBox.warning(self, "Validacion", msg)
            self.selected_info.setText(msg)
            return

        criterios = [
            (CRITERION_DISTANCE, "Distancia", self.crit_dist.isChecked()),
            (CRITERION_TIME, "Tiempo", self.crit_time.isChecked()),
            (CRITERION_COST, "Costo", self.crit_cost.isChecked()),
        ]
        criterios_sel = [key for key, _, selected in criterios if selected]
        criterios_texto = [label for _, label, selected in criterios if selected]
        if not criterios_sel:
            msg = "Debe seleccionar al menos un criterio de optimizacion."
            QMessageBox.warning(self, "Validacion", msg)
            self.selected_info.setText(msg)
            return

        transportes = [
            ("Avion Comercial", self.tr_commercial.isChecked()),
            ("Avion Regional", self.tr_regional.isChecked()),
            ("Helice", self.tr_prop.isChecked()),
        ]
        transportes_sel = [transport for transport, selected in transportes if selected]
        if not transportes_sel:
            msg = "Debe seleccionar al menos un tipo de transporte."
            QMessageBox.warning(self, "Validacion", msg)
            self.selected_info.setText(msg)
            return

        presupuesto = self.budget_spin.value()
        tiempo = self.time_spin.value()
        if presupuesto <= 0:
            msg = "El presupuesto debe ser mayor que cero."
            QMessageBox.warning(self, "Validacion", msg)
            self.selected_info.setText(msg)
            return
        if tiempo <= 0:
            msg = "El tiempo disponible debe ser mayor que cero."
            QMessageBox.warning(self, "Validacion", msg)
            self.selected_info.setText(msg)
            return

        resultados_por_criterio = []
        optimized = {}
        basic = None
        for criterio, etiqueta, _ in criterios:
            if criterio not in criterios_sel:
                continue

            resultado_criterio = plan_itinerary(
                grafo=self.grafo,
                origin_id=origen,
                destination_id=destino,
                budget=presupuesto,
                available_time=tiempo,
                criteria=[criterio],
                selected_transports=transportes_sel,
                include_secondary=self.sec_include.isChecked(),
            )
            if basic is None:
                basic = resultado_criterio.get("basic", {})
            route = resultado_criterio.get("optimized", {}).get(criterio)
            optimized[criterio] = route
            resultados_por_criterio.append(
                {
                    "criterion": criterio,
                    "criterion_label": etiqueta,
                    "result": resultado_criterio,
                    "route": route,
                }
            )

        resultado = {
            "basic": basic or {},
            "optimized": optimized,
        }

        primary_route = self._choose_primary_route(resultado, criterios_sel)
        self._show_executive_summaries(resultados_por_criterio)
        if primary_route:
            self.graph_view.highlight_route(primary_route["path"])
        else:
            self.graph_view.highlight_route([])

        sec_text = "Incluir" if self.sec_include.isChecked() else "Excluir"
        resumen = (
            f"Origen: {origen} -> Destino: {destino}\n"
            f"Criterios: {', '.join(criterios_texto)}\n"
            f"Transportes: {', '.join(transportes_sel)}\n"
            f"Aeropuertos secundarios: {sec_text}\n"
            f"Presupuesto: ${presupuesto:.2f}, Tiempo: {tiempo} h"
        )
        self.selected_info.setText(resumen)
        self.route_calculated.emit(
            {
                "result": resultado,
                "primary_route": primary_route,
                "criteria_results": resultados_por_criterio,
                "context": {
                    "origin": origen,
                    "destination": destino,
                    "budget": presupuesto,
                    "available_time": tiempo,
                    "criteria": criterios_sel,
                    "criteria_labels": criterios_texto,
                    "selected_transports": transportes_sel,
                    "include_secondary": self.sec_include.isChecked(),
                },
            }
        )
    """Auxiliary method to choose the primary route from the calculated results based on the selected criteria. This method iterates through the selected criteria in order of preference and returns the first valid route found for any of those criteria. If no valid route is found for the selected criteria, it falls back to checking the basic routes and returns the first valid one. If no valid routes are found at all, it returns None."""
    def _choose_primary_route(self, resultado, criterios_sel):
        for criterion in criterios_sel:
            route = resultado["optimized"].get(criterion)
            if route and route.get("legs"):
                return route

        for route in resultado["basic"].values():
            if route and route.get("legs"):
                return route

        return None
    """Auxiliary method to display the executive summaries for each criterion in the control panel. This method clears any existing summaries and then creates a new summary block for each criterion result, showing details such as the criterion used, the route found, total distance, time, cost, and number of stops. If no route is found for a criterion, it indicates that the route is not available."""
    def _show_executive_summaries(self, criteria_results):
        self._clear_summary(show_placeholder=False)
        if not criteria_results:
            self.summary_results_layout.addWidget(self._build_summary_label("Ruta encontrada: No disponible"))
            return

        for item in criteria_results:
            self.summary_results_layout.addWidget(
                self._build_criterion_summary_block(
                    item.get("criterion_label", item.get("criterion", "-")),
                    item.get("route"),
                )
            )
    """Auxiliary method to build a summary block widget for a given criterion and route information. This method creates a formatted block of text displaying the criterion used, the route found, total distance, time, cost, and number of stops. If no route is available, it indicates that in the summary. The resulting widget is styled and can be added to the control panel for display."""
    def _build_criterion_summary_block(self, criterion_label, route):
        block = QFrame()
        block.setObjectName("summaryPanel")
        layout = QVBoxLayout(block)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        lines = [f"Criterio utilizado: {criterion_label}"]
        if route:
            stops = max(0, len(route["path"]) - 2)
            lines.extend(
                [
                    f"Ruta encontrada: {' -> '.join(route['path'])}",
                    f"Distancia total: {route['total_distance']:.2f} km",
                    f"Tiempo total: {route['total_time']:.2f} h",
                    f"Costo total: ${route['total_cost']:.2f}",
                    f"Numero de escalas: {stops}",
                ]
            )
        else:
            lines.extend(
                [
                    "Ruta encontrada: No disponible",
                    "Distancia total: -",
                    "Tiempo total: -",
                    "Costo total: -",
                    "Numero de escalas: -",
                ]
            )

        for line in lines:
            layout.addWidget(self._build_summary_label(line))

        return block
    """Auxiliary method to build a formatted label widget for displaying summary information. This method creates a QLabel with the given text, applies styling, and allows for word wrapping to ensure that longer text is displayed properly within the layout. The resulting label can be used in the executive summary blocks to show details about the calculated routes."""
    
    def _build_summary_label(self, text):
        label = QLabel(text)
        label.setObjectName("infoLabel")
        label.setWordWrap(True)
        return label
    """Auxiliary method to clear the summary results displayed in the control panel. This method removes all existing summary widgets from the layout and optionally adds a placeholder message indicating that no route has been found. It is typically called before displaying new summary information to ensure that the displayed data is current and relevant to the latest route calculation."""
    def _clear_summary(self, show_placeholder=True):
        if not hasattr(self, "summary_results_layout"):
            return
        while self.summary_results_layout.count():
            item = self.summary_results_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if show_placeholder:
            self.summary_results_layout.addWidget(self._build_summary_label("Ruta encontrada: -"))
