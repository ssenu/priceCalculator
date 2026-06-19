"""인쇄/PDF/이미지 미리보기 및 출력 다이얼로그.

미리보기를 보여주고, 인쇄/PDF/PNG 중 선택해 출력한다.
'출력한 내역 삭제' 체크 시 출력 성공 후 해당 기록 삭제를 요청한다(시그널).
"""

from __future__ import annotations

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPageSize
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewWidget
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ..models import Record
from ..printing.page_renderer import RecordRenderer
from . import styled_dialog
from .styled_dialog import StyledDialog


class PrintPreviewDialog(StyledDialog):
    """A4 미리보기 + 인쇄/PDF/이미지 출력."""

    deleteRequested = pyqtSignal(set)  # 출력 후 삭제할 record id 집합

    def __init__(self, records: list[Record], parent=None):
        super().__init__("인쇄 / 저장 미리보기", parent)
        self.records = records
        self.renderer = RecordRenderer(records)
        self.resize(720, 860)
        self._build_ui()

    def _build_ui(self) -> None:
        v = self.body
        v.setSpacing(12)

        info = QLabel(f"총 {len(self.records)}건 · {len(self.renderer.pages)}쪽 (A4, 한 쪽 8건)")
        info.setObjectName("fieldLabel")
        v.addWidget(info)

        # 미리보기
        self.printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        self.printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        self.preview = QPrintPreviewWidget(self.printer)
        self.preview.paintRequested.connect(self.renderer.render_to_printer)
        preview_frame = QFrame()
        preview_frame.setObjectName("panel")
        pf = QVBoxLayout(preview_frame)
        pf.setContentsMargins(8, 8, 8, 8)
        pf.addWidget(self.preview)
        v.addWidget(preview_frame, 1)

        # 출력한 내역 삭제 체크박스 (인쇄/저장 버튼 위)
        self.delete_check = QCheckBox("인쇄/저장한 내역 삭제")
        v.addWidget(self.delete_check)

        # 버튼 줄
        btns = QHBoxLayout()
        close = QPushButton("닫기")
        close.clicked.connect(self.reject)
        btns.addWidget(close)
        btns.addStretch(1)

        btn_png = QPushButton("이미지로 저장")
        btn_png.clicked.connect(self._save_image)
        btn_pdf = QPushButton("PDF로 저장")
        btn_pdf.clicked.connect(self._save_pdf)
        btn_print = QPushButton("인쇄")
        btn_print.setObjectName("primary")
        btn_print.clicked.connect(self._print)
        btns.addWidget(btn_png)
        btns.addWidget(btn_pdf)
        btns.addWidget(btn_print)
        v.addLayout(btns)

    # 출력 동작 -----------------------------------------------------------
    def _finish_success(self, message: str) -> None:
        if self.delete_check.isChecked():
            ids = {r.id for r in self.records}
            self.deleteRequested.emit(ids)
        styled_dialog.info(self, "완료", message)
        self.accept()

    def _print(self) -> None:
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        dlg = QPrintDialog(printer, self)
        try:
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.renderer.render_to_printer(printer)
                self._finish_success("인쇄를 전송했습니다.")
        finally:
            dlg.deleteLater()

    def _save_pdf(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "PDF로 저장", "시재내역.pdf", "PDF 파일 (*.pdf)")
        if not path:
            return
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        self.renderer.render_to_printer(printer)
        self._finish_success(f"PDF로 저장했습니다.\n{path}")

    def _save_image(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "이미지로 저장", "시재내역.png", "PNG 이미지 (*.png)")
        if not path:
            return
        images = self.renderer.render_images(dpi=150)
        base, ext = os.path.splitext(path)
        ext = ext or ".png"
        saved = []
        if len(images) == 1:
            images[0].save(path)
            saved.append(path)
        else:
            for i, img in enumerate(images, start=1):
                p = f"{base}_{i}{ext}"
                img.save(p)
                saved.append(p)
        self._finish_success("이미지로 저장했습니다.\n" + "\n".join(saved))
