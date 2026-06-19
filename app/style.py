"""모던/세련된 톤의 QSS 스타일시트."""

import re

# 컬러 팔레트
BG = "#f4f6fb"          # 배경
SURFACE = "#ffffff"     # 카드/패널
BORDER = "#e1e5ee"
TEXT = "#2b2f38"
SUBTLE = "#8a93a3"
ACCENT = "#4f7cff"      # 포인트 (파랑)
ACCENT_DARK = "#3b63d6"
DANGER = "#e5484d"      # 차액 음수/삭제
SUCCESS = "#2f9e44"

STYLESHEET = f"""
* {{
    font-family: "Segoe UI", "Malgun Gothic", "맑은 고딕", sans-serif;
    color: {TEXT};
}}

QWidget#root {{
    background: {BG};
    border: 1px solid #c7cedb;
    border-radius: 10px;
}}

/* 제목 */
QLabel#title {{
    font-size: 30px;
    font-weight: 800;
    color: {TEXT};
}}
QLabel#sectionHeader {{
    font-size: 18px;
    font-weight: 700;
    color: {SUBTLE};
}}

/* 카드/패널 */
QFrame#panel {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
}}

/* 입력창 */
QLineEdit, QPlainTextEdit, QComboBox {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 10px 14px;
    font-size: 18px;
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
}}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus {{
    border: 2px solid {ACCENT};
}}
QLineEdit#amount {{
    font-size: 26px;
    font-weight: 700;
    padding: 8px 16px;
}}

QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    selection-background-color: {ACCENT};
    selection-color: #ffffff;
    outline: none;
}}

/* 값 표시 */
QLabel#valueBig {{ font-size: 30px; font-weight: 800; }}
QLabel#diffPos {{ font-size: 32px; font-weight: 800; color: {SUCCESS}; }}
QLabel#diffNeg {{ font-size: 32px; font-weight: 800; color: {DANGER}; }}
QLabel#fieldLabel {{ font-size: 18px; color: {SUBTLE}; }}
QLabel#fieldName {{ font-size: 22px; font-weight: 700; color: {SUBTLE}; }}
QLabel#prevDiff {{ font-size: 15px; color: {SUBTLE}; }}
QLabel#confirmMsg {{ font-size: 21px; font-weight: 700; color: {TEXT}; }}
QLabel#cardDate {{ font-size: 22px; font-weight: 800; color: {TEXT}; }}
QLabel#cardFoot {{ font-size: 20px; font-weight: 700; color: {TEXT}; }}

/* 단위 라벨 배경 박스 — 기본: 회색 배경 / 검은 텍스트 (모든 단위) */
QLabel#denomLabel {{
    font-size: 24px;
    font-weight: 700;
    background: #eef1f6;
    color: {TEXT};
    border-radius: 8px;
    padding: 2px 12px;
}}
QLabel#cardDenom {{
    font-size: 14px;
    font-weight: 600;
    background: #eef1f6;
    color: {TEXT};
    border-radius: 6px;
    padding: 1px 8px;
}}
/* 5만원=연주황 / 1만원=연초록 (회색 위에 덮어씀) */
QLabel#denomLabel[denom="50000"], QLabel#cardDenom[denom="50000"] {{
    background: #ffe8d2;
    color: #c2410c;
}}
QLabel#denomLabel[denom="10000"], QLabel#cardDenom[denom="10000"] {{
    background: #d9f2e0;
    color: #1f8a44;
}}

/* 지폐/동전 구분선 */
QFrame#denomDivider {{
    border: none;
    border-top: 2px dashed {BORDER};
    max-height: 0px;
}}

/* 버튼 */
QPushButton {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 11px 22px;
    font-size: 17px;
    font-weight: 700;
}}
QPushButton:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton:pressed {{ background: #eef2ff; }}

QPushButton#primary {{
    background: {ACCENT};
    border: 1px solid {ACCENT};
    color: #ffffff;
}}
QPushButton#primary:hover {{ background: {ACCENT_DARK}; border-color: {ACCENT_DARK}; color: #ffffff; }}
QPushButton#primary:pressed {{ background: {ACCENT_DARK}; }}

QPushButton#danger {{ color: {DANGER}; }}
QPushButton#danger:hover {{ border-color: {DANGER}; color: {DANGER}; }}

QPushButton#link {{
    background: transparent;
    border: none;
    color: {SUBTLE};
    font-weight: 700;
    font-size: 18px;
    padding: 6px 8px;
}}
QPushButton#link:hover {{ color: {ACCENT}; }}

/* 핀(고정) 버튼 */
QPushButton#pin {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 0px;
}}
QPushButton#pin:hover {{ background: #eef1f6; }}
QPushButton#pin:checked {{ background: #e3e7f0; }}

/* 커스텀 팝업(다이얼로그) */
QFrame#dialogRoot {{
    background: {SURFACE};
    border: 1px solid #c7cedb;
    border-radius: 12px;
}}
QFrame#dialogHeader {{
    background: transparent;
    border: none;
    border-bottom: 1px solid {BORDER};
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
}}
QLabel#dialogTitle {{ font-size: 18px; font-weight: 800; color: {TEXT}; }}
QLabel#dialogText {{ font-size: 16px; color: {TEXT}; }}

/* 이름 기록 칩 */
QFrame#nameChip {{
    background: #eef1f6;
    border: 1px solid #dce1ea;
    border-radius: 14px;
}}
QPushButton#chipName {{
    background: transparent;
    border: none;
    font-size: 14px;
    font-weight: 600;
    color: {TEXT};
    padding: 2px 2px;
}}
QPushButton#chipName:hover {{ color: {ACCENT}; }}
QPushButton#chipDel {{
    background: transparent;
    border: none;
    color: {SUBTLE};
    font-size: 15px;
    font-weight: 700;
    border-radius: 10px;
    padding: 0px;
}}
QPushButton#chipDel:hover {{ background: {DANGER}; color: #ffffff; }}

/* 커스텀 타이틀바 */
QFrame#titleBar {{
    background: {SURFACE};
    border: none;
    border-bottom: 1px solid {BORDER};
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
}}
QPushButton#winBtn, QPushButton#winClose {{
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 0px;
}}
QPushButton#winBtn:hover {{ background: #eef1f6; }}
QPushButton#winClose:hover {{ background: {DANGER}; }}

/* 확대/축소 */
QPushButton#zoomBtn {{
    background: transparent;
    border: none;
    border-radius: 8px;
    font-size: 20px;
    font-weight: 700;
    color: {TEXT};
    padding: 0px;
}}
QPushButton#zoomBtn:hover {{ background: #eef1f6; color: {ACCENT}; }}
QLabel#zoomLabel {{ font-size: 13px; font-weight: 700; color: {SUBTLE}; }}
QLabel#credit {{ font-size: 13px; color: #b3bac7; }}

/* 내역 카드 */
QFrame#recordCard {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}
QFrame#recordCard[selected="true"] {{
    border: 2px solid {ACCENT};
    background: #f7f9ff;
}}

/* 스크롤 영역 */
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #c7cedb; border-radius: 5px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* 체크박스 */
QCheckBox {{ spacing: 6px; font-size: 13px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px;
    border: 1px solid {BORDER}; border-radius: 5px; background: {SURFACE};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT}; border-color: {ACCENT};
    image: none;
}}
"""


# UI 배율 한계
MIN_SCALE = 0.8
MAX_SCALE = 1.6


def build_stylesheet(scale: float = 1.0) -> str:
    """배율에 맞춰 스타일시트의 모든 px 값을 비례 확대/축소."""
    if abs(scale - 1.0) < 1e-3:
        return STYLESHEET

    def _repl(m: "re.Match") -> str:
        return f"{max(1, round(int(m.group(1)) * scale))}px"

    return re.sub(r"(\d+)px", _repl, STYLESHEET)
