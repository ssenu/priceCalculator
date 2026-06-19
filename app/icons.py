"""간단한 벡터 아이콘 생성 (색상 제어 가능)."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
    QPolygonF,
)


def _canvas(size: int) -> tuple[QPixmap, QPainter]:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    return pm, p


def _stroke_pen(color: str, size: int) -> QPen:
    pen = QPen(QColor(color))
    pen.setWidthF(max(1.4, size * 0.085))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    return pen


def make_min_icon(color: str, size: int = 16) -> QIcon:
    """최소화: 가운데 가로선."""
    pm, p = _canvas(size)
    p.setPen(_stroke_pen(color, size))
    y = size * 0.62
    p.drawLine(QPointF(size * 0.22, y), QPointF(size * 0.78, y))
    p.end()
    return QIcon(pm)


def make_max_icon(color: str, size: int = 16) -> QIcon:
    """전체화면: 사각형 외곽선."""
    pm, p = _canvas(size)
    p.setPen(_stroke_pen(color, size))
    p.setBrush(Qt.BrushStyle.NoBrush)
    r = size * 0.16
    p.drawRoundedRect(QRectF(size * 0.24, size * 0.24, size * 0.52, size * 0.52), r, r)
    p.end()
    return QIcon(pm)


def make_close_icon(color: str, size: int = 16) -> QIcon:
    """닫기: X 모양."""
    pm, p = _canvas(size)
    p.setPen(_stroke_pen(color, size))
    a, b = size * 0.26, size * 0.74
    p.drawLine(QPointF(a, a), QPointF(b, b))
    p.drawLine(QPointF(b, a), QPointF(a, b))
    p.end()
    return QIcon(pm)


def make_pin_icon(color: str, size: int = 26) -> QIcon:
    """압정(핀) 모양 아이콘을 주어진 색으로 그린다."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    c = QColor(color)
    p.setBrush(QBrush(c))
    p.setPen(Qt.PenStyle.NoPen)

    s = size
    # 핀 머리(둥근 부분)
    head = QRectF(s * 0.28, s * 0.12, s * 0.44, s * 0.44)
    p.drawEllipse(head)
    # 핀 몸통(아래로 뾰족한 삼각형/바늘)
    needle = QPolygonF([
        QPointF(s * 0.50, s * 0.92),
        QPointF(s * 0.40, s * 0.48),
        QPointF(s * 0.60, s * 0.48),
    ])
    p.drawPolygon(needle)
    p.end()
    return QIcon(pm)
