from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import (
    QLabel,
    QComboBox,
    QPushButton,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QFormLayout,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QRadioButton,
    QButtonGroup,
    QGroupBox,
    QMessageBox,
)

from ui.graph_view import GraphView


class PaginaPlanificador(QtWidgets.QWidget):
    """Route planner page for graph visualization and future route tools."""

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
        control_panel.setMinimumWidth(320)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(16, 16, 16, 16)
        control_layout.setSpacing(16)

        section_label = QLabel("Selecciona origen y destino")
        section_label.setObjectName("sectionTitle")

        self.origin_combo = QComboBox()
        self.dest_combo = QComboBox()

        # Presupuesto y tiempo
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

        # Criterios de optimización
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

        # Aeropuertos secundarios (radio)
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

        # Tipos de transporte
        transport_box = QGroupBox()
        transport_box.setObjectName("transportBox")
        transport_layout = QVBoxLayout(transport_box)
        transport_layout.setContentsMargins(6, 6, 6, 6)
        self.tr_commercial = QCheckBox("Avión Comercial")
        self.tr_regional = QCheckBox("Avión Regional")
        self.tr_prop = QCheckBox("Hélice")
        for cb in (self.tr_commercial, self.tr_regional, self.tr_prop):
            cb.setChecked(True)
            transport_layout.addWidget(cb)

        form_layout = QFormLayout()
        form_layout.addRow("Origen", self.origin_combo)
        form_layout.addRow("Destino", self.dest_combo)
        form_layout.addRow("Presupuesto inicial (USD)", self.budget_spin)
        form_layout.addRow("Tiempo disponible (horas)", self.time_spin)
        form_layout.addRow("Criterios de optimización", criteria_box)
        form_layout.addRow("Aeropuertos secundarios", secondary_box)
        form_layout.addRow("Tipos de transporte preferidos", transport_box)

        self.calculate_button = QPushButton("Calcular Ruta")
        self.calculate_button.setObjectName("primaryButton")
        self.calculate_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.calculate_button.clicked.connect(self.on_calculate_route)

        

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
        self.selected_code = QLabel("Código: -")
        self.selected_name = QLabel("Nombre: -")
        self.selected_city = QLabel("Ciudad: -")
        self.selected_country = QLabel("País: -")
        self.selected_timezone = QLabel("Zona Horaria: -")

        for widget in [self.selected_code, self.selected_name, self.selected_city, self.selected_country, self.selected_timezone]:
            widget.setObjectName("infoValue")
            info_box_layout.addWidget(widget)

        control_layout.addWidget(section_label)
        control_layout.addLayout(form_layout)
        control_layout.addWidget(self.calculate_button)
        # Mensajes informativos
        self.selected_info = QtWidgets.QLabel("Seleccione un aeropuerto para ver más información.")
        self.selected_info.setWordWrap(True)
        self.selected_info.setObjectName("infoLabel")
        control_layout.addWidget(self.selected_info)
        control_layout.addWidget(legend_label)
        control_layout.addWidget(legend)
        control_layout.addWidget(info_box)
        control_layout.addStretch()

        graph_layout = QVBoxLayout()
        graph_layout.setContentsMargins(0, 0, 0, 0)
        graph_layout.addWidget(self.graph_view)

        content_layout.addWidget(control_panel)
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
        self._clear_selected_info()

    def _refresh_airports(self):
        self.origin_combo.clear()
        self.dest_combo.clear()
        if self.grafo:
            codes = [vertice.identificador for vertice in self.grafo.obtener_vertices()]
            self.origin_combo.addItems(codes)
            self.dest_combo.addItems(codes)

    def _clear_selected_info(self):
        self.selected_code.setText("Código: -")
        self.selected_name.setText("Nombre: -")
        self.selected_city.setText("Ciudad: -")
        self.selected_country.setText("País: -")
        self.selected_timezone.setText("Zona Horaria: -")

    def on_node_selected(self, vertice):
        self.selected_code.setText(f"Código: {vertice.identificador}")
        self.selected_name.setText(f"Nombre: {vertice.nombre}")
        self.selected_city.setText(f"Ciudad: {vertice.ciudad}")
        self.selected_country.setText(f"País: {vertice.pais}")
        self.selected_timezone.setText(f"Zona Horaria: {vertice.zona_horaria}")

    def on_calculate_route(self):
        if not self.grafo:
            self.selected_info.setText("Carga un archivo JSON antes de calcular la ruta.")
            return
        origen = self.origin_combo.currentText()
        destino = self.dest_combo.currentText()

        # Validaciones básicas
        if origen == destino:
            msg = "Origen y destino no pueden ser iguales."
            QMessageBox.warning(self, "Validación", msg)
            self.selected_info.setText(msg)
            return

        criterios = [
            ("Distancia", self.crit_dist.isChecked()),
            ("Tiempo", self.crit_time.isChecked()),
            ("Costo", self.crit_cost.isChecked()),
        ]
        criterios_sel = [c for c, sel in criterios if sel]
        if not criterios_sel:
            msg = "Debe seleccionar al menos un criterio de optimización."
            QMessageBox.warning(self, "Validación", msg)
            self.selected_info.setText(msg)
            return

        transportes = [
            ("Avión Comercial", self.tr_commercial.isChecked()),
            ("Avión Regional", self.tr_regional.isChecked()),
            ("Hélice", self.tr_prop.isChecked()),
        ]
        transportes_sel = [t for t, sel in transportes if sel]
        if not transportes_sel:
            msg = "Debe seleccionar al menos un tipo de transporte."
            QMessageBox.warning(self, "Validación", msg)
            self.selected_info.setText(msg)
            return

        presupuesto = self.budget_spin.value()
        tiempo = self.time_spin.value()
        if presupuesto <= 0:
            msg = "El presupuesto debe ser mayor que cero."
            QMessageBox.warning(self, "Validación", msg)
            self.selected_info.setText(msg)
            return
        if tiempo <= 0:
            msg = "El tiempo disponible debe ser mayor que cero."
            QMessageBox.warning(self, "Validación", msg)
            self.selected_info.setText(msg)
            return

        # Resumen informativo (sin ejecutar algoritmos aún)
        sec_text = "Incluir" if self.sec_include.isChecked() else "Excluir"
        resumen = (
            f"Validación exitosa.\nOrigen: {origen} → Destino: {destino}\n"
            f"Criterios: {', '.join(criterios_sel)}\n"
            f"Transportes: {', '.join(transportes_sel)}\n"
            f"Aeropuertos secundarios: {sec_text}\n"
            f"Presupuesto: ${presupuesto:.2f}, Tiempo: {tiempo} h\n"
            "Se generará una ruta por cada criterio seleccionado (implementación próximamente)."
        )
        QMessageBox.information(self, "Validación correcta", "Los datos son válidos.\n" + "Se procederá a calcular rutas internamente.")
        self.selected_info.setText(resumen)
