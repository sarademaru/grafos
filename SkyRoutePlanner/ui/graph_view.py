from math import atan2, cos, pi, sin, sqrt

from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
    QGraphicsRectItem,
)
from PyQt6.QtGui import QPen, QBrush, QColor, QFont, QPolygonF, QPainter
from PyQt6.QtCore import Qt, QPointF, pyqtSignal


class NodoGrafico(QGraphicsEllipseItem):
    """Graphical node representing an airport vertex."""

    def __init__(self, vertice, position, radius=36):
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.vertice = vertice
        self.setAcceptHoverEvents(True)
        self.setAcceptedMouseButtons(Qt.MouseButton.LeftButton)
        self.setPos(position)

        fill_color = QColor("#fb923c") if vertice.es_hub else QColor("#60a5fa")
        border_width = 4 if vertice.es_hub else 2

        self.setBrush(QBrush(fill_color))
        self.setPen(QPen(QColor("#f8fafc"), border_width))
        self.setZValue(1)

        self._create_labels()
        self.setToolTip(self._build_tooltip())

    """Auxiliary method to create and position the labels for the airport code and city name. This method constructs two QGraphicsTextItem instances, one for the airport code (identifier) and another for the city name (or airport name if city is not available). It sets their font, color, and positions them appropriately relative to the node to ensure they are clearly visible and do not overlap with the node itself."""
    def _create_labels(self):
        code_label = QGraphicsTextItem(self.vertice.identificador, self)
        code_label.setDefaultTextColor(QColor("#0f172a"))
        code_font = QFont("Consolas", 10, QFont.Weight.Bold)
        code_label.setFont(code_font)
        code_rect = code_label.boundingRect()
        code_label.setPos(-code_rect.width() / 2, -18)

        city_name = self.vertice.ciudad or self.vertice.nombre or "Unknown"
        city_label = QGraphicsTextItem(city_name, self)
        city_label.setDefaultTextColor(QColor("#0f172a"))
        city_font = QFont("Consolas", 8)
        city_label.setFont(city_font)
        city_rect = city_label.boundingRect()
        city_label.setPos(-city_rect.width() / 2, 6)

    """Auxiliary method to build the tooltip text for the node. This method constructs a multi-line string containing information about the airport, including its code, name, city, country, and time zone."""
    def _build_tooltip(self):
        fields = [
            f"Código: {self.vertice.identificador}",
            f"Nombre: {self.vertice.nombre}",
            f"Ciudad: {self.vertice.ciudad}",
            f"País: {self.vertice.pais}",
            f"Zona Horaria: {self.vertice.zona_horaria}",
        ]
        return "\n".join(fields)

    """Event handler for when the mouse cursor enters the node area. This method reduces the opacity of the node to create a hover effect, making it visually distinct when the user hovers over it."""
    def hoverEnterEvent(self, event):
        self.setOpacity(0.85)
        super().hoverEnterEvent(event)

    """Event handler for when the mouse cursor leaves the node area. This method restores the opacity of the node to its original state, removing the hover effect when the user moves the cursor away from the node."""
    def hoverLeaveEvent(self, event):
        self.setOpacity(1.0)
        super().hoverLeaveEvent(event)

    """Event handler for when the node is clicked. This method emits a custom signal with the vertex information, allowing other components of the application to respond to the node selection, such as displaying detailed information about the airport or updating other parts of the UI based on the selected node."""
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        views = self.scene().views()
        if not views:
            return

        view = views[0]
        if hasattr(view, "node_selected"):
            view.node_selected.emit(self.vertice)


