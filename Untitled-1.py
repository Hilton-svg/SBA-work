import re
import string
from collections import Counter

# ==================== 常數表 ====================

# 英文單字母頻率（%）
ENGLISH_FREQ = {
    'A': 8.167, 'B': 1.492, 'C': 2.782, 'D': 4.253, 'E': 12.702,
    'F': 2.228, 'G': 2.015, 'H': 6.094, 'I': 6.966, 'J': 0.153,
    'K': 0.772, 'L': 4.025, 'M': 2.406, 'N': 6.749, 'O': 7.507,
    'P': 1.929, 'Q': 0.095, 'R': 5.987, 'S': 6.327, 'T': 9.056,
    'U': 2.758, 'V': 0.978, 'W': 2.360, 'X': 0.150, 'Y': 1.974,
    'Z': 0.074
}

# 常見英文雙字母組
COMMON_BIGRAMS = {
    "th", "he", "in", "er", "an", "re", "nd", "at", "on", "nt",
    "ha", "es", "st", "en", "ed", "to", "it", "ou", "ea", "hi",
    "is", "or", "ti", "as", "te", "et", "ng", "of", "al", "de",
    "se", "le", "sa", "si", "ar", "ve", "ra", "ld", "ur",
}

# 常見英文三字母組
COMMON_TRIGRAMS = {
    "the", "and", "ing", "ent", "ion", "her", "for", "tha", "nth",
    "int", "ere", "tio", "ter", "est", "ers", "ati", "hat", "ate",
    "all", "eth", "hes", "ver", "his", "oft", "sth", "oth", "res",
    "ont",
}

# 混合評分預設權重
CHI_WEIGHT = 0.4
BIGRAM_WEIGHT = 0.3
TRIGRAM_WEIGHT = 0.3


# ==================== 字母統計與評分 ====================

def count_letters(text):
    """
    統計 text 中 A-Z 每個英文字母的出現次數。
    - 不分大小寫，全部先轉成大寫再計數。
    - 回傳的字典保證包含 A-Z 所有字母，沒出現的字母次數為 0。
    """
    counts = Counter(text.upper())
    return {char: counts[char] for char in string.ascii_uppercase}


def chi_square_score(text):
    """
    計算卡方分數（chi-square score）。
    - 分數越低，表示字母分布越接近一般英文。
    - 若文字中完全沒有英文字母，回傳無限大。
    """
    counts = count_letters(text)
    total = sum(counts.values())

    if total == 0:
        return float('inf')

    chi2 = 0.0
    for letter in string.ascii_uppercase:
        observed = counts[letter]
        expected = total * ENGLISH_FREQ[letter] / 100.0
        if expected > 0:
            chi2 += (observed - expected) ** 2 / expected

    return chi2


def extract_words(text):
    """
    以非英文字母為邊界，切出所有單詞。
    - 每個單詞都是純 ASCII 英文字母組成的字串。
    - 特殊字符（空白、標點、數字等）不會被納入單詞。
    """
    return re.findall(r'[A-Za-z]+', text)


def bigram_score(text):
    """
    計算常見雙字母組的命中率。
    - 先以特殊字符為邊界切出單詞，再對每個單詞內部算 bigram。
    - bigram 不會跨越特殊字符。
    - 回傳命中 COMMON_BIGRAMS 的比例，越高越像英文。
    """
    words = extract_words(text)

    total = 0
    hits = 0
    for word in words:
        w = word.lower()
        for i in range(len(w) - 1):
            total += 1
            if w[i:i + 2] in COMMON_BIGRAMS:
                hits += 1

    return hits / total if total > 0 else 0.0


def trigram_score(text):
    """
    計算常見三字母組的命中率。
    - 先以特殊字符為邊界切出單詞，再對每個單詞內部算 trigram。
    - trigram 不會跨越特殊字符。
    - 回傳命中 COMMON_TRIGRAMS 的比例，越高越像英文。
    """
    words = extract_words(text)

    total = 0
    hits = 0
    for word in words:
        w = word.lower()
        for i in range(len(w) - 2):
            total += 1
            if w[i:i + 3] in COMMON_TRIGRAMS:
                hits += 1

    return hits / total if total > 0 else 0.0


def normalize_chi_score(chi2, total_letters):
    """
    把「越低越好」的卡方轉成「越高越好」的分數，範圍 (0, 1]。
    - total_letters 為 0 時回傳 0。
    """
    if total_letters == 0:
        return 0.0
    return 1.0 / (1.0 + chi2 / total_letters)


