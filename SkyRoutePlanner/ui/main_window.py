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
        self.setWindowTitle("SkyRoute Planner")
        self.resize(1200, 800)
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
        main_layout.addWidget(body_widget)
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

        status_label = QtWidgets.QLabel("Status: Ready")
        status_label.setObjectName("headerStatus")
        status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)

        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(status_label)

        return header

    def _build_body(self):
        body = QtWidgets.QFrame()
        body_layout = QtWidgets.QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.menu_selected.connect(self.on_menu_selected)

        self.page_stack = QtWidgets.QStackedWidget()
        self.page_stack.addWidget(PaginaInicio())
        self.page_stack.addWidget(PaginaPlanificador())
        self.page_stack.addWidget(PaginaViajeDinamico())
        self.page_stack.addWidget(PaginaReportes())
        self.page_stack.addWidget(PaginaConfiguracion())

        body_layout.addWidget(self.sidebar)
        body_layout.addWidget(self.page_stack, stretch=1)

        return body

    def _build_footer(self):
        footer = QtWidgets.QFrame()
        footer.setObjectName("footer")
        footer_layout = QtWidgets.QVBoxLayout(footer)
        footer_layout.setContentsMargins(24, 16, 24, 16)

        log_title = QtWidgets.QLabel("System Log")
        log_title.setObjectName("logTitle")

        self.log_view = QtWidgets.QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setObjectName("logView")
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
                color: #9ca3af;
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
                background: #cb9bde;
                color: #ffffff;
            }
            QPushButton#sidebarButton:checked {
                background: #af69cd;
                color: #ffffff;
            }
            QFrame#footer {
                background: #5b21b6;
                border-top: 1px solid #2d3748;
            }
            QLabel#logTitle {
                color: #e2e8f0;
                font-size: 16px;
                font-weight: 600;
            }
            QTextEdit#logView {
                background: #4c1d95;
                color: #e2e8f0;
                border: 1px solid #334155;
                font-family: Consolas, monospace;
                min-height: 160px;
            }
            QLabel#pageTitle {
                font-size: 32px;
                font-weight: 700;
                color: #111827;
            }
        """

    def on_menu_selected(self, index):
        self.page_stack.setCurrentIndex(index)
        self.log_view.append(f"Switched to page index {index}.")
