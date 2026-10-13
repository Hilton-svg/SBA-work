# -*- coding: utf-8 -*-
"""產生專案介紹 PDF：凱撒密碼破解器（CustomTkinter GUI）。

使用 reportlab + Windows 內建中文字型（Microsoft JhengHei / Consolas），
輸出：凱撒密碼破解器_專案介紹.pdf（A4，含頁碼與截圖）。
"""

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, Image,
                                KeepTogether, PageBreak, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle)
from reportlab.pdfgen import canvas as rl_canvas

WORK = Path(__file__).resolve().parent.parent
OUT = WORK / "凱撒密碼破解器_專案介紹.pdf"
REPO_URL = "https://github.com/Hilton-svg/SBA-work"
CODE_FILE = WORK / "Untitled-1.py"      # 程式主體，完整收錄於附錄 B

# ---------------- 字型 ----------------
FONT_DIR = Path(r"C:\Windows\Fonts")
pdfmetrics.registerFont(TTFont("MSJH", str(FONT_DIR / "msjh.ttc"), subfontIndex=0))
pdfmetrics.registerFont(TTFont("MSJH-Bold", str(FONT_DIR / "msjhbd.ttc"), subfontIndex=0))
pdfmetrics.registerFont(TTFont("CONS", str(FONT_DIR / "consola.ttf")))
pdfmetrics.registerFont(TTFont("CONS-Bold", str(FONT_DIR / "consolab.ttf")))
pdfmetrics.registerFontFamily("MSJH", normal="MSJH", bold="MSJH-Bold",
                              italic="MSJH", boldItalic="MSJH-Bold")
pdfmetrics.registerFontFamily("CONS", normal="CONS", bold="CONS-Bold",
                              italic="CONS", boldItalic="CONS-Bold")

# ---------------- 色票 ----------------
NAVY = colors.HexColor("#0F2544")
ACCENT = colors.HexColor("#1D4ED8")
ACCENT_SOFT = colors.HexColor("#EFF4FF")
VIOLET = colors.HexColor("#7C3AED")
AMBER = colors.HexColor("#B45309")
GREEN = colors.HexColor("#15803D")
GRAY = colors.HexColor("#5A6472")
LIGHT = colors.HexColor("#F4F6FA")
BORDER = colors.HexColor("#C9D2E0")
WHITE = colors.white

PAGE_W, PAGE_H = A4
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 18 * mm, 24 * mm, 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN_X


# ---------------- 樣式 ----------------
def style(name, **kw):
    base = dict(name=name, fontName="MSJH", fontSize=10, leading=16,
                wordWrap="CJK", textColor=colors.HexColor("#1B2230"))
    base.update(kw)
    return ParagraphStyle(**base)


S = {
    "body": style("body"),
    "body_small": style("body_small", fontSize=9, leading=14),
    "lead": style("lead", fontSize=11, leading=18, textColor=colors.HexColor("#26303F")),
    "h1": style("h1", fontName="MSJH-Bold", fontSize=15, leading=20, textColor=NAVY),
    "h2": style("h2", fontName="MSJH-Bold", fontSize=11.5, leading=17, textColor=ACCENT,
                spaceBefore=4, spaceAfter=2),
    "bullet": style("bullet", leftIndent=12, bulletIndent=2, spaceAfter=1.5),
    "caption": style("caption", fontSize=8.5, leading=12, textColor=GRAY, alignment=TA_CENTER),
    "code": style("code", fontName="CONS", fontSize=8.4, leading=12.6,
                  textColor=colors.HexColor("#0B3B8C"), wordWrap=None),
    "listing": style("listing", fontName="CONS", fontSize=7.8, leading=10.0,
                     textColor=colors.HexColor("#14213D"), wordWrap=None),
    "cell": style("cell", fontSize=9.2, leading=13.6),
    "cell_b": style("cell_b", fontName="MSJH-Bold", fontSize=9.2, leading=13.6),
    "cell_head": style("cell_head", fontName="MSJH-Bold", fontSize=9.2, leading=13.6,
                       textColor=WHITE),
    "cell_mono": style("cell_mono", fontName="CONS", fontSize=8.6, leading=13, wordWrap=None),
    "cover_title": style("cover_title", fontName="MSJH-Bold", fontSize=23, leading=30,
                         textColor=WHITE),
    "cover_sub": style("cover_sub", fontSize=11.5, leading=17,
                       textColor=colors.HexColor("#C7D9FF")),
    "cover_meta": style("cover_meta", fontName="CONS", fontSize=8.6, leading=13,
                        textColor=colors.HexColor("#9FB6D9"), wordWrap=None),
    "qa_q": style("qa_q", fontName="MSJH-Bold", fontSize=9.6, leading=14.5, textColor=NAVY),
    "qa_a": style("qa_a", fontSize=9.4, leading=14.5, leftIndent=10),
}


def P(text, s="body"):
    """建立段落；等寬字型样式會自動把中文換成中文字型，避免掉字。"""
    if s in MONO_STYLES:
        text = cjk_wrap(text)
    return Paragraph(text, S[s])


# Consolas 沒有中文字形，若直接排版會整段中文消失；
# 因此等寬樣式的中文片段改用 <font name="MSJH"> 包住，由 reportlab 逐段換字型。
MONO_STYLES = {"code", "cell_mono", "cover_meta", "cell_mono_b"}
_CJK_RUN = re.compile(r"([^\x00-\x7F]+)")


def cjk_wrap(text, font="MSJH"):
    return _CJK_RUN.sub(lambda m: f'<font name="{font}">{m.group(1)}</font>', text)


def rule(color=ACCENT, thickness=1.1, space_before=2, space_after=7):
    return HRFlowable(width="100%", thickness=thickness, color=color,
                      spaceBefore=space_before, spaceAfter=space_after)


def h1(number, text):
    return [Spacer(1, 7), P(f"{number}&nbsp;&nbsp;{text}", "h1"), rule()]


def table(data, widths, header=True, align=None, font_col0_bold=True, pad=5):
    """建立樣式統一的表格；data 內含 Paragraph 或字串。"""
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), pad + 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad + 2),
        ("TOPPADDING", (0, 0), (-1, -1), pad),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad),
        ("LINEBELOW", (0, 0), (-1, -2), 0.4, BORDER),
        ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), NAVY),
                 ("LINEBELOW", (0, 0), (-1, 0), 0.6, NAVY)]
        for r in range(1, len(data)):
            if r % 2 == 0:
                cmds.append(("BACKGROUND", (0, r), (-1, r), LIGHT))
    else:
        for r in range(len(data)):
            if r % 2 == 1:
                cmds.append(("BACKGROUND", (0, r), (-1, r), LIGHT))
    if align:
        cmds += align
    t.setStyle(TableStyle(cmds))
    return t


