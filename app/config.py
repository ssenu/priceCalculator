"""애플리케이션 전역 상수 및 경로 정의."""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "시제계산기"


def resource_path(rel: str) -> Path:
    """번들(PyInstaller)/개발 환경 모두에서 리소스 절대경로."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / rel
    return Path(__file__).resolve().parent.parent / rel


def icon_path() -> Path:
    return resource_path("app/assets/icon.ico")

# 지폐/동전 단위 (이미지 기준 고정). 내림차순.
DENOMINATIONS: list[int] = [50000, 10000, 5000, 1000, 500, 100, 50]

# 근무시간 선택지
SHIFTS: list[str] = ["오전", "오후1", "오후2", "야간", "사장님"]

# 메모 기본값 (비워서 저장하면 이 값으로 기록)
DEFAULT_MEMO = "동일"


def default_shift(now) -> str:
    """현재 시각대에 맞는 근무시간 기본값.

    0~6시=야간 / 6~12=오전 / 12~18=오후1 / 18~24=오후2
    """
    h = now.hour
    if h < 6:
        return "야간"
    if h < 12:
        return "오전"
    if h < 18:
        return "오후1"
    return "오후2"

# 인쇄: A4 한 페이지에 들어갈 카드 수
CARDS_PER_PAGE = 8

# 요일 한글 표기
WEEKDAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]


def data_dir() -> Path:
    """데이터 저장 폴더 (%APPDATA%/시재계산기). 없으면 생성."""
    base = os.getenv("APPDATA") or os.path.expanduser("~")
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def records_path() -> Path:
    """기록 JSON 파일 경로."""
    return data_dir() / "records.json"


def format_won(value: int) -> str:
    """천 단위 구분 + '원'. 음수는 부호 유지."""
    return f"{value:,}원"