def compute_all_scores(text):
    """
    一次算好所有分數，避免重複計算。
    回傳 (chi2, chi_score, bg_score, tg_score, total_letters)。
    """
    counts = count_letters(text)
    total_letters = sum(counts.values())

    if total_letters == 0:
        return float('inf'), 0.0, 0.0, 0.0, 0

    chi2 = chi_square_score(text)
    chi_score = normalize_chi_score(chi2, total_letters)
    bg_score = bigram_score(text)
    tg_score = trigram_score(text)

    return chi2, chi_score, bg_score, tg_score, total_letters


def mixed_score_from_parts(chi_score, bg_score, tg_score,
                           chi_weight=CHI_WEIGHT,
                           bigram_weight=BIGRAM_WEIGHT,
                           trigram_weight=TRIGRAM_WEIGHT):
    """用已算好的分數加權，回傳混合分數，越大越好。"""
    return (
        chi_weight * chi_score +
        bigram_weight * bg_score +
        trigram_weight * tg_score
    )


def mixed_score(text,
                chi_weight=CHI_WEIGHT,
                bigram_weight=BIGRAM_WEIGHT,
                trigram_weight=TRIGRAM_WEIGHT):
    """
    混合評分：卡方歸一化分數 + bigram + trigram，越大越好。
    - 這是方便外部直接呼叫的版本，內部會自行計算所有分數。
    """
    chi2, chi_score, bg_score, tg_score, total_letters = compute_all_scores(text)

    if total_letters == 0:
        return -1.0

    return mixed_score_from_parts(
        chi_score, bg_score, tg_score,
        chi_weight, bigram_weight, trigram_weight
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

    print(f"\nLetter Frequency Histogram ( {unit_symbol} = 1% )")
    print("-" * 60)

    if total == 0:
        print("No letters found.")
        return

    print(f"Total letters: {total}")
    print("-" * 60)
    print(f"{'Letter':<8}{'Count':<8}{'Percent':<10}Histogram")
    print("-" * 60)

    for letter, count in counts.items():
        if show_zero or count > 0:
            percent = count / total * 100
            bar_len = int(round(percent))
            if count > 0 and bar_len == 0:
                bar_len = 1  # 非零至少顯示一個符號
            bar = unit_symbol * bar_len
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
            decrypted_char = chr((ord(char) - ord('A') - k) % 26 + ord('A'))
            decryption_text.append(decrypted_char)
        elif 'a' <= char <= 'z':
            decrypted_char = chr((ord(char) - ord('a') - k) % 26 + ord('a'))
            decryption_text.append(decrypted_char)
        else:
            decryption_text.append(char)

    return "".join(decryption_text)


# ==================== 主程式流程 ====================

def main():
    """
    主程式：
    1. 讀取使用者輸入文字。
    2. 統計字母並顯示直方圖。
    3. 枚舉所有 26 個凱撒位移。
    4. 對每個位移解密並計算卡方、bigram、trigram、混合分數。
    5. 選出混合分數最高的位移作為最佳解。
    """
    user_input = input("Enter your text: ")

    # 統計字母出現次數
    result = count_letters(user_input)
    total_letters = sum(result.values())

    # 顯示直方圖
    print_histogram(result)

    # 完全沒有字母時提前結束
    if total_letters == 0:
        print("\nNo letters found.")
        return

    # 枚舉所有 26 個凱撒位移
    possible_k_values = list(range(26))

    print("\nPossible decryption shifts (Caesar):")
    print(possible_k_values)

    best_k = None
    best_score = -1.0

    for k in possible_k_values:
        decrypted_text = decryption(user_input, k)

        # 一次算好所有分數，避免重複計算
        chi2, chi_score, bg, tg, _ = compute_all_scores(decrypted_text)
        score = mixed_score_from_parts(chi_score, bg, tg)

        print(
            f"shift k = {k:2d} | chi2 = {chi2:8.2f} | "
            f"chi = {chi_score:.4f} | bigram = {bg:.4f} | trigram = {tg:.4f} | "
            f"mixed = {score:.4f} | decrypted text: {decrypted_text}"
        )

        if score > best_score:
            best_score = score
            best_k = k

    # 輸出最佳解密結果
    if best_k is not None:
        print(f"\nBest shift by mixed score: k = {best_k} (score = {best_score:.4f})")
        print(f"decrypted text: {decryption(user_input, best_k)}")


if __name__ == "__main__":
    main()