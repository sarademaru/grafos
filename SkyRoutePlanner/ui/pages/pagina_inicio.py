from PyQt6 import QtCore, QtWidgets

from ui.graph_view import GraphView


class PaginaInicio(QtWidgets.QWidget):
    """Dashboard overview for the air network."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.grafo = None
        self.last_route = None
        self.graph_view = GraphView()
        self._setup_ui()

    def _setup_ui(self):
        """Initializes the user interface components of the dashboard, including the layout, title, statistic cards for airports, routes, hubs, and last calculated route, as well as the graph view for visualizing the air network. This method sets up the structure and styling of the dashboard page."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("Inicio")
        title.setObjectName("pageTitle")
        title.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        cards_layout = QtWidgets.QHBoxLayout()
        cards_layout.setSpacing(12)

        self.airports_card = self._build_card("Aeropuertos", "0")
        self.routes_card = self._build_card("Rutas", "0")
        self.hubs_card = self._build_card("Hubs", "0")
        self.last_route_card = self._build_card("Ultima ruta", "Sin calculos")

        for card in (self.airports_card, self.routes_card, self.hubs_card, self.last_route_card):
            cards_layout.addWidget(card["frame"])

        layout.addLayout(cards_layout)

        graph_title = QtWidgets.QLabel("Vista general del grafo")
        graph_title.setObjectName("sectionTitle")
        layout.addWidget(graph_title)
        layout.addWidget(self.graph_view, stretch=1)


    """Auxiliary method to create a statistic card with a label and value. This method constructs a styled card widget that displays a specific statistic (such as the number of airports, routes, hubs, or the last calculated route) in the dashboard. It returns a dictionary containing the card frame and the value label for easy updating of the displayed statistic."""
    def _build_card(self, label, value):
        frame = QtWidgets.QFrame()
        frame.setObjectName("dashboardCard")
        frame_layout = QtWidgets.QVBoxLayout(frame)
        frame_layout.setContentsMargins(14, 12, 14, 12)
        frame_layout.setSpacing(6)

        label_widget = QtWidgets.QLabel(label)
        label_widget.setObjectName("dashboardCardLabel")
        value_widget = QtWidgets.QLabel(value)
        value_widget.setObjectName("dashboardCardValue")
        value_widget.setWordWrap(True)

        frame_layout.addWidget(label_widget)
        frame_layout.addWidget(value_widget)
        return {"frame": frame, "value": value_widget}

    """Sets the graph data for the dashboard and updates the graph view and statistics accordingly. This method is called when a new graph is loaded or updated, allowing the dashboard to reflect the current state of the air network. It also triggers a refresh of the displayed statistics based on the new graph data."""
    def set_graph(self, grafo):
        self.grafo = grafo
        self.graph_view.set_graph(grafo)
        self._refresh_stats()

    """Clears the current graph data from the dashboard, resetting the graph view and statistics to their default state. This method is useful when the user wants to start fresh with a new graph or when the existing graph data is no longer relevant. It ensures that all displayed information is cleared and ready for new input."""
    def clear_graph(self):
        self.grafo = None
        self.last_route = None
        self.graph_view.clear_graph()
        self._refresh_stats()

    """ Sets the last calculated route information for the dashboard, updating the displayed last route statistic and highlighting the route in the graph view. This method is called after a route calculation is performed, allowing the dashboard to show the most recent route found by the planner. It also triggers a refresh of the displayed statistics to reflect the new route information."""
    def set_last_route(self, payload):
        self.last_route = payload
        self._refresh_stats()
        route = payload.get("primary_route") if payload else None
        if route:
            self.graph_view.highlight_route(route["path"])
    """Auxiliary method to refresh the statistics displayed on the dashboard based on the current graph data. This method calculates the number of airports, routes, hubs, and the last calculated route from the graph and updates the corresponding statistic cards in the user interface. It ensures that all displayed information is accurate and up-to-date whenever the graph data changes or a new route is calculated."""
    def _refresh_stats(self):
        if not self.grafo:
            self.airports_card["value"].setText("0")
            self.routes_card["value"].setText("0")
            self.hubs_card["value"].setText("0")
            self.last_route_card["value"].setText("Sin calculos")
            return

        vertices = self.grafo.obtener_vertices()
        route_count = sum(len(vertex.adyacencias) for vertex in vertices)
        hub_count = sum(1 for vertex in vertices if vertex.es_hub)

        self.airports_card["value"].setText(str(len(vertices)))
        self.routes_card["value"].setText(str(route_count))
        self.hubs_card["value"].setText(str(hub_count))

        route = self.last_route.get("primary_route") if self.last_route else None
        if route:
            self.last_route_card["value"].setText(" -> ".join(route["path"]))
        else:
            self.last_route_card["value"].setText("Sin calculos")
