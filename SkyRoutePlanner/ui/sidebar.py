from PyQt6 import QtWidgets, QtCore


class Sidebar(QtWidgets.QFrame):
    """Left navigation sidebar for the application dashboard."""

    menu_selected = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setMinimumWidth(220)
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("SkyRoute")
        title.setObjectName("sidebarTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(title)

        self.buttons = []
        menu_items = [
            "Inicio",
            "Planificador de Rutas",
            "Viaje Dinámico",
            "Reportes",
            "Configuración",
        ]

        for index, item in enumerate(menu_items):
            button = QtWidgets.QPushButton(item)
            button.setObjectName("sidebarButton")
            button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            button.setCheckable(True)
            button.clicked.connect(lambda checked, idx=index: self.on_menu_clicked(idx))
            layout.addWidget(button)
            self.buttons.append(button)

        layout.addStretch()

    def set_default_selection(self):
        if self.buttons:
            self.select_index(0)

    def select_index(self, index):
        if index < 0 or index >= len(self.buttons):
            return

        for idx, button in enumerate(self.buttons):
            button.setChecked(idx == index)

        self.menu_selected.emit(index)

    def on_menu_clicked(self, index):
        self.select_index(index)
