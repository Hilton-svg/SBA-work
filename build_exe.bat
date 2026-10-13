@echo off
rem 把 caesar_gui.py 打包成單一執行檔：dist\CaesarCipherGUI.exe
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [錯誤] 找不到 .venv\Scripts\python.exe
    echo 請先建立虛擬環境並安裝 customtkinter 與 pyinstaller：
    echo     python -m venv .venv
    echo     .venv\Scripts\python.exe -m pip install customtkinter pyinstaller
    pause
    exit /b 1
)

".venv\Scripts\python.exe" ".tools\build_exe.py"
if errorlevel 1 (
    echo.
    echo [失敗] 打包過程發生錯誤，請檢查上方訊息。
    pause
    exit /b 1
)

echo.
echo [完成] 執行檔： %~dp0dist\CaesarCipherGUI.exe
pause
