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
    """Pagina para visualizar el grafo y planificar rutas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grafo = None
        self.graph_view = GraphView()
        self.graph_view.node_selected.connect(self.on_node_selected)
        self._setup_ui()

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

        self.results_view = QtWidgets.QTextEdit()
        self.results_view.setReadOnly(True)
        self.results_view.setObjectName("routeResults")
        self.results_view.setMinimumHeight(150)
        self.results_view.setPlainText("Los resultados del itinerario apareceran aqui.")

        legend_label = QLabel("Leyenda")
        legend_label.setObjectName("sectionTitle")

        legend = QtWidgets.QWidget()
        legend_layout = QVBoxLayout(legend)
        legend_layout.setContentsMargins(0, 0, 0, 0)
        legend_layout.setSpacing(8)
        legend_layout.addWidget(QLabel("Hub"))
        legend_layout.addWidget(QLabel("Aeropuerto Secundario"))

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
        control_layout.addWidget(self.results_view)
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

    def set_graph(self, grafo):
        self.grafo = grafo
        self.graph_view.set_graph(grafo)
        self._refresh_airports()

    def clear_graph(self):
        self.grafo = None
        self.graph_view.clear_graph()
        self.origin_combo.clear()
        self.dest_combo.clear()
        self.results_view.setPlainText("Los resultados del itinerario apareceran aqui.")
        self._clear_selected_info()

    def _refresh_airports(self):
        self.origin_combo.clear()
        self.dest_combo.clear()
        if self.grafo:
            codes = [vertice.identificador for vertice in self.grafo.obtener_vertices()]
            self.origin_combo.addItems(codes)
            self.dest_combo.addItems(codes)

    def _clear_selected_info(self):
        self.selected_code.setText("Codigo: -")
        self.selected_name.setText("Nombre: -")
        self.selected_city.setText("Ciudad: -")
        self.selected_country.setText("Pais: -")
        self.selected_timezone.setText("Zona Horaria: -")

    def on_node_selected(self, vertice):
        self.selected_code.setText(f"Codigo: {vertice.identificador}")
        self.selected_name.setText(f"Nombre: {vertice.nombre}")
        self.selected_city.setText(f"Ciudad: {vertice.ciudad}")
        self.selected_country.setText(f"Pais: {vertice.pais}")
        self.selected_timezone.setText(f"Zona Horaria: {vertice.zona_horaria}")

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

        resultado = plan_itinerary(
            grafo=self.grafo,
            origin_id=origen,
            destination_id=destino,
            budget=presupuesto,
            available_time=tiempo,
            criteria=criterios_sel,
            selected_transports=transportes_sel,
            include_secondary=self.sec_include.isChecked(),
        )

        sec_text = "Incluir" if self.sec_include.isChecked() else "Excluir"
        resumen = (
            f"Origen: {origen} -> Destino: {destino}\n"
            f"Criterios: {', '.join(criterios_texto)}\n"
            f"Transportes: {', '.join(transportes_sel)}\n"
            f"Aeropuertos secundarios: {sec_text}\n"
            f"Presupuesto: ${presupuesto:.2f}, Tiempo: {tiempo} h"
        )
        self.selected_info.setText(resumen)
        self.results_view.setPlainText(self._format_planning_result(resultado))

    def _format_planning_result(self, resultado):
        sections = [
            self._format_route_section(
                "Alternativa A: mayor cantidad de destinos por presupuesto",
                resultado["basic"]["max_destinations_by_budget"],
            ),
            self._format_route_section(
                "Alternativa B: mayor cantidad de destinos en menor tiempo",
                resultado["basic"]["max_destinations_by_time"],
            ),
            "Rutas por criterio de optimizacion",
        ]

        criterion_names = {
            CRITERION_DISTANCE: "Distancia",
            CRITERION_TIME: "Tiempo",
            CRITERION_COST: "Costo USD",
        }
        for criterion, route in resultado["optimized"].items():
            sections.append(
                self._format_route_section(
                    f"Criterio: {criterion_names.get(criterion, criterion)}",
                    route,
                )
            )

        return "\n\n".join(sections)

    def _format_route_section(self, title, route):
        if not route or not route["legs"]:
            return f"{title}\nNo se encontro una ruta valida con las restricciones actuales."

        stops = route["path"][1:-1]
        lines = [
            title,
            f"Secuencia: {' -> '.join(route['path'])}",
            f"Escalas intermedias: {', '.join(stops) if stops else 'Sin escalas'}",
            f"Transportes usados: {', '.join(route['transports_used'])}",
            f"Total: {route['total_distance']:.2f} km | ${route['total_cost']:.2f} | {route['total_time']:.2f} h",
            "Tramos:",
        ]
        lines.extend(route["formatted_legs"])
        return "\n".join(lines)
