"""숫자 입력용 라인에딧. Enter로 다음 칸 이동, 포커스 시 전체선택(자동 삭제 없음)."""

from __future__ import annotations

import re

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import QLineEdit

_NON_DIGIT = re.compile(r"\D")


class AmountLineEdit(QLineEdit):
    """0 이상의 정수만 받는 입력창.

    - Enter/Return: 다음 위젯으로 포커스 이동 (returnPressed에 연결해 사용)
    - 포커스 진입 시 기존 값 전체 선택 → 덮어쓰기 쉽게 (값은 유지)
    - thousands=True: 입력하면서 천 단위 쉼표 자동 삽입
    """

    nextRequested = pyqtSignal()

    def __init__(self, max_value: int = 9_999_999, thousands: bool = False, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setObjectName("amount")
        self._select_on_release = False
        self._thousands = thousands
        self._max_digits = len(str(max_value))
        if thousands:
            # 쉼표 표시를 위해 정수 validator 대신 직접 포맷팅
            self.setMaxLength(self._max_digits + (self._max_digits - 1) // 3)
            self.textEdited.connect(self._reformat)
        else:
            self.setValidator(QIntValidator(0, max_value, self))
            self.setMaxLength(self._max_digits)

    def value(self) -> int:
        digits = _NON_DIGIT.sub("", self.text())
        return int(digits) if digits else 0

    def _reformat(self, _text: str) -> None:
        text = self.text()
        digits = _NON_DIGIT.sub("", text)[: self._max_digits]
        formatted = f"{int(digits):,}" if digits else ""
        if formatted == text:
            return
        # 커서 위치 보정: 커서 앞쪽 숫자 개수를 기준으로 재계산
        cursor = self.cursorPosition()
        digits_before = len(_NON_DIGIT.sub("", text[:cursor]))
        self.blockSignals(True)
        self.setText(formatted)
        self.blockSignals(False)
        # textEdited는 setText로 발생하지 않지만, 외부 textChanged는 발생하므로
        # 값 변경을 알리기 위해 수동으로 textChanged를 다시 쏘지 않아도 됨.
        pos = 0
        if digits_before > 0:
            count = 0
            for i, ch in enumerate(formatted):
                if ch.isdigit():
                    count += 1
                if count >= digits_before:
                    pos = i + 1
                    break
            else:
                pos = len(formatted)
        self.setCursorPosition(pos)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.nextRequested.emit()
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        # 포커스 진입 시 전체 선택 → 새 숫자 입력 시 기존 값이 통째로 교체됨.
        # (마우스 클릭으로 들어온 경우엔 release에서 커서가 재설정되므로 플래그로 처리)
        self._select_on_release = True
        self.selectAll()

    def mousePressEvent(self, event):
        already_focused = self.hasFocus()
        super().mousePressEvent(event)
        if not already_focused:
            # 이번 클릭이 포커스를 막 얻은 경우, release 후 전체선택 유지
            self._select_on_release = True

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._select_on_release:
            self._select_on_release = False
            self.selectAll()
