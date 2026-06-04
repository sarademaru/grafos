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
        footer_widget = self._build_footer()

        main_layout.addWidget(header_widget)
        main_layout.addWidget(body_widget, stretch=1)
        main_layout.addWidget(footer_widget)

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

        self.planificador_page = PaginaPlanificador()
        self.config_page = PaginaConfiguracion()
        self.config_page.graph_loaded.connect(self.on_graph_loaded)
        self.config_page.system_reset.connect(self.on_system_reset)

        self.page_stack = QtWidgets.QStackedWidget()
        self.page_stack.addWidget(PaginaInicio())
        self.page_stack.addWidget(self.planificador_page)
        self.page_stack.addWidget(PaginaViajeDinamico())
        self.page_stack.addWidget(PaginaReportes())
        self.page_stack.addWidget(self.config_page)

        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.page_stack, stretch=1)

        return body

    def _build_footer(self):
        footer = QtWidgets.QFrame()
        footer.setObjectName("footer")
        footer.setMaximumHeight(96)
        footer_layout = QtWidgets.QVBoxLayout(footer)
        footer_layout.setContentsMargins(24, 6, 24, 8)
        footer_layout.setSpacing(4)

        log_title = QtWidgets.QLabel("System Log")
        log_title.setObjectName("logTitle")

        self.log_view = QtWidgets.QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setObjectName("logView")
        self.log_view.setMinimumHeight(42)
        self.log_view.setMaximumHeight(54)
        self.log_view.setPlainText("Application initialized. Navigation is ready.")

        footer_layout.addWidget(log_title)
        footer_layout.addWidget(self.log_view)

        return footer

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
            QPushButton#sidebarButton {
                padding: 12px 16px;
                border: none;
                color: #cbd5e1;
                background: transparent;
                text-align: left;
                font-size: 14px;
            }
            QPushButton#sidebarButton:hover {
                background: #6d28d9;
                color: #ffffff;
            }
            QPushButton#sidebarButton:checked {
                background: #7c3aed;
                color: #ffffff;
            }
            QFrame#footer {
                background: #5b21b6;
                border-top: 1px solid #2d3748;
            }
            QLabel#logTitle {
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 600;
            }
            QTextEdit#logView {
                background: #4c1d95;
                color: #e2e8f0;
                border: 1px solid #334155;
                font-family: Consolas, monospace;
                font-size: 11px;
                min-height: 42px;
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
            QScrollArea#plannerScroll > QWidget > QWidget {
                background: transparent;
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
        self.log_view.append(f"Switched to page index {index}.")

    def on_graph_loaded(self, grafo):
        self.grafo = grafo
        self.planificador_page.set_graph(grafo)
        self.sidebar.select_index(1)
        self.page_stack.setCurrentIndex(1)
        self.status_label.setText("Status: Graph loaded")
        self.log_view.append(f"Loaded graph with {grafo.cantidad_vertices()} airports.")

    def on_system_reset(self):
        self.grafo = None
        self.planificador_page.clear_graph()
        self.status_label.setText("Status: System reset")
        self.log_view.append("System reset requested.")
