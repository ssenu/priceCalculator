"""메인 시재 입력 화면 (스크린샷 1)."""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .. import config
from ..models import Record, compute_diff, compute_safe
from ..widgets import styled_dialog
from ..widgets.amount_edit import AmountLineEdit
from ..widgets.memo_edit import MemoTextEdit
from ..widgets.save_dialog import SaveDialog

# 전체화면에서도 깨지지 않도록 본문 최대 폭 제한 (가로 중앙 정렬)
CONTENT_MAX_WIDTH = 1000


class MainView(QWidget):
    """지폐 매수 입력 → 금고/차액 자동 계산 → 저장."""

    recordSaved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.count_edits: dict[int, AmountLineEdit] = {}
        self._prev_diff: int | None = None
        self._build_ui()
        self._wire_navigation()
        self._update_prev_diff()
        self._recalculate()

    # UI ------------------------------------------------------------------
    def _build_ui(self) -> None:
        # 상하/좌우 모두 중앙 정렬 → 전체화면에서도 본문이 늘어나지 않고 정중앙에 위치
        root_v = QVBoxLayout(self)
        root_v.setContentsMargins(0, 0, 0, 0)
        root_v.addStretch(1)

        hrow = QHBoxLayout()
        hrow.addStretch(1)
        content = QWidget()
        content.setMaximumWidth(CONTENT_MAX_WIDTH)
        self._content = content
        hrow.addWidget(content, 0)
        hrow.addStretch(1)
        root_v.addLayout(hrow, 0)
        root_v.addStretch(1)

        cv = QVBoxLayout(content)
        cv.setContentsMargins(28, 20, 28, 24)
        cv.setSpacing(16)

        title = QLabel(config.APP_NAME)
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cv.addWidget(title)

        # 본문: 좌(지폐 입력) / 우(데이터/금고/차액)
        body = QHBoxLayout()
        body.setSpacing(20)
        body.addWidget(self._build_count_panel(), 3)
        body.addWidget(self._build_summary_panel(), 2)
        cv.addLayout(body, 1)

    def _build_count_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        grid = QGridLayout(panel)
        grid.setContentsMargins(28, 22, 28, 22)
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(16)

        h1 = QLabel("지폐")
        h1.setObjectName("sectionHeader")
        h2 = QLabel("장수")
        h2.setObjectName("sectionHeader")
        grid.addWidget(h1, 0, 0)
        grid.addWidget(h2, 0, 1)

        row = 1
        for denom in config.DENOMINATIONS:
            # 지폐(1천원 이상)와 동전(500원 이하) 사이에 구분선
            if denom == 500:
                divider = QFrame()
                divider.setObjectName("denomDivider")
                divider.setFrameShape(QFrame.Shape.HLine)
                grid.addWidget(divider, row, 0, 1, 2)
                row += 1

            name = self._denom_name(denom)
            lbl = QLabel(name)
            lbl.setObjectName("denomLabel")
            lbl.setProperty("denom", str(denom))
            # 라벨이 텍스트에 맞게 알약처럼 보이도록 좌측 hug
            lbl_wrap = QHBoxLayout()
            lbl_wrap.setContentsMargins(0, 0, 0, 0)
            lbl_wrap.addWidget(lbl)
            lbl_wrap.addStretch(1)
            edit = AmountLineEdit()
            edit.setPlaceholderText("0")
            edit.textChanged.connect(self._recalculate)
            self.count_edits[denom] = edit
            grid.addLayout(lbl_wrap, row, 0)
            grid.addWidget(edit, row, 1)
            row += 1

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        return panel

    def _build_summary_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("panel")
        v = QVBoxLayout(panel)
        v.setContentsMargins(28, 22, 28, 22)
        # 데이터/금고/차액 사이는 조금 좁혀 새 문장 공간 확보 (메모 크기는 유지)
        v.setSpacing(16)

        # 데이터 (수동 입력)
        v.addLayout(self._row_label("데이터", self._make_data_edit()))
        # 금고 (자동)
        self.lbl_safe = QLabel("0원")
        self.lbl_safe.setObjectName("valueBig")
        v.addLayout(self._row_label("금고", self.lbl_safe))
        # 차액 (자동)
        self.lbl_diff = QLabel("0원")
        self.lbl_diff.setObjectName("diffPos")
        v.addLayout(self._row_label("차액", self.lbl_diff))

        # 이전 근무자의 차액 안내 (차액과 메모 사이)
        self.lbl_prev_diff = QLabel()
        self.lbl_prev_diff.setObjectName("prevDiff")
        self.lbl_prev_diff.setTextFormat(Qt.TextFormat.RichText)
        self.lbl_prev_diff.setWordWrap(True)
        v.addWidget(self.lbl_prev_diff)

        # 메모 (차액 아래, 멀티라인) — 비우면 "동일"로 저장. 저장 버튼 위까지 확장
        memo_label = QLabel("메모")
        memo_label.setObjectName("fieldName")
        v.addWidget(memo_label)
        self.memo_edit = MemoTextEdit()
        self.memo_edit.setPlaceholderText(config.DEFAULT_MEMO)
        self.memo_edit.submitted.connect(self._on_save)  # Enter → 저장
        v.addWidget(self.memo_edit, 1)

        self.btn_save = QPushButton("저장")
        self.btn_save.setObjectName("primary")
        self.btn_save.setMinimumSize(140, 56)
        self.btn_save.clicked.connect(self._on_save)
        v.addWidget(self.btn_save, alignment=Qt.AlignmentFlag.AlignRight)
        # 메모에서 Tab → 저장 버튼으로 포커스 이동
        self.setTabOrder(self.memo_edit, self.btn_save)
        return panel

    def apply_scale(self, scale: float) -> None:
        # 배율에 맞춰 본문 최대 폭도 확대 → 확대 시 가로 여백/잘림 방지
        self._content.setMaximumWidth(round(CONTENT_MAX_WIDTH * scale))

    def _update_prev_diff(self) -> None:
        """가장 최근 저장된 기록(이전 근무자)의 차액을 안내 문장으로 표시."""
        from .. import storage
        from ..style import DANGER, SUCCESS

        records = storage.load_records()  # 최신순
        if not records:
            self._prev_diff = None
            self.lbl_prev_diff.setText("이전 근무자의 기록이 없습니다.")
        else:
            self._prev_diff = records[0].diff
            color = DANGER if self._prev_diff < 0 else SUCCESS
            amount = config.format_won(self._prev_diff)
            self.lbl_prev_diff.setText(
                f'이전 근무자의 차액은 '
                f'<span style="color:{color}; font-weight:700;">{amount}</span> 입니다.'
            )
        self._update_memo_placeholder()

    def _current_default_memo(self) -> str:
        """메모 기본값: 차액==이전차액이면 '동일', 아니면 (차액 - 이전차액) 값."""
        if self._prev_diff is None:
            return config.DEFAULT_MEMO
        cur_diff = compute_diff(compute_safe(self.current_counts()), self.data_edit.value())
        delta = cur_diff - self._prev_diff
        if delta == 0:
            return config.DEFAULT_MEMO
        return config.format_won(delta)

    def _update_memo_placeholder(self) -> None:
        self.memo_edit.setPlaceholderText(self._current_default_memo())
        # 포커스가 없어도 즉시 보이도록 강제 리페인트
        self.memo_edit.viewport().update()

    def _make_data_edit(self) -> AmountLineEdit:
        self.data_edit = AmountLineEdit(max_value=999_999_999, thousands=True)
        self.data_edit.setPlaceholderText("0")
        self.data_edit.textChanged.connect(self._recalculate)
        return self.data_edit

    def _row_label(self, name: str, widget: QWidget) -> QHBoxLayout:
        row = QHBoxLayout()
        lbl = QLabel(name)
        lbl.setObjectName("fieldName")
        lbl.setMinimumWidth(72)
        row.addWidget(lbl)
        row.addStretch(1)
        if isinstance(widget, AmountLineEdit):
            widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            widget.setMinimumWidth(200)
            widget.setAlignment(Qt.AlignmentFlag.AlignRight)
        else:
            widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        row.addWidget(widget)
        return row

    # 동작 ----------------------------------------------------------------
    @staticmethod
    def _denom_name(denom: int) -> str:
        if denom >= 10000:
            return f"{denom // 10000}만원"
        if denom >= 1000:
            return f"{denom // 1000}천원"
        return f"{denom}원"

    def _wire_navigation(self) -> None:
        # Tab 순서: 5만 → ... → 50 → 데이터 → 메모
        edits = [self.count_edits[d] for d in config.DENOMINATIONS] + [self.data_edit]
        for i in range(len(edits) - 1):
            self.setTabOrder(edits[i], edits[i + 1])
        self.setTabOrder(self.data_edit, self.memo_edit)
        # Enter 이동: 장수 → 다음 장수 → 데이터, 데이터 → 메모(마지막은 메모로)
        for i, edit in enumerate(edits):
            nxt = self.memo_edit if edit is self.data_edit else edits[i + 1]
            edit.nextRequested.connect(lambda w=nxt: w.setFocus())

    def current_counts(self) -> dict[int, int]:
        return {d: self.count_edits[d].value() for d in config.DENOMINATIONS}

    def _recalculate(self) -> None:
        counts = self.current_counts()
        safe = compute_safe(counts)
        data = self.data_edit.value()
        diff = compute_diff(safe, data)

        self.lbl_safe.setText(config.format_won(safe))
        self.lbl_diff.setText(config.format_won(diff))
        self.lbl_diff.setObjectName("diffNeg" if diff < 0 else "diffPos")
        # objectName 변경 후 스타일 재적용
        self.lbl_diff.style().unpolish(self.lbl_diff)
        self.lbl_diff.style().polish(self.lbl_diff)

        # 메모 기본값(placeholder)도 차액 변화에 맞춰 갱신
        self._update_memo_placeholder()

    def _on_save(self) -> None:
        counts = self.current_counts()
        data = self.data_edit.value()
        diff = compute_diff(compute_safe(counts), data)

        memo = self.memo_edit.toPlainText().strip() or self._current_default_memo()

        dialog = SaveDialog(diff=diff, parent=self)
        try:
            if dialog.exec():
                name, shift = dialog.result_values()
                record = Record(counts=counts, data=data, memo=memo, name=name, shift=shift)
                from .. import settings_store, storage

                # 디스크 오류(공간 부족/권한/잠금)에도 앱이 죽지 않도록 가드
                try:
                    storage.add_record(record)
                    if name:
                        settings_store.add_name(name)  # 이름 기록(칩)
                except Exception:
                    styled_dialog.info(
                        self, "저장 실패",
                        "저장에 실패했습니다. 디스크 공간이나 폴더 권한을 확인해 주세요.",
                    )
                    return
                self.recordSaved.emit()
                # 방금 저장한 기록이 다음 '이전 근무자' → 안내 문장 갱신
                self._update_prev_diff()
                # 장수·데이터는 유지, 메모만 비움(placeholder "동일" 표시)
                self.memo_edit.clear()
                styled_dialog.info(self, "저장", "저장되었습니다.")
        finally:
            dialog.deleteLater()
