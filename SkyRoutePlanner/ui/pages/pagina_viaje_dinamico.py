import re

from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QHeaderView,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from models.viajero import Viajero
from simulation.gestor_viaje import GestorViaje
from ui.graph_view import GraphView


class PaginaViajeDinamico(QtWidgets.QWidget):
    """Step-by-step dynamic travel simulation page."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grafo = None
        self.gestor = None
        self.alternativas = []
        self.sin_destinos_eficientes = False
        self.actividades_actuales = []
        self.trabajos_actuales = []
        self.graph_view = GraphView()
        self.flight_timer = QtCore.QTimer(self)
        self.flight_timer.setInterval(200)
        self.flight_timer.timeout.connect(self._on_flight_timer_tick)
        self._setup_ui()

    """Auxiliary method to format a value as a monetary amount. This method takes a value, converts it to a float, and formats it as a string with a dollar sign and two decimal places. If the value is None or cannot be converted to a float, it defaults to 0.00. This method is used to consistently display monetary values in the report sections."""
    def _money(self, value):
        return f"${float(value or 0):.2f}"

    """Auxiliary method to format a value as a duration in hours. This method takes a value, converts it to a float, and formats it as a string with two decimal places followed by "h". If the value is None or cannot be converted to a float, it defaults to 0.00 h. This method is used to consistently display time durations in the report sections."""
    def _hours(self, value):
        return f"{float(value or 0):.2f} h"

    """Auxiliary method to format a value as a distance in kilometers. This method takes a value, converts it to a float, and formats it as a string with two decimal places followed by "km". If the value is None or cannot be converted to a float, it defaults to 0.00 km. This method is used to consistently display distance values in the report sections."""
    def _km(self, value):
        return f"{float(value or 0):.0f} km"

    """Auxiliary method to display a warning message box with a specified title and message. This method uses the QMessageBox class to create and show a warning dialog, allowing the user to acknowledge important information or issues that arise during the simulation."""
    def _show_warning(self, title, message):
        QMessageBox.warning(self, title, message)

    """Auxiliary method to format a message for when a route is blocked. This method takes an alternative route information dictionary and constructs a user-friendly message explaining why the route is blocked, including details about the origin, destination, distance, subsidy limits, and budget constraints. The message is tailored based on the specific reason for the blockage, such as returning to the initial origin or exceeding subsidy limits."""
    def _format_route_block_message(self, alternativa):
        if alternativa.get("bloqueada_por_origen_inicial", False):
            origen = alternativa.get("destino", "origen")
            if alternativa.get("fin_por_origen_inicial", False):
                return "No existen más destinos disponibles para continuar el viaje de manera eficiente."

            return (
                "Se evita regresar al aeropuerto de origen inicial.\n\n"
                f"Origen inicial: {origen}.\n"
                "Seleccione una alternativa hacia otro destino disponible."
            )

        tramo = float(alternativa.get("distancia_km", 0) or 0)
        limite = float(alternativa.get("limite_subsidio_km", 0) or 0)
        usada = float(alternativa.get("distancia_subsidiada_usada_km", 0) or 0)
        disponible = max(0.0, limite - usada)

        if alternativa.get("es_subsidiada", False) and not alternativa.get("puede_usar_subsidio", True):
            return (
                "No puede utilizar esta ruta subsidiada.\n\n"
                f"Distancia del tramo: {self._km(tramo)}.\n"
                f"Distancia subsidiada disponible: {self._km(disponible)}."
            )

        costo = float(alternativa.get("costo_vuelo", 0) or 0)
        presupuesto = 0.0
        if self.gestor:
            presupuesto = float(self.gestor.viajero.presupuesto_actual or 0)
        return (
            "No se puede avanzar.\n"
            f"Se requieren {self._money(costo)} para continuar,\n"
            f"pero solo dispone de {self._money(presupuesto)}."
        )

    """Auxiliary method to format a message for when a route is not available. This method takes a message and an alternative route information dictionary, and constructs a user-friendly message explaining why the route is not available, including details about the origin, destination, and any relevant constraints."""
    def _format_route_exception_message(self, message, alternativa=None):
        if "No existe ruta directa" in message and alternativa:
            origen = alternativa.get("origen", "-")
            destino = alternativa.get("destino", "-")
            return (
                "No se encontro una ruta directa para la seleccion actual.\n\n"
                f"Origen seleccionado: {origen}.\n"
                f"Destino seleccionado: {destino}."
            )

        if "ruta subsidiada supera" in message and alternativa:
            return self._format_route_block_message(alternativa)

        return self._format_resource_exception_message(message)

    """Auxiliary method to format a message for resource-related exceptions. This method takes an exception message and uses regular expressions to identify specific patterns related to spending, time consumption, activity budgets, and work hours. It then constructs user-friendly messages based on the identified patterns, providing clear explanations of the issues and the required versus available resources."""
    def _format_resource_exception_message(self, message):
        spend_match = re.search(
            r"Cannot spend ([0-9]+(?:\.[0-9]+)?): only ([0-9]+(?:\.[0-9]+)?) available",
            message,
        )
        if spend_match:
            return (
                "No se puede avanzar.\n"
                f"Se requieren {self._money(spend_match.group(1))} para continuar,\n"
                f"pero solo dispone de {self._money(spend_match.group(2))}."
            )

        time_match = re.search(
            r"Cannot consume ([0-9]+(?:\.[0-9]+)?) hours: only ([0-9]+(?:\.[0-9]+)?) available",
            message,
        )
        if time_match:
            return (
                "No hay tiempo suficiente para continuar.\n"
                f"Tiempo requerido: {self._hours(time_match.group(1))}.\n"
                f"Tiempo disponible: {self._hours(time_match.group(2))}."
            )

        activity_budget = re.search(
            r"Insufficient budget for activity '(.+)': need ([0-9]+(?:\.[0-9]+)?), have ([0-9]+(?:\.[0-9]+)?)",
            message,
        )
        if activity_budget:
            return (
                f"No se puede realizar la actividad \"{activity_budget.group(1)}\".\n"
                f"Costo requerido: {self._money(activity_budget.group(2))}.\n"
                f"Presupuesto disponible: {self._money(activity_budget.group(3))}."
            )

        activity_time = re.search(
            r"Insufficient time for activity '(.+)': need ([0-9]+(?:\.[0-9]+)?) hours, have ([0-9]+(?:\.[0-9]+)?) hours",
            message,
        )
        if activity_time:
            return (
                f"No se puede realizar la actividad \"{activity_time.group(1)}\".\n"
                f"Tiempo requerido: {self._hours(activity_time.group(2))}.\n"
                f"Tiempo disponible: {self._hours(activity_time.group(3))}."
            )

        work_time = re.search(
            r"Insufficient time for work: need ([0-9]+(?:\.[0-9]+)?) hours, have ([0-9]+(?:\.[0-9]+)?) hours",
            message,
        )
        if work_time:
            return (
                "No se puede aceptar el trabajo.\n"
                f"Tiempo requerido: {self._hours(work_time.group(1))}.\n"
                f"Tiempo disponible: {self._hours(work_time.group(2))}."
            )

        if "Solo se puede trabajar" in message:
            return "Solo puede aceptar trabajos cuando el presupuesto esta por debajo del minimo configurado."
        if "Work hours must be positive" in message:
            return "Ingrese una cantidad de horas mayor que cero para aceptar el trabajo."
        if "Spending amount must be non-negative" in message:
            return "El costo no puede ser negativo."
        if "Income amount must be non-negative" in message:
            return "El ingreso no puede ser negativo."
        if "Time consumption must be non-negative" in message:
            return "El tiempo no puede ser negativo."

        return message

    """Auxiliary method to build a status value label. This method creates and returns a QLabel widget with a specific object name for styling. The label is intended to display the value of a particular status item in the simulation, such as the current airport, remaining budget, or time left."""
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Viaje Dinamico")
        title.setObjectName("pageTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(18)

        control_panel = QFrame()
        control_panel.setObjectName("controlPanel")
        control_panel.setMinimumWidth(360)
        control_panel.setMaximumWidth(460)
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(16, 16, 16, 16)
        control_layout.setSpacing(14)

        setup_title = QLabel("Inicio de simulacion")
        setup_title.setObjectName("sectionTitle")
        self.origin_combo = QComboBox()

        self.budget_spin = QDoubleSpinBox()
        self.budget_spin.setPrefix("$")
        self.budget_spin.setMaximum(1e9)
        self.budget_spin.setDecimals(2)
        self.budget_spin.setSingleStep(25)
        self.budget_spin.setValue(500)

        self.time_spin = QSpinBox()
        self.time_spin.setMinimum(1)
        self.time_spin.setMaximum(10_000)
        self.time_spin.setSuffix(" h")
        self.time_spin.setValue(72)

        form = QFormLayout()
        form.addRow("Origen", self.origin_combo)
        form.addRow("Presupuesto", self.budget_spin)
        form.addRow("Tiempo total", self.time_spin)

        self.start_button = QPushButton("Iniciar viaje")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.start_button.clicked.connect(self.on_start_trip)

        self.suggested_label = QLabel("Sugerencia: -")
        self.suggested_label.setObjectName("infoLabel")
        self.suggested_label.setWordWrap(True)

        self.subsidy_label = QLabel("Distancia subsidiada utilizada: 0.00 km / 0.00 km permitidos (20%)")
        self.subsidy_label.setObjectName("infoLabel")
        self.subsidy_label.setWordWrap(True)

        self.alternatives_table = QTableWidget(0, 6)
        self.alternatives_table.setObjectName("routeResults")
        self.alternatives_table.setHorizontalHeaderLabels(
            ["D", "Aero", "(km)", "(USD)", "(horas)", "Sub"]
        )
        self.alternatives_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.alternatives_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.alternatives_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.alternatives_table.setAlternatingRowColors(True)
        self.alternatives_table.setMinimumHeight(180)
        self.alternatives_table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.alternatives_table.verticalHeader().setVisible(False)
        table_header = self.alternatives_table.horizontalHeader()
        table_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.alternatives_table.itemSelectionChanged.connect(self.on_alternative_table_selection_changed)

        self.advance_button = QPushButton("Avanzar al destino seleccionado")
        self.advance_button.setObjectName("primaryButton")
        self.advance_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.advance_button.clicked.connect(self.on_advance_selected)
        self.advance_button.setEnabled(False)

        routes_title = QLabel("Interrupciones de Ruta")
        routes_title.setObjectName("sectionTitle")
        self.routes_table = QTableWidget(0, 3)
        self.routes_table.setObjectName("routeResults")
        self.routes_table.setHorizontalHeaderLabels(["Origen", "Destino", "Estado"])
        self.routes_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.routes_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.routes_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.routes_table.setAlternatingRowColors(True)
        self.routes_table.setMinimumHeight(120)
        self.routes_table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.routes_table.verticalHeader().setVisible(False)
        self.routes_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.block_route_button = QPushButton("Bloquear Ruta")
        self.block_route_button.setObjectName("primaryButton")
        self.block_route_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.block_route_button.clicked.connect(self.on_block_route)

        status_title = QLabel("Estado actual")
        status_title.setObjectName("sectionTitle")
        self.status_grid = QGridLayout()
        self.status_labels = {
            "aeropuerto": self._build_status_value("-"),
            "presupuesto": self._build_status_value("-"),
            "tiempo": self._build_status_value("-"),
            "visitados": self._build_status_value("-"),
            "alimentacion": self._build_status_value("-"),
            "hospedaje": self._build_status_value("-"),
        }
        self._add_status_row(0, "Aeropuerto", self.status_labels["aeropuerto"])
        self._add_status_row(1, "Presupuesto", self.status_labels["presupuesto"])
        self._add_status_row(2, "Tiempo restante", self.status_labels["tiempo"])
        self._add_status_row(3, "Visitados", self.status_labels["visitados"])
        self._add_status_row(4, "Alimentacion", self.status_labels["alimentacion"])
        self._add_status_row(5, "Hospedaje", self.status_labels["hospedaje"])
        
        activities_title = QLabel("Actividades")
        activities_title.setObjectName("sectionTitle")
        self.activity_table = QTableWidget(0, 3)
        self.activity_table.setObjectName("routeResults")
        self.activity_table.setHorizontalHeaderLabels(["Actividad", "Duracion", "Costo"])
        self.activity_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.activity_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.activity_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setMinimumHeight(120)
        self.activity_table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.activity_table.verticalHeader().setVisible(False)
        self.activity_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.activity_table.itemSelectionChanged.connect(self._refresh_action_buttons)

        activity_buttons = QHBoxLayout()
        self.do_activity_button = QPushButton("Realizar actividad")
        self.do_activity_button.setObjectName("primaryButton")
        self.do_activity_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.do_activity_button.clicked.connect(self.on_do_activity)
        activity_buttons.addWidget(self.do_activity_button)

        job_title = QLabel("Trabajos disponibles")
        job_title.setObjectName("sectionTitle")
        self.job_table = QTableWidget(0, 3)
        self.job_table.setObjectName("routeResults")
        self.job_table.setHorizontalHeaderLabels(["Trabajo", "Tarifa", "Max"])
        self.job_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.job_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.job_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.job_table.setAlternatingRowColors(True)
        self.job_table.setMinimumHeight(120)
        self.job_table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.job_table.verticalHeader().setVisible(False)
        self.job_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.job_table.itemSelectionChanged.connect(self._refresh_job_hours_limit)

        self.work_hours_spin = QDoubleSpinBox()
        self.work_hours_spin.setMinimum(0.25)
        self.work_hours_spin.setMaximum(24)
        self.work_hours_spin.setDecimals(2)
        self.work_hours_spin.setSingleStep(0.5)
        self.work_hours_spin.setSuffix(" h")

        job_form = QFormLayout()
        job_form.addRow("Horas", self.work_hours_spin)

        job_buttons = QHBoxLayout()
        self.accept_job_button = QPushButton("Aceptar trabajo")
        self.accept_job_button.setObjectName("primaryButton")
        self.accept_job_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.accept_job_button.clicked.connect(self.on_accept_job)
        job_buttons.addWidget(self.accept_job_button)

        log_title = QLabel("Registro de decisiones")
        log_title.setObjectName("sectionTitle")
        self.decision_log = QTextEdit()
        self.decision_log.setObjectName("routeResults")
        self.decision_log.setReadOnly(True)
        self.decision_log.setMinimumHeight(160)
        self.decision_log.setPlainText("Aun no hay decisiones registradas.")

        control_layout.addWidget(setup_title)
        control_layout.addLayout(form)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(status_title)
        control_layout.addLayout(self.status_grid)
        control_layout.addWidget(self.suggested_label)
        control_layout.addWidget(self.subsidy_label)
        control_layout.addWidget(self.alternatives_table)
        control_layout.addWidget(self.advance_button)
        control_layout.addWidget(routes_title)
        control_layout.addWidget(self.routes_table)
        control_layout.addWidget(self.block_route_button)
        control_layout.addWidget(activities_title)
        control_layout.addWidget(self.activity_table)
        control_layout.addLayout(activity_buttons)
        control_layout.addWidget(job_title)
        control_layout.addWidget(self.job_table)
        control_layout.addLayout(job_form)
        control_layout.addLayout(job_buttons)
        control_layout.addWidget(log_title)
        control_layout.addWidget(self.decision_log)
        control_layout.addStretch()

        scroll = QtWidgets.QScrollArea()
        scroll.setObjectName("plannerScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(control_panel)

        content_layout.addWidget(scroll,3)
        content_layout.addWidget(self.graph_view, 5)
        layout.addLayout(content_layout, stretch=1)

    """Auxiliary method to add a status row to the status grid layout. This method takes a row index, a title for the status item, and a value widget (such as a QLabel) to display the value of the status item. It creates a title label with specific styling and adds both the title and value widgets to the grid layout at the specified row."""
    def _build_status_value(self, text):
        label = QLabel(text)
        label.setObjectName("infoValue")
        label.setWordWrap(True)
        return label
    
    """Auxiliary method to add a status row to the status grid layout. This method takes a row index, a title for the status item, and a value widget (such as a QLabel) to display the value of the status item. It creates a title label with specific styling and adds both the title and value widgets to the grid layout at the specified row."""
    def _add_status_row(self, row, title, value_widget):
        title_label = QLabel(title)
        title_label.setObjectName("infoLabel")
        self.status_grid.addWidget(title_label, row, 0)
        self.status_grid.addWidget(value_widget, row, 1)


    """Auxiliary method to refresh the state of action buttons based on the current selection and simulation state. This method checks the selected activity and job, as well as the current state of the gestor, to determine whether the "Realizar actividad" and "Aceptar trabajo" buttons should be enabled or disabled. It ensures that the user can only perform valid actions based on the current context of the simulation."""
    def set_graph(self, grafo):
        self.grafo = grafo
        self.graph_view.set_graph(grafo)
        self._refresh_airports()
        self._reset_simulation_view()

    """Auxiliary method to clear the current graph and reset the simulation state. This method stops any ongoing flight timers, clears the graph and gestor references, resets the graph view, clears the origin selection, and resets all simulation-related views and data to their initial states. It ensures that the user can start fresh with a new graph or configuration."""
    def clear_graph(self):
        self.flight_timer.stop()
        self.grafo = None
        self.gestor = None
        self.graph_view.clear_graph()
        self.origin_combo.clear()
        self._reset_simulation_view()

    """Auxiliary method to refresh the list of available airports in the origin selection combo box. This method clears the current items in the combo box and repopulates it with the identifiers of the vertices from the graph, allowing the user to select a valid starting point for the dynamic travel simulation."""
    def _refresh_airports(self):
        self.origin_combo.clear()
        if self.grafo:
            self.origin_combo.addItems([vertice.identificador for vertice in self.grafo.obtener_vertices()])

    """Auxiliary method to reset the simulation view to its initial state. This method clears all simulation data, stops any ongoing timers, and resets the graph view and tables."""
    def _reset_simulation_view(self):
        self.alternativas = []
        self.sin_destinos_eficientes = False
        self.flight_timer.stop()
        self.graph_view.clear_flight_progress()
        self.alternatives_table.setRowCount(0)
        self.advance_button.setEnabled(False)
        self.suggested_label.setText("Sugerencia: -")
        self.subsidy_label.setText("Distancia subsidiada utilizada: 0.00 km / 0.00 km permitidos (20%)")
        self.subsidy_label.setStyleSheet("")
        for label in self.status_labels.values():
            label.setText("-")
        self.actividades_actuales = []
        self.trabajos_actuales = []
        self.activity_table.setRowCount(0)
        self.job_table.setRowCount(0)
        self.routes_table.setRowCount(0)
        self._refresh_action_buttons()
        self.decision_log.setPlainText("Aun no hay decisiones registradas.")

    """Auxiliary method to handle the start of the dynamic travel simulation. This method validates that a graph is loaded and an origin airport is selected, then initializes the GestorViaje with the provided graph and traveler information. It also resets the flight timer and updates the graph view to reflect the starting point of the simulation."""
    def on_start_trip(self):
        if not self.grafo:
            self._show_warning("Validacion", "Carga un grafo antes de iniciar el viaje dinamico.")
            return

        origen = self.origin_combo.currentText()
        if not origen:
            self._show_warning("Validacion", "Selecciona un aeropuerto de origen.")
            return

        viajero = Viajero(
            presupuesto_inicial=self.budget_spin.value(),
            tiempo_total_horas=self.time_spin.value(),
        )
        self.gestor = GestorViaje(self.grafo, viajero)
        self.gestor.iniciar_viaje_dinamico(origen)
        self.flight_timer.stop()
        self.graph_view.clear_flight_progress()
        self.graph_view.highlight_route([origen])
        self._refresh_dynamic_view()

    """Auxiliary method to handle advancing to the selected destination. This method checks if the gestor is in a valid state to advance, retrieves the selected alternative route, and attempts to advance to the destination using the gestor. It also handles any exceptions that may arise during the advancement process, providing user-friendly messages and updating the graph view accordingly."""
    def on_advance_selected(self):
        if not self.gestor:
            return
        if self.gestor.estado_movimiento == "en_vuelo":
            QMessageBox.warning(self, "Vuelo en curso", "Espera a que termine el vuelo actual.")
            return

        index = self._selected_alternative_index()
        if index < 0 or index >= len(self.alternativas):
            return

        alternativa = self.alternativas[index]
        if not alternativa.get("puede_pagarse", True):
            self._show_warning("No se puede avanzar", self._format_route_block_message(alternativa))
            self._refresh_dynamic_view()
            return

        try:
            self.gestor.avanzar_a_destino(alternativa["destino"], alternativa["transporte"])
        except ValueError as exc:
            self._show_warning(
                "No se puede avanzar",
                self._format_route_exception_message(str(exc), alternativa),
            )
            return

        vuelo = self.gestor.vuelo_actual
        if vuelo:
            self.graph_view.highlight_route([vuelo["origen"], vuelo["destino"]])
            self.graph_view.set_flight_progress(vuelo["origen"], vuelo["destino"], 0.0)
            self.flight_timer.start()
        self._refresh_dynamic_view()

    """Auxiliary method to handle changes in the selection of alternative routes. This method retrieves the currently selected row in the alternatives table and updates the enabled state of the advance button based on whether the selected alternative can be advanced to, ensuring that the user can only attempt to advance to valid destinations."""
    def on_alternative_table_selection_changed(self):
        index = self._selected_table_row()
        self.advance_button.setEnabled(self._can_advance_from_index(index))

    """Auxiliary method to retrieve the index of the currently selected row in the alternatives table. This method checks the selection model of the table and returns the row index of the first selected item, or -1 if no row is selected. This index is used to determine which alternative route the user has selected for potential advancement."""
    def _selected_table_row(self):
        selected = self.alternatives_table.selectionModel().selectedRows()
        if not selected:
            return -1
        return selected[0].row()

    """Auxiliary method to determine if the user can advance to the destination corresponding to the given index in the alternatives list. This method checks if the gestor is currently in flight, and if not, it verifies that the index is within bounds and that the alternative at that index can be paid for, returning True if advancement is possible and False otherwise."""
    def _selected_alternative_index(self):
        return self._selected_table_row()

    """Auxiliary method to determine if the user can advance to the destination corresponding to the given index in the alternatives list. This method checks if the gestor is currently in flight, and if not, it verifies that the index is within bounds and that the alternative at that index can be paid for, returning True if advancement is possible and False otherwise."""
    def _can_advance_from_index(self, index):
        if self.gestor and self.gestor.estado_movimiento == "en_vuelo":
            return False
        if index < 0 or index >= len(self.alternativas):
            return False
        return bool(self.alternativas[index].get("puede_pagarse", True))

    """Auxiliary method to handle the flight timer tick event. This method is called periodically while a flight is in progress, and it updates the flight progress on the graph view based on the current state of the gestor. It also checks for any exceptions that may occur during the flight advancement and handles them appropriately, including stopping the timer and showing warning messages if necessary."""
    def _on_flight_timer_tick(self):
        if not self.gestor or self.gestor.estado_movimiento != "en_vuelo" or not self.gestor.vuelo_actual:
            self.flight_timer.stop()
            self.graph_view.clear_flight_progress()
            return

        vuelo = self.gestor.vuelo_actual
        total = float(vuelo.get("tiempo_total_horas", 0) or 0)
        delta = total / 60 if total > 0 else 0
        try:
            resultado = self.gestor.avanzar_vuelo(delta)
        except ValueError as exc:
            try:
                self.gestor.cancelar_vuelo(str(exc))
            except ValueError:
                pass
            self.flight_timer.stop()
            self.graph_view.clear_flight_progress()
            self._show_warning("Vuelo cancelado", self._format_resource_exception_message(str(exc)))
            self._refresh_dynamic_view()
            return

        if self.gestor.estado_movimiento == "en_vuelo" and self.gestor.vuelo_actual:
            vuelo = self.gestor.vuelo_actual
            self.graph_view.set_flight_progress(
                vuelo["origen"],
                vuelo["destino"],
                self.gestor.obtener_progreso_vuelo(),
            )
            self._refresh_status()
            return

        self.flight_timer.stop()
        self.graph_view.clear_flight_progress()
        self.graph_view.highlight_route(self.gestor.ruta_actual)
        self._refresh_dynamic_view()
        if resultado and resultado.get("tipo") == "vuelo_cancelado":
            self._show_warning(
                "Vuelo cancelado",
                self._format_resource_exception_message(resultado.get("motivo", "Vuelo cancelado")),
            )

    """Auxiliary method to find the index of the first alternative route that can be paid for. This method iterates through the list of alternatives and returns the index of the first one that has the "puede_pagarse" flag set to True. If no such alternative is found, it returns -1, indicating that there are no payable alternatives available."""
    def _first_payable_alternative_index(self):
        for index, alternativa in enumerate(self.alternativas):
            if alternativa.get("puede_pagarse", True):
                return index
        return -1

    """Auxiliary method to retrieve the initial origin of the journey. This method checks the current state of the gestor and returns the code of the first airport in the current route, or None if no route is available."""
    def _obtener_origen_inicial(self):
        if not self.gestor:
            return None

        estado = self.gestor.obtener_estado()
        ruta = estado.get("ruta_actual", [])
        if not ruta:
            return None
        return str(ruta[0]).upper().strip()

    """Auxiliary method to apply the rule of preventing return to the initial origin. This method checks the current alternatives and marks those that would return to the initial origin as not payable, while also determining if there are any efficient destinations available. It updates the state of the alternatives accordingly and sets a flag if there are no efficient destinations left."""
    def _aplicar_regla_regreso_origen(self):
        self.sin_destinos_eficientes = False
        origen_inicial = self._obtener_origen_inicial()
        if not origen_inicial or not self.alternativas:
            return

        alternativas_viables = [
            alternativa
            for alternativa in self.alternativas
            if alternativa.get("puede_pagarse", True)
        ]
        if not alternativas_viables:
            return

        alternativas_viables_no_origen = [
            alternativa
            for alternativa in alternativas_viables
            if str(alternativa.get("destino", "")).upper().strip() != origen_inicial
        ]
        solo_regreso_al_origen = not alternativas_viables_no_origen

        for alternativa in self.alternativas:
            destino = str(alternativa.get("destino", "")).upper().strip()
            if destino == origen_inicial:
                alternativa["puede_pagarse"] = False
                alternativa["bloqueada_por_origen_inicial"] = True
                alternativa["fin_por_origen_inicial"] = solo_regreso_al_origen

        self.sin_destinos_eficientes = solo_regreso_al_origen

    """Auxiliary method to suggest an alternative route for the user. This method checks the current alternatives and the airports that have already been visited by the traveler, and it prioritizes suggesting routes to new destinations that can be paid for. If no such routes are available, it falls back to suggesting any payable route, even if it leads to a previously visited airport. It returns the suggested alternative or None if no alternatives are available."""
    def _sugerir_alternativa_ui(self):
        visitados = set()
        if self.gestor:
            visitados = {codigo.upper().strip() for codigo in self.gestor.viajero.aeropuertos_visitados}

        no_visitadas = [
            alternativa
            for alternativa in self.alternativas
            if alternativa.get("puede_pagarse", True)
            and str(alternativa.get("destino", "")).upper().strip() not in visitados
        ]
        if no_visitadas:
            return no_visitadas[0]

        pagables = [
            alternativa
            for alternativa in self.alternativas
            if alternativa.get("puede_pagarse", True)
        ]
        return pagables[0] if pagables else None

    """Auxiliary method to refresh all dynamic views related to the current state of the simulation. This method calls individual refresh methods for the status, alternatives, routes panel, action controls, and decision log, ensuring that all displayed information is up-to-date with the current state of the gestor and the travel simulation."""
    def _refresh_dynamic_view(self):
        self._refresh_status()
        self._refresh_alternatives()
        self._refresh_routes_panel()
        self._refresh_action_controls()
        self._refresh_decision_log()

    """Auxiliary method to refresh the status display based on the current state of the gestor. This method retrieves the current state, including the traveler information and current flight status, and updates the corresponding labels in the UI to reflect the current airport, remaining budget, time left, visited airports count, and time since last alimentation and lodging."""
    def _refresh_status(self):
        if not self.gestor:
            return

        estado = self.gestor.obtener_estado()
        viajero = estado["viajero"]
        vuelo = estado.get("vuelo_actual")
        if estado.get("estado_movimiento") == "en_vuelo" and vuelo:
            progreso = self.gestor.obtener_progreso_vuelo() * 100
            self.status_labels["aeropuerto"].setText(
                f"En vuelo {vuelo['origen']} -> {vuelo['destino']} ({progreso:.0f}%)"
            )
        else:
            self.status_labels["aeropuerto"].setText(str(estado["aeropuerto_actual"]))
        self.status_labels["presupuesto"].setText(f"${viajero['presupuesto_actual']:.2f}")
        self.status_labels["tiempo"].setText(f"{viajero['tiempo_restante_horas']:.2f} h")
        self.status_labels["visitados"].setText(str(viajero["cantidad_aeropuertos_visitados"]))
        self.status_labels["alimentacion"].setText(
            f"{estado['horas_desde_ultima_alimentacion']:.2f} / 8 h"
        )
        self.status_labels["hospedaje"].setText(
            f"{estado['horas_desde_ultimo_hospedaje']:.2f} / 20 h"
        )

    """Auxiliary method to refresh the alternatives table and related information. This method retrieves the available alternatives from the gestor, applies the rule to prevent returning to the initial origin, updates the subsidy summary, and refreshes the alternatives table with the current data. It also updates the suggested alternative label based on the current alternatives and their payability."""
    def _refresh_alternatives(self):
        self.alternativas = []
        self.advance_button.setEnabled(False)

        if not self.gestor:
            self.suggested_label.setText("Sugerencia: -")
            return
        if self.gestor.estado_movimiento == "en_vuelo":
            self.suggested_label.setText("Sugerencia: vuelo en curso.")
            self._refresh_subsidy_summary()
            self._refresh_alternatives_table()
            return

        self.alternativas = self.gestor.obtener_alternativas_disponibles()
        self._aplicar_regla_regreso_origen()
        self._refresh_subsidy_summary()
        sugerida = self._sugerir_alternativa_ui()
        if self.sin_destinos_eficientes:
            self.suggested_label.setText(
                "No existen más destinos disponibles para continuar el viaje de manera eficiente."
            )
        elif sugerida:
            self.suggested_label.setText(
                "Sugerencia: "
                f"{sugerida['origen']} -> {sugerida['destino']} en {sugerida['transporte']} "
                f"(${sugerida['costo_vuelo']:.2f}, {sugerida['tiempo_vuelo_horas']:.2f} h)"
            )
        else:
            self.suggested_label.setText("Sugerencia: no hay vuelos pagables hacia nuevos destinos.")

        self._refresh_alternatives_table()

    """Auxiliary method to refresh the subsidy summary display based on the current state of the gestor. This method retrieves the subsidized distance used and total distance flown from the current state, calculates the allowed subsidized distance, and updates the subsidy label with this information. It also applies color coding to the label based on how much of the subsidy has been used, providing a visual indication of the subsidy usage."""
    def _refresh_subsidy_summary(self):
        if not self.gestor:
            return

        estado = self.gestor.obtener_estado()
        utilizada = float(estado.get("distancia_subsidiada_km", 0) or 0)
        total = float(estado.get("distancia_volada_km", 0) or 0)
        permitida = total * 0.20
        self.subsidy_label.setText(
            "Distancia subsidiada utilizada: "
            f"{utilizada:.2f} km / {permitida:.2f} km permitidos (20%)"
        )

        porcentaje = utilizada / permitida if permitida > 0 else 0
        if porcentaje >= 0.90:
            self.subsidy_label.setStyleSheet("color: #f87171; font-weight: 700;")
        elif porcentaje >= 0.75:
            self.subsidy_label.setStyleSheet("color: #facc15; font-weight: 700;")
        else:
            self.subsidy_label.setStyleSheet("")

    """Auxiliary method to refresh the alternatives table with the current list of alternatives. This method populates the table with the destination, transport, distance, cost, time, and subsidy information for each alternative. It also applies styling to indicate which alternatives are subsidized, which are not payable, and highlights the best options based on cost and time. Finally, it selects the first payable alternative if available and enables the advance button accordingly."""
    def _refresh_alternatives_table(self):
        self.alternatives_table.setRowCount(len(self.alternativas))
        if not self.alternativas:
            self.advance_button.setEnabled(False)
            return

        costos = [float(alt.get("costo_vuelo", 0) or 0) for alt in self.alternativas]
        tiempos = [float(alt.get("tiempo_vuelo_horas", 0) or 0) for alt in self.alternativas]
        menor_costo = min(costos)
        menor_tiempo = min(tiempos)

        for row, alternativa in enumerate(self.alternativas):
            values = [
                alternativa.get("destino", "-"),
                alternativa.get("transporte", "-"),
                f"{float(alternativa.get('distancia_km', 0) or 0):.2f}",
                f"${float(alternativa.get('costo_vuelo', 0) or 0):.2f}",
                f"{float(alternativa.get('tiempo_vuelo_horas', 0) or 0):.2f}",
                "Si" if alternativa.get("es_subsidiada", False) else "No",
            ]

            row_enabled = alternativa.get("puede_pagarse", True)
            blocked_message = ""
            if not row_enabled:
                blocked_message = self._format_route_block_message(alternativa)

            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
                if not row_enabled:
                    item.setForeground(QtGui.QBrush(QtGui.QColor("#94a3b8")))
                    item.setToolTip(blocked_message)
                    item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEnabled)
                self.alternatives_table.setItem(row, column, item)

            if alternativa.get("es_subsidiada", False):
                self._paint_table_row(row, "#713f12")
            if not row_enabled:
                self._paint_table_row(row, "#334155")

            costo = float(alternativa.get("costo_vuelo", 0) or 0)
            tiempo = float(alternativa.get("tiempo_vuelo_horas", 0) or 0)
            if row_enabled and costo == menor_costo:
                self._paint_table_cell(row, 3, "#14532d")
            if row_enabled and tiempo == menor_tiempo:
                self._paint_table_cell(row, 4, "#1e3a8a")

        self.alternatives_table.resizeRowsToContents()
        selectable_row = self._first_payable_alternative_index()
        if selectable_row >= 0:
            self.alternatives_table.selectRow(selectable_row)
            self.advance_button.setEnabled(True)
        else:
            self.alternatives_table.clearSelection()
            self.advance_button.setEnabled(False)

    """Auxiliary method to format a message for blocked routes based on the given alternative. This method checks the properties of the alternative to determine the reason why it cannot be paid for, such as being blocked due to returning to the initial origin or being unaffordable, and returns an appropriate message to explain the situation to the user."""
    def _paint_table_cell(self, row, column, color):
        item = self.alternatives_table.item(row, column)
        if item:
            item.setBackground(QtGui.QBrush(QtGui.QColor(color)))

    """Auxiliary method to format a message for blocked routes based on the given alternative. This method checks the properties of the alternative to determine the reason why it cannot be paid for, such as being blocked due to returning to the initial origin or being unaffordable, and returns an appropriate message to explain the situation to the user."""
    def _paint_table_row(self, row, color):
        for column in range(self.alternatives_table.columnCount()):
            self._paint_table_cell(row, column, color)
    
    """Auxiliary method to format a message for blocked routes based on the given alternative. This method checks the properties of the alternative to determine the reason why it cannot be paid for, such as being blocked due to returning to the initial origin or being unaffordable, and returns an appropriate message to explain the situation to the user."""
    def _paint_routes_table_row(self, row, color):
        for column in range(self.routes_table.columnCount()):
            item = self.routes_table.item(row, column)
            if item:
                item.setBackground(QtGui.QBrush(QtGui.QColor(color)))

    """Auxiliary method to format a message for blocked routes based on the given alternative. This method checks the properties of the alternative to determine the reason why it cannot be paid for, such as being blocked due to returning to the initial origin or being unaffordable, and returns an appropriate message to explain the situation to the user."""
    def _refresh_action_controls(self):
        self.actividades_actuales = []
        self.trabajos_actuales = []
        self.activity_table.setRowCount(0)
        self.job_table.setRowCount(0)

        if not self.gestor:
            self._refresh_action_buttons()
            return

        opciones = self.gestor.obtener_actividades_y_trabajos_actuales()
        self.actividades_actuales = list(opciones.get("actividades", []))
        self.trabajos_actuales = list(opciones.get("trabajos", [])) if self.gestor.puede_trabajar() else []

        self.activity_table.clearSpans()
        self.activity_table.setRowCount(len(self.actividades_actuales))
        for row, actividad in enumerate(self.actividades_actuales):
            duracion_min = float(getattr(actividad, "duracion_horas", 0) or 0) * 60
            costo = float(getattr(actividad, "costo_usd", 0) or 0)
            values = [actividad.nombre, f"{duracion_min:.0f} min", f"${costo:.2f}"]
            self._set_table_row(self.activity_table, row, values)

        if self.actividades_actuales:
            self.activity_table.selectRow(0)

        if self.trabajos_actuales:
            self.job_table.clearSpans()
            self.job_table.setRowCount(len(self.trabajos_actuales))
            for row, trabajo in enumerate(self.trabajos_actuales):
                values = [
                    trabajo.nombre,
                    f"${trabajo.tarifa_hora:.2f}/h",
                    f"{trabajo.max_horas:.2f} h",
                ]
                self._set_table_row(self.job_table, row, values)
            self.job_table.selectRow(0)
        elif opciones.get("trabajos"):
            self._set_empty_table_message(
                self.job_table,
                3,
                "Trabajos disponibles solo con presupuesto bajo.",
            )
        else:
            self._set_empty_table_message(self.job_table, 3, "No hay trabajos registrados.")

        if not self.actividades_actuales:
            self._set_empty_table_message(self.activity_table, 3, "No hay actividades registradas.")

        self._refresh_job_hours_limit()
        self._refresh_action_buttons()


    """Auxiliary method to set the values of a table row based on the given list of values. This method iterates through the values and creates a QTableWidgetItem for each one, setting the text alignment to center and adding it to the specified row and column in the table. After populating the row, it resizes the rows to fit the contents."""
    def _set_table_row(self, table, row, values):
        for column, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, column, item)
        table.resizeRowsToContents()


    """Auxiliary method to set a message in a table when there are no records to display. This method clears any existing spans in the table, sets the row count to 1, and creates a span across all columns to display the provided message. It also centers the text within the cell for better presentation."""
    def _set_empty_table_message(self, table, columns, message):
        table.clearSpans()
        table.setRowCount(1)
        table.setSpan(0, 0, 1, columns)
        item = QTableWidgetItem(message)
        item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        table.setItem(0, 0, item)

    """Auxiliary method to refresh the enabled state of action buttons based on the current selection and simulation state. This method checks the selected activity and job, as well as the current state of the gestor, to determine whether the "Realizar actividad" and "Aceptar trabajo" buttons should be enabled or disabled. It ensures that the user can only perform valid actions based on the current context of the simulation."""
    def _refresh_action_buttons(self):
        has_gestor = self.gestor is not None
        en_aeropuerto = has_gestor and self.gestor.estado_movimiento == "en_aeropuerto"
        activity_row = self._selected_activity_row()
        job_row = self._selected_job_row()
        activity_selected = en_aeropuerto and 0 <= activity_row < len(self.actividades_actuales)
        job_selected = en_aeropuerto and 0 <= job_row < len(self.trabajos_actuales)
        activity_available = activity_selected and not self._actividad_realizada(self.actividades_actuales[activity_row])
        job_available = job_selected and not self._trabajo_realizado(self.trabajos_actuales[job_row])
        self.do_activity_button.setEnabled(activity_available)
        self.accept_job_button.setEnabled(job_available)
        self.work_hours_spin.setEnabled(job_available)

    """Auxiliary method to normalize text values from activity and job records for comparison purposes. This method takes a value, converts it to a string, and applies stripping and lowercasing to ensure consistent formatting when comparing against the records of performed activities and jobs. This helps in accurately determining whether a given activity or job has already been performed by the traveler."""
    def _normalizar_texto_registro(self, valor):
        return str(valor or "").strip().lower()


    """Auxiliary method to normalize numeric values from activity and job records for comparison purposes. This method takes a value and converts it to a float, treating None or non-numeric values as 0. This ensures consistent formatting when comparing against the records of performed activities and jobs, allowing for accurate determination of whether a given activity or job has already been performed by the traveler."""
    def _normalizar_numero_registro(self, valor):
        return float(valor or 0)

    """Auxiliary method to check if a given activity has already been performed by the traveler. This method retrieves the current airport from the gestor's state and compares the normalized name, cost, and duration of the activity against the records of performed activities in the gestor's traveler data. It returns True if a matching record is found, indicating that the activity has already been performed, and False otherwise."""
    def _actividad_realizada(self, actividad):
        if not self.gestor or not actividad:
            return False
        aeropuerto_actual = self._normalizar_texto_registro(self.gestor.obtener_estado().get("aeropuerto_actual"))
        nombre = self._normalizar_texto_registro(getattr(actividad, "nombre", ""))
        costo = self._normalizar_numero_registro(getattr(actividad, "costo_usd", 0))
        tiempo_horas = self._normalizar_numero_registro(getattr(actividad, "duracion_horas", 0))
        return any(
            self._normalizar_texto_registro(registro.get("nombre")) == nombre
            and self._normalizar_texto_registro(registro.get("aeropuerto")) == aeropuerto_actual
            and self._normalizar_numero_registro(registro.get("costo")) == costo
            and self._normalizar_numero_registro(registro.get("tiempo_horas")) == tiempo_horas
            for registro in self.gestor.viajero.actividades_realizadas
        )

    """Auxiliary method to check if a given job has already been performed by the traveler. This method retrieves the current airport from the gestor's state and compares the normalized description, hourly rate, and maximum hours of the job against the records of performed jobs in the gestor's traveler data. It returns True if a matching record is found, indicating that the job has already been performed, and False otherwise."""
    def _trabajo_realizado(self, trabajo):
        if not self.gestor or not trabajo:
            return False
        aeropuerto_actual = self._normalizar_texto_registro(self.gestor.obtener_estado().get("aeropuerto_actual"))
        descripcion = self._normalizar_texto_registro(getattr(trabajo, "nombre", ""))
        tarifa_hora = self._normalizar_numero_registro(getattr(trabajo, "tarifa_hora", 0))
        max_horas = self._normalizar_numero_registro(getattr(trabajo, "max_horas", 0))
        return any(
            self._normalizar_texto_registro(registro.get("descripcion")) == descripcion
            and self._normalizar_texto_registro(registro.get("aeropuerto")) == aeropuerto_actual
            and self._normalizar_numero_registro(registro.get("tarifa_hora")) == tarifa_hora
            and self._normalizar_numero_registro(registro.get("max_horas")) == max_horas
            for registro in self.gestor.viajero.trabajos_realizados
        )
    
    """Auxiliary method to refresh the enabled state of the job hours spin box based on the currently selected job and its maximum hours. This method retrieves the selected job, checks if it is valid, and updates the maximum value of the spin box to match the maximum hours allowed for that job. It also ensures that the current value of the spin box does not exceed the new maximum, and then calls the method to refresh the action buttons to reflect any changes in availability."""
    def _refresh_job_hours_limit(self):
        row = self._selected_job_row()
        if 0 <= row < len(self.trabajos_actuales):
            max_horas = float(getattr(self.trabajos_actuales[row], "max_horas", 0) or 0)
            self.work_hours_spin.setMaximum(max_horas)
            self.work_hours_spin.setValue(min(max_horas, max(0.25, self.work_hours_spin.value())))
        self._refresh_action_buttons()
    """Auxiliary method to retrieve the index of the currently selected row in the activity table. This method checks the selection model of the activity table and returns the row index of the first selected item, or -1 if no row is selected. This index is used to determine which activity the user has selected for potential action."""
    def _selected_activity_row(self):
        selected = self.activity_table.selectionModel().selectedRows()
        if not selected:
            return -1
        return selected[0].row()

    """Auxiliary method to retrieve the index of the currently selected row in the job table. This method checks the selection model of the job table and returns the row index of the first selected item, or -1 if no row is selected. This index is used to determine which job the user has selected for potential action."""
    def _selected_job_row(self):
        selected = self.job_table.selectionModel().selectedRows()
        if not selected:
            return -1
        return selected[0].row()
    """Auxiliary method to handle the action of performing an activity. This method checks if the gestor is in a valid state and if an activity is selected, then it verifies if the selected activity has already been performed. If not, it attempts to perform the activity using the gestor and handles any exceptions that may arise, providing user-friendly messages and refreshing the view accordingly."""
    def on_do_activity(self):
        if not self.gestor:
            return
        row = self._selected_activity_row()
        if row < 0 or row >= len(self.actividades_actuales):
            return
        if self._actividad_realizada(self.actividades_actuales[row]):
            self._refresh_action_buttons()
            return
        try:
            self.gestor.realizar_actividad(self.actividades_actuales[row])
        except ValueError as exc:
            self._show_warning(
                "No se puede realizar actividad",
                self._format_resource_exception_message(str(exc)),
            )
            return
        self._refresh_after_action()
    """Auxiliary method to handle the action of accepting a job. This method checks if the gestor is in a valid state and if a job is selected, then it verifies if the selected job has already been performed. If not, it attempts to perform the job using the gestor with the specified number of hours and handles any exceptions that may arise, providing user-friendly messages and refreshing the view accordingly."""
    def on_accept_job(self):
        if not self.gestor:
            return
        row = self._selected_job_row()
        if row < 0 or row >= len(self.trabajos_actuales):
            return
        if self._trabajo_realizado(self.trabajos_actuales[row]):
            self._refresh_action_buttons()
            return
        try:
            self.gestor.realizar_trabajo(self.trabajos_actuales[row], self.work_hours_spin.value())
        except ValueError as exc:
            self._show_warning(
                "No se puede aceptar trabajo",
                self._format_resource_exception_message(str(exc)),
            )
            return
        self._refresh_after_action()
    """Auxiliary method to refresh the view after performing an action such as doing an activity or accepting a job. This method calls individual refresh methods for the status, alternatives, action controls, and decision log to ensure that all displayed information is up-to-date with the current state of the gestor and the travel simulation after the action has been performed."""
    def _refresh_after_action(self):
        self._refresh_status()
        self._refresh_alternatives()
        self._refresh_action_controls()
        self._refresh_decision_log()
    """Auxiliary method to refresh the decision log display based on the current state of the gestor. This method retrieves the list of decisions made during the simulation and formats them into a readable format, displaying them in the decision log text area. It handles various types of decisions, such as flights, activities, jobs, and cancellations, providing a comprehensive log of the traveler's actions and events throughout the simulation."""
    def _refresh_decision_log(self):
        if not self.gestor:
            return

        decisiones = self.gestor.obtener_estado()["decisiones"]
        if not decisiones:
            self.decision_log.setPlainText("Aun no hay decisiones registradas.")
            return

        lines = []
        for index, decision in enumerate(decisiones, start=1):
            tipo = decision.get("tipo", "decision")
            if tipo == "vuelo":
                lines.append(
                    f"{index}. Vuelo {decision['origen']} -> {decision['destino']} "
                    f"({decision['transporte']}) | ${decision['costo_vuelo']:.2f} | "
                    f"{decision['tiempo_vuelo_horas']:.2f} h"
                )
            elif tipo == "vuelo_iniciado":
                lines.append(f"{index}. {decision.get('descripcion', 'Vuelo iniciado')}")
            elif tipo == "vuelo_cancelado":
                lines.append(
                    f"{index}. Vuelo cancelado {decision['origen']} -> {decision['destino']} | "
                    f"{decision.get('motivo', 'Vuelo cancelado')}"
                )
            elif tipo in ("alimentacion", "hospedaje"):
                lines.append(
                    f"{index}. {tipo.capitalize()} en {decision['aeropuerto']} | "
                    f"${decision['costo']:.2f} | t={decision['tiempo']:.2f} h"
                )
            elif tipo == "actividad":
                lines.append(
                    f"{index}. Actividad {decision['actividad']} en {decision['aeropuerto']} | "
                    f"${decision['costo']:.2f} | {decision['duracion_horas']:.2f} h"
                )
            elif tipo == "trabajo":
                lines.append(
                    f"{index}. Trabajo {decision['trabajo']} en {decision['aeropuerto']} | "
                    f"{decision['horas']:.2f} h | +${decision['ingreso']:.2f}"
                )
            elif tipo == "tiempo_libre":
                lines.append(
                    f"{index}. Tiempo libre en {decision['aeropuerto']} | "
                    f"{decision['duracion_horas']:.2f} h"
                )
            elif tipo == "actividad_omitida":
                lines.append(f"{index}. Actividad omitida: {decision['actividad']} en {decision['aeropuerto']}")
            elif tipo == "trabajo_rechazado":
                lines.append(f"{index}. Trabajo rechazado: {decision['trabajo']} en {decision['aeropuerto']}")
            else:
                lines.append(f"{index}. {decision.get('descripcion', tipo)}")

        self.decision_log.setPlainText("\n".join(lines))

    """Auxiliary method to refresh the routes panel with the current state of the graph. This method retrieves the vertices and edges from the graph, populates the routes table with the origin, destination, and status of each route, and applies styling to indicate which routes are blocked. It ensures that the routes panel accurately reflects the current state of the graph and any changes that may have occurred due to user actions or events in the simulation."""
    def _refresh_routes_panel(self):
        self.routes_table.clearSpans()
        self.routes_table.setRowCount(0)
        if not self.grafo:
            return

        aristas = []
        for vertice in self.grafo.obtener_vertices():
            for arista in vertice.adyacencias:
                aristas.append((vertice.identificador, arista))

        self.routes_table.setRowCount(len(aristas))
        for row, (origen, arista) in enumerate(aristas):
            destino = arista.vertice_destino.identificador
            estado = "Bloqueada" if arista.esta_bloqueada() else "Activa"
            values = [origen, destino, estado]
            self._set_table_row(self.routes_table, row, values)

            if arista.esta_bloqueada():
                self._paint_routes_table_row(row, "#dc2626")
    """Auxiliary method to handle the action of blocking a route. This method checks if the gestor is in a valid state and if a route is selected, then it attempts to block the selected route using the gestor and handles any exceptions that may arise, providing user-friendly messages and refreshing the view accordingly. If the blocked route was part of an ongoing flight, it also handles the interruption of the flight and updates the relevant UI components."""
    def on_block_route(self):
        if not self.gestor:
            QMessageBox.warning(self, "Validacion", "Inicia un viaje antes de bloquear rutas.")
            return

        selected = self.routes_table.selectionModel().selectedRows()
        if not selected:
            QMessageBox.warning(self, "Validacion", "Selecciona una ruta para bloquear.")
            return

        row = selected[0].row()
        origen_item = self.routes_table.item(row, 0)
        destino_item = self.routes_table.item(row, 1)
        if not origen_item or not destino_item:
            return

        origen = origen_item.text()
        destino = destino_item.text()
        habia_vuelo = self.gestor.estado_movimiento == "en_vuelo"

        try:
            self.gestor.bloquear_ruta(origen, destino)
        except ValueError as exc:
            self._show_warning("Error al bloquear ruta", self._format_resource_exception_message(str(exc)))
            return

        self._refresh_routes_panel()
        self._refresh_alternatives()
        self.graph_view.refresh_graph_state()
        if habia_vuelo and self.gestor.estado_movimiento == "en_aeropuerto":
            self.flight_timer.stop()
            self.graph_view.clear_flight_progress()
            self.graph_view.highlight_route(self.gestor.ruta_actual)
            QMessageBox.warning(self, "Vuelo cancelado", "La ruta bloqueada interrumpio el vuelo en curso.")
        self._refresh_dynamic_view()
