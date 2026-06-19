"""앱 설정 저장소 (관리자 비밀번호 · 동작 보호 옵션)."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import tempfile

from . import config

_PBKDF_ROUNDS = 120_000


def _settings_path():
    return config.data_dir() / "settings.json"


def _load() -> dict:
    path = _settings_path()
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    path = _settings_path()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, str(path))
    except Exception:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass
        raise


def _hash(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF_ROUNDS).hex()


# 공개 API ---------------------------------------------------------------
def has_password() -> bool:
    return bool(_load().get("password"))


def set_password(new_password: str) -> None:
    salt = secrets.token_bytes(16)
    data = _load()
    data["password"] = {"salt": salt.hex(), "hash": _hash(new_password, salt)}
    _save(data)


def verify_password(password: str) -> bool:
    entry = _load().get("password")
    if not entry:
        return False
    salt = bytes.fromhex(entry["salt"])
    return secrets.compare_digest(_hash(password, salt), entry["hash"])


def require_password_for_actions() -> bool:
    """내역 삭제/프린트 시 비밀번호 확인 여부."""
    return bool(_load().get("require_password", False))


def set_require_password_for_actions(value: bool) -> None:
    data = _load()
    data["require_password"] = bool(value)
    _save(data)


# UI 배율 ----------------------------------------------------------------
def get_ui_scale() -> float:
    try:
        return float(_load().get("ui_scale", 1.0))
    except (TypeError, ValueError):
        return 1.0


def set_ui_scale(value: float) -> None:
    data = _load()
    data["ui_scale"] = round(float(value), 2)
    _save(data)


# 이름 기록 --------------------------------------------------------------
def get_names() -> list[str]:
    names = _load().get("names", [])
    return [str(n) for n in names if str(n).strip()]


def add_name(name: str) -> None:
    name = name.strip()
    if not name:
        return
    data = _load()
    names = [str(n) for n in data.get("names", []) if str(n).strip()]
    if name in names:
        # 최근 사용 순으로 맨 앞으로
        names.remove(name)
    names.insert(0, name)
    data["names"] = names[:30]  # 최대 30개 유지
    _save(data)


def remove_name(name: str) -> None:
    data = _load()
    names = [str(n) for n in data.get("names", []) if str(n).strip() and str(n) != name]
    data["names"] = names
    _save(data)
