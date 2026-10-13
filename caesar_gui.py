# -*- coding: utf-8 -*-
"""
caesar_gui.py：凱撒密碼破解工具的 CustomTkinter 圖形介面

設計重點：
    1. 直接沿用 Untitled-1.py 內所有既有的計算邏輯（不重寫演算法），
       以 importlib 依檔案路徑載入，因此原檔名含「-」也能正常匯入。
    2. 現代化外觀：CustomTkinter + 圓角卡片式版面，支援「跟隨系統 / 淺色 / 深色」。
    3. 輸出分成左右兩個區塊：
         左方區塊（統計資料）：字母頻率直方圖、每個位移的分數明細、候選排名、
                               字母總數與動態權重等輔助數據。
         右方區塊（主要結果）：最有可能的偏移量 k，以及該 k 底下的完整解密結果。
    4. 視窗固定為最大化（不可縮放），在小螢幕上也維持一致的版面。
    5. 其他便利功能：從檔案載入、載入 test.txt 範例密文、複製結果、另存新檔、
                     Ctrl+Enter 快速分析。

執行方式：
    .venv\\Scripts\\python.exe caesar_gui.py            # 一般啟動
    .venv\\Scripts\\python.exe caesar_gui.py --demo     # 啟動時自動載入範例並分析
    .venv\\Scripts\\python.exe caesar_gui.py --selftest # 非互動自我測試後自動關閉
    也可直接雙擊同資料夾的 run_gui.bat，或執行打包後的 CaesarCipherGUI.exe

其他參數（除錯／自動化用）：
    --appearance=深色|淺色|跟隨系統   指定啟動時的外觀模式
    --tab=頻率直方圖|位移明細|候選排名 啟動後直接切到左方指定分頁
    --auto-close=秒數                 指定秒數後自動關閉視窗

相依套件：customtkinter（已安裝於本專案的 .venv）。
打包 exe：執行 build_exe.bat，產物為 dist\\CaesarCipherGUI.exe。
"""

import importlib.util
import sys
import time
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk


# ==================== 基本路徑與核心模組載入 ====================


def _resolve_dirs():
    """
    決定「資源目錄」與「工作目錄」，同時支援原始碼執行與 PyInstaller 打包後的 exe。

    - 原始碼執行：兩者都是本檔所在資料夾。
    - 打包成 exe：資源被打包進 PyInstaller 的暫存解壓目錄（sys._MEIPASS），
      但工作目錄要指向 exe 本身所在位置，這樣檔案對話框、存檔，
      以及使用者自行替換的 Untitled-1.py / test.txt 才會正確。
    """
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        bundle_dir = Path(getattr(sys, "_MEIPASS", exe_dir))
        return bundle_dir, exe_dir
    here = Path(__file__).resolve().parent
    return here, here


BUNDLE_DIR, WORK_DIR = _resolve_dirs()


def _data_file(name):
    """資料檔優先採用 exe／程式旁邊的外部檔案，找不到才用打包進去的版本。"""
    external = WORK_DIR / name
    if external.exists():
        return external
    return BUNDLE_DIR / name


CORE_FILE = _data_file("Untitled-1.py")     # 既有的凱撒密碼運算程式
SAMPLE_FILE = _data_file("test.txt")        # 內含明文本與對應密文的範例檔


def _log(message):
    """
    輸出除錯訊息。

    打包成視窗模式的 exe 沒有可見的主控台，因此打包後（sys.frozen）一律
    另外寫入 %TEMP%\\caesar_gui.log，方便使用者回報問題
    （例如 --selftest 的檢查結果或未預期例外）。
    """
    if not getattr(sys, "frozen", False) and sys.stdout is not None:
        try:
            print(message)
            return
        except Exception:
            pass
    try:
        import datetime
        import tempfile

        log_path = Path(tempfile.gettempdir()) / "caesar_gui.log"
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp} {message}\n")
    except Exception:
        pass


