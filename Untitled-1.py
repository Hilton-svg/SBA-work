# -*- coding: utf-8 -*-
"""
Untitled-1.py：凱撒密碼（Caesar cipher）破解 + 英文相似度評分工具

功能概述：
    1. 讀入一段文字（通常是密文）。
    2. 統計其中 A-Z 出現次數，並用文字直方圖顯示字母頻率。
    3. 依文本長度決定四項評分的「動態權重」。
    4. 對 26 種可能的位移 k 逐一凱撒解密，計算每個結果的混合分數。
    5. 印出所有 k 的分數明細，並輸出分數最高（最像英文）的解密結果。

混合評分（分數越高越像英文）由四項加權而成：
    chi     ：卡方分數正規化（字母頻率分布是否接近一般英文）
    bigram  ：常見雙字母組（bigram）命中率
    trigram ：常見三字母組（trigram）命中率
    vowel   ：元音比例是否接近 TARGET_VOWEL_RATIO
"""

import re                        # 用於以正規表示式切出單詞
import string                    # 提供 ascii_uppercase 等常數
from collections import Counter  # 用於快速統計字元出現次數

# ==================== 常數表 ====================

# 英文單字母頻率（%）
# 一般英文書面文本中各字母出現的百分比，作為卡方分數的「期望分布」。
# 鍵為 A-Z 大寫字母，數值為百分比（總和約 100）。
ENGLISH_FREQ = {
    'A': 8.167, 'B': 1.492, 'C': 2.782, 'D': 4.253, 'E': 12.702,
    'F': 2.228, 'G': 2.015, 'H': 6.094, 'I': 6.966, 'J': 0.153,
    'K': 0.772, 'L': 4.025, 'M': 2.406, 'N': 6.749, 'O': 7.507,
    'P': 1.929, 'Q': 0.095, 'R': 5.987, 'S': 6.327, 'T': 9.056,
    'U': 2.758, 'V': 0.978, 'W': 2.360, 'X': 0.150, 'Y': 1.974,
    'Z': 0.074
}

# 常見英文雙字母組（小寫），用來衡量解密結果是否含有自然的字母組合
COMMON_BIGRAMS = {
    "th", "he", "in", "er", "an", "re", "nd", "at", "on", "nt",
    "ha", "es", "st", "en", "ed", "to", "it", "ou", "ea", "hi",
    "is", "or", "ti", "as", "te", "et", "ng", "of", "al", "de",
    "se", "le", "sa", "si", "ar", "ve", "ra", "ld", "ur",
}

# 常見英文三字母組（小寫），比 bigram 更能反映真實英文結構
COMMON_TRIGRAMS = {
    "the", "and", "ing", "ent", "ion", "her", "for", "tha", "nth",
    "int", "ere", "tio", "ter", "est", "ers", "ati", "hat", "ate",
    "all", "eth", "hes", "ver", "his", "oft", "sth", "oth", "res",
    "ont",
}

# 混合評分預設權重（當呼叫端未指定權重、也無法使用動態權重時的備援值）
CHI_WEIGHT = 0.35
BIGRAM_WEIGHT = 0.28
TRIGRAM_WEIGHT = 0.27
VOWEL_WEIGHT = 0.10
TARGET_VOWEL_RATIO = 0.38   # 一般英文文本中元音約佔 38%

# ==================== 動態權重 ====================

def get_dynamic_weights(total_letters):
    """
    根據字母總數動態調整混合評分權重。

    設計原則：
    - 短文本（< 20 字母）：卡方極不穩定，主要依賴 bigram / trigram / 元音。
    - 中文本：四項均衡。
    - 長文本（> 200 字母）：卡方穩定，提高卡方權重。

    做法：用線性插值，在「短文本權重」與「長文本權重」之間平滑過渡。

    回傳 (chi_weight, bigram_weight, trigram_weight, vowel_weight)。
    """
    # 短文本權重（偏向 n-gram 與元音）
    short_w = (0.15, 0.35, 0.25, 0.25)
    # 長文本權重（偏向卡方）
    long_w = (0.50, 0.22, 0.20, 0.08)

    # 插值參數 t：0 = 完全短文本，1 = 完全長文本
    if total_letters <= 20:
        t = 0.0
    elif total_letters >= 200:
        t = 1.0
    else:
        # 20~200 字母之間：以線性比例決定過渡程度
        t = (total_letters - 20) / (200 - 20)

    # 依 t 在 short_w 與 long_w 之間做線性插值，得到四項最終權重
    chi_w = short_w[0] + t * (long_w[0] - short_w[0])
    bg_w = short_w[1] + t * (long_w[1] - short_w[1])
    tg_w = short_w[2] + t * (long_w[2] - short_w[2])
    vw_w = short_w[3] + t * (long_w[3] - short_w[3])

    return chi_w, bg_w, tg_w, vw_w


