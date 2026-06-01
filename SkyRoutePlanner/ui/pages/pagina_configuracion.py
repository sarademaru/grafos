from pathlib import Path

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from utils.json_loader import cargar_json


class PaginaConfiguracion(QtWidgets.QWidget):
    """Configuration page for loading JSON and displaying graph metadata."""

    graph_loaded = QtCore.pyqtSignal(object)
    system_reset = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grafo = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QtWidgets.QLabel("Configuración")
        title.setObjectName("pageTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.load_btn = QtWidgets.QPushButton("Cargar JSON")
        self.load_btn.setObjectName("primaryButton")
        self.load_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.load_btn.clicked.connect(self.cargar_archivo)

        self.reset_btn = QtWidgets.QPushButton("Reiniciar Sistema")
        self.reset_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.reset_btn.clicked.connect(self.on_reset)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.load_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addStretch()

        info_frame = QtWidgets.QFrame()
        info_frame.setObjectName("infoFrame")
        info_layout = QtWidgets.QVBoxLayout(info_frame)
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(12)

        self.file_row = self._create_info_row("Archivo:", "-")
        self.airports_row = self._create_info_row("Aeropuertos:", "0")
        self.routes_row = self._create_info_row("Rutas:", "0")
        self.status_row = self._create_info_row("Estado:", "Esperando datos")
        self.status_row.setObjectName("statusBanner")

        info_layout.addWidget(self.file_row)
        info_layout.addWidget(self.airports_row)
        info_layout.addWidget(self.routes_row)
        info_layout.addWidget(self.status_row)

        layout.addWidget(title)
        layout.addLayout(button_layout)
        layout.addWidget(info_frame)
        layout.addStretch()

    def _create_info_row(self, label_text, initial_value):
        container = QtWidgets.QWidget()
        row_layout = QtWidgets.QHBoxLayout(container)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(12)

        label = QtWidgets.QLabel(label_text)
        label.setObjectName("infoLabel")
        value = QtWidgets.QLabel(initial_value)
        value.setObjectName("infoValue")
        value.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)

        row_layout.addWidget(label)
        row_layout.addStretch()
        row_layout.addWidget(value)

        container.value_widget = value
        return container

    def cargar_archivo(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar JSON",
            "",
            "JSON (*.json)"
        )

        if not archivo:
            return

        try:
            grafo = cargar_json(archivo)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar el JSON:\n{e}")
            self._set_status("Error al cargar JSON", success=False)
            return

        self.grafo = grafo
        self._update_info(archivo, grafo)
        self.graph_loaded.emit(grafo)

    def _update_info(self, archivo, grafo):
        self.file_row.value_widget.setText(Path(archivo).name)
        self.airports_row.value_widget.setText(str(grafo.cantidad_vertices()))
        route_count = sum(len(vertice.adyacencias) for vertice in grafo.obtener_vertices())
        self.routes_row.value_widget.setText(str(route_count))
        self._set_status("✓ Datos cargados correctamente", success=True)

    def _set_status(self, text, success=False):
        self.status_row.value_widget.setText(text)
        color = "#86efac" if success else "#fda4af"
        self.status_row.value_widget.setStyleSheet(f"color: {color};")

    def on_reset(self):
        self.grafo = None
        self.file_row.value_widget.setText("-")
        self.airports_row.value_widget.setText("0")
        self.routes_row.value_widget.setText("0")
        self._set_status("Sistema reiniciado", success=False)
        self.system_reset.emit()