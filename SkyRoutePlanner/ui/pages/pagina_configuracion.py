from PyQt6 import QtWidgets, QtCore


class PaginaConfiguracion(QtWidgets.QWidget):
    """Configuration page placeholder for application settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QtWidgets.QLabel("Configuración")
        title.setObjectName("pageTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        message = QtWidgets.QLabel(
            "This page will allow configuration of the planner when settings are ready."
        )
        message.setWordWrap(True)
        message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch()
