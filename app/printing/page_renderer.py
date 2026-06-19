"""A4 페이지에 내역 카드를 8개/쪽으로 렌더링하고 인쇄/PDF/이미지로 출력."""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QImage, QPainter, QPen
from PyQt6.QtPrintSupport import QPrinter

from .. import config
from ..models import Record
from ..widgets.record_card import _denom_name

COLS, ROWS = 2, 4
DANGER = QColor("#e5484d")
SUCCESS = QColor("#2f9e44")
TEXT = QColor("#2b2f38")
SUBTLE = QColor("#8a93a3")
BORDER = QColor("#cfd6e4")

# 단위 박스 색 (앱 카드와 동일): 5만=연주황 / 1만=연초록 / 나머지=회색
DENOM_BG_DEFAULT = QColor("#eef1f6")
DENOM_FG_DEFAULT = QColor("#2b2f38")
DENOM_COLORS = {
    50000: (QColor("#ffe8d2"), QColor("#c2410c")),
    10000: (QColor("#d9f2e0"), QColor("#1f8a44")),
}


def _chunk(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)] or [[]]


class RecordRenderer:
    """주어진 기록들을 페이지 단위로 그린다 (장치 비종속)."""

    def __init__(self, records: list[Record]):
        self.records = records
        self.pages = _chunk(records, config.CARDS_PER_PAGE)

    # 공통 페인팅 ---------------------------------------------------------
    def render_to_printer(self, printer: QPrinter) -> None:
        painter = QPainter(printer)
        try:
            for i, page in enumerate(self.pages):
                if i > 0:
                    printer.newPage()
                rect = QRectF(painter.viewport())
                self._paint_page(painter, rect, page, i + 1, len(self.pages))
        finally:
            painter.end()

    def render_images(self, dpi: int = 150) -> list[QImage]:
        w = int(8.27 * dpi)
        h = int(11.69 * dpi)
        images: list[QImage] = []
        for i, page in enumerate(self.pages):
            img = QImage(w, h, QImage.Format.Format_ARGB32)
            img.fill(Qt.GlobalColor.white)
            painter = QPainter(img)
            try:
                self._paint_page(painter, QRectF(0, 0, w, h), page, i + 1, len(self.pages))
            finally:
                painter.end()
            images.append(img)
        return images

    # 페이지 / 카드 -------------------------------------------------------
    def _paint_page(self, p: QPainter, rect: QRectF, page: list[Record], page_no: int, total: int) -> None:
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        margin = rect.width() * 0.04
        header_h = rect.height() * 0.05

        # 페이지 제목
        title_font = QFont("Malgun Gothic")
        title_font.setPixelSize(int(header_h * 0.5))
        title_font.setBold(True)
        p.setFont(title_font)
        p.setPen(QPen(TEXT))
        p.drawText(
            QRectF(rect.left() + margin, rect.top() + margin * 0.4, rect.width() - margin * 2, header_h),
            Qt.AlignmentFlag.AlignCenter,
            f"{config.APP_NAME} 내역",
        )

        # 페이지 번호
        pn_font = QFont("Malgun Gothic")
        pn_font.setPixelSize(int(header_h * 0.32))
        p.setFont(pn_font)
        p.setPen(QPen(SUBTLE))
        p.drawText(
            QRectF(rect.left() + margin, rect.top() + margin * 0.4, rect.width() - margin * 2, header_h),
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            f"{page_no} / {total}",
        )

        grid_top = rect.top() + margin + header_h
        grid_w = rect.width() - margin * 2
        grid_h = rect.height() - margin * 2 - header_h
        gap = margin * 0.5
        cell_w = (grid_w - gap * (COLS - 1)) / COLS
        cell_h = (grid_h - gap * (ROWS - 1)) / ROWS

        for idx, rec in enumerate(page):
            r = idx // COLS
            c = idx % COLS
            x = rect.left() + margin + c * (cell_w + gap)
            y = grid_top + r * (cell_h + gap)
            self._paint_card(p, QRectF(x, y, cell_w, cell_h), rec)

    def _paint_card(self, p: QPainter, rect: QRectF, rec: Record) -> None:
        # 테두리
        p.setPen(QPen(BORDER, max(1.0, rect.height() * 0.004)))
        p.setBrush(Qt.BrushStyle.NoBrush)
        radius = rect.height() * 0.04
        p.drawRoundedRect(rect.adjusted(2, 2, -2, -2), radius, radius)

        pad = rect.width() * 0.05
        inner = rect.adjusted(pad, pad, -pad, -pad)
        line_h = inner.height() / 10.0

        base_font = QFont("Malgun Gothic")
        base_font.setPixelSize(max(7, int(line_h * 0.5)))
        bold_font = QFont(base_font)
        bold_font.setBold(True)

        # 날짜 + 시각 (상단 중앙, 앱과 동일하게 datetime)
        date_font = QFont(base_font)
        date_font.setBold(True)
        date_font.setPixelSize(max(8, int(line_h * 0.58)))
        p.setFont(date_font)
        p.setPen(QPen(TEXT))
        p.drawText(
            QRectF(inner.left(), inner.top(), inner.width(), line_h * 1.2),
            Qt.AlignmentFlag.AlignCenter,
            rec.datetime_display(),
        )

        content_top = inner.top() + line_h * 1.5
        col_w = inner.width() / 2.0

        # 좌측: 단위(색상 박스, 우정렬) + 매수(좌정렬) → 매수 숫자 세로 정렬
        name_w = col_w * 0.52
        gap_w = col_w * 0.08
        fm = QFontMetricsF(bold_font)
        box_h = line_h * 0.82
        pad_x = line_h * 0.22
        for i, denom in enumerate(config.DENOMINATIONS):
            cnt = rec.counts.get(denom, 0)
            y = content_top + i * line_h
            name = _denom_name(denom)
            bg, fg = DENOM_COLORS.get(denom, (DENOM_BG_DEFAULT, DENOM_FG_DEFAULT))
            tw = fm.horizontalAdvance(name)
            box_w = tw + pad_x * 2
            box_right = inner.left() + name_w
            box = QRectF(box_right - box_w, y + (line_h - box_h) / 2, box_w, box_h)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(bg))
            p.drawRoundedRect(box, box_h * 0.35, box_h * 0.35)
            p.setFont(bold_font)
            p.setPen(QPen(fg))
            p.drawText(box, Qt.AlignmentFlag.AlignCenter, name)
            # 매수
            p.setFont(base_font)
            p.setPen(QPen(TEXT))
            p.drawText(
                QRectF(inner.left() + name_w + gap_w, y, col_w - name_w - gap_w, line_h),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                str(cnt),
            )

        # 우측: 데이터/금고/차액/메모 (앱과 동일하게 굵게)
        rx = inner.left() + col_w
        p.setFont(bold_font)
        rows = [
            ("데이터  " + f"{rec.data:,}", TEXT),
            ("금고  " + f"{rec.safe:,}", TEXT),
            ("차액  " + f"{rec.diff:,}", DANGER if rec.diff < 0 else SUCCESS),
        ]
        for i, (text, color) in enumerate(rows):
            y = content_top + i * line_h
            p.setPen(QPen(color))
            p.drawText(
                QRectF(rx, y, col_w, line_h),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                text,
            )
        # 메모 라벨 + 차액과 간격
        p.setPen(QPen(TEXT))
        p.drawText(
            QRectF(rx, content_top + 3.6 * line_h, col_w, line_h),
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            "메모",
        )
        memo_rect = QRectF(rx, content_top + 4.6 * line_h, col_w, line_h * 2.2)
        p.drawText(memo_rect, Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap, rec.memo or "")

        # 하단: 이름 / 근무시간 (굵게)
        p.setFont(bold_font)
        p.setPen(QPen(TEXT))
        foot_rect = QRectF(inner.left(), inner.bottom() - line_h, inner.width(), line_h)
        p.drawText(
            QRectF(inner.left(), foot_rect.top(), inner.width() * 0.5, line_h),
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
            rec.name or "-",
        )
        p.drawText(
            QRectF(inner.left() + inner.width() * 0.5, foot_rect.top(), inner.width() * 0.5, line_h),
            Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter,
            rec.shift or "",
        )
