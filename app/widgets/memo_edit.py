"""메모 입력용 멀티라인 위젯. Tab=포커스 이동, Enter=제출(Shift+Enter=줄바꿈)."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QPlainTextEdit


class MemoTextEdit(QPlainTextEdit):
    submitted = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Tab → 탭 문자 입력이 아니라 다음 위젯으로 포커스 이동
        self.setTabChangesFocus(True)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                # Shift+Enter → 줄바꿈
                super().keyPressEvent(event)
            else:
                # Enter → 저장 제출
                self.submitted.emit()
            return
        super().keyPressEvent(event)