# ==================== 字母統計與評分 ====================

def count_letters(text):
    """
    統計 text 中 A-Z 每個英文字母的出現次數。
    - 不分大小寫，全部先轉成大寫再計數。
    - 回傳的字典保證包含 A-Z 所有字母，沒出現的字母次數為 0。
    """
    # 先統一轉成大寫，再用 Counter 統計每個字元出現次數
    counts = Counter(text.upper())
    # 只取出 A-Z；未出現的字母在 Counter 中不存在，因此會得到 0
    return {char: counts[char] for char in string.ascii_uppercase}


def chi_square_score(text):
    """
    計算卡方分數（chi-square score）。
    - 分數越低，表示字母分布越接近一般英文。
    - 若文字中完全沒有英文字母，回傳無限大。
    """
    counts = count_letters(text)
    total = sum(counts.values())        # 文本中的字母總數

    if total == 0:                      # 沒有任何字母 → 無法比較分布
        return float('inf')

    chi2 = 0.0
    for letter in string.ascii_uppercase:
        observed = counts[letter]                           # 實際觀測次數
        expected = total * ENGLISH_FREQ[letter] / 100.0     # 依英文頻率推算的期望次數
        if expected > 0:                                    # 避免除以 0
            # 卡方公式：Σ (觀測 - 期望)^2 / 期望
            chi2 += (observed - expected) ** 2 / expected

    return chi2


def extract_words(text):
    """
    以非英文字母為邊界，切出所有單詞。
    - 每個單詞都是純 ASCII 英文字母組成的字串。
    - 特殊字符（空白、標點、數字等）不會被納入單詞。
    """
    # [A-Za-z]+ 會把連續的英文字母視為一個單詞，
    # 因此空白、標點、數字等天然成為單詞邊界而不被計入
    return re.findall(r'[A-Za-z]+', text)


def bigram_score(text):
    """
    計算常見雙字母組的命中率。
    - 先以特殊字符為邊界切出單詞，再對每個單詞內部算 bigram。
    - bigram 不會跨越特殊字符。
    - 回傳命中 COMMON_BIGRAMS 的比例，越高越像英文。
    """
    words = extract_words(text)

    total = 0   # 所有單詞內的 bigram 總數
    hits = 0    # 命中 COMMON_BIGRAMS 的 bigram 數量
    for word in words:
        w = word.lower()                # 轉小寫以比對小寫的常數表
        for i in range(len(w) - 1):     # 逐一切出長度 2 的連續子字串
            total += 1
            if w[i:i + 2] in COMMON_BIGRAMS:
                hits += 1

    # 若沒有任何 bigram（例如空字串或全是單字母單詞），回傳 0 避免除以 0
    return hits / total if total > 0 else 0.0


def trigram_score(text):
    """
    計算常見三字母組的命中率。
    - 先以特殊字符為邊界切出單詞，再對每個單詞內部算 trigram。
    - trigram 不會跨越特殊字符。
    - 回傳命中 COMMON_TRIGRAMS 的比例，越高越像英文。
    """
    words = extract_words(text)

    total = 0   # 所有單詞內的 trigram 總數
    hits = 0    # 命中 COMMON_TRIGRAMS 的 trigram 數量
    for word in words:
        w = word.lower()                # 轉小寫以比對小寫的常數表
        for i in range(len(w) - 2):     # 逐一切出長度 3 的連續子字串
            total += 1
            if w[i:i + 3] in COMMON_TRIGRAMS:
                hits += 1

    # 若沒有任何 trigram（單詞都太短），回傳 0 避免除以 0
    return hits / total if total > 0 else 0.0


