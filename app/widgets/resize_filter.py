"""프레임리스 창 가장자리 리사이즈 (OS 위임: startSystemResize).

QApplication에 설치하는 이벤트 필터. 자식 위젯이 창을 덮어도 최상위 창
가장자리 근처의 마우스를 감지해 OS 시스템 리사이즈를 시작한다. 멀티모니터/DPI/
스냅은 OS가 처리하므로 안전하다.
"""

from __future__ import annotations

from PyQt6.QtCore import QEvent, QObject, Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QAbstractButton, QApplication


class ResizeEdgeFilter(QObject):
    def __init__(self, window, border: int = 6):
        super().__init__(window)
        self._win = window
        self._border = border
        self._override = False

    # 커서 -----------------------------------------------------------------
    def _restore_cursor(self) -> None:
        if self._override:
            QApplication.restoreOverrideCursor()
            self._override = False

    def _set_cursor(self, edges) -> None:
        left = bool(edges & Qt.Edge.LeftEdge)
        right = bool(edges & Qt.Edge.RightEdge)
        top = bool(edges & Qt.Edge.TopEdge)
        bottom = bool(edges & Qt.Edge.BottomEdge)
        if (top and left) or (bottom and right):
            shape = Qt.CursorShape.SizeFDiagCursor
        elif (top and right) or (bottom and left):
            shape = Qt.CursorShape.SizeBDiagCursor
        elif left or right:
            shape = Qt.CursorShape.SizeHorCursor
        else:
            shape = Qt.CursorShape.SizeVerCursor
        cur = QCursor(shape)
        if self._override:
            QApplication.changeOverrideCursor(cur)
        else:
            QApplication.setOverrideCursor(cur)
            self._override = True

    # 가장자리 판정 --------------------------------------------------------
    def _edges_at(self, x: int, y: int, w: int, h: int):
        m = self._border
        parts = []
        if y <= m:
            parts.append(Qt.Edge.TopEdge)
        if y >= h - m:
            parts.append(Qt.Edge.BottomEdge)
        if x <= m:
            parts.append(Qt.Edge.LeftEdge)
        if x >= w - m:
            parts.append(Qt.Edge.RightEdge)
        if not parts:
            return None
        edges = parts[0]
        for p in parts[1:]:
            edges = edges | p
        return edges

    # 필터 -----------------------------------------------------------------
    def eventFilter(self, obj, event):
        et = event.type()
        if et not in (
            QEvent.Type.MouseMove,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.Leave,
        ):
            return False

        win = self._win
        try:
            if not win.isVisible() or win.isMaximized() or win.isFullScreen():
                self._restore_cursor()
                return False

            gp = QCursor.pos()
            local = win.mapFromGlobal(gp)
            x, y, w, h = local.x(), local.y(), win.width(), win.height()
            if x < 0 or y < 0 or x > w or y > h:
                self._restore_cursor()
                return False

            edges = self._edges_at(x, y, w, h)
            if edges is None:
                self._restore_cursor()
                return False

            # 버튼 위(타이틀바 닫기 등)는 리사이즈로 가로채지 않음
            if isinstance(QApplication.widgetAt(gp), QAbstractButton):
                self._restore_cursor()
                return False

            if et == QEvent.Type.MouseMove:
                if not (QApplication.mouseButtons() & Qt.MouseButton.LeftButton):
                    self._set_cursor(edges)
                return False

            if et == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                self._restore_cursor()
                handle = win.windowHandle()
                if handle is not None:
                    handle.startSystemResize(edges)
                    return True
        except Exception:
            self._restore_cursor()
        return False