def code_box(lines, width=None):
    """等寬字型的步驟／指令方塊（保留縮排、自動為中文換字型）。"""
    fixed = []
    for line in lines:
        stripped = line.lstrip(" ")
        # Paragraph 會合併連續空白，因此縮排改用 &nbsp; 實體
        fixed.append("&nbsp;" * (len(line) - len(stripped)) + stripped)
    body = "<br/>".join(fixed)
    t = Table([[P(body, "code")]], colWidths=[width or CONTENT_W], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F9FF")),
        ("BOX", (0, 0), (-1, -1), 0.7, colors.HexColor("#CBD9F5")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return t


def listing_line(text):
    """原始碼單行：完整保留縮排與空白，並把中文片段換成中文字型（Consolas 沒有中文字形）。"""
    buf = []
    for ch in text.replace("\t", "    "):
        if ch == " ":
            buf.append("&nbsp;")
        elif ch == "&":
            buf.append("&amp;")
        elif ch == "<":
            buf.append("&lt;")
        elif ch == ">":
            buf.append("&gt;")
        else:
            buf.append(ch)
    return Paragraph(cjk_wrap("".join(buf)) or "&nbsp;", S["listing"])


def pseudo_block(name, lines):
    """附錄 C 用：一個函式的偽代碼區塊（標題 + 等寬方塊），並避免標題與方塊被分頁拆散。"""
    return KeepTogether([P(name, "h2"), code_box(lines), Spacer(1, 7)])


def note_box(title, text, color=ACCENT_SOFT, border=ACCENT):
    lines = [[P(f"<b>{title}</b>", "cell_b")], [P(text, "cell")]]
    t = Table(lines, colWidths=[CONTENT_W], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("LINEBEFORE", (0, 0), (0, -1), 2.6, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (0, 0), 7),
        ("BOTTOMPADDING", (0, 0), (0, 0), 0),
        ("TOPPADDING", (0, 1), (0, 1), 0),
        ("BOTTOMPADDING", (0, 1), (0, 1), 7),
    ]))
    return t


def screenshot(path, width, caption):
    img = Image(str(path))
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = width
    img.drawHeight = width * ratio
    img.hAlign = "CENTER"
    return KeepTogether([img, Spacer(1, 3), P(caption, "caption"), Spacer(1, 8)])


