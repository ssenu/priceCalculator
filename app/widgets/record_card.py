"""내역 요약 카드 위젯 (스크린샷 3)."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .. import config
from ..models import Record


def _denom_name(denom: int) -> str:
    if denom >= 10000:
        return f"{denom // 10000}만원"
    if denom >= 1000:
        return f"{denom // 1000}천원"
    return f"{denom}원"


class RecordCard(QFrame):
    """체크박스 + 시재 요약을 보여주는 카드."""

    def __init__(self, record: Record, parent=None):
        super().__init__(parent)
        self.record = record
        self.setObjectName("recordCard")
        self.setProperty("selected", False)
        # 카드가 세로로 늘어나지 않도록 (내역 적을 때 길어지는 문제 방지)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 12)
        root.setSpacing(6)

        # 상단: 체크박스(좌) + 날짜(중앙)
        head = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.toggled.connect(self._on_toggle)
        head.addWidget(self.checkbox, 0, Qt.AlignmentFlag.AlignTop)

        date_lbl = QLabel(self.record.datetime_display())
        date_lbl.setObjectName("cardDate")
        date_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        head.addWidget(date_lbl, 1)
        # 우측 균형용 여백
        spacer = QLabel("")
        spacer.setFixedWidth(18)
        head.addWidget(spacer, 0)
        root.addLayout(head)

        # 본문: 좌(단위/매수) | 우(데이터/금고/차액/메모)
        body = QHBoxLayout()
        body.setSpacing(12)

        # 좌측: 단위(우정렬) + 매수(좌정렬) → 매수 숫자 세로 정렬
        left_grid = QGridLayout()
        left_grid.setContentsMargins(12, 0, 0, 0)  # 좌측 여백 확보
        left_grid.setHorizontalSpacing(10)
        left_grid.setVerticalSpacing(5)
        for i, denom in enumerate(config.DENOMINATIONS):
            cnt = self.record.counts.get(denom, 0)
            # 단위명: 색상 알약(5만/1만)을 위해 텍스트에 hug → [stretch][라벨]
            name_lbl = QLabel(_denom_name(denom))
            name_lbl.setObjectName("cardDenom")
            name_lbl.setProperty("denom", str(denom))
            name_wrap = QHBoxLayout()
            name_wrap.setContentsMargins(0, 0, 0, 0)
            name_wrap.addStretch(1)
            name_wrap.addWidget(name_lbl)
            cnt_lbl = self._small(str(cnt))
            cnt_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            left_grid.addLayout(name_wrap, i, 0)
            left_grid.addWidget(cnt_lbl, i, 1)
        left_grid.setColumnStretch(1, 1)
        left_box = QWidget()
        left_box.setLayout(left_grid)
        body.addWidget(left_box, 1)

        # 우측: 데이터/금고/차액/메모 (모두 굵게)
        right_box = QVBoxLayout()
        right_box.setSpacing(3)
        right_box.addWidget(self._bold(f"데이터  {self.record.data:,}"))
        right_box.addWidget(self._bold(f"금고  {self.record.safe:,}"))
        diff_lbl = QLabel(f"차액  {self.record.diff:,}")
        diff_color = "#e5484d" if self.record.diff < 0 else "#2f9e44"
        diff_lbl.setStyleSheet(f"font-size: 14px; color: {diff_color}; font-weight: 700;")
        right_box.addWidget(diff_lbl)
        right_box.addSpacing(12)  # 차액과 메모 구분
        right_box.addWidget(self._bold("메모"))
        memo_val = self._bold(self.record.memo or "")
        memo_val.setWordWrap(True)
        right_box.addWidget(memo_val)
        right_box.addStretch(1)
        right_wrap = QWidget()
        right_wrap.setLayout(right_box)
        body.addWidget(right_wrap, 1)

        root.addLayout(body)

        # 하단: 이름 / 근무시간
        foot = QHBoxLayout()
        name_lbl = QLabel(self.record.name or "-")
        name_lbl.setObjectName("cardFoot")
        foot.addStretch(1)
        foot.addWidget(name_lbl)
        foot.addStretch(1)
        shift_lbl = QLabel(self.record.shift or "")
        shift_lbl.setObjectName("cardFoot")
        foot.addWidget(shift_lbl)
        foot.addStretch(1)
        root.addLayout(foot)

    @staticmethod
    def _small(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 14px;")
        return lbl

    @staticmethod
    def _bold(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 14px; font-weight: 700;")
        return lbl

    def _on_toggle(self, checked: bool) -> None:
        self.setProperty("selected", checked)
        self.style().unpolish(self)
        self.style().polish(self)

    def is_checked(self) -> bool:
        return self.checkbox.isChecked()

    def set_checked(self, value: bool) -> None:
        self.checkbox.setChecked(value)
