from PyQt6 import QtWidgets


class MainWindow(QtWidgets.QMainWindow):
    """Main application window for SkyRoute Planner."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SkyRoute Planner")
        self.resize(1000, 700)
        self._setup_ui()

    def _setup_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        layout = QtWidgets.QVBoxLayout(central_widget)
        self.graph_view = QtWidgets.QLabel("Graph visualization will be displayed here.")
        self.graph_view.setAlignment(QtWidgets.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.graph_view)
