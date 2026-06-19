"""프레임리스 커스텀 다이얼로그 베이스 + 메시지 헬퍼.

메인 창과 동일하게 OS 타이틀바 없이 둥근 모서리·테두리·커스텀 헤더를 사용한다.
헤더 드래그는 startSystemMove로 OS에 위임(멀티모니터 안전).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..icons import make_close_icon
from .title_bar import WIN_BTN_SIZE, WIN_ICON, WIN_ICON_SIZE, HoverIconButton


class _DragHeader(QFrame):
    """드래그하면 창을 이동하는 헤더 (startSystemMove)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._press = False
        self._pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press = True
            self._pos = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press and event.buttons() & Qt.MouseButton.LeftButton and self._pos is not None:
            if (event.position().toPoint() - self._pos).manhattanLength() >= 5:
                self._press = False
                handle = self.window().windowHandle()
                if handle is not None:
                    handle.startSystemMove()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._press = False
        super().mouseReleaseEvent(event)


class StyledDialog(QDialog):
    """프레임리스 + 둥근모서리 + 커스텀 헤더 다이얼로그.

    서브클래스는 self.body(QVBoxLayout)에 내용을 추가한다.
    """

    def __init__(self, title: str = "", parent=None, show_close: bool = True):
        super().__init__(parent)
        self.setModal(True)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        root = QFrame()
        root.setObjectName("dialogRoot")
        outer.addWidget(root)

        rv = QVBoxLayout(root)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)

        header = _DragHeader()
        header.setObjectName("dialogHeader")
        header.setFixedHeight(44)
        hl = QHBoxLayout(header)
        hl.setContentsMargins(18, 6, 10, 6)
        self._title_lbl = QLabel(title)
        self._title_lbl.setObjectName("dialogTitle")
        hl.addWidget(self._title_lbl)
        hl.addStretch(1)
        if show_close:
            close = HoverIconButton(make_close_icon(WIN_ICON), make_close_icon("#ffffff"))
            close.setObjectName("winClose")
            close.setFixedSize(WIN_BTN_SIZE)
            close.setIconSize(WIN_ICON_SIZE)
            close.setToolTip("닫기")
            close.clicked.connect(self.reject)
            hl.addWidget(close)
        rv.addWidget(header)

        body_wrap = QWidget()
        self.body = QVBoxLayout(body_wrap)
        self.body.setContentsMargins(22, 14, 22, 20)
        self.body.setSpacing(14)
        rv.addWidget(body_wrap, 1)


class _MessageDialog(StyledDialog):
    def __init__(self, title: str, text: str, parent=None, mode: str = "info"):
        super().__init__(title, parent, show_close=True)
        self.setMinimumWidth(340)

        lbl = QLabel(text)
        lbl.setObjectName("dialogText")
        lbl.setWordWrap(True)
        self.body.addWidget(lbl)

        btns = QHBoxLayout()
        btns.addStretch(1)
        if mode == "confirm":
            no = QPushButton("아니오")
            no.setAutoDefault(False)
            no.clicked.connect(self.reject)
            yes = QPushButton("예")
            yes.setObjectName("primary")
            yes.setAutoDefault(False)
            yes.clicked.connect(self.accept)
            btns.addWidget(no)
            btns.addWidget(yes)
            self._default_btn = yes
        else:
            ok = QPushButton("확인")
            ok.setObjectName("primary")
            ok.setAutoDefault(False)
            ok.clicked.connect(self.accept)
            btns.addWidget(ok)
            self._default_btn = ok
        self.body.addLayout(btns)
        self._default_btn.setFocus()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._default_btn.click()
            return
        super().keyPressEvent(event)


def info(parent, title: str, text: str) -> None:
    dlg = _MessageDialog(title, text, parent, "info")
    try:
        dlg.exec()
    finally:
        dlg.deleteLater()


def confirm(parent, title: str, text: str) -> bool:
    dlg = _MessageDialog(title, text, parent, "confirm")
    try:
        return dlg.exec() == QDialog.DialogCode.Accepted
    finally:
        dlg.deleteLater()
