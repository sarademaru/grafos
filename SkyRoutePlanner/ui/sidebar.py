from PyQt6 import QtCore, QtWidgets


class Sidebar(QtWidgets.QFrame):
    """Left navigation sidebar with collapsible VS Code-like behavior."""

    menu_selected = QtCore.pyqtSignal(int)

    EXPANDED_WIDTH = 260
    COLLAPSED_WIDTH = 70

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self._collapsed = False
        self._sidebar_width = self.EXPANDED_WIDTH
        self.buttons = []
        self.menu_items = [
            ("⌂", "Inicio"),
            ("✈", "Planificador de Rutas"),
            ("↻", "Viaje Dinamico"),
            ("▦", "Reportes"),
            ("⚙", "Configuracion"),
        ]
        self._setup_ui()
        self._set_sidebar_width(self.EXPANDED_WIDTH)

    def _setup_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)

        self.toggle_button = QtWidgets.QPushButton("☰")
        self.toggle_button.setObjectName("sidebarToggle")
        self.toggle_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.toggle_button.setToolTip("Contraer menu")
        self.toggle_button.clicked.connect(self.toggle_collapsed)
        self.layout.addWidget(self.toggle_button)

        for index, (icon, label) in enumerate(self.menu_items):
            button = QtWidgets.QPushButton()
            button.setObjectName("sidebarButton")
            button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            button.setCheckable(True)
            button.setToolTip(label)
            button.clicked.connect(lambda checked, idx=index: self.on_menu_clicked(idx))
            self.layout.addWidget(button)
            self.buttons.append(button)

        self.layout.addStretch()
        self._update_button_texts()

    def toggle_collapsed(self):
        self._collapsed = not self._collapsed
        self._update_button_texts()

        start_width = self._sidebar_width
        end_width = self.COLLAPSED_WIDTH if self._collapsed else self.EXPANDED_WIDTH
        self.animation = QtCore.QPropertyAnimation(self, b"sidebarWidth")
        self.animation.setDuration(220)
        self.animation.setStartValue(start_width)
        self.animation.setEndValue(end_width)
        self.animation.setEasingCurve(QtCore.QEasingCurve.Type.InOutCubic)
        self.animation.start()

    def _update_button_texts(self):
        self.toggle_button.setToolTip("Expandir menu" if self._collapsed else "Contraer menu")
        self.layout.setContentsMargins(8 if self._collapsed else 12, 12, 8 if self._collapsed else 12, 12)

        for button, (icon, label) in zip(self.buttons, self.menu_items):
            button.setText(icon if self._collapsed else f"{icon}  {label}")
            button.setProperty("collapsed", self._collapsed)
            button.style().unpolish(button)
            button.style().polish(button)

        self.toggle_button.setProperty("collapsed", self._collapsed)
        self.toggle_button.style().unpolish(self.toggle_button)
        self.toggle_button.style().polish(self.toggle_button)

    def get_sidebar_width(self):
        return self._sidebar_width

    def _set_sidebar_width(self, width):
        self._sidebar_width = width
        self.setMinimumWidth(width)
        self.setMaximumWidth(width)

    sidebarWidth = QtCore.pyqtProperty(int, fget=get_sidebar_width, fset=_set_sidebar_width)

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