class AristaGrafica:
    """Graphical edge with directed arrow and distance label."""

    def __init__(self, origin_id, destination_id, source_item, target_item, distancia_km, arista=None):
        self.origin_id = origin_id
        self.destination_id = destination_id
        self.source_item = source_item
        self.target_item = target_item
        self.distancia_km = distancia_km
        self.arista = arista
        self.highlighted = False
        self.line_item = None
        self.arrow_item = None
        self.label_background_item = None
        self.label_item = None

    """Auxiliary method to add the edge to the scene. This method calculates the appropriate positions for the line, arrow, and label based on the positions of the source and target nodes. It creates a QGraphicsLineItem for the edge, a QGraphicsPolygonItem for the arrowhead, and a QGraphicsTextItem for the distance label, adding them to the scene with appropriate styling and z-ordering."""
    def add_to_scene(self, scene):
        start = self.source_item.scenePos()
        end = self.target_item.scenePos()
        if start == end:
            return

        direction = end - start
        length = sqrt(direction.x() ** 2 + direction.y() ** 2)
        if length == 0:
            return

        offset = 44
        start_point = start + QPointF(direction.x() * offset / length, direction.y() * offset / length)
        end_point = end - QPointF(direction.x() * offset / length, direction.y() * offset / length)

        self.line_item = QGraphicsLineItem(start_point.x(), start_point.y(), end_point.x(), end_point.y())
        self.line_item.setZValue(0)
        scene.addItem(self.line_item)

        arrow_polygon = self._build_arrow(end_point, start_point)
        self.arrow_item = QGraphicsPolygonItem(arrow_polygon)
        self.arrow_item.setPen(QPen(Qt.PenStyle.NoPen))
        self.arrow_item.setZValue(0)
        scene.addItem(self.arrow_item)

        unit = QPointF(direction.x() / length, direction.y() / length)
        perp = QPointF(-unit.y(), unit.x())
        label_side = 1 if self.origin_id <= self.destination_id else -1
        label_offset = 14

        self.label_item = QGraphicsTextItem(f"{self.distancia_km} km")
        label_font = QFont("Consolas", 9)
        self.label_item.setFont(label_font)
        label_rect = self.label_item.boundingRect()

        arrow_size = 14
        label_gap = 8
        label_distance_from_tip = arrow_size + label_rect.width() / 2 + label_gap
        label_center = end_point - unit * label_distance_from_tip
        label_center += perp * label_offset * label_side
        label_pos = QPointF(label_center.x() - label_rect.width() / 2, label_center.y() - label_rect.height() / 2)

        label_angle = atan2(end_point.y() - start_point.y(), end_point.x() - start_point.x()) * 180 / pi
        if label_angle > 90 or label_angle < -90:
            label_angle += 180

        padding_x = 5
        padding_y = 2
        self.label_background_item = QGraphicsRectItem(
            -padding_x,
            -padding_y,
            label_rect.width() + padding_x * 2,
            label_rect.height() + padding_y * 2,
        )
        self.label_background_item.setPen(QPen(Qt.PenStyle.NoPen))
        self.label_background_item.setBrush(QBrush(QColor(15, 23, 42, 205)))
        self.label_background_item.setPos(label_pos)
        self.label_background_item.setTransformOriginPoint(label_rect.width() / 2, label_rect.height() / 2)
        self.label_background_item.setRotation(label_angle)
        self.label_background_item.setZValue(3)
        scene.addItem(self.label_background_item)

        self.label_item.setPos(label_pos)
        self.label_item.setTransformOriginPoint(label_rect.width() / 2, label_rect.height() / 2)
        self.label_item.setRotation(label_angle)
        self.label_item.setZValue(4)
        scene.addItem(self.label_item)
        self.refresh_style()

    def mostrar_etiqueta(self, visible):
        if self.label_background_item:
            self.label_background_item.setVisible(visible)
        if self.label_item:
            self.label_item.setVisible(visible)

    """Auxiliary method to set the highlighted state of the edge. This method updates the internal highlighted flag and calls the refresh_style method to update the visual appearance of the edge based on whether it is highlighted or not. Highlighting can be used to visually distinguish edges that are part of a selected route or path in the graph."""
    def set_highlighted(self, highlighted):
        self.highlighted = highlighted
        self.refresh_style()

    """Auxiliary method to refresh the visual style of the edge based on its current state. This method checks if the edge is blocked and updates the color, pen style, and opacity accordingly. It also updates the appearance of the arrow and label background to reflect the blocked state, providing a clear visual indication of whether the route is available or not."""
    def refresh_style(self):
        if not self.line_item:
            return

        is_blocked = bool(self.arista and self.arista.esta_bloqueada())
        if is_blocked:
            color = QColor("#991b1b")
            label_color = QColor("#fca5a5")
            pen = QPen(color, 3)
            pen.setStyle(Qt.PenStyle.DashLine)
            opacity = 0.45
        else:
            color = QColor("#facc15") if self.highlighted else QColor("#e5e7eb")
            label_color = color if self.highlighted else QColor("#f8fafc")
            pen = QPen(color, 4 if self.highlighted else 2)
            pen.setStyle(Qt.PenStyle.SolidLine)
            opacity = 1.0

        self.line_item.setPen(pen)
        self.line_item.setOpacity(opacity)

        if self.arrow_item:
            self.arrow_item.setBrush(QBrush(color))
            self.arrow_item.setOpacity(opacity)

        if self.label_background_item:
            background_color = QColor(69, 10, 10, 215) if is_blocked else QColor(15, 23, 42, 215)
            self.label_background_item.setBrush(QBrush(background_color))
            self.label_background_item.setOpacity(0.75 if is_blocked else 1.0)

        if self.label_item:
            self.label_item.setDefaultTextColor(label_color)
            self.label_item.setOpacity(0.7 if is_blocked else 1.0)

    """Auxiliary method to build the arrow polygon for the directed edge. This method calculates the points for a triangular arrowhead based on the direction from the tail to the tip of the edge. It returns a QPolygonF representing the arrowhead, which can be added to the scene to visually indicate the direction of the edge."""
    def _build_arrow(self, tip, tail):
        direction = tail - tip
        length = sqrt(direction.x() ** 2 + direction.y() ** 2)
        if length == 0:
            return QPolygonF()

        unit = QPointF(direction.x() / length, direction.y() / length)
        perp = QPointF(-unit.y(), unit.x())
        arrow_size = 14

        point1 = tip
        point2 = tip + unit * arrow_size + perp * (arrow_size / 2)
        point3 = tip + unit * arrow_size - perp * (arrow_size / 2)
        polygon = QPolygonF([point1, point2, point3])
        return polygon


