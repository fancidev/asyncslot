""" bouncingwidget.py - Qt widget that displays a bouncing ball """

from PySide6.QtCore import Qt, QTimerEvent
from PySide6.QtGui import QPaintEvent, QPainter, QBrush
from PySide6.QtWidgets import QWidget


__all__ = ("BouncingWidget", )


class BouncingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._x = 0
        self._y = 0
        self._d = 20
        self._vx = 10
        self._vy = 5
        self.setMinimumSize(self._d * 2, self._d * 2)
        self.startTimer(50)

    def timerEvent(self, event: QTimerEvent) -> None:
        w = self.width()
        h = self.height()
        self._x += self._vx
        if self._x < 0:
            self._x = -self._x
            self._vx = -self._vx
        elif self._x + self._d > w:
            self._x -= (self._x + self._d - w)
            self._vx = -self._vx
        self._y += self._vy
        if self._y < 0:
            self._y = -self._y
            self._vy = -self._vy
        elif self._y + self._d > h:
            self._y -= (self._y + self._d - h)
            self._vy = -self._vy
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawRect(0, 0, self.width(), self.height())
        brush = QBrush(Qt.black)
        painter.setBrush(brush)
        painter.drawEllipse(self._x, self._y, self._d, self._d)
