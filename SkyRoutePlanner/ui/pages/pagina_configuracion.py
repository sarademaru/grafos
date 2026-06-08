from copy import deepcopy
from pathlib import Path

from PyQt6 import QtWidgets, QtCore
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from utils.json_loader import cargar_json


class PaginaConfiguracion(QtWidgets.QWidget):
    """Configuration page for loading JSON and displaying graph metadata."""

    graph_loaded = QtCore.pyqtSignal(object)
    system_reset = QtCore.pyqtSignal()
    configuration_updated = QtCore.pyqtSignal()

    AIRCRAFT_ALIASES = ["Comercial", "Regional", "Helice"]
    AIRCRAFT_FALLBACK_KEYS = {
        "Comercial": "Avion Comercial",
        "Regional": "Avion Regional",
        "Helice": "Helice",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grafo = None
        self._original_aircraft_config = {}
        self.aircraft_inputs = {}
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

        # --- Aircraft configuration group (table-based, stable) ---
        aircraft_group = QtWidgets.QGroupBox("Configuración de Aeronaves")
        aircraft_group.setObjectName("infoFrame")
        aircraft_group.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)

        group_layout = QtWidgets.QVBoxLayout(aircraft_group)
        group_layout.setContentsMargins(16, 16, 16, 16)
        group_layout.setSpacing(10)

        # Table with 3 visible rows: Aeronave, costoKm, tiempoKm
        table = QtWidgets.QTableWidget()
        table.setColumnCount(3)
        table.setRowCount(len(self.AIRCRAFT_ALIASES))
        table.setHorizontalHeaderLabels(["Aeronave", "costoKm", "tiempoKm"])
        table.verticalHeader().setVisible(False)
        table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        table.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustIgnored)

        # Use stretch so columns fill available width and no horizontal scrolling
        header = table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.ResizeMode.Stretch)

        # Populate rows and keep spinboxes for numeric input
        for row, alias in enumerate(self.AIRCRAFT_ALIASES):
            item = QtWidgets.QTableWidgetItem(alias)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 0, item)

            costo_spin = QtWidgets.QDoubleSpinBox()
            costo_spin.setMaximum(999.9999)
            costo_spin.setDecimals(4)
            costo_spin.setSingleStep(0.01)
            costo_spin.setSuffix(" USD/km")
            costo_spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

            tiempo_spin = QtWidgets.QDoubleSpinBox()
            tiempo_spin.setMaximum(999.9999)
            tiempo_spin.setDecimals(4)
            tiempo_spin.setSingleStep(0.01)
            tiempo_spin.setSuffix(" h/km")
            tiempo_spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)

            table.setCellWidget(row, 1, costo_spin)
            table.setCellWidget(row, 2, tiempo_spin)

            # keep references for existing logic
            self.aircraft_inputs[alias] = {
                "costoKm": costo_spin,
                "tiempoKm": tiempo_spin,
            }

        # Fix the table height so all 3 rows are always visible and the rest of the
        # section stays below it even when the window is maximized.
        table.resizeRowsToContents()
        row_height_total = sum(
            table.verticalHeader().sectionSize(r) or table.verticalHeader().defaultSectionSize() or 30
            for r in range(table.rowCount())
        )
        header_height = table.horizontalHeader().sizeHint().height() or 30
        frame_height = table.frameWidth() * 2
        total_height = header_height + row_height_total + frame_height + 14
        table.setFixedHeight(total_height)

        # Description and buttons
        desc = QtWidgets.QLabel("Modifica los valores de costo y tiempo por km para las aeronaves.")
        desc.setWordWrap(True)
        desc.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)

        button_container = QtWidgets.QWidget()
        button_container.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        btn_row = QtWidgets.QHBoxLayout(button_container)
        btn_row.setContentsMargins(0, 0, 0, 0)
        btn_row.setSpacing(8)
        btn_row.addStretch()
        self.restore_aircraft_btn = QtWidgets.QPushButton("Restaurar")
        self.restore_aircraft_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.restore_aircraft_btn.clicked.connect(self.on_restore_aircraft_configuration)
        self.apply_aircraft_btn = QtWidgets.QPushButton("Aplicar")
        self.apply_aircraft_btn.setObjectName("primaryButton")
        self.apply_aircraft_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.apply_aircraft_btn.clicked.connect(self.on_apply_aircraft_configuration)
        btn_row.addWidget(self.restore_aircraft_btn)
        btn_row.addWidget(self.apply_aircraft_btn)

        group_layout.addWidget(table, 0)
        group_layout.addWidget(desc, 0)
        group_layout.addSpacing(8)
        group_layout.addWidget(button_container, 0)
        group_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        group_layout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetMinimumSize)

        layout.addWidget(title)
        layout.addLayout(button_layout)
        layout.addWidget(info_frame)
        layout.addWidget(aircraft_group, 0)
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

    def _find_aircraft_key(self, alias):
        if not self.grafo:
            return self.AIRCRAFT_FALLBACK_KEYS.get(alias, alias)

        aeronaves = self.grafo.configuracion.get("aeronaves", {})
        for key in aeronaves:
            normalized_key = key.strip().lower()
            alias_lower = alias.strip().lower()
            if normalized_key == alias_lower or alias_lower in normalized_key or normalized_key in alias_lower:
                return key

        return self.AIRCRAFT_FALLBACK_KEYS.get(alias, alias)

    def _refresh_aircraft_inputs(self):
        if not self.grafo:
            return

        aeronaves = self.grafo.obtener_configuracion().get("aeronaves", {})
        for alias in self.AIRCRAFT_ALIASES:
            key = self._find_aircraft_key(alias)
            aeronave = aeronaves.get(key, {})
            costo = float(aeronave.get("costoKm", 0) or 0)
            tiempo = float(aeronave.get("tiempoKm", 0) or 0)
            campos = self.aircraft_inputs.get(alias)
            if campos:
                campos["costoKm"].setValue(costo)
                campos["tiempoKm"].setValue(tiempo)

    def _read_aircraft_input_values(self):
        values = {}
        for alias in self.AIRCRAFT_ALIASES:
            key = self._find_aircraft_key(alias)
            campos = self.aircraft_inputs.get(alias, {})
            costo = float(campos.get("costoKm").value() if campos.get("costoKm") else 0)
            tiempo = float(campos.get("tiempoKm").value() if campos.get("tiempoKm") else 0)
            values[key] = {
                "costoKm": costo,
                "tiempoKm": tiempo,
            }
        return values

    def _parse_float(self, raw_value):
        if raw_value is None:
            return 0.0
        try:
            return float(str(raw_value).replace(",", "."))
        except (ValueError, TypeError):
            return 0.0

    def on_apply_aircraft_configuration(self):
        if not self.grafo:
            QMessageBox.warning(self, "Validacion", "Carga un archivo JSON antes de aplicar los cambios.")
            return

        nuevos_valores = self._read_aircraft_input_values()
        aeronaves = self.grafo.configuracion.setdefault("aeronaves", {})
        for key, datos in nuevos_valores.items():
            aeronaves[key] = datos

        self._set_status("Valores de aeronaves aplicados en memoria", success=True)
        self.configuration_updated.emit()

    def on_restore_aircraft_configuration(self):
        if not self.grafo:
            QMessageBox.warning(self, "Validacion", "Carga un archivo JSON antes de restaurar la configuración.")
            return

        self.grafo.configuracion["aeronaves"] = deepcopy(self._original_aircraft_config)
        self._refresh_aircraft_inputs()
        self._set_status("Valores de aeronaves restaurados desde el JSON", success=True)
        self.configuration_updated.emit()

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
        self._original_aircraft_config = deepcopy(grafo.obtener_configuracion().get("aeronaves", {}))
        self._refresh_aircraft_inputs()
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
        self._original_aircraft_config = {}
        self.file_row.value_widget.setText("-")
        self.airports_row.value_widget.setText("0")
        self.routes_row.value_widget.setText("0")
        for alias in self.AIRCRAFT_ALIASES:
            campos = self.aircraft_inputs.get(alias, {})
            if campos.get("costoKm"):
                campos["costoKm"].setValue(0)
            if campos.get("tiempoKm"):
                campos["tiempoKm"].setValue(0)
        self._set_status("Sistema reiniciado", success=False)
        self.system_reset.emit()
