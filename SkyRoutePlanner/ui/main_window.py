from PyQt6 import QtWidgets, QtCore
from .sidebar import Sidebar
from .pages import (
    PaginaInicio,
    PaginaPlanificador,
    PaginaViajeDinamico,
    PaginaReportes,
    PaginaConfiguracion,
)


class MainWindow(QtWidgets.QMainWindow):
    """Main application window for SkyRoute Planner."""

    def __init__(self):
        super().__init__()
        self.grafo = None
        self.last_route_payload = None
        self.setWindowTitle("SkyRoute Planner")
        self.resize(1200, 850)
        self._setup_ui()

    def _setup_ui(self):
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QtWidgets.QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header_widget = self._build_header()
        body_widget = self._build_body()

        main_layout.addWidget(header_widget)
        main_layout.addWidget(body_widget, stretch=1)

        self.setStyleSheet(self._load_styles())
        self.sidebar.set_default_selection()

    def _build_header(self):
        header = QtWidgets.QFrame()
        header.setObjectName("header")
        header_layout = QtWidgets.QHBoxLayout(header)
        header_layout.setContentsMargins(24, 16, 24, 16)

        title_label = QtWidgets.QLabel("SkyRoute Planner")
        title_label.setObjectName("headerTitle")

        self.status_label = QtWidgets.QLabel("Status: Ready")
        self.status_label.setObjectName("headerStatus")
        self.status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.status_label)

        return header

    def _build_body(self):
        body = QtWidgets.QFrame()
        body_layout = QtWidgets.QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.menu_selected.connect(self.on_menu_selected)

        self.inicio_page = PaginaInicio()
        self.planificador_page = PaginaPlanificador()
        self.viaje_dinamico_page = PaginaViajeDinamico()
        self.reportes_page = PaginaReportes()
        self.config_page = PaginaConfiguracion()
        self.planificador_page.route_calculated.connect(self.on_route_calculated)
        self.config_page.graph_loaded.connect(self.on_graph_loaded)
        self.config_page.system_reset.connect(self.on_system_reset)
        self.config_page.configuration_updated.connect(self.on_graph_configuration_updated)

        self.page_stack = QtWidgets.QStackedWidget()
        self.page_stack.addWidget(self.inicio_page)
        self.page_stack.addWidget(self.planificador_page)
        self.page_stack.addWidget(self.viaje_dinamico_page)
        self.page_stack.addWidget(self.reportes_page)
        self.page_stack.addWidget(self.config_page)

        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.page_stack, stretch=1)

        return body

    def _load_styles(self):
        return """
            #header {
                background: #5b21b6;
                color: #ffffff;
                border-bottom: 1px solid #2d3748;
            }
            #headerTitle {
                font-size: 24px;
                font-weight: 700;
            }
            #headerStatus {
                color: #d8b4fe;
                font-size: 14px;
            }
            #sidebar {
                background: #4c1d95;
                color: #e2e8f0;
                border-right: 1px solid #334155;
            }
            #sidebarTitle {
                font-size: 20px;
                font-weight: 700;
                color: #ffffff;
            }
            QPushButton#sidebarToggle {
                min-height: 40px;
                border: none;
                color: #f8fafc;
                background: transparent;
                text-align: left;
                padding: 8px 14px;
                font-size: 22px;
            }
            QPushButton#sidebarToggle:hover {
                background: #6d28d9;
            }
            QPushButton#sidebarToggle[collapsed="true"] {
                text-align: center;
                padding: 8px 0;
            }
            QPushButton#sidebarButton {
                min-height: 44px;
                padding: 12px 16px;
                border: none;
                color: #cbd5e1;
                background: transparent;
                text-align: left;
                font-size: 14px;
            }
            QPushButton#sidebarButton[collapsed="true"] {
                text-align: center;
                padding: 12px 0;
                font-size: 18px;
            }
            QPushButton#sidebarButton:hover {
                background: #6d28d9;
                color: #ffffff;
            }
            QPushButton#sidebarButton:checked {
                background: #7c3aed;
                color: #ffffff;
            }
            QTextEdit#routeResults {
                background: #0f172a;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 6px;
                font-family: Consolas, monospace;
                font-size: 12px;
                padding: 8px;
            }
            QLabel#pageTitle {
                font-size: 32px;
                font-weight: 700;
                color: #f8fafc;
            }
            QFrame#infoFrame {
                background: #1f2937;
                border: 1px solid #4c1d95;
                border-radius: 12px;
            }
            QFrame#dashboardCard,
            QFrame#summaryPanel,
            QFrame#reportCard,
            QFrame#placeholderPanel,
            QFrame#placeholderCard {
                background: #111827;
                border: 1px solid #334155;
                border-radius: 8px;
            }
            QGroupBox#reportGroup {
                background: #111827;
                border: 1px solid #334155;
                border-radius: 8px;
                color: #f8fafc;
                font-size: 16px;
                font-weight: 700;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox#reportGroup::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QTableWidget {
                background: #0f172a;
                alternate-background-color: #111827;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 6px;
                gridline-color: #334155;
                selection-background-color: #6d28d9;
            }
            QHeaderView::section {
                background: #1f2937;
                color: #f8fafc;
                border: 1px solid #334155;
                padding: 6px;
                font-weight: 700;
            }
            QLabel#dashboardCardLabel,
            QLabel#reportLine {
                color: #cbd5e1;
                font-size: 13px;
            }
            QLabel#dashboardCardValue {
                color: #f8fafc;
                font-size: 22px;
                font-weight: 700;
            }
            QLabel#reportCardTitle,
            QLabel#placeholderTitle {
                color: #f8fafc;
                font-size: 18px;
                font-weight: 700;
            }
            QLabel#infoLabel {
                color: #cbd5e1;
                font-size: 14px;
            }
            QLabel#infoValue {
                color: #f8fafc;
                font-size: 16px;
                font-weight: 600;
            }
            QPushButton#primaryButton {
                background: #8b5cf6;
                color: #ffffff;
                padding: 10px 16px;
                border: none;
                border-radius: 8px;
            }
            QPushButton#primaryButton:hover {
                background: #a78bfa;
            }
            QComboBox {
                background: #1f2937;
                color: #f8fafc;
                border: 1px solid #4c1d95;
                padding: 8px;
                border-radius: 6px;
            }
            QComboBox QAbstractItemView {
                background: #111827;
                color: #f8fafc;
            }
            QLabel#sectionTitle {
                color: #d8b4fe;
                font-size: 18px;
                font-weight: 600;
            }
            QFrame#controlPanel {
                background: #111827;
                border: 1px solid #4c1d95;
                border-radius: 8px;
            }
            QScrollArea#plannerScroll {
                background: transparent;
                border: none;
            }
            QScrollArea#plannerScroll > QWidget > QWidget,
            QScrollArea#reportsScroll > QWidget > QWidget {
                background: transparent;
            }
            QScrollArea#reportsScroll {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #1f2937;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #8b5cf6;
                border-radius: 5px;
                min-height: 28px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0;
            }
            QFrame#legendBox {
                background: #111827;
                border: 1px solid #4c1d95;
                border-radius: 12px;
            }
            QLabel#legendLabel {
                color: #f8fafc;
                font-size: 13px;
            }
            QLabel#statusBanner {
                color: #86efac;
                font-size: 16px;
                font-weight: 600;
            }
        """

    def on_menu_selected(self, index):
        self.page_stack.setCurrentIndex(index)
        if index == 3:
            self._refresh_reports_from_sources()

    def on_graph_loaded(self, grafo):
        self.grafo = grafo
        self.last_route_payload = None
        self.inicio_page.set_graph(grafo)
        self.planificador_page.set_graph(grafo)
        self.viaje_dinamico_page.set_graph(grafo)
        self.reportes_page.clear_report()
        self.sidebar.select_index(1)
        self.page_stack.setCurrentIndex(1)
        self.status_label.setText("Status: Graph loaded")

    def on_system_reset(self):
        self.grafo = None
        self.last_route_payload = None
        self.inicio_page.clear_graph()
        self.planificador_page.clear_graph()
        self.viaje_dinamico_page.clear_graph()
        self.reportes_page.clear_report()
        self.status_label.setText("Status: System reset")

    def on_graph_configuration_updated(self):
        if self.viaje_dinamico_page:
            self.viaje_dinamico_page.on_graph_configuration_updated()
        self.status_label.setText("Status: Configuration updated")

    def on_route_calculated(self, payload):
        self.last_route_payload = payload
        self.inicio_page.set_last_route(payload)
        self.reportes_page.set_planning_report(payload)

    def _refresh_reports_from_sources(self):
        gestor = getattr(self.viaje_dinamico_page, "gestor", None)
        alternativas = getattr(self.viaje_dinamico_page, "alternativas", [])
        if not gestor:
            self.reportes_page.set_dynamic_report(None, alternativas)
            return

        estado = gestor.obtener_estado()
        estado["actividades_realizadas"] = list(gestor.viajero.actividades_realizadas)
        estado["trabajos_realizados"] = list(gestor.viajero.trabajos_realizados)
        estado["tiempo_libre_registrado"] = list(gestor.viajero.tiempo_libre_registrado)
        self.reportes_page.set_dynamic_report(estado, alternativas)