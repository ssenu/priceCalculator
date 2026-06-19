"""메인 윈도우: 프레임리스 + 커스텀 타이틀바 + QStackedWidget 화면 전환."""

from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from . import config, settings_store
from .style import MAX_SCALE, MIN_SCALE, build_stylesheet
from .views.history_view import HistoryView
from .views.main_view import MainView
from .views.settings_view import SettingsView
from .widgets.resize_filter import ResizeEdgeFilter
from .widgets.title_bar import TitleBar

# 배율 1.0 기준 기본 창 크기
BASE_W, BASE_H = 960, 760
BASE_MIN_W, BASE_MIN_H = 840, 640


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(config.APP_NAME)
        _icon = config.icon_path()
        if _icon.exists():
            from PyQt6.QtGui import QIcon

            self.setWindowIcon(QIcon(str(_icon)))
        # 네이티브 타이틀바 제거 (커스텀 타이틀바 사용)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        root = QWidget()
        root.setObjectName("root")
        layout = QVBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 커스텀 타이틀바
        self.title_bar = TitleBar()
        layout.addWidget(self.title_bar)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        # 화면들 (한 번만 생성, 재사용)
        self.main_view = MainView()
        self.history_view = HistoryView()
        self.settings_view = SettingsView()
        self.stack.addWidget(self.main_view)      # 0
        self.stack.addWidget(self.history_view)   # 1
        self.stack.addWidget(self.settings_view)  # 2

        # 타이틀바 시그널 연결
        self.title_bar.openHistory.connect(self._show_history)
        self.title_bar.openSettings.connect(self._show_settings)
        self.title_bar.pinToggled.connect(self._set_always_on_top)
        self.title_bar.minimizeRequested.connect(self.showMinimized)
        self.title_bar.maximizeRequested.connect(self._toggle_maximize)
        self.title_bar.closeRequested.connect(self.close)
        self.title_bar.zoomIn.connect(lambda: self._change_scale(0.1))
        self.title_bar.zoomOut.connect(lambda: self._change_scale(-0.1))

        # 화면 내 뒤로가기
        self.history_view.goBack.connect(self._show_main)
        self.settings_view.goBack.connect(self._show_main)

        # 타이틀바는 배율 영향 X (창 전체엔 기본 스타일, 콘텐츠 stack에만 배율 스타일)
        self.setStyleSheet(build_stylesheet(1.0))

        # UI 배율 (저장된 값 적용) + 그 배율에 맞춰 초기 창 크기 설정
        self._scale = max(MIN_SCALE, min(MAX_SCALE, settings_store.get_ui_scale()))
        self._apply_scale()
        self.resize(round(BASE_W * self._scale), round(BASE_H * self._scale))

        # 가장자리 리사이즈 (OS 위임) — QApplication에 필터 1회 설치
        self._resize_filter = ResizeEdgeFilter(self)
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self._resize_filter)

    # UI 배율 -------------------------------------------------------------
    def _apply_scale(self) -> None:
        # 콘텐츠(stack)에만 배율 적용 → 타이틀바(설정/내역/배율/창버튼)는 그대로
        self.stack.setStyleSheet(build_stylesheet(self._scale))
        self.title_bar.set_zoom_label(self._scale)
        self.setMinimumSize(round(BASE_MIN_W * self._scale), round(BASE_MIN_H * self._scale))
        self.main_view.apply_scale(self._scale)

    def _change_scale(self, delta: float) -> None:
        old = self._scale
        new = round(max(MIN_SCALE, min(MAX_SCALE, old + delta)), 2)
        if abs(new - old) < 1e-3:
            return
        self._scale = new
        self._apply_scale()
        settings_store.set_ui_scale(new)
        # 배율에 맞춰 창 크기도 비례 조절 (잘림 방지)
        if not self.isMaximized() and not self.isFullScreen():
            ratio = new / old
            screen = self.screen().availableGeometry() if self.screen() else None
            w = round(self.width() * ratio)
            h = round(self.height() * ratio)
            if screen is not None:
                w = min(w, screen.width())
                h = min(h, screen.height())
            self.resize(w, h)

    # 둥근 모서리 (Windows 11 DWM) ----------------------------------------
    def showEvent(self, event):
        super().showEvent(event)
        # 핀 토글 등으로 네이티브 창이 재생성되면 모서리가 풀리므로 매번 재적용
        self._apply_round_corners()

    def _apply_round_corners(self) -> None:
        if not sys.platform.startswith("win"):
            return
        try:
            import ctypes
            from ctypes import byref, c_int, sizeof, windll, wintypes

            fn = windll.dwmapi.DwmSetWindowAttribute
            fn.restype = ctypes.c_long
            fn.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
            hwnd = int(self.winId())
            # DWMWA_WINDOW_CORNER_PREFERENCE = 33, DWMWCP_ROUND = 2
            pref = c_int(2)
            fn(hwnd, 33, byref(pref), sizeof(pref))
        except Exception:
            pass

    def _toggle_maximize(self) -> None:
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def _set_always_on_top(self, on: bool) -> None:
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, on)
        # 플래그 변경 후에는 다시 show 해야 적용됨 (프레임리스 상태 유지)
        self.show()

    def _show_main(self) -> None:
        self.stack.setCurrentWidget(self.main_view)

    def _show_history(self) -> None:
        # 화면을 먼저 전환(올바른 폭 확보) 후 로드 → 더블 빌드/지연 감소
        self.stack.setCurrentWidget(self.history_view)
        self.history_view.reload()

    def _show_settings(self) -> None:
        self.settings_view.refresh()
        self.stack.setCurrentWidget(self.settings_view)
