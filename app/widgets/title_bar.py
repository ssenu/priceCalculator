"""커스텀 타이틀 바 (프레임리스 창용).

좌측: 설정 / 내역 · 우측: 고정핀 / 최소화 / 전체화면 / 닫기
타이틀 바 영역을 드래그하면 창 이동, 더블클릭하면 전체화면 토글.
"""

from __future__ import annotations

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton

from ..icons import make_close_icon, make_max_icon, make_min_icon, make_pin_icon

PIN_GREY = "#a8b0be"
PIN_BLACK = "#2b2f38"
WIN_ICON = "#5a6273"      # 창 버튼 기본 아이콘색
WIN_BTN_SIZE = QSize(40, 32)
WIN_ICON_SIZE = QSize(16, 16)


class HoverIconButton(QPushButton):
    """호버 시 아이콘이 바뀌는 버튼 (예: 닫기 X 흰색)."""

    def __init__(self, normal_icon, hover_icon, parent=None):
        super().__init__(parent)
        self._normal = normal_icon
        self._hover = hover_icon
        self.setIcon(self._normal)

    def enterEvent(self, event):
        self.setIcon(self._hover)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.setIcon(self._normal)
        super().leaveEvent(event)


class TitleBar(QFrame):
    openSettings = pyqtSignal()
    openHistory = pyqtSignal()
    pinToggled = pyqtSignal(bool)
    minimizeRequested = pyqtSignal()
    maximizeRequested = pyqtSignal()
    closeRequested = pyqtSignal()
    zoomIn = pyqtSignal()
    zoomOut = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(46)
        self._press_pos = None
        self._pressed = False
        self._build_ui()

    def _build_ui(self) -> None:
        h = QHBoxLayout(self)
        h.setContentsMargins(14, 6, 10, 6)
        h.setSpacing(6)

        # 좌측: 설정 / 내역
        btn_settings = QPushButton("설정")
        btn_settings.setObjectName("link")
        btn_settings.clicked.connect(self.openSettings.emit)
        btn_history = QPushButton("내역")
        btn_history.setObjectName("link")
        btn_history.clicked.connect(self.openHistory.emit)
        h.addWidget(btn_settings)
        h.addWidget(btn_history)

        # 확대/축소 (− 100% +) — 내역 오른쪽(좌측 고정)이라 창 크기가 바뀌어도 위치 고정
        h.addSpacing(10)
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setObjectName("zoomBtn")
        self.btn_zoom_out.setFixedSize(30, 30)
        self.btn_zoom_out.setToolTip("축소")
        self.btn_zoom_out.clicked.connect(self.zoomOut.emit)
        self.zoom_label = QLabel("100%")
        self.zoom_label.setObjectName("zoomLabel")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setFixedWidth(48)
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setObjectName("zoomBtn")
        self.btn_zoom_in.setFixedSize(30, 30)
        self.btn_zoom_in.setToolTip("확대")
        self.btn_zoom_in.clicked.connect(self.zoomIn.emit)
        h.addWidget(self.btn_zoom_out)
        h.addWidget(self.zoom_label)
        h.addWidget(self.btn_zoom_in)

        h.addStretch(1)

        # 우측: 고정핀
        self.btn_pin = QPushButton()
        self.btn_pin.setObjectName("pin")
        self.btn_pin.setCheckable(True)
        self.btn_pin.setToolTip("창 위에 고정")
        self.btn_pin.setFixedSize(36, 32)
        self.btn_pin.setIconSize(QSize(20, 20))
        self._icon_pin_off = make_pin_icon(PIN_GREY)
        self._icon_pin_on = make_pin_icon(PIN_BLACK)
        self.btn_pin.setIcon(self._icon_pin_off)
        self.btn_pin.toggled.connect(self._on_pin_toggled)
        h.addWidget(self.btn_pin)

        # 최소화 / 전체화면 / 닫기 (직접 그린 아이콘, 크기 통일)
        self.btn_min = self._win_button(make_min_icon(WIN_ICON), "winBtn", "최소화")
        self.btn_min.clicked.connect(self.minimizeRequested.emit)
        self.btn_max = self._win_button(make_max_icon(WIN_ICON), "winBtn", "전체화면")
        self.btn_max.clicked.connect(self.maximizeRequested.emit)
        self.btn_close = HoverIconButton(
            make_close_icon(WIN_ICON), make_close_icon("#ffffff")
        )
        self.btn_close.setObjectName("winClose")
        self.btn_close.setToolTip("닫기")
        self.btn_close.setFixedSize(WIN_BTN_SIZE)
        self.btn_close.setIconSize(WIN_ICON_SIZE)
        self.btn_close.clicked.connect(self.closeRequested.emit)
        h.addWidget(self.btn_min)
        h.addWidget(self.btn_max)
        h.addWidget(self.btn_close)

    def _win_button(self, icon, obj: str, tip: str) -> QPushButton:
        b = QPushButton()
        b.setIcon(icon)
        b.setIconSize(WIN_ICON_SIZE)
        b.setObjectName(obj)
        b.setToolTip(tip)
        b.setFixedSize(WIN_BTN_SIZE)
        return b

    def _on_pin_toggled(self, checked: bool) -> None:
        self.btn_pin.setIcon(self._icon_pin_on if checked else self._icon_pin_off)
        self.pinToggled.emit(checked)

    def set_zoom_label(self, scale: float) -> None:
        self.zoom_label.setText(f"{round(scale * 100)}%")

    # 창 드래그 이동 (OS 위임: startSystemMove) ---------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position().toPoint()
            self._pressed = True
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # 임계값 넘으면 한 번만 OS 시스템 이동 시작 (멀티모니터/DPI 안전)
        if self._pressed and event.buttons() & Qt.MouseButton.LeftButton:
            if self._press_pos is not None:
                moved = (event.position().toPoint() - self._press_pos).manhattanLength()
                if moved >= 5:
                    self._pressed = False
                    self._start_system_move()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self._press_pos = None
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = False
            self.maximizeRequested.emit()
        super().mouseDoubleClickEvent(event)

    def _start_system_move(self) -> None:
        win = self.window()
        if win.isMaximized():
            win.showNormal()
        handle = win.windowHandle()
        if handle is not None:
            handle.startSystemMove()
