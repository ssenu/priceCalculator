"""설정 화면: 데이터 위치 · 관리자 비밀번호 · 동작 보호 옵션."""

from __future__ import annotations

import os
import subprocess
import sys

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import config, settings_store
from ..widgets import styled_dialog
from ..widgets.password_dialog import PasswordPromptDialog, SetPasswordDialog


class SettingsView(QWidget):
    goBack = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 20, 28, 24)
        outer.setSpacing(16)

        top = QHBoxLayout()
        back = QPushButton("뒤로가기")
        back.setObjectName("link")
        back.clicked.connect(self.goBack.emit)
        top.addWidget(back)
        top.addStretch(1)
        title = QLabel("설정")
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch(1)
        spacer = QLabel("")
        spacer.setFixedWidth(back.sizeHint().width())
        top.addWidget(spacer)
        outer.addLayout(top)

        # 보안 설정 패널
        sec = QFrame()
        sec.setObjectName("panel")
        sv = QVBoxLayout(sec)
        sv.setContentsMargins(22, 20, 22, 20)
        sv.setSpacing(14)

        # 관리자 비밀번호
        row1 = QHBoxLayout()
        self.pw_state = QLabel()
        self.pw_state.setObjectName("fieldName")
        row1.addWidget(self.pw_state)
        row1.addStretch(1)
        self.btn_set_pw = QPushButton("비밀번호 설정")
        self.btn_set_pw.setObjectName("primary")
        self.btn_set_pw.clicked.connect(self._set_password)
        row1.addWidget(self.btn_set_pw)
        sv.addLayout(row1)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #e8ebf2;")
        sv.addWidget(line)

        # 내역 삭제/프린트 시 비밀번호 확인
        row2 = QHBoxLayout()
        lbl2 = QLabel("내역 삭제/프린트 시 비밀번호 확인")
        lbl2.setObjectName("fieldName")
        row2.addWidget(lbl2)
        row2.addStretch(1)
        self.btn_toggle_req = QPushButton()
        self.btn_toggle_req.clicked.connect(self._toggle_require)
        row2.addWidget(self.btn_toggle_req)
        sv.addLayout(row2)

        hint = QLabel("이 설정과 비밀번호 변경은 관리자 비밀번호가 있어야 변경할 수 있습니다.")
        hint.setObjectName("fieldLabel")
        hint.setWordWrap(True)
        sv.addWidget(hint)

        outer.addWidget(sec)

        # 데이터 위치 패널
        panel = QFrame()
        panel.setObjectName("panel")
        pv = QVBoxLayout(panel)
        pv.setContentsMargins(22, 20, 22, 20)
        pv.setSpacing(12)
        pv.addWidget(QLabel("데이터 저장 위치"))
        path_lbl = QLabel(str(config.data_dir()))
        path_lbl.setObjectName("fieldLabel")
        path_lbl.setWordWrap(True)
        path_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        pv.addWidget(path_lbl)
        open_btn = QPushButton("저장 폴더 열기")
        open_btn.clicked.connect(self._open_folder)
        pv.addWidget(open_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        outer.addWidget(panel)

        outer.addStretch(1)

        # 우측 하단 제작자 표기
        credit = QLabel("made by ssenu")
        credit.setObjectName("credit")
        outer.addWidget(credit, alignment=Qt.AlignmentFlag.AlignRight)

    # 상태 갱신 -----------------------------------------------------------
    def refresh(self) -> None:
        if settings_store.has_password():
            self.pw_state.setText("관리자 비밀번호: 설정됨")
            self.btn_set_pw.setText("비밀번호 변경")
        else:
            self.pw_state.setText("관리자 비밀번호: 없음")
            self.btn_set_pw.setText("비밀번호 설정")

        on = settings_store.require_password_for_actions()
        self.btn_toggle_req.setText("사용중" if on else "사용안함")
        self.btn_toggle_req.setObjectName("primary" if on else "")
        # objectName 변경 후 스타일 재적용
        self.btn_toggle_req.style().unpolish(self.btn_toggle_req)
        self.btn_toggle_req.style().polish(self.btn_toggle_req)

    # 동작 ----------------------------------------------------------------
    def _set_password(self) -> None:
        dlg = SetPasswordDialog(self)
        try:
            if dlg.exec():
                self.refresh()
        finally:
            dlg.deleteLater()

    def _toggle_require(self) -> None:
        new_value = not settings_store.require_password_for_actions()
        if new_value and not settings_store.has_password():
            styled_dialog.info(self, "안내", "먼저 관리자 비밀번호를 설정하세요.")
            return
        # 변경 시 비밀번호 확인 (비밀번호가 설정돼 있으면)
        if not PasswordPromptDialog.confirm(self, "설정 변경을 위해 비밀번호를 입력하세요."):
            return
        settings_store.set_require_password_for_actions(new_value)
        self.refresh()

    def _open_folder(self) -> None:
        path = str(config.data_dir())
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except OSError:
            pass
