# -*- coding: utf-8 -*-
"""使用 PyInstaller 把 caesar_gui.py 打包成單一 exe。

沙箱相容處理：
    1. tempfile.mkdtemp() 建出的目錄在本環境無法寫入檔案，
       因此換成等價的 os.makedirs 版本，並把暫存目錄指到工作區內。
    2. PyInstaller 預設會把快取寫到 %LOCALAPPDATA%\\pyinstaller（工作區外，會被沙箱阻擋），
       改用 PYINSTALLER_CONFIG_DIR 指到工作區內的 .build_cache。

用法：python .tools/build_exe.py   （或直接執行 build_exe.bat）
產物：dist\\CaesarCipherGUI.exe
"""

import os
import sys
import tempfile
import uuid
from pathlib import Path

WORK = Path(__file__).resolve().parent.parent
TMP = WORK / ".build_tmp"
CACHE = WORK / ".build_cache"
TMP.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)

os.environ["TEMP"] = os.environ["TMP"] = os.environ["TMPDIR"] = str(TMP)
os.environ["PYINSTALLER_CONFIG_DIR"] = str(CACHE)
tempfile.tempdir = str(TMP)


def mkdtemp(suffix=None, prefix=None, dir=None):
    """與 tempfile.mkdtemp 相同用途，但用 os.makedirs 建立（不套用 0o700 模式）。"""
    base = dir or tempfile.gettempdir()
    path = os.path.join(base, f"{prefix or 'tmp'}{uuid.uuid4().hex[:10]}{suffix or ''}")
    os.makedirs(path, exist_ok=True)
    return path


tempfile.mkdtemp = mkdtemp

os.chdir(WORK)  # 讓 --add-data 的相對路徑與輸出目錄都相對於專案根目錄

import PyInstaller.__main__ as pyinstaller  # noqa: E402

# 預設打包成單一 exe；加上 --onedir 則改打包成資料夾版本（啟動較快、不必解壓到暫存目錄）
ONEDIR = "--onedir" in sys.argv[1:]

COMMON = [
    "--noconfirm",
    "--clean",
    "--windowed",           # 不顯示主控台視窗
    "--name", "CaesarCipherGUI",
    "--collect-all", "customtkinter",   # 一併打包 CustomTkinter 的主題 JSON 等資源
    "--add-data", "Untitled-1.py;.",    # 核心運算程式
    "--add-data", "test.txt;.",         # 範例密文
    "caesar_gui.py",
]

if ONEDIR:
    ARGS = COMMON + ["--onedir", "--distpath", "dist_portable"]
    OUTPUT = WORK / "dist_portable" / "CaesarCipherGUI" / "CaesarCipherGUI.exe"
else:
    ARGS = COMMON + ["--onefile"]
    OUTPUT = WORK / "dist" / "CaesarCipherGUI.exe"

if __name__ == "__main__":
    print("[build] 模式:", "onedir（資料夾版）" if ONEDIR else "onefile（單一 exe）")
    print("[build] args:", " ".join(ARGS))
    pyinstaller.run(ARGS)
    print("[build] 完成：", OUTPUT, "存在" if OUTPUT.exists() else "不存在")
    sys.exit(0 if OUTPUT.exists() else 1)
