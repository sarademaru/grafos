from math import cos, pi, sin, sqrt

from PyQt6.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
    QGraphicsLineItem,
    QGraphicsPolygonItem,
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

    def _build_tooltip(self):
        fields = [
            f"Código: {self.vertice.identificador}",
            f"Nombre: {self.vertice.nombre}",
            f"Ciudad: {self.vertice.ciudad}",
            f"País: {self.vertice.pais}",
            f"Zona Horaria: {self.vertice.zona_horaria}",
        ]
        return "\n".join(fields)

    def hoverEnterEvent(self, event):
        self.setOpacity(0.85)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setOpacity(1.0)
        super().hoverLeaveEvent(event)

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

    def __init__(self, source_item, target_item, distancia_km):
        self.source_item = source_item
        self.target_item = target_item
        self.distancia_km = distancia_km
        self.line_item = None
        self.arrow_item = None
        self.label_item = None

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
        self.line_item.setPen(QPen(QColor("#e5e7eb"), 2))
        self.line_item.setZValue(0)
        scene.addItem(self.line_item)

        arrow_polygon = self._build_arrow(end_point, start_point)
        self.arrow_item = QGraphicsPolygonItem(arrow_polygon)
        self.arrow_item.setBrush(QBrush(QColor("#e5e7eb")))
        self.arrow_item.setPen(QPen(Qt.PenStyle.NoPen))
        self.arrow_item.setZValue(0)
        scene.addItem(self.arrow_item)

        self.label_item = QGraphicsTextItem(f"{self.distancia_km} km")
        self.label_item.setDefaultTextColor(QColor("#f8fafc"))
        label_font = QFont("Consolas", 9)
        self.label_item.setFont(label_font)
        midpoint = QPointF((start_point.x() + end_point.x()) / 2, (start_point.y() + end_point.y()) / 2)
        label_rect = self.label_item.boundingRect()
        self.label_item.setPos(midpoint.x() - label_rect.width() / 2, midpoint.y() - label_rect.height() / 2)
        self.label_item.setZValue(0)
        scene.addItem(self.label_item)

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

    def set_graph(self, grafo):
        self.grafo = grafo
        self.dibujar_grafo(grafo)

    def clear_graph(self):
        self.grafo = None
        self.scene.clear()

    def dibujar_grafo(self, grafo):
        self.scene.clear()
        self.node_items.clear()

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
                edge = AristaGrafica(source_node, target_node, arista.distancia_km)
                edge.add_to_scene(self.scene)

        self.scene.setBackgroundBrush(QColor("#0f172a"))
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-80, -80, 80, 80))
        self._zoom_to_fit()

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

    def _zoom_to_fit(self):
        rect = self.scene.sceneRect()
        if rect.isNull():
            return
        self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            self.scale(zoom_in_factor, zoom_in_factor)
        else:
            self.scale(zoom_out_factor, zoom_out_factor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.grafo:
            self._zoom_to_fit()