# ---------------- 頁碼畫布 ----------------
class NumberedCanvas(rl_canvas.Canvas):
    """兩段式頁碼：先蒐集頁面，最後統一補上「第 X 頁 / 共 Y 頁」。"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_states = []

    def showPage(self):
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_states)
        for state in self._saved_states:
            self.__dict__.update(state)
            self._draw_footer(total)
            super().showPage()
        super().save()

    def _draw_footer(self, total):
        self.setStrokeColor(BORDER)
        self.setLineWidth(0.6)
        self.line(MARGIN_X, MARGIN_BOTTOM - 7 * mm,
                  PAGE_W - MARGIN_X, MARGIN_BOTTOM - 7 * mm)
        self.setFont("MSJH", 8.2)
        self.setFillColor(GRAY)
        self.drawString(MARGIN_X, MARGIN_BOTTOM - 13 * mm,
                        "凱撒密碼破解器 · Caesar Cipher Analyzer｜專案介紹"
                        "｜github.com/Hilton-svg/SBA-work")
        self.drawRightString(PAGE_W - MARGIN_X, MARGIN_BOTTOM - 13 * mm,
                             f"第 {self._pageNumber} 頁 / 共 {total} 頁")


def draw_page_decor(canv, doc):
    """每一頁最上方的細裝飾線。"""
    canv.saveState()
    canv.setFillColor(ACCENT)
    canv.rect(0, PAGE_H - 8 * mm, PAGE_W, 8 * mm, stroke=0, fill=1)
    canv.setFont("CONS", 7.6)
    canv.setFillColor(WHITE)
    canv.drawString(MARGIN_X, PAGE_H - 5.6 * mm, "CAESAR CIPHER ANALYZER  ·  CustomTkinter GUI")
    canv.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 5.6 * mm, "PROJECT OVERVIEW  ·  v1.0")
    canv.restoreState()


# ---------------- 內容 ----------------
def build_story():
    story = []

    # ===== 封面橫幅 =====
    banner = Table(
        [[P("凱撒密碼破解器", "cover_title")],
         [P("Caesar Cipher Analyzer｜以 CustomTkinter 打造的現代化密碼分析工具", "cover_sub")],
         [Spacer(1, 6)],
         [P("Python 3.14 · CustomTkinter 5.2.2 · PyInstaller 6.22.3 · Windows 桌面應用 · "
            "支援深色模式與單一 exe 打包", "cover_meta")],
         [P(f"GitHub 專案倉庫　{REPO_URL}", "cover_meta")]],
        colWidths=[CONTENT_W],
    )
    banner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("LEFTPADDING", (0, 0), (-1, -1), 18),
        ("RIGHTPADDING", (0, 0), (-1, -1), 18),
        ("TOPPADDING", (0, 0), (0, 0), 16),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 16),
    ]))
    story += [banner, Spacer(1, 12)]

    story += [P(
        "本專案是一套完整的<b>凱撒密碼破解工具</b>：運算核心在 <b>Untitled-1.py</b>"
        "（字母統計、卡方檢定、n-gram 命中率、元音比例與凱撒解密），互動介面在 "
        "<b>caesar_gui.py</b>（CustomTkinter 桌面視窗），兩者以函式呼叫串接。"
        "程式對 26 種可能的位移逐一評分，並把輸出編排為<b>左右兩個區塊</b>——"
        "右方放「最有可能偏移量與該偏移量下的解密結果」，左方放其餘所有統計數據。", "lead")]
    story += [Spacer(1, 10)]

    # ===== 特色 =====
    story += h1("01", "專案特色")
    feats = [
        [P("特色", "cell_head"), P("說明", "cell_head")],
        [P("雙區塊輸出", "cell_b"),
         P("右方區塊＝主要結果（最有可能偏移量 k、混合分數、該 k 的完整解密全文、候選前三名切換）；"
           "左方區塊＝其餘數據（字母頻率直方圖、26 種位移分數明細、候選排名、字母總數與動態權重）。")],
        [P("深色模式", "cell_b"),
         P("提供「跟隨系統／淺色／深色」即時切換；所有顏色以 (淺色, 深色) 色票定義，切換不需重建介面。")],
        [P("現代化版面", "cell_b"),
         P("圓角卡片式配置、彩色進度條直方圖、等寬字型數據表、狀態列即時顯示耗時與結論。")],
        [P("固定最大化視窗", "cell_b"),
         P("啟動即以 zoomed 狀態填滿工作區並鎖定尺寸（resizable 關閉），版面永遠一致、不會被誤縮放。")],
        [P("一鍵打包 exe", "cell_b"),
         P("build_exe.bat 可產出單一檔案 exe（13.1 MB）或免解壓資料夾版；核心程式與範例檔一併內嵌。")],
        [P("可重現的自我測試", "cell_b"),
         P("內建 --selftest：12 項功能檢查（分析、左右區塊內容、候選切換、剪貼簿、清空、無字母輸入等），"
           "以結束碼 0/1 表示通過與否，適合自動化驗證。")],
    ]
    story += [table(feats, [30 * mm, CONTENT_W - 30 * mm]), Spacer(1, 6)]

    # ===== 快速開始 =====
    story += h1("02", "快速開始")
    story += [P("三種啟動方式，任選一種即可：", "body"), Spacer(1, 5)]
    story += [code_box([
        "1) 雙擊執行檔（推薦，免安裝）",
        "   dist\\CaesarCipherGUI.exe                            # 單一檔案版",
        "   dist_portable\\CaesarCipherGUI\\CaesarCipherGUI.exe  # 資料夾版，啟動最快",
        "",
        "2) 雙擊批次檔：run_gui.bat（自動使用專案 .venv）",
        "",
        "3) 命令列：.venv\\Scripts\\python.exe caesar_gui.py [--demo | --selftest]",
    ])]
    story += [Spacer(1, 8)]
    story += [note_box(
        "操作提示",
        "在輸入框貼上密文後按 <b>開始分析</b>（或直接按 <b>Ctrl + Enter</b>）即可破解。"
        "也可以按「從檔案載入」讀取 .txt，或按「載入範例密文」載入 test.txt 中自動偵測到的密文段落。",
    )]

    # ===== 介面導覽 =====
    story += h1("03", "介面導覽")
    story += [screenshot(WORK / ".tools" / "preview_dark.png", CONTENT_W,
                         "圖 1　深色模式（固定最大化）：左方為統計數據，右方為主要結果")]
    layout = [
        [P("區域", "cell_head"), P("內容", "cell_head")],
        [P("標題列", "cell_b"), P("程式名稱與「外觀模式」三段切換鈕（跟隨系統／淺色／深色）。")],
        [P("輸入區", "cell_b"),
         P("密文輸入框，以及 <b>開始分析</b>、<b>從檔案載入</b>、<b>載入範例密文</b>、<b>清空</b> 四個按鈕。")],
        [P("左方：統計數據", "cell_b"),
         P("字母總數／單詞數／相異字母數、四項動態權重長條，以及三個分頁："
           "<b>頻率直方圖</b>（A–Z 彩色長條，可切換顯示 0 次字母）、"
           "<b>位移明細</b>（k = 0–25 的 chi2／chi／bigram／trigram／vowel／mixed 與預覽，最佳者標 ★）、"
           "<b>候選排名</b>（依混合分數排序的完整表格）。")],
        [P("右方：主要結果", "cell_b"),
         P("大字顯示<b>最有可能偏移量 k</b> 與混合分數（含進度條、領先差距、chi2），"
           "候選前三名可點選切換，下方為<b>該偏移量下的完整解密全文</b>，並提供複製與另存 .txt。")],
        [P("狀態列", "cell_b"),
         P("顯示分析結果摘要：位移數、字母總數、最可能 k、混合分數與耗時（毫秒）。")],
    ]
    story += [table(layout, [32 * mm, CONTENT_W - 32 * mm])]

    story += [Spacer(1, 10)]
    story += [screenshot(WORK / ".tools" / "preview_light.png", CONTENT_W,
                         "圖 2　淺色模式：同一份版面，僅外觀色票不同")]

    # ===== 操作流程 =====
    story += h1("04", "操作流程")
    steps = [
        ("步驟 1｜輸入密文", "在輸入區貼上要破解的英文字母密文（標點、數字、空白會保留但不列入評分）。"),
        ("步驟 2｜開始分析", "按「開始分析」或 Ctrl + Enter。程式會統計字母分布、取得動態權重，"
                             "再對 26 種位移逐一解密與評分。"),
        ("步驟 3｜看右方結論", "右方大字顯示最有可能的偏移量 k 以及混合分數；下方文字框即為該 k 的解密全文。"),
        ("步驟 4｜驗證其他候選", "若結果讀不通，可點選右方的候選第 2、3 名按鈕，立即切換顯示該位移的全文；"
                                 "狀態列會提示目前顯示的是第幾名。"),
        ("步驟 5｜取用結果", "按「複製結果」複製到剪貼簿，或「另存為 .txt」存成 decrypted_k<偏移量>.txt。"),
    ]
    rows = [[P(t, "cell_b"), P(d, "cell")] for t, d in steps]
    story += [table(rows, [38 * mm, CONTENT_W - 38 * mm], header=False)]

    # ===== 核心程式：Untitled-1.py（程式主體） =====
    story += h1("05", "核心程式：Untitled-1.py（程式主體）")
    story += [P(
        "本專案的運算核心是 <b>Untitled-1.py</b>（410 行、15.4 KB）：所有密碼學運算都在這裡完成——"
        "字母統計、卡方檢定、n-gram 命中率、元音比例、凱撒解密與最佳位移排序。"
        "<b>caesar_gui.py</b> 負責操作介面：它載入核心模組，呼叫其中的函式取得結果並繪製成畫面。"
        "兩者職責分明——核心可獨立以命令列執行，也能被介面重複呼叫。"
        "完整原始碼收錄於<b>附錄 B</b>。", "lead")]
    story += [Spacer(1, 8)]
    story += [note_box(
        "核心與介面的銜接方式",
        "執行 <font face='CONS'>caesar_gui.py</font> 時，它會載入同資料夾的 "
        "<font face='CONS'>Untitled-1.py</font> 作為運算模組。因為檔名含有「-」，"
        "無法使用一般 <font face='CONS'>import</font> 語法，所以改用 "
        "<font face='CONS'>importlib.util.spec_from_file_location(\"caesar_core\", path)</font> 動態載入；"
        "模組名稱設為 <font face='CONS'>caesar_core</font>，核心檔案最後的 "
        "<font face='CONS'>if __name__ == \"__main__\"</font> 因此不會成立，"
        "它的命令列流程不會被介面意外觸發。<br/>"
        "打包成 exe 後，程式會<b>優先讀取 exe 旁邊的同名 Untitled-1.py</b>，找不到才使用內嵌版本；"
        "因此替換這一個檔案就能更換運算核心，不必重新打包。",
    )]
    story += [Spacer(1, 10), P("模組層級常數與資料表", "h2")]
    consts = [
        [P("名稱", "cell_head"), P("內容", "cell_head"), P("用途", "cell_head")],
        [P("ENGLISH_FREQ", "cell_mono"), P("26 個字母的英文出現頻率（%，總和 100）", "cell"),
         P("卡方檢定的期望分布。", "cell")],
        [P("COMMON_BIGRAMS", "cell_mono"), P("39 組常見雙字母組（th、he、in…）", "cell"),
         P("計算 bigram 命中率。", "cell")],
        [P("COMMON_TRIGRAMS", "cell_mono"), P("28 組常見三字母組（the、and、ing…）", "cell"),
         P("計算 trigram 命中率。", "cell")],
        [P("CHI_WEIGHT 等四項", "cell_mono"), P("0.35 / 0.28 / 0.27 / 0.10", "cell_mono"),
         P("呼叫端未指定權重時的預設值。", "cell")],
        [P("TARGET_VOWEL_RATIO", "cell_mono"), P("0.38", "cell_mono"),
         P("一般英文文本的元音比例目標。", "cell")],
    ]
    story += [table(consts, [44 * mm, 66 * mm, CONTENT_W - 110 * mm]), Spacer(1, 10)]

    story += [P("函式一覽（共 14 個，依檔案順序）", "h2")]
    funcs = [
        [P("函式", "cell_head"), P("回傳", "cell_head"), P("說明", "cell_head")],
        [P("get_dynamic_weights", "cell_mono"), P("4-tuple", "cell_mono"),
         P("依字母總數在「短文本權重」與「長文本權重」之間線性插值。", "cell")],
        [P("count_letters", "cell_mono"), P("dict", "cell_mono"),
         P("統計 A–Z 每個字母的出現次數，不分大小寫；未出現的字母為 0。", "cell")],
        [P("chi_square_score", "cell_mono"), P("float", "cell_mono"),
         P("卡方統計量 Σ(觀測 - 期望)² / 期望；完全沒有字母時回傳無限大。", "cell")],
        [P("extract_words", "cell_mono"), P("list", "cell_mono"),
         P("以非英文字母為邊界切出所有單詞，標點與數字不會被計入。", "cell")],
        [P("bigram_score", "cell_mono"), P("float", "cell_mono"),
         P("單詞內相鄰兩字母命中 COMMON_BIGRAMS 的比例，不跨越標點。", "cell")],
        [P("trigram_score", "cell_mono"), P("float", "cell_mono"),
         P("同上但取相鄰三字母，比 bigram 更能反映真實英文結構。", "cell")],
        [P("vowel_score", "cell_mono"), P("float", "cell_mono"),
         P("元音佔比與 0.38 的接近程度，回傳 0～1。", "cell")],
        [P("normalize_chi_score", "cell_mono"), P("float", "cell_mono"),
         P("1 / (1 + chi2 / 字母數)，把「越低越好」的卡方轉成 0～1 的分數。", "cell")],
        [P("compute_all_scores", "cell_mono"), P("6-tuple", "cell_mono"),
         P("一次算好卡方與四項分數及字母總數，避免重複計算。", "cell")],
        [P("mixed_score_from_parts", "cell_mono"), P("float", "cell_mono"),
         P("以既有分數與權重加權合成混合分數（四項權重和為 1）。", "cell")],
        [P("mixed_score", "cell_mono"), P("float", "cell_mono"),
         P("混合評分；未指定權重時自動採用動態權重；無字母回傳 -1.0。", "cell")],
        [P("print_histogram", "cell_mono"), P("None", "cell_mono"),
         P("命令列版的文字直方圖（1 符號 = 1%）；GUI 改以彩色進度條重繪。", "cell")],
        [P("decryption", "cell_mono"), P("str", "cell_mono"),
         P("凱撒解密：字母往前移 k 位，大小寫保持，其他字元原樣保留。", "cell")],
        [P("main", "cell_mono"), P("None", "cell_mono"),
         P("命令列流程：讀入文字 → 直方圖 → 26 種位移評分 → 印出最佳解。", "cell")],
    ]
    story += [table(funcs, [46 * mm, 20 * mm, CONTENT_W - 66 * mm]), Spacer(1, 8)]
    story += [P(
        "GUI 實際呼叫其中 7 個函式：<font face='CONS'>count_letters</font>、"
        "<font face='CONS'>extract_words</font>、<font face='CONS'>get_dynamic_weights</font>、"
        "<font face='CONS'>decryption</font>、<font face='CONS'>compute_all_scores</font>、"
        "<font face='CONS'>mixed_score_from_parts</font> 與 <font face='CONS'>mixed_score</font>。"
        "其餘的 <font face='CONS'>chi_square_score</font>、<font face='CONS'>bigram_score</font>、"
        "<font face='CONS'>trigram_score</font>、<font face='CONS'>vowel_score</font>、"
        "<font face='CONS'>normalize_chi_score</font> 由 "
        "<font face='CONS'>compute_all_scores</font> 在內部呼叫；"
        "<font face='CONS'>print_histogram</font> 與 <font face='CONS'>main</font> 屬於命令列介面，"
        "GUI 以自己的版面取代。", "body_small")]

    # ===== 運作原理 =====
    story += h1("06", "運作原理")
    flow = [
        [P("① 輸入密文", "cell_b"), P("② count_letters", "cell_mono"),
         P("③ get_dynamic_weights", "cell_mono"), P("④ 26 次 decryption", "cell_b")],
        [P("⑤ compute_all_scores", "cell_mono"), P("⑥ mixed_score_from_parts", "cell_mono"),
         P("⑦ 排序取最佳 k", "cell_b"), P("⑧ 左方數據／右方結果", "cell_b")],
    ]
    ft = Table(flow, colWidths=[CONTENT_W / 4] * 4, hAlign="LEFT")
    ft.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT_SOFT),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#B9CBF0")),
        ("INNERGRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#D8E2F7")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    story += [ft, Spacer(1, 4),
              P("流程由左至右、上至下：先統計 → 決定權重 → 對每個位移解密並計算四項分數 → 加權合成 → 排序顯示。",
                "caption"), Spacer(1, 9)]

    story += [P("混合評分（分數越高越像英文）", "h2")]
    scores = [
        [P("分項", "cell_head"), P("計算方式", "cell_head"), P("方向", "cell_head")],
        [P("chi 卡方", "cell_b"),
         P("對解密結果做卡方檢定：Σ (觀測次數 - 期望次數)² / 期望次數，期望值取自一般英文單字母頻率；"
           "再正規化為 1 / (1 + chi2 / 字母數)。", "cell"),
         P("越低越好 → 正規化後越高越好", "cell")],
        [P("bigram 雙字母", "cell_b"),
         P("以非字母字元切出單詞後，統計單詞內相鄰兩字母命中常見雙字母組（th、he、in…）的比例，不跨標點。", "cell"),
         P("越高越好", "cell")],
        [P("trigram 三字母", "cell_b"),
         P("同上但取相鄰三字母（the、and、ing…），比 bigram 更能反映真實英文結構。", "cell"),
         P("越高越好", "cell")],
        [P("vowel 元音", "cell_b"),
         P("元音（a/e/i/o/u）佔全部字母的比例，與目標值 0.38 的距離越近分數越高："
           "1 - |比例 - 0.38| / 0.38。", "cell"),
         P("越接近 0.38 越好", "cell")],
    ]
    story += [table(scores, [26 * mm, CONTENT_W - 26 * mm - 34 * mm, 34 * mm]), Spacer(1, 9)]

    story += [P("動態權重：依文本長度自動調整四項比重", "h2")]
    weights = [
        [P("文本長度（字母數）", "cell_head"), P("chi", "cell_head"), P("bigram", "cell_head"),
         P("trigram", "cell_head"), P("vowel", "cell_head")],
        [P("&lt;= 20（短文本，卡方不穩定）", "cell"), P("0.15", "cell_mono"), P("0.35", "cell_mono"),
         P("0.25", "cell_mono"), P("0.25", "cell_mono")],
        [P("20 ～ 200（線性插值過渡）", "cell"), P("0.15→0.50", "cell_mono"), P("0.35→0.22", "cell_mono"),
         P("0.25→0.20", "cell_mono"), P("0.25→0.08", "cell_mono")],
        [P("&gt;= 200（長文本，卡方穩定）", "cell"), P("0.50", "cell_mono"), P("0.22", "cell_mono"),
         P("0.20", "cell_mono"), P("0.08", "cell_mono")],
    ]
    story += [table(weights, [70 * mm] + [(CONTENT_W - 70 * mm) / 4] * 4), Spacer(1, 7)]
    story += [code_box([
        "插值：t = 0（n &lt;= 20）　|　t = (n - 20) / 180（20 &lt; n &lt; 200）　|　t = 1（n &gt;= 200）",
        "混合分數 = w_chi * chi + w_bigram * bigram + w_trigram * trigram + w_vowel * vowel",
        "本範例（test.txt，1467 字母）取得長文本權重：0.500 / 0.220 / 0.200 / 0.080",
    ])]

    # ===== 檔案結構 =====
    story += h1("07", "檔案結構")
    files = [
        [P("檔案／資料夾", "cell_head"), P("行數／大小", "cell_head"), P("說明", "cell_head")],
        [P("caesar_gui.py", "cell_mono"), P("1241 行 / 49 KB", "cell_mono"),
         P("互動介面：版面組裝、事件處理、分析流程、自我測試與打包相容處理。", "cell")],
        [P("Untitled-1.py", "cell_mono"), P("410 行 / 15.4 KB", "cell_mono"),
         P("<b>運算核心</b>：字母統計、卡方、bigram／trigram、元音與凱撒解密，"
           "並附命令列版本；介面直接呼叫其中的函式。完整原始碼見附錄 B。", "cell")],
        [P("test.txt", "cell_mono"), P("9 行 / 3.5 KB", "cell_mono"),
         P("範例資料：前 4 段明文＋後 4 段 ROT13 密文；程式會自動判斷並只取密文段落。", "cell")],
        [P("run_gui.bat", "cell_mono"), P("10 行", "cell_mono"),
         P("以專案 .venv 啟動圖形介面（雙擊即可）。", "cell")],
        [P("build_exe.bat", "cell_mono"), P("25 行", "cell_mono"),
         P("一鍵打包 exe，內部呼叫 .tools\\build_exe.py。", "cell")],
        [P(".tools\\", "cell_mono"), P("5 個檔案", "cell_mono"),
         P("打包與環境工具：build_exe.py（PyInstaller 設定）、pip_patch.py（沙箱可用的 pip 包裝）、"
           "make_intro_pdf.py（本介紹文件的產生腳本）、兩張介面截圖。", "cell")],
        [P("dist\\CaesarCipherGUI.exe", "cell_mono"), P("13.1 MB", "cell_mono"),
         P("單一檔案執行檔（onefile），雙擊即用。", "cell")],
        [P("dist_portable\\", "cell_mono"), P("29.5 MB", "cell_mono"),
         P("免解壓資料夾版（onedir，主程式 3.2 MB），啟動最快。", "cell")],
        [P("CaesarCipherGUI.spec", "cell_mono"), P("—", "cell_mono"),
         P("PyInstaller 打包設定檔，可自行調整後重打包。", "cell")],
        [P(".venv\\", "cell_mono"), P("—", "cell_mono"),
         P("虛擬環境：customtkinter 5.2.2、darkdetect 0.8.0、pyinstaller 6.22.3 等。", "cell")],
    ]
    story += [table(files, [46 * mm, 30 * mm, CONTENT_W - 76 * mm]), Spacer(1, 8)]
    story += [note_box(
        "專案倉庫（GitHub）",
        f"<font face='CONS'>{REPO_URL}</font>　·　公開倉庫，內容與本文件所述一致，"
        "可直接以 <font face='CONS'>git clone</font> 取得完整專案（含程式主體 Untitled-1.py）。",
    )]

    # ===== 打包 =====
    story += h1("08", "打包成執行檔（exe）")
    story += [P("雙擊 <b>build_exe.bat</b> 即可重新打包；或執行 "
                "<font face='CONS'>python .tools\\build_exe.py [--onedir]</font>。"
                "打包指令使用 PyInstaller 的 onefile／windowed 模式，並以 "
                "<font face='CONS'>--collect-all customtkinter</font> 一併收錄主題 JSON 與字型資源。", "body")]
    story += [Spacer(1, 6)]
    pack = [
        [P("版本", "cell_head"), P("產物", "cell_head"), P("體積", "cell_head"), P("特性", "cell_head")],
        [P("單一檔案（onefile）", "cell_b"), P("dist\\CaesarCipherGUI.exe", "cell_mono"), P("13.1 MB", "cell_mono"),
         P("只有一個檔案、方便攜帶；啟動時會先解壓到 %TEMP% 再執行，首次啟動約 2–4 秒。", "cell")],
        [P("資料夾版（onedir）", "cell_b"), P("dist_portable\\CaesarCipherGUI\\", "cell_mono"),
         P("29.5 MB", "cell_mono"),
         P("不需解壓、啟動最快，適合放在固定位置長期使用。", "cell")],
    ]
    story += [table(pack, [32 * mm, 57 * mm, 18 * mm, CONTENT_W - 107 * mm]), Spacer(1, 8)]
    story += [note_box(
        "兩項打包設計",
        "① <b>外部檔案優先</b>：資料檔（Untitled-1.py、test.txt）會先找 exe 旁邊的同名檔案，"
        "找不到才用內嵌版本；因此只要把修改後的 Untitled-1.py 放到 exe 同資料夾，就能換掉演算法而不必重新打包。<br/>"
        "② <b>內建診斷記錄</b>：打包後的程式會把 --selftest 結果與未預期例外寫入 "
        "<font face='CONS'>%TEMP%\\caesar_gui.log</font>（視窗模式沒有主控台可看），方便回報問題。",
    )]

    # ===== 驗證 =====
    story += h1("09", "驗證與實測結果")
    story += [P("程式內建 12 項自我測試（<font face='CONS'>--selftest</font>），"
                "原始碼與打包後的 exe 皆為 <b>12/12 通過、結束碼 0</b>：", "body"), Spacer(1, 5)]
    checks = [
        [P("檢查項目", "cell_head"), P("檢查內容", "cell_head")],
        [P("分析產生 26 種位移", "cell_b"), P("對 k = 0–25 全部完成解密與評分。", "cell")],
        [P("找出最有可能偏移量", "cell_b"), P("最佳 k 不為 None，且混合分數取最大值。", "cell")],
        [P("範例密文最佳位移為 13", "cell_b"), P("test.txt 的密文為 ROT13，程式須正確判為 k = 13。", "cell")],
        [P("左右區塊內容", "cell_b"), P("位移明細與候選排名文字長度正常、右方顯示出正確明文關鍵字。", "cell")],
        [P("直方圖有資料列", "cell_b"), P("頻率直方圖確實產生 25 列（非零字母數）。", "cell")],
        [P("候選切換、複製、清空", "cell_b"), P("切換到第 2 名、剪貼簿內容與結果框一致、清空後回復初始狀態。", "cell")],
        [P("邊界情境", "cell_b"), P("純數字／符號輸入（無英文字母）不會崩潰，並顯示「找不到任何英文字母」。", "cell")],
        [P("載入範例", "cell_b"), P("「載入範例密文」能正確讀入並填入輸入框。", "cell")],
    ]
    story += [table(checks, [46 * mm, CONTENT_W - 46 * mm]), Spacer(1, 8)]

    story += [P("以 test.txt 的密文段切實測（1467 個字母）", "h2")]
    perf = [
        [P("項目", "cell_head"), P("結果", "cell_head"), P("項目", "cell_head"), P("結果", "cell_head")],
        [P("字母總數", "cell_b"), P("1467", "cell_mono"), P("單詞數", "cell_b"), P("227", "cell_mono")],
        [P("相異字母數", "cell_b"), P("25", "cell_mono"), P("嘗試位移數", "cell_b"), P("26", "cell_mono")],
        [P("最可能偏移量", "cell_b"), P("k = 13（ROT13）", "cell_mono"), P("混合分數", "cell_b"), P("0.6624", "cell_mono")],
        [P("領先第 2 名", "cell_b"), P("0.4702", "cell_mono"), P("chi2", "cell_b"), P("112.45", "cell_mono")],
        [P("分析耗時", "cell_b"), P("約 0.44–0.53 秒（含左方重繪）", "cell_mono"), P("自我測試", "cell_b"), P("12/12 通過（exit 0）", "cell_mono")],
    ]
    story += [table(perf, [34 * mm, 52 * mm, 34 * mm, CONTENT_W - 120 * mm])]

    # ===== 疑難排解 =====
    story += h1("10", "疑難排解")
    qa = [
        ("找不到核心程式檔案：Untitled-1.py",
         "GUI 與 Untitled-1.py 必須放在同一個資料夾（原始碼模式），或把 Untitled-1.py 放到 exe 旁邊。"),
        ("第一次啟動 exe 要等幾秒",
         "單一檔案版啟動時會把內容解壓到 %TEMP%\\_MEIxxxxxx，屬於正常現象；若想秒開請改用資料夾版。"),
        ("結果讀起來不通順",
         "密文太短（少於 20 個字母）時卡方統計不穩定，請多貼一些內容；也可直接點選右方候選第 2、3 名比較。"),
        ("想確認程式內部狀態",
         "執行 --selftest 會產生 12 項檢查；打包後的版本請看 %TEMP%\\caesar_gui.log。"),
        ("防毒軟體攔阻 exe",
         "PyInstaller 產生的未簽章執行檔常被誤判，可改用資料夾版或將檔案加入白名單。"),
        ("想調整演算法或介面",
         "演算法改 Untitled-1.py，畫面改 caesar_gui.py，兩者以函式名稱溝通；"
         "若只想換掉運算核心，直接替換 exe 旁邊的 Untitled-1.py 即可，不必重新打包。"),
    ]
    rows = [[P(f"Q：{q}", "qa_q")] for q, _ in qa]
    flat = []
    for q, a in qa:
        flat.append([P(f"Q：{q}", "qa_q")])
        flat.append([P(f"A：{a}", "qa_a")])
    qt = Table(flat, colWidths=[CONTENT_W], hAlign="LEFT")
    cmds = [("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("BOX", (0, 0), (-1, -1), 0.6, BORDER)]
    for i in range(0, len(flat), 2):
        cmds += [("BACKGROUND", (0, i), (0, i), LIGHT),
                 ("LINEABOVE", (0, i), (0, i), 0.5, BORDER if i else WHITE)]
    qt.setStyle(TableStyle(cmds))
    story += [qt]

    # ===== 附錄 A：命令列參數與環境（新開一頁） =====
    story += [PageBreak()]
    story += h1("11", "附錄 A：命令列參數與環境")
    args = [
        [P("參數", "cell_head"), P("說明", "cell_head")],
        [P("--demo", "cell_mono"), P("啟動後自動載入 test.txt 的密文段落並立即分析。", "cell")],
        [P("--selftest", "cell_mono"), P("執行 12 項自我測試後自動關閉；結束碼 0 表示全部通過。", "cell")],
        [P("--appearance=…", "cell_mono"),
         P("指定啟動外觀：深色／淺色／跟隨系統（亦可寫 Dark／Light／System）。", "cell")],
        [P("--tab=…", "cell_mono"),
         P("啟動後直接切到左方指定分頁：頻率直方圖／位移明細／候選排名。", "cell")],
        [P("--auto-close=秒", "cell_mono"), P("指定秒數後自動關閉視窗（供截圖與自動化使用）。", "cell")],
        [P("Ctrl + Enter", "cell_mono"), P("在輸入框中直接開始分析。", "cell")],
    ]
    story += [table(args, [38 * mm, CONTENT_W - 38 * mm]), Spacer(1, 9)]

    env = [
        [P("元件", "cell_head"), P("版本／內容", "cell_head"), P("用途", "cell_head")],
        [P("Python", "cell_mono"), P("3.14.6（.venv 虛擬環境）", "cell"), P("執行 GUI 與打包。", "cell")],
        [P("CustomTkinter", "cell_mono"), P("5.2.2", "cell"), P("現代化深色模式介面元件。", "cell")],
        [P("darkdetect", "cell_mono"), P("0.8.0", "cell"), P("「跟隨系統」外觀偵測。", "cell")],
        [P("PyInstaller", "cell_mono"), P("6.22.3", "cell"), P("打包成單一 exe／資料夾版。", "cell")],
        [P("字型", "cell_mono"), P("Microsoft JhengHei UI／Consolas", "cell"),
         P("中文介面文字與等寬數據表格。", "cell")],
    ]
    story += [table(env, [34 * mm, 62 * mm, CONTENT_W - 96 * mm]), Spacer(1, 10)]
    story += [rule(BORDER, 0.8, 2, 6)]
    story += [P("本文件由專案內 .tools 的產生腳本自動排版輸出（reportlab + Microsoft JhengHei）。"
                "文件中的所有數據均取自實際執行的測試結果。", "caption")]

    # ===== 附錄 B：程式主體完整原始碼 =====
    story += [PageBreak()]
    story += h1("12", "附錄 B：Untitled-1.py 完整原始碼")
    src_lines = CODE_FILE.read_text(encoding="utf-8").splitlines()
    story += [P(
        f"以下是程式主體 <b>Untitled-1.py</b> 的完整內容：{len(src_lines)} 行、"
        f"{CODE_FILE.stat().st_size / 1024:.1f} KB、UTF-8 編碼，"
        "只使用 Python 標準函式庫（<font face='CONS'>re</font>、<font face='CONS'>string</font>、"
        "<font face='CONS'>collections</font>）。本清單與 GitHub 倉庫中的檔案一致"
        f"（{REPO_URL}）。", "body_small"), Spacer(1, 6)]
    story += [listing_line(line) for line in src_lines]

    # ===== 附錄 C：各函式偽代碼 =====
    story += [PageBreak()]
    story += h1("13", "附錄 C：各函式偽代碼")
    story += [P(
        "本附錄以偽代碼逐一描述附錄 B 中 14 個函式的做法，順序與原始碼相同，便於對照；"
        "最後另附介面端的主流程 <font face='CONS'>run_analysis()</font>，"
        "說明核心函式在圖形介面中如何被串起來使用。", "body_small"), Spacer(1, 6)]
    story += [P("閱讀記號", "h2"), code_box([
        "← 賦值　·　回傳 = 結束並輸出結果　·　× 乘法　·　mod 取餘數　·　∞ 無限大　·　|…| 絕對值",
        "對 X 中每個 Y： 逐一走訪　·　若／否則： 條件判斷　·　結果[i]：取出第 i 個元素",
    ]), Spacer(1, 9)]
    story += [P("共用的常數與資料表", "h2"), code_box([
        "ENGLISH_FREQ['A' .. 'Z'] ← 26 個字母的英文出現頻率（%，總和 100）",
        "COMMON_BIGRAMS[39]        ← 常見雙字母組（th、he、in…）",
        "COMMON_TRIGRAMS[28]       ← 常見三字母組（the、and、ing…）",
        "CHI_WEIGHT ← 0.35　BIGRAM_WEIGHT ← 0.28　TRIGRAM_WEIGHT ← 0.27　VOWEL_WEIGHT ← 0.10",
        "TARGET_VOWEL_RATIO ← 0.38（一般英文的元音比例）",
    ]), Spacer(1, 11)]

    pseudo_funcs = [
        ("get_dynamic_weights(total_letters)", [
            "短 ← (0.15, 0.35, 0.25, 0.25)          # 短文本：偏重 n-gram 與元音",
            "長 ← (0.50, 0.22, 0.20, 0.08)          # 長文本：偏重卡方",
            "若 total_letters &lt;= 20 ： t ← 0",
            "若 total_letters &gt;= 200： t ← 1",
            "否則                  ： t ← (total_letters - 20) / 180",
            "對 i ← 0 到 3： w[i] ← 短[i] + t × (長[i] - 短[i])",
            "回傳 (w[0], w[1], w[2], w[3])",
        ]),
        ("count_letters(text)", [
            "上層 ← 把 text 轉成大寫",
            "計數 ← 空映射",
            "對 上層 中每個字元 c：",
            "    若 c 屬於 'A'~'Z'： 計數[c] ← 計數[c] + 1",
            "對 'A'~'Z' 中每個字母 L：",
            "    結果[L] ← 計數[L]（不存在時為 0）",
            "回傳 結果（固定 26 個鍵）",
        ]),
        ("chi_square_score(text)", [
            "計數 ← count_letters(text)； n ← 26 個計數的總和",
            "若 n = 0： 回傳 ∞                        # 沒有字母，無法比較分布",
            "chi2 ← 0",
            "對 'A'~'Z' 中每個字母 L：",
            "    觀測 ← 計數[L]",
            "    期望 ← n × ENGLISH_FREQ[L] / 100",
            "    若 期望 &gt; 0： chi2 ← chi2 + (觀測 - 期望)² / 期望",
            "回傳 chi2（越低越像英文）",
        ]),
        ("extract_words(text)", [
            "回傳 所有符合 [A-Za-z]+ 的子字串",
            "# 連續英文字母視為一個單詞；空白、標點、數字自然成為邊界",
        ]),
        ("bigram_score(text)", [
            "單詞 ← extract_words(text)； 總數 ← 0； 命中 ← 0",
            "對 單詞 中每個 word：",
            "    w ← word 轉小寫",
            "    對 i ← 0 到 len(w) - 2：",
            "        總數 ← 總數 + 1",
            "        若 w[i:i+2] 在 COMMON_BIGRAMS： 命中 ← 命中 + 1",
            "若 總數 = 0： 回傳 0.0",
            "回傳 命中 / 總數",
        ]),
        ("trigram_score(text)", [
            "單詞 ← extract_words(text)； 總數 ← 0； 命中 ← 0",
            "對 單詞 中每個 word：",
            "    w ← word 轉小寫",
            "    對 i ← 0 到 len(w) - 3：",
            "        總數 ← 總數 + 1",
            "        若 w[i:i+3] 在 COMMON_TRIGRAMS： 命中 ← 命中 + 1",
            "若 總數 = 0： 回傳 0.0",
            "回傳 命中 / 總數",
        ]),
        ("vowel_score(text)", [
            "字母 ← text 中所有英文字母（轉小寫）； 若為空： 回傳 0.0",
            "元音 ← 字母 中屬於 {a, e, i, o, u} 的個數",
            "比例 ← 元音 / len(字母)",
            "距離 ← |比例 - TARGET_VOWEL_RATIO|",
            "回傳 max(0.0, 1.0 - 距離 / TARGET_VOWEL_RATIO)",
        ]),
        ("normalize_chi_score(chi2, total_letters)", [
            "若 total_letters = 0： 回傳 0.0",
            "回傳 1.0 / (1.0 + chi2 / total_letters)    # 把「越低越好」轉成 0~1",
        ]),
        ("compute_all_scores(text)", [
            "n ← count_letters(text) 的總和",
            "若 n = 0： 回傳 (∞, 0.0, 0.0, 0.0, 0.0, 0)",
            "chi2 ← chi_square_score(text)",
            "chi  ← normalize_chi_score(chi2, n)",
            "bg   ← bigram_score(text)",
            "tg   ← trigram_score(text)",
            "vw   ← vowel_score(text)",
            "回傳 (chi2, chi, bg, tg, vw, n)",
        ]),
        ("mixed_score_from_parts(chi, bg, tg, vw, w_chi, w_bg, w_tg, w_vw)", [
            "# 四項分數皆為 0~1，四項權重和為 1，故結果也落在 0~1",
            "回傳 w_chi × chi + w_bg × bg + w_tg × tg + w_vw × vw",
        ]),
        ("mixed_score(text, 四項權重可省略)", [
            "(chi2, chi, bg, tg, vw, n) ← compute_all_scores(text)",
            "若 n = 0： 回傳 -1.0                    # 沒有字母就給最低分",
            "若 未指定權重： (w_chi, w_bg, w_tg, w_vw) ← get_dynamic_weights(n)",
            "回傳 mixed_score_from_parts(chi, bg, tg, vw, w_chi, w_bg, w_tg, w_vw)",
        ]),
        ("print_histogram(counts, unit_symbol ← '█', show_zero ← 假)", [
            "總數 ← counts 的總和",
            "印出表頭（一個 █ 代表 1%）",
            "若 總數 = 0： 印出 \"No letters found.\"； 結束",
            "對 counts 中每個 (字母, 次數)：",
            "    若 show_zero 為真 或 次數 &gt; 0：",
            "        百分比 ← 次數 / 總數 × 100",
            "        長度 ← round(百分比)； 若 次數 &gt; 0 且 長度 = 0： 長度 ← 1",
            "        印出 字母、次數、百分比與 unit_symbol × 長度",
        ]),
        ("decryption(cipher_text, k)", [
            "結果 ← \"\"",
            "對 cipher_text 中每個字元 c：",
            "    若 'A' &lt;= c &lt;= 'Z'： 結果 ← 結果 + 位移(c, 'A', k)",
            "    若 'a' &lt;= c &lt;= 'z'： 結果 ← 結果 + 位移(c, 'a', k)",
            "    否則： 結果 ← 結果 + c            # 標點、數字、非 ASCII 原樣保留",
            "回傳 結果",
            "",
            "其中 位移(ch, 基準, k) = chr((ord(ch) - ord(基準) - k) mod 26 + ord(基準))",
        ]),
        ("main()", [
            "文字 ← 讀取使用者輸入",
            "計數 ← count_letters(文字)； n ← 總和",
            "print_histogram(計數)",
            "若 n = 0： 印出 \"No letters found.\"； 結束",
            "(w_chi, w_bg, w_tg, w_vw) ← get_dynamic_weights(n)",
            "最佳k ← 無； 最佳分數 ← -1.0",
            "對 k ← 0 到 25：",
            "    解密 ← decryption(文字, k)",
            "    (chi2, chi, bg, tg, vw, _) ← compute_all_scores(解密)",
            "    分數 ← mixed_score_from_parts(chi, bg, tg, vw, w_chi, w_bg, w_tg, w_vw)",
            "    印出 k、chi2、chi、bg、tg、vw、分數 與解密文字",
            "    若 分數 &gt; 最佳分數： 最佳分數 ← 分數； 最佳k ← k",
            "印出 最佳k 與 decryption(文字, 最佳k)",
        ]),
    ]
    for name, lines in pseudo_funcs:
        story += [pseudo_block(name, lines)]

    story += [pseudo_block("（介面端）run_analysis()  —— caesar_gui.py", [
        "文字 ← 讀取輸入框內容",
        "若 文字 為空： 狀態列提示「請先輸入要破解的密文」； 結束",
        "計數 ← core.count_letters(文字)； n ← 總和",
        "若 n = 0： 顯示「找不到任何英文字母」； 結束",
        "權重 ← core.get_dynamic_weights(n)",
        "對 k ← 0 到 25：",
        "    解密 ← core.decryption(文字, k)",
        "    (chi2, chi, bg, tg, vw, _) ← core.compute_all_scores(解密)",
        "    分數 ← core.mixed_score_from_parts(chi, bg, tg, vw, 權重)",
        "    rows[k] ← {k, chi2, chi, bg, tg, vw, 分數, 解密}",
        "排名 ← rows 依分數由高到低排序",
        "左方 ← 頻率直方圖、位移明細、候選排名、動態權重長條",
        "右方 ← 排名第 1 名的 k、混合分數與該 k 的完整解密全文",
        "狀態列 ← 位移數、字母總數、最可能 k、混合分數與耗時",
    ])]

    return story


def main():
    doc = BaseDocTemplate(
        str(OUT), pagesize=A4,
        leftMargin=MARGIN_X, rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP, bottomMargin=MARGIN_BOTTOM,
        title="凱撒密碼破解器 · 專案介紹", author="SBA-work 專案",
        subject="CustomTkinter 凱撒密碼破解工具介紹",
    )
    frame = Frame(MARGIN_X, MARGIN_BOTTOM, CONTENT_W,
                  PAGE_H - MARGIN_TOP - MARGIN_BOTTOM, id="main",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=draw_page_decor)])
    doc.build(build_story(), canvasmaker=NumberedCanvas)
    print("已輸出：", OUT, OUT.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
