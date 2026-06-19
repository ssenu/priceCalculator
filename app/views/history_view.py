"""내역 화면 (스크린샷 3): 요약 카드 목록 + 삭제/프린트."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .. import settings_store, storage
from ..widgets import styled_dialog
from ..widgets.password_dialog import PasswordPromptDialog
from ..widgets.print_preview_dialog import PrintPreviewDialog
from ..widgets.record_card import RecordCard

MIN_COLUMNS = 2          # 기본(기존) 한 줄 2개
MAX_COLUMNS = 4          # 전체화면 시 최대 4개
CARD_MIN_WIDTH = 360     # 카드 1개 + 여백 기준 폭


class HistoryView(QWidget):
    """저장된 내역을 최신순으로 보여주고 삭제/인쇄."""

    goBack = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards: list[RecordCard] = []
        self._records: list = []
        self._columns = MIN_COLUMNS
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 20, 28, 24)
        outer.setSpacing(14)

        # 상단: 뒤로가기 + 제목
        top = QHBoxLayout()
        self.btn_back = QPushButton("뒤로가기")
        self.btn_back.setObjectName("link")
        self.btn_back.clicked.connect(self.goBack.emit)
        top.addWidget(self.btn_back)
        top.addStretch(1)
        title = QLabel("내역")
        title.setObjectName("title")
        top.addWidget(title)
        top.addStretch(1)
        # 좌우 균형용
        spacer = QLabel("")
        spacer.setFixedWidth(self.btn_back.sizeHint().width())
        top.addWidget(spacer)
        outer.addLayout(top)

        # 액션 바: 삭제 / 프린트 / 전체선택
        actions = QHBoxLayout()
        self.btn_delete = QPushButton("삭제")
        self.btn_delete.setObjectName("danger")
        self.btn_delete.clicked.connect(self._delete_selected)
        self.btn_print = QPushButton("프린트")
        self.btn_print.clicked.connect(self._print_selected)
        self.chk_all = QCheckBox("전체선택")
        self.chk_all.toggled.connect(self._toggle_all)
        actions.addWidget(self.btn_delete)
        actions.addWidget(self.btn_print)
        actions.addSpacing(12)
        actions.addWidget(self.chk_all)
        actions.addStretch(1)
        self.count_label = QLabel("")
        self.count_label.setObjectName("fieldLabel")
        actions.addWidget(self.count_label)
        outer.addLayout(actions)

        # 스크롤 영역
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(4, 4, 4, 4)
        self.grid.setHorizontalSpacing(16)
        self.grid.setVerticalSpacing(16)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.container)
        outer.addWidget(self.scroll, 1)

        self.empty_label = QLabel("저장된 내역이 없습니다.")
        self.empty_label.setObjectName("fieldLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    # 데이터 로드 ---------------------------------------------------------
    def reload(self) -> None:
        """디스크에서 다시 읽어 카드 갱신. 내용이 동일하면 재생성 생략(빠른 재진입)."""
        records = storage.load_records()  # 최신순
        sig = tuple(r.id for r in records)
        if sig == getattr(self, "_last_sig", None) and self.cards:
            # 기록이 그대로면 카드 재생성 없이 그대로 사용 (열 보정만)
            self._records = records
            self._apply_columns()
            return
        self._records = records
        self._last_sig = sig
        self._columns = self._calc_columns()
        self._populate()
        # 화면 전환 직후엔 위젯 크기가 아직 확정 전일 수 있어, 한 번 더 보정
        QTimer.singleShot(0, self._apply_columns)

    def _calc_columns(self) -> int:
        width = self.scroll.viewport().width()
        if width <= 0:
            return self._columns
        return max(MIN_COLUMNS, min(MAX_COLUMNS, width // CARD_MIN_WIDTH))

    def _apply_columns(self) -> None:
        new_cols = self._calc_columns()
        if new_cols != self._columns and self._records:
            self._columns = new_cols
            self._populate()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_columns()

    def _populate(self) -> None:
        self._clear_cards()
        cols = self._columns
        records = self._records
        self.count_label.setText(f"총 {len(records)}건")

        # 이전 행 stretch 초기화 + 열 stretch 재설정
        prev = getattr(self, "_stretch_row", None)
        if prev is not None:
            self.grid.setRowStretch(prev, 0)
        for c in range(MAX_COLUMNS):
            self.grid.setColumnStretch(c, 1 if c < cols else 0)

        if not records:
            self.grid.addWidget(self.empty_label, 0, 0, 1, cols)
            self.chk_all.setChecked(False)
            self._stretch_row = 1
            self.grid.setRowStretch(1, 1)
            return

        # 하루 단위로 묶어 연한 구분선(날짜 헤더)을 삽입
        row = 0
        col = 0
        current_date: str | None = None
        for rec in records:
            day = rec.date_display()
            if day != current_date:
                # 이전 그룹이 한 줄을 다 못 채웠으면 다음 줄로
                if col != 0:
                    row += 1
                    col = 0
                self.grid.addWidget(self._day_header(day), row, 0, 1, cols)
                row += 1
                current_date = day

            card = RecordCard(rec)
            self.grid.addWidget(card, row, col)
            self.cards.append(card)
            col += 1
            if col >= cols:
                col = 0
                row += 1
        # 남는 세로 공간을 맨 아래 빈 행이 흡수 → 카드가 위로 정렬, 세로로 늘어나지 않음
        self.grid.setRowStretch(row + 1, 1)
        self._stretch_row = row + 1
        self.chk_all.blockSignals(True)
        self.chk_all.setChecked(False)
        self.chk_all.blockSignals(False)

    def _day_header(self, day: str) -> QWidget:
        """하루 구분: 날짜 라벨 + 연한 가로선."""
        wrap = QWidget()
        h = QHBoxLayout(wrap)
        h.setContentsMargins(2, 10, 2, 2)
        h.setSpacing(10)
        label = QLabel(day)
        label.setStyleSheet("font-size: 15px; font-weight: 700; color: #8a93a3;")
        h.addWidget(label)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #e8ebf2;")
        h.addWidget(line, 1)
        return wrap

    def _clear_cards(self) -> None:
        while self.grid.count():
            item = self.grid.takeAt(0)
            w = item.widget()
            if w is not None and w is not self.empty_label:
                w.setParent(None)
                w.deleteLater()
            elif w is self.empty_label:
                w.setParent(None)
        self.cards = []

    # 선택 / 동작 ---------------------------------------------------------
    def _toggle_all(self, checked: bool) -> None:
        for card in self.cards:
            card.set_checked(checked)

    def _selected_records(self) -> list:
        return [c.record for c in self.cards if c.is_checked()]

    def _check_action_password(self) -> bool:
        """삭제/프린트 보호 설정이 켜져 있으면 비밀번호 확인."""
        if not settings_store.require_password_for_actions():
            return True
        return PasswordPromptDialog.confirm(self, "관리자 비밀번호를 입력하세요.")

    def _delete_selected(self) -> None:
        selected = self._selected_records()
        if not selected:
            styled_dialog.info(self, "삭제", "삭제할 내역을 선택하세요.")
            return
        if not self._check_action_password():
            return
        if styled_dialog.confirm(self, "삭제 확인", f"선택한 {len(selected)}건을 삭제하시겠습니까?"):
            storage.delete_records({r.id for r in selected})
            self.reload()

    def _print_selected(self) -> None:
        selected = self._selected_records()
        # 선택이 없으면 전체 출력
        records = selected if selected else [c.record for c in self.cards]
        if not records:
            styled_dialog.info(self, "프린트", "출력할 내역이 없습니다.")
            return
        if not self._check_action_password():
            return
        dialog = PrintPreviewDialog(records, parent=self)
        dialog.deleteRequested.connect(self._on_delete_after_print)
        try:
            dialog.exec()
        finally:
            dialog.deleteLater()

    def _on_delete_after_print(self, ids: set) -> None:
        storage.delete_records(ids)
        self.reload()