def vowel_score(text):
    """
    計算元音比例分數。
    - 元音為 a, e, i, o, u（不分大小寫）。
    - 英文文本元音比例約 0.38，越接近越高分。
    - 回傳 0~1，1 表示比例剛好等於 TARGET_VOWEL_RATIO。
    """
    # 取出所有英文字母並轉小寫；標點、數字、其他字元一律忽略
    letters = [c.lower() for c in text
            if ('a' <= c <= 'z') or ('A' <= c <= 'Z')]

    total = len(letters)
    if total == 0:                      # 沒有字母 → 無法評估
        return 0.0

    vowels = sum(1 for c in letters if c in 'aeiou')    # 元音字母個數
    ratio = vowels / total                              # 實際元音比例

    # 距離目標比例越遠，分數越低；最大距離為 TARGET_VOWEL_RATIO
    distance = abs(ratio - TARGET_VOWEL_RATIO)
    score = max(0.0, 1.0 - distance / TARGET_VOWEL_RATIO)
    return score


def normalize_chi_score(chi2, total_letters):
    """
    把「越低越好」的卡方轉成「越高越好」的分數，範圍 (0, 1]。
    - total_letters 為 0 時回傳 0。
    """
    if total_letters == 0:
        return 0.0
    # chi2 / total_letters 是「平均每字母的卡方貢獻」，值越小越像英文；
    # 透過 1 / (1 + x) 映射到 0~1，x = 0 時分數為 1
    return 1.0 / (1.0 + chi2 / total_letters)


def compute_all_scores(text):
    """
    一次算好所有分數，避免重複計算。
    回傳 (chi2, chi_score, bg_score, tg_score, vw_score, total_letters)。
    """
    counts = count_letters(text)
    total_letters = sum(counts.values())

    if total_letters == 0:              # 完全沒有字母 → 回傳無效分數
        return float('inf'), 0.0, 0.0, 0.0, 0.0, 0

    # 依序計算四項分數（後三項本來就在 0~1，卡方需再正規化）
    chi2 = chi_square_score(text)
    chi_score = normalize_chi_score(chi2, total_letters)
    bg_score = bigram_score(text)
    tg_score = trigram_score(text)
    vw_score = vowel_score(text)

    return chi2, chi_score, bg_score, tg_score, vw_score, total_letters


def mixed_score_from_parts(chi_score, bg_score, tg_score, vw_score,
                        chi_weight=CHI_WEIGHT,
                        bigram_weight=BIGRAM_WEIGHT,
                        trigram_weight=TRIGRAM_WEIGHT,
                        vowel_weight=VOWEL_WEIGHT):
    """用已算好的分數加權，回傳混合分數，越大越好。"""
    # 四項分數皆為 0~1，權重和為 1，因此混合分數也落在 0~1
    return (
        chi_weight * chi_score +
        bigram_weight * bg_score +
        trigram_weight * tg_score +
        vowel_weight * vw_score
    )


def mixed_score(text, chi_weight=None, bigram_weight=None,
                trigram_weight=None, vowel_weight=None):
    """
    混合評分。
    - 若未指定權重，會依文本長度自動使用動態權重。
    """
    chi2, chi_score, bg_score, tg_score, vw_score, total_letters = compute_all_scores(text)

    if total_letters == 0:
        return -1.0     # 沒有字母 → 給予最低分，讓任何合法結果都能勝出

    if chi_weight is None:
        # 呼叫端未指定權重 → 依字母總數自動取得動態權重
        chi_weight, bigram_weight, trigram_weight, vowel_weight = \
            get_dynamic_weights(total_letters)

    return mixed_score_from_parts(
        chi_score, bg_score, tg_score, vw_score,
        chi_weight, bigram_weight, trigram_weight, vowel_weight
    )


# ==================== 直方圖 ====================

