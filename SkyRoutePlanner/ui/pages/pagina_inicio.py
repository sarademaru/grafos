from PyQt6 import QtWidgets, QtCore


class PaginaInicio(QtWidgets.QWidget):
    """Landing page for the dashboard overview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QtWidgets.QLabel("Inicio")
        title.setObjectName("pageTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        message = QtWidgets.QLabel(
            "This page is a placeholder for the dashboard overview. Functionality will be implemented later."
        )
        message.setWordWrap(True)
        message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch()
