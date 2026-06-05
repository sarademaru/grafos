from PyQt6 import QtCore, QtWidgets

from algorithms.itinerary_planner import CRITERION_COST, CRITERION_DISTANCE, CRITERION_TIME


class PaginaReportes(QtWidgets.QWidget):
    """Detailed route reports."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.last_payload = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Reportes")
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
        self._show_placeholder()

    def clear_report(self):
        self.last_payload = None
        self._show_placeholder()

    def set_report(self, payload):
        self.last_payload = payload
        self._clear_content()

        if not payload:
            self._show_placeholder()
            return

        context = payload.get("context", {})
        self.content_layout.addWidget(
            self._build_card(
                "Resumen del calculo",
                [
                    f"Origen: {context.get('origin', '-')}",
                    f"Destino: {context.get('destination', '-')}",
                    f"Presupuesto: ${context.get('budget', 0):.2f}",
                    f"Tiempo disponible: {context.get('available_time', 0)} h",
                    f"Criterios: {', '.join(context.get('criteria_labels', []))}",
                    f"Aeronaves: {', '.join(context.get('selected_transports', []))}",
                    f"Secundarios: {'Incluir' if context.get('include_secondary') else 'Excluir'}",
                ],
            )
        )

        result = payload.get("result", {})
        basic = result.get("basic", {})
        self.content_layout.addWidget(
            self._build_route_card(
                "Alternativa A: mayor cantidad de destinos por presupuesto",
                basic.get("max_destinations_by_budget"),
            )
        )
        self.content_layout.addWidget(
            self._build_route_card(
                "Alternativa B: mayor cantidad de destinos en menor tiempo",
                basic.get("max_destinations_by_time"),
            )
        )

        criterion_names = {
            CRITERION_DISTANCE: "Distancia",
            CRITERION_TIME: "Tiempo",
            CRITERION_COST: "Costo USD",
        }
        for criterion, route in result.get("optimized", {}).items():
            self.content_layout.addWidget(
                self._build_route_card(f"Criterio: {criterion_names.get(criterion, criterion)}", route)
            )

        self.content_layout.addStretch()

    def _show_placeholder(self):
        self._clear_content()
        placeholder = QtWidgets.QLabel("No hay reportes disponibles. Calcula una ruta en el Planificador.")
        placeholder.setObjectName("infoLabel")
        placeholder.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        placeholder.setWordWrap(True)
        self.content_layout.addStretch()
        self.content_layout.addWidget(placeholder)
        self.content_layout.addStretch()

    def _clear_content(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _build_card(self, title, lines):
        frame = QtWidgets.QFrame()
        frame.setObjectName("reportCard")
        layout = QtWidgets.QVBoxLayout(frame)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        title_label = QtWidgets.QLabel(title)
        title_label.setObjectName("reportCardTitle")
        layout.addWidget(title_label)

        for line in lines:
            label = QtWidgets.QLabel(line)
            label.setObjectName("reportLine")
            label.setWordWrap(True)
            layout.addWidget(label)

        return frame

    def _build_route_card(self, title, route):
        if not route or not route.get("legs"):
            return self._build_card(
                title,
                ["No se encontro una ruta valida con las restricciones actuales."],
            )

        stops = route["path"][1:-1]
        lines = [
            f"Secuencia completa: {' -> '.join(route['path'])}",
            f"Escalas: {', '.join(stops) if stops else 'Sin escalas'}",
            f"Distancia total: {route['total_distance']:.2f} km",
            f"Tiempo total: {route['total_time']:.2f} h",
            f"Costo total: ${route['total_cost']:.2f}",
            f"Transportes utilizados: {', '.join(route['transports_used'])}",
            "Tramos:",
        ]
        lines.extend(route["formatted_legs"])
        return self._build_card(title, lines)