class GraphView(QGraphicsView):
    """Display the airport graph with automatic layout, zoom, and pan."""

    node_selected = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.setRenderHints(self.renderHints() | QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.grafo = None
        self.node_items = {}
        self.edge_items = []
        self.flight_marker = None
        self.etiquetas_distancia_visibles = True

    """Auxiliary method to set the graph data and trigger the drawing of the graph. This method takes a graph object as input, stores it in the instance variable, and calls the dibujar_grafo method to visualize the graph in the view. It allows the view to be updated with new graph data whenever necessary."""
    def set_graph(self, grafo):
        self.grafo = grafo
        self.dibujar_grafo(grafo)

    """Auxiliary method to clear the current graph data from the view. This method resets the graph variable, clears all items from the scene, and resets the node and edge item collections, as well as the flight marker. It prepares the view for a new graph to be loaded or for a reset state."""
    def clear_graph(self):
        self.grafo = None
        self.scene.clear()
        self.node_items.clear()
        self.edge_items.clear()
        self.flight_marker = None
    """Auxiliary method to draw the graph in the view. This method takes a graph object as input, calculates the positions for the vertices, creates graphical items for the nodes and edges, and adds them to the scene. It also sets the background color and adjusts the view to fit the entire graph. The method handles both small and large graphs, applying different layout strategies to ensure a clear visualization."""
    def dibujar_grafo(self, grafo):
        self.scene.clear()
        self.node_items.clear()
        self.edge_items.clear()

        if not grafo:
            return

        positions = self._calculate_positions(grafo)

        for vertice in grafo.obtener_vertices():
            position = positions.get(vertice.identificador, QPointF(0, 0))
            node = NodoGrafico(vertice, position)
            self.scene.addItem(node)
            self.node_items[vertice.identificador] = node

        for vertice in grafo.obtener_vertices():
            source_node = self.node_items[vertice.identificador]
            for arista in vertice.adyacencias:
                target_node = self.node_items.get(arista.vertice_destino.identificador)
                if not target_node:
                    continue
                edge = AristaGrafica(
                    vertice.identificador,
                    arista.vertice_destino.identificador,
                    source_node,
                    target_node,
                    arista.distancia_km,
                    arista,
                )
                edge.add_to_scene(self.scene)
                edge.mostrar_etiqueta(self.etiquetas_distancia_visibles)
                self.edge_items.append(edge)

        self.scene.setBackgroundBrush(QColor("#0f172a"))
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-80, -80, 80, 80))
        self._zoom_to_fit()

    def mostrar_etiquetas(self, visible):
        self.etiquetas_distancia_visibles = bool(visible)
        for edge in self.edge_items:
            edge.mostrar_etiqueta(self.etiquetas_distancia_visibles)
        self.viewport().update()

    """Auxiliary method to calculate the positions of the vertices in the graph for visualization. This method uses a circular layout for small graphs and a hub-and-spoke layout for larger graphs, positioning hubs closer to the center and other vertices around them. It returns a dictionary mapping vertex identifiers to their calculated positions as QPointF objects."""
    def _calculate_positions(self, grafo):
        vertices = grafo.obtener_vertices()
        count = len(vertices)
        positions = {}
        radius = 260 if count < 20 else 320
        center = QPointF(0, 0)

        if count == 0:
            return positions

        if count < 20:
            for index, vertice in enumerate(vertices):
                angle = 2 * pi * index / count
                positions[vertice.identificador] = QPointF(
                    center.x() + cos(angle) * radius,
                    center.y() + sin(angle) * radius,
                )
            return positions

        hubs = [v for v in vertices if v.es_hub]
        others = [v for v in vertices if not v.es_hub]
        hub_count = max(1, len(hubs))
        hub_radius = radius * 0.7
        outer_radius = radius * 1.3

        for idx, vertice in enumerate(hubs):
            angle = 2 * pi * idx / hub_count
            positions[vertice.identificador] = QPointF(
                center.x() + cos(angle) * hub_radius,
                center.y() + sin(angle) * hub_radius,
            )

        if others:
            for idx, vertice in enumerate(others):
                angle = 2 * pi * idx / len(others)
                positions[vertice.identificador] = QPointF(
                    center.x() + cos(angle) * outer_radius,
                    center.y() + sin(angle) * outer_radius,
                )

        return positions

    """Auxiliary method to adjust the view to fit the entire graph. This method calculates the bounding rectangle of all items in the scene and adjusts the view to ensure that all nodes and edges are visible within the viewport, maintaining the aspect ratio. It is typically called after drawing the graph or when the view is resized to ensure an optimal display of the graph content."""
    def _zoom_to_fit(self):
        rect = self.scene.sceneRect()
        if rect.isNull():
            return
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    """Event handler for mouse wheel events to implement zooming functionality. This method checks the direction of the wheel scroll and applies a scaling transformation to the view to zoom in or out accordingly. It allows users to easily zoom into specific areas of the graph for a closer look or zoom out for an overview of the entire graph."""
    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)
    """Event handler for resize events to adjust the view when the window size changes. This method calls the _zoom_to_fit method to ensure that the graph remains fully visible and properly scaled within the new window dimensions whenever the view is resized."""
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.grafo:
            self._zoom_to_fit()
    """Auxiliary method to refresh the visual state of the graph. This method iterates through all edge items and calls their refresh_style method to update their appearance based on their current state (e.g., blocked, highlighted). It then triggers a viewport update to ensure that all changes are rendered on the screen. This method can be called after changes to the graph data or edge states to ensure that the visualization remains accurate and up-to-date."""
    def refresh_graph_state(self):
        for edge in self.edge_items:
            edge.refresh_style()
        self.viewport().update()

    """Auxiliary method to set the progress of a flight on the graph. This method updates the position of the flight marker along the specified route based on the progress value."""
    def set_flight_progress(self, origen, destino, progreso):
        edge = self._find_edge(origen, destino)
        if not edge or not edge.line_item:
            self.clear_flight_progress()
            return

        if self.flight_marker is None:
            self.flight_marker = QGraphicsEllipseItem(-9, -9, 18, 18)
            self.flight_marker.setBrush(QBrush(QColor("#22c55e")))
            self.flight_marker.setPen(QPen(QColor("#f8fafc"), 2))
            self.flight_marker.setZValue(3)
            self.scene.addItem(self.flight_marker)

        progreso = max(0.0, min(1.0, float(progreso)))
        line = edge.line_item.line()
        start = line.p1()
        end = line.p2()
        x = start.x() + (end.x() - start.x()) * progreso
        y = start.y() + (end.y() - start.y()) * progreso
        self.flight_marker.setPos(QPointF(x, y))
        self.flight_marker.setVisible(True)
        self.viewport().update()

    """Auxiliary method to clear the flight progress marker from the graph. This method hides the flight marker and triggers a viewport update to remove it from the display. It is typically called when a flight is completed or when the progress needs to be reset for any reason."""
    def clear_flight_progress(self):
        if self.flight_marker:
            self.flight_marker.setVisible(False)
        self.viewport().update()

    """Auxiliary method to find the edge item corresponding to a given origin and destination. This method iterates through the list of edge items and checks if any edge matches the specified origin and destination identifiers. If a matching edge is found, it is returned; otherwise, the method returns None. This is useful for updating the state of specific edges based on user interactions or changes in the graph data."""
    def _find_edge(self, origen, destino):
        for edge in self.edge_items:
            if edge.origin_id == origen and edge.destination_id == destino:
                return edge
        return None

    """Auxiliary method to retrieve the vertex object for a given identifier. This method checks if the specified identifier exists in the graph's vertices and returns the corresponding vertex object. If the identifier does not exist, it raises a ValueError indicating that the airport does not exist in the graph."""
    def highlight_route(self, path):
        route_edges = set()
        if path and len(path) > 1:
            route_edges = set(zip(path, path[1:]))

        for edge in self.edge_items:
            edge.set_highlighted((edge.origin_id, edge.destination_id) in route_edges)
