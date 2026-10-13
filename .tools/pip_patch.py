# -*- coding: utf-8 -*-
"""在受限沙箱中執行 pip。

本環境的沙箱會讓 tempfile.mkdtemp() 建出的目錄無法寫入檔案（繼承了 DENY 的 ACL），
導致 pip 解壓 wheel 時失敗。這裡把 mkdtemp 換成等價但使用 os.makedirs 的版本，
並把暫存目錄指到工作區內，pip 就能正常運作。

用法：python .tools/pip_patch.py install pyinstaller
"""

import os
import sys
import tempfile
import uuid
from pathlib import Path

WORK = Path(__file__).resolve().parent.parent
TMP = WORK / ".build_tmp"
TMP.mkdir(exist_ok=True)

os.environ["TEMP"] = os.environ["TMP"] = os.environ["TMPDIR"] = str(TMP)
tempfile.tempdir = str(TMP)


def mkdtemp(suffix=None, prefix=None, dir=None):
    """與 tempfile.mkdtemp 相同用途，但用 os.makedirs 建立（不套用 0o700 模式）。"""
    base = dir or tempfile.gettempdir()
    path = os.path.join(base, f"{prefix or 'tmp'}{uuid.uuid4().hex[:10]}{suffix or ''}")
    os.makedirs(path, exist_ok=True)
    return path


tempfile.mkdtemp = mkdtemp

from pip._internal.cli.main import main as pip_main  # noqa: E402

if __name__ == "__main__":
    sys.exit(pip_main(sys.argv[1:]))
