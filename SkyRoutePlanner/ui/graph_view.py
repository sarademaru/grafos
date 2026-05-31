import pyqtgraph as pg
from PyQt6 import QtWidgets


class GraphView(QtWidgets.QWidget):
    """Custom widget for rendering a graph view using pyqtgraph."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        self.plot_widget = pg.PlotWidget()
        layout.addWidget(self.plot_widget)

    def display_route(self, vertices, edges):
        """Display a route on the graph view placeholder."""
        self.plot_widget.clear()
        self.plot_widget.plot([0], [0], pen=None, symbol='o')
