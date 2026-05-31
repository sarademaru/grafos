from PyQt6 import QtWidgets


class InfoDialog(QtWidgets.QMessageBox):
    """Simple information dialog used by the UI."""

    def __init__(self, title, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setText(message)
        self.setIcon(QtWidgets.QMessageBox.Icon.Information)
