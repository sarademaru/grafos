from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QLabel, QComboBox, QPushButton, QFrame, QHBoxLayout, QVBoxLayout, QFormLayout

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
        self.algorithm_combo = QComboBox()
        self.algorithm_combo.addItems(["Dijkstra", "BFS", "DFS", "Bellman-Ford"])

        form_layout = QFormLayout()
        form_layout.addRow("Origen", self.origin_combo)
        form_layout.addRow("Destino", self.dest_combo)
        form_layout.addRow("Algoritmo", self.algorithm_combo)

        self.calculate_button = QPushButton("Calcular Ruta")
        self.calculate_button.setObjectName("primaryButton")
        self.calculate_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.calculate_button.clicked.connect(self.on_calculate_route)

        self.selected_info = QtWidgets.QLabel("Seleccione un aeropuerto para ver más información.")
        self.selected_info.setWordWrap(True)
        self.selected_info.setObjectName("infoLabel")

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
        algoritmo = self.algorithm_combo.currentText()
        self.selected_info.setText(
            f"Ruta solicitada: {origen} → {destino} con {algoritmo}.\n" \
            "Las funciones de cálculo se implementarán próximamente."
        )
