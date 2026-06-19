@echo off
REM 시재계산기 exe 빌드 (PyInstaller onefile)
REM uv 환경에서 실행: build.bat
cd /d "%~dp0"
uv run pyinstaller --noconfirm --onefile --windowed --name 시재계산기 ^
  --icon app\assets\icon.ico ^
  --version-file version_info.txt ^
  --add-data "app\assets\icon.ico;app/assets" ^
  --collect-submodules app ^
  main.py
echo.
echo 빌드 완료: dist\시재계산기.exe
pause