def print_histogram(counts, unit_symbol='█', show_zero=False):
    """
    以文字直方圖顯示字母出現的百分比。
    - 每個 unit_symbol 代表 1%。
    - show_zero 為 True 時，連次數 0 的字母也顯示。
    - 百分比 = 該字母出現次數 / 總字母數 * 100。
    """
    total = sum(counts.values())

    # 表頭與分隔線
    print(f"\nLetter Frequency Histogram ( {unit_symbol} = 1% )")
    print("-" * 60)

    if total == 0:                      # 沒有任何字母 → 只印提示訊息
        print("No letters found.")
        return

    print(f"Total letters: {total}")
    print("-" * 60)
    print(f"{'Letter':<8}{'Count':<8}{'Percent':<10}Histogram")
    print("-" * 60)

    for letter, count in counts.items():
        if show_zero or count > 0:      # 依參數決定是否顯示次數為 0 的字母
            percent = count / total * 100       # 該字母佔全部字母的百分比
            bar_len = int(round(percent))       # 1 個符號代表 1%，四捨五入
            if count > 0 and bar_len == 0:
                bar_len = 1  # 非零至少顯示一個符號
            bar = unit_symbol * bar_len
            # 依序印出：字母、次數、百分比、直方圖
            print(f"{letter:<8}({count:>3})   {percent:>6.2f}%   {bar}")


# ==================== 凱撒解密 ====================

def decryption(cipher_text, k):
    """
    凱撒解密：
    - 將每個英文字母往前移 k 位。
    - 只處理 ASCII 英文字母，大寫保持大寫，小寫保持小寫。
    - 非 ASCII 英文字母（含其他 Unicode 字母、標點、數字等）原樣保留。
    """
    decryption_text = []

    for char in cipher_text:
        if 'A' <= char <= 'Z':
            # 大寫字母：先轉成 0~25，減去 k 後對 26 取模，再轉回字母
            decrypted_char = chr((ord(char) - ord('A') - k) % 26 + ord('A'))
            decryption_text.append(decrypted_char)
        elif 'a' <= char <= 'z':
            # 小寫字母：同上，但以 ord('a') 為基準，維持小寫
            decrypted_char = chr((ord(char) - ord('a') - k) % 26 + ord('a'))
            decryption_text.append(decrypted_char)
        else:
            # 標點、空白、數字、非 ASCII 字元：不加密，原樣保留
            decryption_text.append(char)

    # 把字元串列接回完整字串後回傳
    return "".join(decryption_text)


# ==================== 主程式流程 ====================

def main():
    # 讀入使用者輸入的文字（通常是待破解的密文）
    user_input = input("Enter your text: ")

    # 統計字母分布，並印出頻率直方圖
    result = count_letters(user_input)
    total_letters = sum(result.values())

    print_histogram(result)

    if total_letters == 0:              # 無字母則無需嘗試解密
        print("\nNo letters found.")
        return

    possible_k_values = list(range(26))     # 凱撒位移所有可能值：0~25

    print("\nPossible decryption shifts (Caesar):")
    print(possible_k_values)

    # 依密文長度決定動態權重
    chi_w, bg_w, tg_w, vw_w = get_dynamic_weights(total_letters)
    print(
        f"\nDynamic weights (total letters = {total_letters}): "
        f"chi = {chi_w:.3f}, bigram = {bg_w:.3f}, "
        f"trigram = {tg_w:.3f}, vowel = {vw_w:.3f}"
    )

    # 記錄目前最佳的位移與分數（分數範圍 0~1，故初始值設為 -1）
    best_k = None
    best_score = -1.0

    for k in possible_k_values:
        decrypted_text = decryption(user_input, k)

        # 每個位移只需計算一次四項分數，再用同一組權重組合成混合分數
        chi2, chi_score, bg, tg, vw, _ = compute_all_scores(decrypted_text)
        score = mixed_score_from_parts(
            chi_score, bg, tg, vw,
            chi_w, bg_w, tg_w, vw_w
        )

        # 印出此位移的完整分數明細，方便檢視與除錯
        print(
            f"shift k = {k:2d} | chi2 = {chi2:8.2f} | "
            f"chi = {chi_score:.4f} | bigram = {bg:.4f} | trigram = {tg:.4f} | "
            f"vowel = {vw:.4f} | mixed = {score:.4f} | "
            f"decrypted text: {decrypted_text}"
        )

        # 分數更高就更新最佳解
        if score > best_score:
            best_score = score
            best_k = k

    if best_k is not None:
        print(f"\nBest shift by mixed score: k = {best_k} (score = {best_score:.4f})")
        print(f"decrypted text: {decryption(user_input, best_k)}")


# 只有直接執行本檔案時才啟動主流程（被當成模組 import 時不會執行）
if __name__ == "__main__":
    main()
