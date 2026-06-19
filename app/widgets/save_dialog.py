"""저장 다이얼로그: 이름/근무시간 입력 후 저장 (프레임리스 커스텀)."""

from __future__ import annotations

from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import config, settings_store
from ..style import DANGER, SUCCESS
from .flow_layout import FlowLayout
from .styled_dialog import StyledDialog


class SaveDialog(StyledDialog):
    """차액 안내 + 이름/근무시간 입력."""

    def __init__(self, diff: int, parent=None):
        super().__init__("저장", parent)
        self.setMinimumWidth(440)
        self._build_ui(diff)

    def _build_ui(self, diff: int) -> None:
        v = self.body

        # 이름 + 근무시간
        row = QHBoxLayout()
        row.setSpacing(12)
        name_box = QVBoxLayout()
        name_box.addWidget(self._label("이름"))
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("이름 입력")
        name_box.addWidget(self.name_edit)
        row.addLayout(name_box, 1)

        shift_box = QVBoxLayout()
        shift_box.addWidget(self._label("근무시간"))
        self.shift_combo = QComboBox()
        self.shift_combo.addItems(config.SHIFTS)
        shift_box.addWidget(self.shift_combo)
        row.addLayout(shift_box, 1)
        v.addLayout(row)

        # 이전에 쓴 이름 칩 (클릭=입력, × = 삭제)
        self._chips_host = QWidget()
        self._chips_layout = FlowLayout(self._chips_host, spacing=6)
        v.addWidget(self._chips_host)
        self._refresh_chips()

        # 저장 시간 (자동) + 시각대별 근무시간 기본값
        now = datetime.now()
        self.shift_combo.setCurrentText(config.default_shift(now))
        wd = config.WEEKDAYS_KO[now.weekday()]
        time_text = f"{now.year}/{now.month:02d}/{now.day:02d} {wd}요일 {now.hour:02d}:{now.minute:02d}"
        time_label = QLabel(f"저장 시간   {time_text}")
        time_label.setObjectName("fieldLabel")
        v.addWidget(time_label)

        # 안내 문구 (차액 금액은 음수=빨강 / 양수=초록)
        amount_color = DANGER if diff < 0 else SUCCESS
        amount = config.format_won(diff)
        msg = QLabel(
            f'차액이 <span style="color:{amount_color}; font-weight:800;">{amount}</span> '
            "입니다. 저장하시겠습니까?"
        )
        msg.setObjectName("confirmMsg")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setWordWrap(True)
        v.addWidget(msg)

        # 버튼
        btns = QHBoxLayout()
        btns.addStretch(1)
        cancel = QPushButton("취소")
        cancel.setAutoDefault(False)
        cancel.clicked.connect(self.reject)
        self.save_btn = QPushButton("저장하기")
        self.save_btn.setObjectName("primary")
        self.save_btn.setAutoDefault(False)
        self.save_btn.clicked.connect(self.accept)
        btns.addWidget(cancel)
        btns.addWidget(self.save_btn)
        v.addLayout(btns)

        # 탭 순서: 이름 → 근무시간 → 저장하기 → 취소
        self.setTabOrder(self.name_edit, self.shift_combo)
        self.setTabOrder(self.shift_combo, self.save_btn)
        self.setTabOrder(self.save_btn, cancel)
        # 이름에서 Enter → 근무시간 콤보로 이동하며 목록 펼침
        self.name_edit.returnPressed.connect(self._focus_shift)
        self.name_edit.setFocus()

    def _refresh_chips(self) -> None:
        # 기존 칩 제거
        while self._chips_layout.count():
            item = self._chips_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        names = settings_store.get_names()
        self._chips_host.setVisible(bool(names))
        for name in names:
            self._chips_layout.addWidget(self._make_chip(name))

    def _make_chip(self, name: str) -> QFrame:
        chip = QFrame()
        chip.setObjectName("nameChip")
        cl = QHBoxLayout(chip)
        cl.setContentsMargins(10, 2, 4, 2)
        cl.setSpacing(2)
        name_btn = QPushButton(name)
        name_btn.setObjectName("chipName")
        name_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        name_btn.clicked.connect(lambda _=False, n=name: self.name_edit.setText(n))
        del_btn = QPushButton("×")
        del_btn.setObjectName("chipDel")
        del_btn.setFixedSize(20, 20)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setToolTip("이름 삭제")
        del_btn.clicked.connect(lambda _=False, n=name: self._remove_name(n))
        cl.addWidget(name_btn)
        cl.addWidget(del_btn)
        return chip

    def _remove_name(self, name: str) -> None:
        settings_store.remove_name(name)
        self._refresh_chips()

    def _focus_shift(self) -> None:
        self.shift_combo.setFocus()
        self.shift_combo.showPopup()

    def keyPressEvent(self, event):
        # 저장 버튼이 포커스일 때만 Enter로 저장 (콤보/그 외에선 저장 안 함)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.focusWidget() is self.save_btn:
                self.accept()
            return
        super().keyPressEvent(event)

    @staticmethod
    def _label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("fieldLabel")
        return lbl

    def result_values(self) -> tuple[str, str]:
        return (
            self.name_edit.text().strip(),
            self.shift_combo.currentText(),
        )
