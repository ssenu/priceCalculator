"""기록 JSON 저장소 (원자적 쓰기 + 백업)."""

from __future__ import annotations

import json
import os
import tempfile

from . import config
from .models import Record


def load_records() -> list[Record]:
    """디스크에서 기록을 읽어 최신순으로 반환. 파일 없거나 손상 시 빈 목록."""
    path = config.records_path()
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8") as f:
            raw = json.load(f)
    except (json.JSONDecodeError, OSError):
        # 손상된 경우 백업에서 복구 시도
        bak = path.with_suffix(".json.bak")
        if bak.exists():
            try:
                with bak.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        else:
            return []

    records = [Record.from_dict(d) for d in raw]
    records.sort(key=lambda r: r.timestamp, reverse=True)
    return records


def save_records(records: list[Record]) -> None:
    """기록 전체를 원자적으로 저장. 이전 파일은 .bak로 백업."""
    path = config.records_path()
    data = [r.to_dict() for r in records]

    # 임시 파일에 먼저 쓰고 os.replace로 교체 → 쓰기 도중 종료돼도 손상 방지
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        # 기존 파일 백업
        if path.exists():
            bak = path.with_suffix(".json.bak")
            try:
                os.replace(str(path), str(bak))
            except OSError:
                pass
        os.replace(tmp_name, str(path))
    except Exception:
        if os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass
        raise


def add_record(record: Record) -> list[Record]:
    """기록 1건 추가 후 전체 목록(최신순) 반환."""
    records = load_records()
    records.append(record)
    records.sort(key=lambda r: r.timestamp, reverse=True)
    save_records(records)
    return records


def delete_records(ids: set[str]) -> list[Record]:
    """주어진 id 집합을 삭제 후 전체 목록 반환."""
    records = [r for r in load_records() if r.id not in ids]
    save_records(records)
    return records
