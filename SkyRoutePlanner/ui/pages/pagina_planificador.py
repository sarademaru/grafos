from PyQt6 import QtWidgets, QtCore


class PaginaPlanificador(QtWidgets.QWidget):
    """Route planner page for future route configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QtWidgets.QLabel("Planificador de Rutas")
        title.setObjectName("pageTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        message = QtWidgets.QLabel(
            "This page will host the route planning interface. The graph and algorithms are not implemented yet."
        )
        message.setWordWrap(True)
        message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch()
