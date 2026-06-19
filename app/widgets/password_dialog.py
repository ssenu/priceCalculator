"""비밀번호 입력 / 설정 다이얼로그 (프레임리스 커스텀)."""

from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton

from .. import settings_store
from . import styled_dialog
from .styled_dialog import StyledDialog


class PasswordPromptDialog(StyledDialog):
    """기존 관리자 비밀번호를 입력받아 검증."""

    def __init__(self, prompt: str = "관리자 비밀번호를 입력하세요.", parent=None):
        super().__init__("비밀번호 확인", parent)
        self.setMinimumWidth(360)
        v = self.body

        v.addWidget(QLabel(prompt))
        self.edit = QLineEdit()
        self.edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.edit.setPlaceholderText("비밀번호")
        self.edit.returnPressed.connect(self._try_accept)
        v.addWidget(self.edit)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = QPushButton("취소")
        cancel.setAutoDefault(False)
        cancel.clicked.connect(self.reject)
        ok = QPushButton("확인")
        ok.setObjectName("primary")
        ok.setAutoDefault(False)
        ok.clicked.connect(self._try_accept)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        v.addLayout(btns)
        self.edit.setFocus()

    def _try_accept(self) -> None:
        if settings_store.verify_password(self.edit.text()):
            self.accept()
        else:
            styled_dialog.info(self, "오류", "비밀번호가 올바르지 않습니다.")
            self.edit.selectAll()
            self.edit.setFocus()

    @staticmethod
    def confirm(parent, prompt: str = "관리자 비밀번호를 입력하세요.") -> bool:
        """비밀번호가 설정돼 있으면 검증, 없으면 통과(True)."""
        if not settings_store.has_password():
            return True
        dlg = PasswordPromptDialog(prompt, parent)
        try:
            return dlg.exec() == QDialog.DialogCode.Accepted
        finally:
            dlg.deleteLater()


class SetPasswordDialog(StyledDialog):
    """관리자 비밀번호 설정/변경 (기존 비밀번호가 있으면 먼저 확인)."""

    def __init__(self, parent=None):
        super().__init__("관리자 비밀번호 설정", parent)
        self.setMinimumWidth(380)
        v = self.body

        self._has_existing = settings_store.has_password()
        if self._has_existing:
            v.addWidget(QLabel("현재 비밀번호"))
            self.current_edit = QLineEdit()
            self.current_edit.setEchoMode(QLineEdit.EchoMode.Password)
            v.addWidget(self.current_edit)

        v.addWidget(QLabel("새 비밀번호"))
        self.new_edit = QLineEdit()
        self.new_edit.setEchoMode(QLineEdit.EchoMode.Password)
        v.addWidget(self.new_edit)

        v.addWidget(QLabel("새 비밀번호 확인"))
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        v.addWidget(self.confirm_edit)

        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = QPushButton("취소")
        cancel.setAutoDefault(False)
        cancel.clicked.connect(self.reject)
        ok = QPushButton("저장")
        ok.setObjectName("primary")
        ok.setAutoDefault(False)
        ok.clicked.connect(self._try_save)
        btns.addWidget(cancel)
        btns.addWidget(ok)
        v.addLayout(btns)

        # Tab 순서 + 시작 포커스 + Enter 제출
        first = self.current_edit if self._has_existing else self.new_edit
        if self._has_existing:
            self.setTabOrder(self.current_edit, self.new_edit)
            self.current_edit.returnPressed.connect(self._try_save)
        self.setTabOrder(self.new_edit, self.confirm_edit)
        self.new_edit.returnPressed.connect(self._try_save)
        self.confirm_edit.returnPressed.connect(self._try_save)
        first.setFocus()

    def _try_save(self) -> None:
        if self._has_existing and not settings_store.verify_password(self.current_edit.text()):
            styled_dialog.info(self, "오류", "현재 비밀번호가 올바르지 않습니다.")
            return
        new = self.new_edit.text()
        if not new:
            styled_dialog.info(self, "오류", "새 비밀번호를 입력하세요.")
            return
        if new != self.confirm_edit.text():
            styled_dialog.info(self, "오류", "새 비밀번호가 일치하지 않습니다.")
            return
        settings_store.set_password(new)
        styled_dialog.info(self, "완료", "비밀번호가 설정되었습니다.")
        self.accept()
