from PyQt6 import QtCore, QtWidgets
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
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
        self.graph_view = GraphView()
        self._setup_ui()

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

        self.alternatives_combo = QComboBox()
        self.advance_button = QPushButton("Avanzar al destino seleccionado")
        self.advance_button.setObjectName("primaryButton")
        self.advance_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.advance_button.clicked.connect(self.on_advance_selected)
        self.advance_button.setEnabled(False)

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

        info_title = QLabel("Actividades y trabajos disponibles")
        info_title.setObjectName("sectionTitle")
        self.local_info = QTextEdit()
        self.local_info.setObjectName("routeResults")
        self.local_info.setReadOnly(True)
        self.local_info.setMinimumHeight(120)
        self.local_info.setPlainText("Inicia el viaje para ver opciones del aeropuerto actual.")

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
        control_layout.addWidget(self.alternatives_combo)
        control_layout.addWidget(self.advance_button)
        control_layout.addWidget(info_title)
        control_layout.addWidget(self.local_info)
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

    def _build_status_value(self, text):
        label = QLabel(text)
        label.setObjectName("infoValue")
        label.setWordWrap(True)
        return label

    def _add_status_row(self, row, title, value_widget):
        title_label = QLabel(title)
        title_label.setObjectName("infoLabel")
        self.status_grid.addWidget(title_label, row, 0)
        self.status_grid.addWidget(value_widget, row, 1)

    def set_graph(self, grafo):
        self.grafo = grafo
        self.graph_view.set_graph(grafo)
        self._refresh_airports()
        self._reset_simulation_view()

    def clear_graph(self):
        self.grafo = None
        self.gestor = None
        self.graph_view.clear_graph()
        self.origin_combo.clear()
        self.alternatives_combo.clear()
        self._reset_simulation_view()

    def _refresh_airports(self):
        self.origin_combo.clear()
        if self.grafo:
            self.origin_combo.addItems([vertice.identificador for vertice in self.grafo.obtener_vertices()])

    def _reset_simulation_view(self):
        self.alternativas = []
        self.alternatives_combo.clear()
        self.advance_button.setEnabled(False)
        self.suggested_label.setText("Sugerencia: -")
        for label in self.status_labels.values():
            label.setText("-")
        self.local_info.setPlainText("Inicia el viaje para ver opciones del aeropuerto actual.")
        self.decision_log.setPlainText("Aun no hay decisiones registradas.")

    def on_start_trip(self):
        if not self.grafo:
            QMessageBox.warning(self, "Validacion", "Carga un grafo antes de iniciar el viaje dinamico.")
            return

        origen = self.origin_combo.currentText()
        if not origen:
            QMessageBox.warning(self, "Validacion", "Selecciona un aeropuerto de origen.")
            return

        viajero = Viajero(
            presupuesto_inicial=self.budget_spin.value(),
            tiempo_total_horas=self.time_spin.value(),
        )
        self.gestor = GestorViaje(self.grafo, viajero)
        self.gestor.iniciar_viaje_dinamico(origen)
        self.graph_view.highlight_route([origen])
        self._refresh_dynamic_view()

    def on_advance_selected(self):
        if not self.gestor:
            return

        index = self.alternatives_combo.currentIndex()
        if index < 0 or index >= len(self.alternativas):
            return

        alternativa = self.alternativas[index]
        try:
            self.gestor.avanzar_a_destino(alternativa["destino"], alternativa["transporte"])
        except ValueError as exc:
            QMessageBox.warning(self, "No se puede avanzar", str(exc))
            return

        self.graph_view.highlight_route(self.gestor.ruta_actual)
        self._refresh_dynamic_view()

    def _refresh_dynamic_view(self):
        self._refresh_status()
        self._refresh_alternatives()
        self._refresh_local_info()
        self._refresh_decision_log()

    def _refresh_status(self):
        if not self.gestor:
            return

        estado = self.gestor.obtener_estado()
        viajero = estado["viajero"]
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

    def _refresh_alternatives(self):
        self.alternatives_combo.clear()
        self.alternativas = []
        self.advance_button.setEnabled(False)

        if not self.gestor:
            self.suggested_label.setText("Sugerencia: -")
            return

        self.alternativas = self.gestor.obtener_alternativas_disponibles()
        sugerida = self.gestor.sugerir_siguiente_alternativa()
        if sugerida:
            self.suggested_label.setText(
                "Sugerencia: "
                f"{sugerida['origen']} -> {sugerida['destino']} en {sugerida['transporte']} "
                f"(${sugerida['costo_vuelo']:.2f}, {sugerida['tiempo_vuelo_horas']:.2f} h)"
            )
        else:
            self.suggested_label.setText("Sugerencia: no hay vuelos pagables hacia nuevos destinos.")

        for alternativa in self.alternativas:
            estado_pago = "pagable" if alternativa["puede_pagarse"] else "sin presupuesto"
            self.alternatives_combo.addItem(
                f"{alternativa['origen']} -> {alternativa['destino']} | "
                f"{alternativa['transporte']} | ${alternativa['costo_vuelo']:.2f} | "
                f"{alternativa['tiempo_vuelo_horas']:.2f} h | {estado_pago}"
            )

        self.advance_button.setEnabled(bool(self.alternativas))

    def _refresh_local_info(self):
        if not self.gestor:
            return

        opciones = self.gestor.obtener_actividades_y_trabajos_actuales()
        lines = ["Actividades:"]
        if opciones["actividades"]:
            for actividad in opciones["actividades"]:
                lines.append(
                    f"- {actividad.nombre}: {actividad.duracion_horas:.2f} h, ${actividad.costo_usd:.2f}"
                )
        else:
            lines.append("- No hay actividades registradas.")

        lines.append("")
        lines.append("Trabajos:")
        if opciones["trabajos"]:
            for trabajo in opciones["trabajos"]:
                lines.append(
                    f"- {trabajo.nombre}: ${trabajo.tarifa_hora:.2f}/h, max {trabajo.max_horas:.2f} h"
                )
        else:
            lines.append("- No hay trabajos registrados.")

        self.local_info.setPlainText("\n".join(lines))

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
            elif tipo in ("alimentacion", "hospedaje"):
                lines.append(
                    f"{index}. {tipo.capitalize()} en {decision['aeropuerto']} | "
                    f"${decision['costo']:.2f} | t={decision['tiempo']:.2f} h"
                )
            else:
                lines.append(f"{index}. {decision.get('descripcion', tipo)}")

        self.decision_log.setPlainText("\n".join(lines))
