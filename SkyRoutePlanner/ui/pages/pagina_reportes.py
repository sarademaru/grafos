from PyQt6 import QtWidgets, QtCore


class PaginaReportes(QtWidgets.QWidget):
    """Reports page placeholder for system analytics and results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QtWidgets.QLabel("Reportes")
        title.setObjectName("pageTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        message = QtWidgets.QLabel(
            "This page will display reports and analytics after the feature is implemented."
        )
        message.setWordWrap(True)
        message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()
        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch()