def load_core_module(path=CORE_FILE):
    """
    以檔案路徑載入 Untitled-1.py，回傳該模組物件。

    因為檔名含有「-」，無法使用一般的 import 語法，
    所以用 importlib.util.spec_from_file_location 動態載入；
    模組名稱設為 caesar_core，因此原檔中的 __main__ 判斷不會成立，
    不會意外執行它的命令列流程。
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"找不到核心程式檔案：{path}")

    spec = importlib.util.spec_from_file_location("caesar_core", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["caesar_core"] = module
    spec.loader.exec_module(module)
    return module


# ==================== 主題色票與字型 ====================
# CustomTkinter 允許顏色使用 (淺色模式, 深色模式) 的 tuple，
# 切換外觀模式時會自動選用對應色，因此不需要手動重建介面。

COLOR_BG = ("#EEF1F6", "#101014")            # 視窗底色
COLOR_CARD = ("#FFFFFF", "#1B1C22")          # 卡片底色
COLOR_CARD_ALT = ("#F4F6FA", "#23242C")      # 次要卡片底色
COLOR_BORDER = ("#DCE1EA", "#2C2E38")        # 卡片邊框
COLOR_TEXT = ("#171A20", "#ECEDF1")          # 主要文字
COLOR_MUTED = ("#5C6472", "#98A0AE")         # 次要文字
COLOR_ENTRY = ("#F7F9FC", "#15161B")         # 輸入框底色

COLOR_ACCENT = "#3B82F6"                     # 主要強調色（藍）
COLOR_ACCENT_HOVER = "#2F6FDB"
COLOR_VIOLET = "#8B5CF6"                     # 次要強調色（紫）
COLOR_AMBER = "#F59E0B"                      # 高分提示色（琥珀）
COLOR_GREEN = "#22C55E"                      # 成功色
COLOR_RED = "#EF4444"                        # 錯誤色

FONT_TITLE = ("Microsoft JhengHei UI", 18, "bold")
FONT_SECTION = ("Microsoft JhengHei UI", 14, "bold")
FONT_BODY = ("Microsoft JhengHei UI", 12)
FONT_SMALL = ("Microsoft JhengHei UI", 11)
FONT_CAPTION = ("Microsoft JhengHei UI", 11)
FONT_MONO = ("Consolas", 12)
FONT_MONO_SMALL = ("Consolas", 11)
FONT_SHIFT_BIG = ("Consolas", 40, "bold")
FONT_SCORE_BIG = ("Consolas", 26, "bold")

# 沒有 test.txt 時使用的備用範例密文（位移 3 的凱撒密文）
FALLBACK_CIPHER = (
    "Wkh txlfn eurzq ira mxpsv ryhu wkh odcb grj. "
    "Sdfnlqj pbdq wkh wklug vkliw lv d vlpsoh zdb wr klgh phvvdjhv."
)

_SAMPLE_CACHE = {}      # 快取從 test.txt 判斷出來的範例密文

# 左方區塊的三個分頁名稱（同時用於 --tab 除錯參數的合法性檢查）
TAB_NAMES = ("頻率直方圖", "位移明細", "候選排名")


# ==================== 範例密文 ====================


def _looks_like_cipher(core, line):
    """
    用既有的混合評分判斷某一行是否「像被位移過的密文」。

    作法：對 26 種位移各算一次混合分數；
    若最佳位移不是 0（未位移），且明顯優於位移 0，就視為密文行。
    這樣即使範例檔混雜明文與密文，也能自動挑出密文段落。
    """
    if len(core.extract_words(line)) < 3:      # 太短的行無法可靠判斷
        return False
    scores = [core.mixed_score(core.decryption(line, k)) for k in range(26)]
    best_k = max(range(26), key=lambda k: scores[k])
    return best_k != 0 and scores[best_k] > scores[0] + 0.05


def load_sample_cipher(core=None):
    """
    取得範例密文：優先自動挑出 test.txt 中的密文段落。

    順序為：
        1. 逐行用 _looks_like_cipher 判斷，收集所有像密文的行。
        2. 若一行都判斷不出來，退而假設後半段（第 5 行之後）是密文。
        3. 最後才使用程式內建的備用範例。

    判斷結果會快取，避免重複按「載入範例密文」時重算。
    """
    if core is None or not SAMPLE_FILE.exists():
        return FALLBACK_CIPHER
    if "sample" in _SAMPLE_CACHE:
        return _SAMPLE_CACHE["sample"]
    try:
        text = SAMPLE_FILE.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return FALLBACK_CIPHER

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return FALLBACK_CIPHER

    cipher_lines = [ln for ln in lines if _looks_like_cipher(core, ln)]
    if cipher_lines:
        result = "\n".join(cipher_lines)
    elif len(lines) > 4:
        result = "\n".join(lines[4:])
    else:
        result = text.strip() or FALLBACK_CIPHER

    _SAMPLE_CACHE["sample"] = result
    return result


# ==================== 主應用程式 ====================


class CaesarCipherApp(ctk.CTk):
    """凱撒密碼破解工具的主視窗。"""

    def __init__(self, core, prefill="", appearance="跟隨系統"):
        super().__init__()
        self.core = core
        self.appearance_name = appearance

        # 最近一次分析的結果（提供給候選按鈕與複製功能使用）
        self.rows = []            # 每個位移的完整分數與解密文字
        self.best_k = None        # 混合分數最高的位移
        self.display_k = None     # 目前顯示在右方區塊的位移
        self.counts = {}          # 原始密文的 A-Z 次數
        self.total_letters = 0

        self.title("凱撒密碼破解器 · Caesar Cipher Analyzer")
        self.configure(fg_color=COLOR_BG)

        # 視窗固定為最大化：先配置一個足以容納版面的尺寸，鎖定不可縮放後再最大化。
        # Windows 上 resizable(False, False) 會一併停用標題列的最大化／還原鈕，
        # 因此使用者無法把視窗改成其他大小，達到「固定最大化」的效果。
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"{max(1100, screen_w - 180)}x{max(640, screen_h - 120)}+0+0")
        self.minsize(1100, 640)
        self.resizable(False, False)
        # 注意：不可用 after(0)。CustomTkinter 在 mainloop() 一開始會先
        # withdraw() 再 update_idletasks() 後還原視窗狀態（為了設定標題列深色），
        # after(0) 會在該 update_idletasks() 內被執行，導致我們的最大化被它還原成
        # normal；延遲 50ms 可確保在它之後才最大化。
        self.after(50, self._maximize_window)

        # 視窗以三列為主：標題列 / 輸入區 / 左右輸出區，最後再加上狀態列
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_input()
        self._build_panes()
        self._build_status()

        # Ctrl+Enter 可直接開始分析
        self.bind("<Control-Return>", lambda _event: self.run_analysis())

        if prefill:
            self.entry.delete("1.0", "end")
            self.entry.insert("1.0", prefill)
            self.after(200, self.run_analysis)
        else:
            self.after(150, self.entry.focus_set)

    # ---------- 視窗最大化 ----------

    def _maximize_window(self):
        """
        把視窗最大化。

        優先用 Windows 的 'zoomed' 狀態（填滿工作區、保留工作列）；
        若平台不支援，才退回填滿整個螢幕。
        """
        try:
            self.state("zoomed")
        except tk.TclError:
            self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}+0+0")

    # ---------- 版面：標題列 ----------

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(12, 8))
        header.grid_columnconfigure(0, weight=1)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            left, text="凱撒密碼破解器", font=FONT_TITLE, text_color=COLOR_TEXT
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            left,
            text="卡方分布 + 雙字母組 + 三字母組 + 元音比例的混合評分",
            font=FONT_CAPTION,
            text_color=COLOR_MUTED,
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.grid(row=0, column=1, sticky="e")

        ctk.CTkLabel(right, text="外觀模式", font=FONT_SMALL, text_color=COLOR_MUTED).grid(
            row=0, column=0, padx=(0, 8)
        )
        self.appearance_var = tk.StringVar(value=self.appearance_name)
        ctk.CTkSegmentedButton(
            right,
            values=["跟隨系統", "淺色", "深色"],
            variable=self.appearance_var,
            command=self._on_appearance_change,
            font=FONT_SMALL,
        ).grid(row=0, column=1)

    def _on_appearance_change(self, choice):
        """切換 CustomTkinter 外觀模式（顏色 tuple 會自動套用）。"""
        mapping = {"跟隨系統": "System", "淺色": "Light", "深色": "Dark"}
        ctk.set_appearance_mode(mapping.get(choice, "System"))

    # ---------- 版面：輸入區 ----------

    def _build_input(self):
        card = ctk.CTkFrame(
            self, corner_radius=16, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER
        )
        card.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        card.grid_columnconfigure(0, weight=1)

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        head.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(head, text="密文輸入", font=FONT_SECTION, text_color=COLOR_TEXT).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(
            head,
            text="提示：Ctrl + Enter 可直接分析",
            font=FONT_CAPTION,
            text_color=COLOR_MUTED,
        ).grid(row=0, column=1, sticky="e")

        self.entry = ctk.CTkTextbox(
            card,
            height=96,
            corner_radius=12,
            font=FONT_MONO,
            fg_color=COLOR_ENTRY,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
            wrap="word",
        )
        self.entry.grid(row=1, column=0, sticky="ew", padx=16)

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="ew", padx=16, pady=(10, 14))

        self.analyze_btn = ctk.CTkButton(
            actions,
            text="開始分析",
            width=120,
            height=34,
            corner_radius=10,
            font=FONT_BODY,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self.run_analysis,
        )
        self.analyze_btn.grid(row=0, column=0)

        for col, (text, command) in enumerate(
            [
                ("從檔案載入", self.load_from_file),
                ("載入範例密文", self.load_sample),
                ("清空", self.clear_all),
            ],
            start=1,
        ):
            ctk.CTkButton(
                actions,
                text=text,
                width=110,
                height=34,
                corner_radius=10,
                font=FONT_BODY,
                fg_color=COLOR_CARD_ALT,
                text_color=COLOR_TEXT,
                hover_color=COLOR_BORDER,
                border_width=1,
                border_color=COLOR_BORDER,
                command=command,
            ).grid(row=0, column=col, padx=(8, 0))

    # ---------- 版面：左右兩個輸出區塊 ----------

    def _build_panes(self):
        panes = ctk.CTkFrame(self, fg_color="transparent")
        panes.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 8))
        panes.grid_rowconfigure(0, weight=1)
        # 右方是主要結果（解密全文），寬度給得比左方多一些
        panes.grid_columnconfigure(0, weight=10, uniform="pane")
        panes.grid_columnconfigure(1, weight=11, uniform="pane")

        self._build_left_pane(panes)
        self._build_right_pane(panes)

    # 左方區塊：所有輔助統計數據

    def _build_left_pane(self, parent):
        card = ctk.CTkFrame(
            parent, corner_radius=16, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER
        )
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(3, weight=1)

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="統計數據", font=FONT_SECTION, text_color=COLOR_TEXT).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(
            head, text="頻率分布 · 各位移分數 · 候選排名", font=FONT_CAPTION, text_color=COLOR_MUTED
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # 摘要數字（字母總數 / 單詞數 / 相異字母數）
        summary = ctk.CTkFrame(card, corner_radius=12, fg_color=COLOR_CARD_ALT)
        summary.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 6))
        for col in range(3):
            summary.grid_columnconfigure(col, weight=1)

        self.stat_letters = self._make_stat(summary, 0, "字母總數")
        self.stat_words = self._make_stat(summary, 1, "單詞數")
        self.stat_distinct = self._make_stat(summary, 2, "相異字母數")

        # 動態權重（依文本長度自動調整）：四個迷你長條並排，節省垂直空間
        weights_box = ctk.CTkFrame(card, corner_radius=12, fg_color="transparent")
        weights_box.grid(row=2, column=0, sticky="ew", padx=16, pady=(2, 4))
        weights_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            weights_box,
            text="動態權重（依字母總數自動調整）",
            font=FONT_SMALL,
            text_color=COLOR_MUTED,
        ).grid(row=0, column=0, sticky="w")

        bars_row = ctk.CTkFrame(weights_box, fg_color="transparent")
        bars_row.grid(row=1, column=0, sticky="ew", pady=(4, 0))
        self.weight_rows = {}
        for col, (key, label) in enumerate(
            [
                ("chi", "chi 卡方"),
                ("bigram", "bigram 雙字母"),
                ("trigram", "trigram 三字母"),
                ("vowel", "vowel 元音"),
            ]
        ):
            bars_row.grid_columnconfigure(col, weight=1, uniform="wcol")
            cell = ctk.CTkFrame(bars_row, fg_color="transparent")
            cell.grid(row=0, column=col, sticky="ew", padx=(0, 10) if col < 3 else 0)
            cell.grid_columnconfigure(0, weight=1)

            head_line = ctk.CTkFrame(cell, fg_color="transparent")
            head_line.grid(row=0, column=0, sticky="ew")
            head_line.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(
                head_line, text=label, font=FONT_CAPTION, text_color=COLOR_MUTED, anchor="w"
            ).grid(row=0, column=0, sticky="w")
            value = ctk.CTkLabel(
                head_line, text="—", font=FONT_MONO_SMALL, text_color=COLOR_TEXT, anchor="e"
            )
            value.grid(row=0, column=1, sticky="e")

            bar = ctk.CTkProgressBar(cell, height=7, corner_radius=4, progress_color=COLOR_ACCENT)
            bar.set(0)
            bar.grid(row=1, column=0, sticky="ew", pady=(2, 0))
            self.weight_rows[key] = (bar, value)

        # 分頁：直方圖 / 位移明細 / 候選排名（全部都在左方區塊內）
        self.tabs = ctk.CTkTabview(
            card,
            corner_radius=12,
            fg_color=COLOR_CARD_ALT,
            segmented_button_selected_color=COLOR_ACCENT,
            segmented_button_selected_hover_color=COLOR_ACCENT_HOVER,
            text_color=COLOR_TEXT,
        )
        self.tabs.grid(row=3, column=0, sticky="nsew", padx=16, pady=(4, 16))
        for name in TAB_NAMES:
            self.tabs.add(name)
            tab = self.tabs.tab(name)
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)
            if name != "頻率直方圖":
                tab.grid_rowconfigure(1, weight=1)

        self._build_histogram_tab(self.tabs.tab("頻率直方圖"))

        self.detail_box = self._make_readonly_box(self.tabs.tab("位移明細"), row=0)
        self.ranking_box = self._make_readonly_box(self.tabs.tab("候選排名"), row=0)

    def _make_stat(self, parent, column, caption):
        """建立單一統計數字方塊，回傳數值標籤以便更新。"""
        box = ctk.CTkFrame(parent, fg_color="transparent")
        box.grid(row=0, column=column, sticky="ew", padx=10, pady=10)
        value = ctk.CTkLabel(box, text="—", font=("Consolas", 18, "bold"), text_color=COLOR_TEXT)
        value.grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(box, text=caption, font=FONT_CAPTION, text_color=COLOR_MUTED).grid(
            row=1, column=0, sticky="w"
        )
        return value

    def _make_readonly_box(self, parent, row=0):
        """建立唯讀的文字輸出框（唯讀 = 使用者不能編輯，但仍可選取複製）。"""
        box = ctk.CTkTextbox(
            parent,
            corner_radius=10,
            font=FONT_MONO_SMALL,
            fg_color=COLOR_ENTRY,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
            wrap="word",
        )
        box.grid(row=row, column=0, sticky="nsew", padx=6, pady=6)
        box.configure(state="disabled")
        return box

    def _build_histogram_tab(self, tab):
        """字母頻率直方圖：以進度條呈現每個字母的百分比。"""
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 4))
        top.grid_columnconfigure(0, weight=1)

        self.hist_caption = ctk.CTkLabel(
            top, text="尚無資料", font=FONT_CAPTION, text_color=COLOR_MUTED
        )
        self.hist_caption.grid(row=0, column=0, sticky="w")

        self.show_zero_var = tk.BooleanVar(value=False)
        ctk.CTkSwitch(
            top,
            text="顯示 0 次字母",
            variable=self.show_zero_var,
            font=FONT_CAPTION,
            text_color=COLOR_MUTED,
            command=self._render_histogram,
            progress_color=COLOR_ACCENT,
            width=40,
        ).grid(row=0, column=1, sticky="e")

        self.hist_frame = ctk.CTkScrollableFrame(
            tab, corner_radius=10, fg_color=COLOR_ENTRY, border_width=1, border_color=COLOR_BORDER
        )
        self.hist_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.hist_frame.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

    # 右方區塊：最有可能的偏移量與該位移底下的解密結果

    def _build_right_pane(self, parent):
        card = ctk.CTkFrame(
            parent, corner_radius=16, fg_color=COLOR_CARD, border_width=1, border_color=COLOR_BORDER
        )
        card.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(4, weight=1)

        head = ctk.CTkFrame(card, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 4))
        head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(head, text="主要結果", font=FONT_SECTION, text_color=COLOR_TEXT).grid(
            row=0, column=0, sticky="w"
        )
        ctk.CTkLabel(
            head, text="最有可能的偏移量與其解密結果", font=FONT_CAPTION, text_color=COLOR_MUTED
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # 最有可能偏移量 + 混合分數
        best = ctk.CTkFrame(card, corner_radius=14, fg_color=COLOR_CARD_ALT)
        best.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 8))
        best.grid_columnconfigure(0, weight=1)
        best.grid_columnconfigure(1, weight=1)

        shift_box = ctk.CTkFrame(best, fg_color="transparent")
        shift_box.grid(row=0, column=0, sticky="nsew", padx=16, pady=12)
        ctk.CTkLabel(
            shift_box, text="最有可能偏移量", font=FONT_CAPTION, text_color=COLOR_MUTED
        ).grid(row=0, column=0, sticky="w")
        self.shift_label = ctk.CTkLabel(
            shift_box, text="k = —", font=FONT_SHIFT_BIG, text_color=COLOR_ACCENT
        )
        self.shift_label.grid(row=1, column=0, sticky="w")

        score_box = ctk.CTkFrame(best, fg_color="transparent")
        score_box.grid(row=0, column=1, sticky="nsew", padx=16, pady=12)
        score_box.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            score_box, text="混合分數（越高越像英文）", font=FONT_CAPTION, text_color=COLOR_MUTED
        ).grid(row=0, column=0, sticky="w")
        self.score_label = ctk.CTkLabel(
            score_box, text="—", font=FONT_SCORE_BIG, text_color=COLOR_TEXT
        )
        self.score_label.grid(row=1, column=0, sticky="w", pady=(2, 4))
        self.score_bar = ctk.CTkProgressBar(
            score_box, height=10, corner_radius=5, progress_color=COLOR_ACCENT
        )
        self.score_bar.set(0)
        self.score_bar.grid(row=2, column=0, sticky="ew")
        self.score_note = ctk.CTkLabel(
            score_box, text="等待分析", font=FONT_CAPTION, text_color=COLOR_MUTED
        )
        self.score_note.grid(row=3, column=0, sticky="w", pady=(4, 0))

        # 候選前三名（點選可切換右下方要顯示哪個位移的結果）
        candidates = ctk.CTkFrame(card, fg_color="transparent")
        candidates.grid(row=2, column=0, sticky="ew", padx=16)
        candidates.grid_columnconfigure(4, weight=1)
        ctk.CTkLabel(
            candidates, text="候選前三名", font=FONT_CAPTION, text_color=COLOR_MUTED
        ).grid(row=0, column=0, padx=(0, 8))
        self.candidate_buttons = []
        for idx in range(3):
            btn = ctk.CTkButton(
                candidates,
                text="—",
                width=132,
                height=30,
                corner_radius=9,
                font=FONT_MONO_SMALL,
                fg_color=COLOR_CARD_ALT,
                text_color=COLOR_TEXT,
                hover_color=COLOR_BORDER,
                border_width=1,
                border_color=COLOR_BORDER,
                command=lambda i=idx: self._show_candidate(i),
                state="disabled",
            )
            btn.grid(row=0, column=idx + 1, padx=4)
            self.candidate_buttons.append(btn)

        # 解密結果
        result_head = ctk.CTkFrame(card, fg_color="transparent")
        result_head.grid(row=3, column=0, sticky="ew", padx=16, pady=(12, 4))
        result_head.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            result_head, text="在此偏移量下的解密結果", font=FONT_SECTION, text_color=COLOR_TEXT
        ).grid(row=0, column=0, sticky="w")
        self.display_note = ctk.CTkLabel(
            result_head, text="尚未分析", font=FONT_CAPTION, text_color=COLOR_MUTED
        )
        self.display_note.grid(row=1, column=0, sticky="w", pady=(2, 0))

        self.result_box = ctk.CTkTextbox(
            card,
            corner_radius=12,
            font=("Consolas", 14),
            fg_color=COLOR_ENTRY,
            border_width=1,
            border_color=COLOR_BORDER,
            text_color=COLOR_TEXT,
            wrap="word",
        )
        self.result_box.grid(row=4, column=0, sticky="nsew", padx=16)
        self.result_box.insert("1.0", "請在上方輸入密文後按「開始分析」。")
        self.result_box.configure(state="disabled")

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=5, column=0, sticky="ew", padx=16, pady=(10, 14))
        self.copy_btn = ctk.CTkButton(
            actions,
            text="複製結果",
            width=110,
            height=34,
            corner_radius=10,
            font=FONT_BODY,
            fg_color=COLOR_ACCENT,
            hover_color=COLOR_ACCENT_HOVER,
            command=self.copy_result,
            state="disabled",
        )
        self.copy_btn.grid(row=0, column=0)
        self.save_btn = ctk.CTkButton(
            actions,
            text="另存為 .txt",
            width=120,
            height=34,
            corner_radius=10,
            font=FONT_BODY,
            fg_color=COLOR_CARD_ALT,
            text_color=COLOR_TEXT,
            hover_color=COLOR_BORDER,
            border_width=1,
            border_color=COLOR_BORDER,
            command=self.save_result,
            state="disabled",
        )
        self.save_btn.grid(row=0, column=1, padx=(8, 0))

    # ---------- 版面：狀態列 ----------

    def _build_status(self):
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 12))
        bar.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(
            bar, text="就緒：請輸入密文。", font=FONT_CAPTION, text_color=COLOR_MUTED, anchor="w"
        )
        self.status_label.grid(row=0, column=0, sticky="w")

    def _set_status(self, text, color=COLOR_MUTED):
        self.status_label.configure(text=text, text_color=color)

    # ---------- 輸入區按鈕行為 ----------

    def load_from_file(self):
        """從外部文字檔載入密文。"""
        path = filedialog.askopenfilename(
            title="選擇要破解的文字檔",
            filetypes=[("文字檔", "*.txt"), ("所有檔案", "*.*")],
            initialdir=str(WORK_DIR),
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            self._set_status(f"讀取失敗：{exc}", COLOR_RED)
            return
        self.entry.delete("1.0", "end")
        self.entry.insert("1.0", text)
        self._set_status(f"已載入檔案：{Path(path).name}（{len(text)} 字元）", COLOR_MUTED)

    def load_sample(self):
        """載入內建 / test.txt 的範例密文。"""
        sample = load_sample_cipher(self.core)
        self.entry.delete("1.0", "end")
        self.entry.insert("1.0", sample)
        self._set_status("已載入範例密文，按「開始分析」即可破解。", COLOR_MUTED)

    def _reset_outputs(self, result_placeholder="請在上方輸入密文後按「開始分析」。"):
        """把左右兩個區塊重設回「尚未分析」的狀態（清空或無字母時使用）。"""
        self.rows = []
        self.best_k = None
        self.display_k = None

        self._set_text(self.detail_box, "")
        self._set_text(self.ranking_box, "")

        self.shift_label.configure(text="k = —", text_color=COLOR_ACCENT)
        self.score_label.configure(text="—")
        self.score_bar.set(0)
        self.score_note.configure(text="等待分析")
        self.display_note.configure(text="尚未分析")
        self._set_text(self.result_box, result_placeholder)

        for _key, (bar, value) in self.weight_rows.items():
            bar.set(0)
            value.configure(text="—")
        for btn in self.candidate_buttons:
            btn.configure(text="—", state="disabled")
        self.copy_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")

        self.stat_letters.configure(text="—")
        self.stat_words.configure(text="—")
        self.stat_distinct.configure(text="—")

    def clear_all(self):
        """清空輸入與所有輸出。"""
        self.entry.delete("1.0", "end")
        self.counts = {}
        self.total_letters = 0
        self._reset_outputs()
        self._render_histogram()
        self._set_status("已清空。", COLOR_MUTED)
        self.entry.focus_set()

    # ---------- 主要分析流程 ----------

    def run_analysis(self):
        """
        核心流程：完全沿用 Untitled-1.py 的函式。

        1. 統計密文字母分布（count_letters）並畫出直方圖。
        2. 依字母總數取得動態權重（get_dynamic_weights）。
        3. 對 k = 0..25 逐一凱撒解密（decryption），並計算四項分數與混合分數。
        4. 左方顯示所有數據，右方顯示最佳 k 及其解密結果。
        """
        text = self.entry.get("1.0", "end-1c")
        if not text.strip():
            self._set_status("請先輸入要破解的密文。", COLOR_AMBER)
            self.entry.focus_set()
            return

        started = time.perf_counter()

        counts = self.core.count_letters(text)
        total_letters = sum(counts.values())
        self.counts = counts
        self.total_letters = total_letters

        if total_letters == 0:
            # 與原程式一致：沒有英文字母就不必嘗試解密
            self._set_status("輸入中找不到任何英文字母，無法進行破解。", COLOR_RED)
            self._reset_outputs("無有效字母，沒有可顯示的解密結果。")
            self._render_histogram()
            self._set_text(self.detail_box, "No letters found.\n（找不到任何英文字母）")
            self._set_text(self.ranking_box, "No letters found.\n（找不到任何英文字母）")
            return

        # 字數統計與動態權重
        words = self.core.extract_words(text)
        weights = self.core.get_dynamic_weights(total_letters)
        chi_w, bg_w, tg_w, vw_w = weights

        self.stat_letters.configure(text=f"{total_letters}")
        self.stat_words.configure(text=f"{len(words)}")
        self.stat_distinct.configure(text=f"{sum(1 for c in counts.values() if c > 0)}")

        for key, value in zip(("chi", "bigram", "trigram", "vowel"), weights):
            bar, label = self.weight_rows[key]
            bar.set(value)
            label.configure(text=f"{value:.3f}")

        self._render_histogram()

        # 逐一嘗試 26 種位移
        rows = []
        for k in range(26):
            decrypted = self.core.decryption(text, k)
            chi2, chi_score, bg, tg, vw, _ = self.core.compute_all_scores(decrypted)
            mixed = self.core.mixed_score_from_parts(chi_score, bg, tg, vw, *weights)
            rows.append(
                {
                    "k": k,
                    "chi2": chi2,
                    "chi": chi_score,
                    "bigram": bg,
                    "trigram": tg,
                    "vowel": vw,
                    "mixed": mixed,
                    "text": decrypted,
                }
            )

        self.rows = rows
        # sorted 為穩定排序，分數相同時會保持 k 由小到大的順序
        ranking = sorted(rows, key=lambda r: r["mixed"], reverse=True)
        self.best_k = ranking[0]["k"]

        self._render_details(rows, weights, total_letters)
        self._render_ranking(ranking)
        self._show_candidate(0)

        elapsed = (time.perf_counter() - started) * 1000
        self._set_status(
            f"分析完成：26 種位移 · 字母總數 {total_letters} · 最可能偏移量 k = {self.best_k}"
            f" · 混合分數 {ranking[0]['mixed']:.4f} · 耗時 {elapsed:.1f} 毫秒",
            COLOR_GREEN,
        )

    # ---------- 左方區塊的內容 ----------

    def _set_text(self, box, content):
        """更新唯讀文字框內容。"""
        box.configure(state="normal")
        box.delete("1.0", "end")
        box.insert("1.0", content)
        box.configure(state="disabled")

    def _render_histogram(self):
        """
        以進度條重繪字母頻率直方圖。

        每個進度條代表該字母佔全部字母的百分比（1% 對應 0.01），
        等同原程式文字直方圖中「1 個符號 = 1%」的概念。
        """
        for child in self.hist_frame.winfo_children():
            child.destroy()

        total = sum(self.counts.values())
        if total == 0:
            self.hist_caption.configure(text="尚無資料（請先分析）")
            ctk.CTkLabel(
                self.hist_frame, text="尚未分析，沒有頻率資料。", font=FONT_SMALL, text_color=COLOR_MUTED
            ).grid(row=0, column=0, sticky="w", padx=6, pady=6)
            return

        self.hist_caption.configure(text=f"Total letters: {total}　（每條長度 = 該字母佔比）")

        show_zero = self.show_zero_var.get()
        row_index = 0
        for letter, count in self.counts.items():
            if not show_zero and count == 0:
                continue

            percent = count / total * 100
            if count == 0:
                bar_color = COLOR_BORDER
            elif percent >= 8:
                bar_color = COLOR_AMBER
            elif percent >= 4:
                bar_color = COLOR_ACCENT
            else:
                bar_color = COLOR_VIOLET

            row = ctk.CTkFrame(self.hist_frame, fg_color="transparent")
            row.grid(row=row_index, column=0, sticky="ew", pady=1)
            row.grid_columnconfigure(2, weight=1)

            ctk.CTkLabel(
                row, text=letter, font=FONT_MONO_SMALL, text_color=COLOR_TEXT, width=18, anchor="w"
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(
                row,
                text=f"{count:>3}",
                font=FONT_MONO_SMALL,
                text_color=COLOR_MUTED,
                width=34,
                anchor="e",
            ).grid(row=0, column=1, sticky="e", padx=(4, 8))

            bar = ctk.CTkProgressBar(row, height=10, corner_radius=5, progress_color=bar_color)
            bar.set(min(percent / 100.0, 1.0))
            bar.grid(row=0, column=2, sticky="ew")

            ctk.CTkLabel(
                row,
                text=f"{percent:>6.2f}%",
                font=FONT_MONO_SMALL,
                text_color=COLOR_TEXT if count else COLOR_MUTED,
                width=60,
                anchor="e",
            ).grid(row=0, column=3, sticky="e", padx=(8, 4))
            row_index += 1

    def _render_details(self, rows, weights, total_letters):
        """
        位移明細：每一行對應原程式針對單一 k 的輸出格式，
        另外附上該位移解密文字的預覽（完整內容顯示在右方區塊）。
        """
        chi_w, bg_w, tg_w, vw_w = weights
        lines = [
            "Possible decryption shifts (Caesar):",
            str(list(range(26))),
            "",
            f"Dynamic weights (total letters = {total_letters}): "
            f"chi = {chi_w:.3f}, bigram = {bg_w:.3f}, "
            f"trigram = {tg_w:.3f}, vowel = {vw_w:.3f}",
            "",
        ]
        for row in rows:
            marker = "  " if row["k"] != self.best_k else "★ "
            lines.append(
                f"{marker}shift k = {row['k']:2d} | chi2 = {row['chi2']:8.2f} | "
                f"chi = {row['chi']:.4f} | bigram = {row['bigram']:.4f} | "
                f"trigram = {row['trigram']:.4f} | vowel = {row['vowel']:.4f} | "
                f"mixed = {row['mixed']:.4f}"
            )
            preview = " ".join(row["text"].split())
            if len(preview) > 90:
                preview = preview[:90] + "…"
            lines.append(f"      ↳ {preview}")
        lines.append("")
        lines.append("★ = 混合分數最高（最像英文）的位移；完整解密內容請見右方區塊。")
        self._set_text(self.detail_box, "\n".join(lines))

    def _render_ranking(self, ranking):
        """候選排名：依混合分數由高到低列出 26 種位移。"""
        lines = [
            "rank   k    mixed     chi    bigram  trigram   vowel   preview",
            "-" * 78,
        ]
        for rank, row in enumerate(ranking, start=1):
            preview = " ".join(row["text"].split())
            if len(preview) > 40:
                preview = preview[:40] + "…"
            lines.append(
                f"{rank:>4}  {row['k']:>2}  {row['mixed']:.4f}  {row['chi']:.4f}  "
                f"{row['bigram']:.4f}  {row['trigram']:.4f}  {row['vowel']:.4f}  {preview}"
            )
        lines.append("")
        lines.append("（mixed 為混合分數，其餘四項為各分項分數，皆介於 0~1）")
        self._set_text(self.ranking_box, "\n".join(lines))

    # ---------- 右方區塊的內容 ----------

    def _show_candidate(self, index):
        """
        在右方區塊顯示候選排名第 index 名（0 起算）的位移與解密結果。

        預設會顯示第 1 名，也就是「最有可能偏移量」。
        """
        if not self.rows:
            return
        ranking = sorted(self.rows, key=lambda r: r["mixed"], reverse=True)
        if index >= len(ranking):
            return

        row = ranking[index]
        self.display_k = row["k"]
        is_best = row["k"] == self.best_k

        # 候選按鈕文字與樣式
        for idx, btn in enumerate(self.candidate_buttons):
            if idx < len(ranking):
                cand = ranking[idx]
                btn.configure(
                    text=f"k={cand['k']:>2}  {cand['mixed']:.4f}",
                    state="normal",
                    fg_color=COLOR_ACCENT if idx == index else COLOR_CARD_ALT,
                    text_color="#FFFFFF" if idx == index else COLOR_TEXT,
                )

        self.shift_label.configure(text=f"k = {row['k']}", text_color=COLOR_ACCENT)
        self.score_label.configure(text=f"{row['mixed']:.4f}")
        self.score_bar.set(max(0.0, min(row["mixed"], 1.0)))

        top_score = ranking[0]["mixed"]
        gap = top_score - ranking[1]["mixed"] if len(ranking) > 1 else top_score
        if is_best:
            self.score_note.configure(
                text=f"領先第 2 名 {gap:.4f}　·　chi2 = {row['chi2']:.2f}", text_color=COLOR_MUTED
            )
            self.display_note.configure(
                text=f"顯示第 1 名（最有可能偏移量 k = {row['k']}）", text_color=COLOR_GREEN
            )
        else:
            self.score_note.configure(
                text=f"落後第 1 名 {top_score - row['mixed']:.4f}　·　chi2 = {row['chi2']:.2f}",
                text_color=COLOR_MUTED,
            )
            self.display_note.configure(
                text=f"目前顯示候選第 {index + 1} 名：k = {row['k']}（最有可能為 k = {self.best_k}）",
                text_color=COLOR_AMBER,
            )

        self._set_text(self.result_box, row["text"])
        self.copy_btn.configure(state="normal")
        self.save_btn.configure(state="normal")

    # ---------- 右方區塊的按鈕行為 ----------

    def copy_result(self):
        """把目前顯示的解密結果複製到剪貼簿。"""
        if self.display_k is None:
            return
        text = self.result_box.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(text)
        self._set_status(f"已複製 k = {self.display_k} 的解密結果到剪貼簿。", COLOR_GREEN)

    def save_result(self):
        """把目前顯示的解密結果另存為文字檔。"""
        if self.display_k is None:
            return
        path = filedialog.asksaveasfilename(
            title="儲存解密結果",
            defaultextension=".txt",
            initialfile=f"decrypted_k{self.display_k}.txt",
            filetypes=[("文字檔", "*.txt"), ("所有檔案", "*.*")],
            initialdir=str(WORK_DIR),
        )
        if not path:
            return
        try:
            Path(path).write_text(self.result_box.get("1.0", "end-1c"), encoding="utf-8")
        except OSError as exc:
            self._set_status(f"儲存失敗：{exc}", COLOR_RED)
            return
        self._set_status(f"已儲存：{path}", COLOR_GREEN)


# ==================== 程式進入點 ====================


def _parse_args(argv):
    """解析命令列參數，回傳 (appearance, tab, demo, selftest, auto_close)。"""
    appearance = "跟隨系統"
    tab = None
    auto_close = None
    for arg in argv:
        if arg.startswith("--auto-close="):
            auto_close = float(arg.split("=", 1)[1])
        elif arg.startswith("--appearance="):
            appearance = arg.split("=", 1)[1]
        elif arg.startswith("--tab="):
            # 除錯／截圖用：啟動後直接切到左方指定的分頁
            tab = arg.split("=", 1)[1]
    return appearance, tab, ("--demo" in argv), ("--selftest" in argv), auto_close


def _run_selftest(app, core):
    """
    非互動自我測試：檢查分析流程與兩個輸出區塊的內容是否正確。

    回傳 True 表示全部通過；打包成視窗模式 exe 時沒有主控台，
    結果會以程式結束碼呈現（0 = 通過、1 = 失敗）。
    """
    checks = []

    def check(name, condition, detail=""):
        checks.append(bool(condition))
        _log(f"[selftest] {'PASS' if condition else 'FAIL'}  {name} {detail}")

    app.update()  # 讓所有待處理的繪製與 after 工作先完成

    check("分析產生 26 種位移", len(app.rows) == 26, f"rows={len(app.rows)}")
    ranking = sorted(app.rows, key=lambda r: r["mixed"], reverse=True)
    check("找出最有可能偏移量", app.best_k is not None, f"best_k={app.best_k}")
    check(
        "範例密文（ROT13）最佳位移為 13",
        app.best_k == 13,
        f"best_k={app.best_k} score={ranking[0]['mixed']:.4f}" if app.rows else "",
    )
    check("左方位移明細有內容", len(app.detail_box.get("1.0", "end-1c")) > 500)
    check("左方候選排名有內容", len(app.ranking_box.get("1.0", "end-1c")) > 500)
    check(
        "直方圖有資料列",
        len(app.hist_frame.winfo_children()) > 0,
        f"rows={len(app.hist_frame.winfo_children())}",
    )
    check("右方顯示解密結果", "rapidly evolving" in app.result_box.get("1.0", "end-1c"))

    # 切換候選名次
    app._show_candidate(1)
    app.update()
    check(
        "可切換到候選第 2 名",
        app.display_k == ranking[1]["k"] and "第 2 名" in app.display_note.cget("text"),
        f"display_k={app.display_k}",
    )
    app._show_candidate(0)
    app.update()

    # 複製結果
    try:
        app.copy_result()
        copied = app.clipboard_get()
        check("複製結果到剪貼簿", copied == app.result_box.get("1.0", "end-1c"))
    except tk.TclError as exc:
        check("複製結果到剪貼簿", False, f"clipboard error: {exc}")

    # 沒有英文字母的輸入
    app.entry.delete("1.0", "end")
    app.entry.insert("1.0", "12345 !!! ???")
    app.run_analysis()
    app.update()
    check("無字母輸入不會崩潰", app.rows == [] and app.best_k is None)

    # 清空
    app.clear_all()
    app.update()
    check("清空後回復初始狀態", app.rows == [] and app.weight_rows["chi"][1].cget("text") == "—")

    # 載入範例密文
    app.load_sample()
    app.update()
    check("載入範例密文", len(app.entry.get("1.0", "end-1c")) > 100)

    _log(f"[selftest] {sum(checks)}/{len(checks)} checks passed")
    _log("[selftest] OK" if all(checks) else "[selftest] FAILED")
    return all(checks)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    appearance, tab, demo, selftest, auto_close = _parse_args(argv)

    # 外觀模式可接受中文或英文名稱
    appearance_map = {
        "深色": "Dark", "Dark": "Dark", "dark": "Dark",
        "淺色": "Light", "Light": "Light", "light": "Light",
        "跟隨系統": "System", "System": "System", "system": "System",
    }
    if appearance not in appearance_map:
        appearance = "跟隨系統"
    ctk.set_appearance_mode(appearance_map[appearance])
    ctk.set_default_color_theme("blue")

    try:
        core = load_core_module()
    except Exception as exc:  # 核心檔案缺失或載入失敗時，給出明確訊息
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()
        root.title("錯誤")
        messagebox.showerror(
            "無法載入核心程式",
            f"載入 Untitled-1.py 失敗：\n{exc}\n\n請確認 caesar_gui.py 與 Untitled-1.py 位於同一個資料夾。",
        )
        root.destroy()
        return 1

    prefill = load_sample_cipher(core) if (demo or selftest) else ""
    app = CaesarCipherApp(core, prefill=prefill, appearance=appearance)
    if tab in TAB_NAMES:
        app.after(400, lambda: app.tabs.set(tab))

    outcome = {"ok": True}

    if selftest or auto_close:
        def _finish():
            # 自我測試／自動關閉：只結束 mainloop，不在事件回呼中 destroy 視窗。
            # 若在回呼中直接 destroy，CustomTkinter 於 mainloop 內的標題列處理
            # （withdraw -> update_idletasks -> 還原狀態）會對已銷毀的視窗呼叫
            # self.state()，而拋出 TclError: can't invoke "wm" command。
            try:
                outcome["ok"] = _run_selftest(app, core)
            except Exception as exc:            # 任何未預期錯誤都視為測試失敗
                _log(f"[selftest] EXCEPTION {exc!r}")
                outcome["ok"] = False
            finally:
                app.quit()

        delay = int((auto_close if auto_close else 1.5) * 1000)
        app.after(delay, _finish)

    app.mainloop()

    try:
        app.destroy()      # 真正關閉視窗留到 mainloop 結束之後
    except tk.TclError:
        pass

    return 0 if outcome["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
