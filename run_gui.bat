@echo off
rem 凱撒密碼破解器：以專案內的 .venv 啟動圖形介面
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "caesar_gui.py" %*
) else (
    start "" pythonw "caesar_gui.py" %*
)
