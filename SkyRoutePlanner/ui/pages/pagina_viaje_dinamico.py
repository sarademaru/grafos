from PyQt6 import QtCore, QtWidgets


class PaginaViajeDinamico(QtWidgets.QWidget):
    """Visual shell for the future dynamic travel simulation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Viaje Dinamico")
        title.setObjectName("pageTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        placeholder = QtWidgets.QFrame()
        placeholder.setObjectName("placeholderPanel")
        placeholder_layout = QtWidgets.QVBoxLayout(placeholder)
        placeholder_layout.setContentsMargins(24, 24, 24, 24)
        placeholder_layout.setSpacing(18)

        message = QtWidgets.QLabel("Proximamente: Simulacion dinamica del viaje")
        message.setObjectName("placeholderTitle")
        message.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        message.setWordWrap(True)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(12)
        items = [
            "Simulacion del recorrido",
            "Animacion del avion",
            "Presupuesto restante",
            "Tiempo restante",
            "Actividades",
            "Trabajos",
            "Interrupciones de rutas",
        ]
        for index, text in enumerate(items):
            card = QtWidgets.QFrame()
            card.setObjectName("placeholderCard")
            card_layout = QtWidgets.QVBoxLayout(card)
            card_layout.setContentsMargins(14, 14, 14, 14)
            label = QtWidgets.QLabel(text)
            label.setObjectName("reportLine")
            label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            label.setWordWrap(True)
            card_layout.addWidget(label)
            grid.addWidget(card, index // 3, index % 3)

        placeholder_layout.addStretch()
        placeholder_layout.addWidget(message)
        placeholder_layout.addLayout(grid)
        placeholder_layout.addStretch()

        layout.addWidget(placeholder, stretch=1)
