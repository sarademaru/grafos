import pyqtgraph as pg
from PyQt6.QtWidgets import QApplication

app = QApplication([])

win = pg.plot()
win.plot([1, 2, 3, 4], [2, 5, 1, 7])

app.exec()