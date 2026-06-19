"""데이터 모델 및 계산 로직."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

from . import config


def compute_safe(counts: dict[int, int]) -> int:
    """금고 = Σ(단위 × 매수)."""
    return sum(denom * counts.get(denom, 0) for denom in config.DENOMINATIONS)


def compute_diff(safe: int, data: int) -> int:
    """차액 = 금고 - 데이터 (음수 가능)."""
    return safe - data


@dataclass
class Record:
    """하나의 시재 기록."""

    counts: dict[int, int]
    data: int
    memo: str
    name: str
    shift: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    @property
    def safe(self) -> int:
        return compute_safe(self.counts)

    @property
    def diff(self) -> int:
        return compute_diff(self.safe, self.data)

    def datetime_obj(self) -> datetime:
        try:
            return datetime.fromisoformat(self.timestamp)
        except ValueError:
            return datetime.now()

    def date_display(self) -> str:
        """예: 2026/10/18 수요일."""
        dt = self.datetime_obj()
        wd = config.WEEKDAYS_KO[dt.weekday()]
        return f"{dt.year}/{dt.month:02d}/{dt.day:02d} {wd}요일"

    def datetime_display(self) -> str:
        """예: 2026/10/18 수요일 14:30."""
        dt = self.datetime_obj()
        return f"{self.date_display()} {dt.hour:02d}:{dt.minute:02d}"

    # 직렬화 ---------------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            # JSON 키는 문자열로 저장
            "counts": {str(k): int(v) for k, v in self.counts.items()},
            "data": int(self.data),
            "memo": self.memo,
            "name": self.name,
            "shift": self.shift,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Record":
        counts = {int(k): int(v) for k, v in d.get("counts", {}).items()}
        return cls(
            counts=counts,
            data=int(d.get("data", 0)),
            memo=d.get("memo", ""),
            name=d.get("name", ""),
            shift=d.get("shift", ""),
            timestamp=d.get("timestamp", datetime.now().isoformat(timespec="seconds")),
            id=d.get("id", uuid.uuid4().hex),
        )
