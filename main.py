"""시재계산기 진입점."""

from __future__ import annotations

import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication

from app import config
from app.config import APP_NAME
from app.main_window import MainWindow


def _install_excepthook() -> None:
    """예기치 못한 예외가 나도 앱이 강제 종료되지 않도록 로그만 남기고 유지.

    24시간 상시 구동 환경에서 일시적 오류로 프로그램이 죽는 것을 방지한다.
    """
    import traceback
    from datetime import datetime

    def hook(exc_type, exc, tb):
        text = "".join(traceback.format_exception(exc_type, exc, tb))
        try:
            log = config.data_dir() / "error.log"
            with log.open("a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().isoformat(timespec='seconds')}]\n{text}\n")
        except Exception:
            pass
        # 콘솔에도 출력하되 프로세스를 종료하지 않음
        sys.stderr.write(text)

    sys.excepthook = hook


def main() -> int:
    _install_excepthook()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    icon = config.icon_path()
    if icon.exists():
        app.setWindowIcon(QIcon(str(icon)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
