import string
from collections import Counter

# 英文單字母頻率（%）
# 用於卡方檢定：比對待測文字與一般英文文本的字母分布差異。
ENGLISH_FREQ = {
    'A': 8.167, 'B': 1.492, 'C': 2.782, 'D': 4.253, 'E': 12.702,
    'F': 2.228, 'G': 2.015, 'H': 6.094, 'I': 6.966, 'J': 0.153,
    'K': 0.772, 'L': 4.025, 'M': 2.406, 'N': 6.749, 'O': 7.507,
    'P': 1.929, 'Q': 0.095, 'R': 5.987, 'S': 6.327, 'T': 9.056,
    'U': 2.758, 'V': 0.978, 'W': 2.360, 'X': 0.150, 'Y': 1.974,
    'Z': 0.074
}

# 常見英文雙字母組
# 若解密後文字命中越多這些雙字母組，越可能是一段正常英文。
COMMON_BIGRAMS = {
    "th", "he", "in", "er", "an", "re", "nd", "at", "on", "nt",
    "ha", "es", "st", "en", "ed", "to", "it", "ou", "ea", "hi",
    "is", "or", "ti", "as", "te", "et", "ng", "of", "al", "de",
    "se", "le", "sa", "si", "ar", "ve", "ra", "ld", "ur",
}

# 常見英文三字母組（trigram）
COMMON_TRIGRAMS = {
    "the", "and", "ing", "ent", "ion", "her", "for", "tha", "nth",
    "int", "ere", "tio", "ter", "est", "ers", "ati", "hat", "ate",
    "all", "eth", "hes", "ver", "his", "oft", "sth", "oth", "res",
    "ont",
}

def count_letters(text):
    """
    統計 text 中 A-Z 每個英文字母的出現次數。
    - 不分大小寫，全部先轉成大寫再計數。
    - 回傳的字典保證包含 A-Z 所有字母，沒出現的字母次數為 0。
    """
    counts = Counter(text.upper())  # 將文字轉大寫後計數
    return {char: counts[char] for char in string.ascii_uppercase}  # 確保 A-Z 都有鍵

def chi_square_score(text):
    """
    計算卡方分數（chi-square score）。
    - 分數越低，表示字母分布越接近一般英文。
    - 若文字中完全沒有英文字母，回傳無限大。
    """
    counts = count_letters(text)
    total = sum(counts.values())

    if total == 0:
        return float('inf')  # 沒有字母，無法比較

    chi2 = 0.0
    for letter in string.ascii_uppercase:
        observed = counts[letter]  # 實際觀察到的次數
        expected = total * ENGLISH_FREQ[letter] / 100.0  # 依英文頻率計算期望次數
        if expected > 0:
            chi2 += (observed - expected) ** 2 / expected  # 卡方公式

    return chi2  # 越低越像英文

def extract_letters(text):
    """
    取出文字中的所有英文字母，並轉成小寫。
    - 非英文字母（空白、標點、數字等）會被忽略。
    """
    return [c.lower() for c in text if ('a' <= c <= 'z') or ('A' <= c <= 'Z')]

def bigram_score(text):
    """
    計算常見雙字母組的分數。
    - 先取出所有英文字母，再兩兩組成 bigram。
    - 回傳命中 COMMON_BIGRAMS 的比例，越高越像英文。
    """
    letters = extract_letters(text)

    if len(letters) < 2:
        return 0.0  # 少於兩個字母，無法形成雙字母組

    # 建立所有相鄰雙字母組，例如 "hello" -> "he", "el", "ll", "lo"
    bigrams = [''.join(letters[i:i + 2]) for i in range(len(letters) - 1)]

    # 計算有多少個雙字母組出現在常見英文雙字母組集合中
    hits = sum(1 for bg in bigrams if bg in COMMON_BIGRAMS)

    return hits / len(bigrams)  # 命中比例

def trigram_score(text):
    """常見三字母組命中率，回傳 0~1，越大越像英文。"""
    letters = extract_letters(text)
    if len(letters) < 3:
        return 0.0
    trigrams = [''.join(letters[i:i + 3]) for i in range(len(letters) - 2)]
    hits = sum(1 for tg in trigrams if tg in COMMON_TRIGRAMS)
    return hits / len(trigrams)

def mixed_score(text, chi_weight=0.4, bigram_weight=0.3, trigram_weight=0.3):
    """混合評分：卡方歸一化分數 + bigram + trigram，越大越好。"""
    counts = count_letters(text)
    total = sum(counts.values())
    if total == 0:
        return -1.0

    chi2 = chi_square_score(text)
    chi_score = 1.0 / (1.0 + chi2 / total)   # 歸一化到 (0, 1]
    bg_score = bigram_score(text)            # 0~1
    tg_score = trigram_score(text)           # 0~1

    return (
        chi_weight * chi_score +
        bigram_weight * bg_score +
        trigram_weight * tg_score
    )

def print_histogram(counts, ten_symbol="█", unit_symbol='*', show_zero=False):
    """
    以文字直方圖顯示字母計數。
    - ten_symbol 表示每 10 次出現的符號。
    - unit_symbol 表示每 1 次出現的符號。
    - show_zero 為 True 時，連次數 0 的字母也顯示。
    """
    print(f"\nScaled Histogram ( {ten_symbol} = 10 units, {unit_symbol} = 1 unit ):")
    print("-" * 50)
    print("Letter counts:")

    for letter, count in counts.items():
        if show_zero or count > 0:
            # 每 10 個用 ten_symbol，餘數用 unit_symbol
            bar = ten_symbol * (count // 10) + unit_symbol * (count % 10)
            print(f"{letter}: ({count})| {bar}")

def displacement_searching(counts):
    """
    根據最高頻字母推測可能的凱撒位移。
    - 一般英文中 E 出現頻率最高，因此假設密文中最高頻字母可能是 E 加密後的結果。
    - 回傳所有可能位移 k 的清單。
    """
    max_count = max(counts.values())

    if max_count == 0:
        return []  # 完全沒有字母

    # 計算最高頻字母要往前移多少才會變成 E
    return [(ord(letter) - ord('E')) % 26
            for letter, count in counts.items()
            if count == max_count]

def decryption(cipher_text, k):
    """
    凱撒解密：
    - 將每個英文字母往前移 k 位。
    - 大寫字母保持大寫，小寫字母保持小寫。
    - 非英文字母原樣保留。
    """
    decryption_text = []

    for char in cipher_text:
        if char.isupper():
            # 大寫字母解密
            decrypted_char = chr((ord(char) - ord('A') - k) % 26 + ord('A'))
            decryption_text.append(decrypted_char)
        elif char.islower():
            # 小寫字母解密
            decrypted_char = chr((ord(char) - ord('a') - k) % 26 + ord('a'))
            decryption_text.append(decrypted_char)
        else:
            # 非字母字元直接保留
            decryption_text.append(char)

    return "".join(decryption_text)

# ==================== 主程式流程 (Main Flow) ====================

def main():
    """
    主程式：
    1. 讀取使用者輸入文字。
    2. 統計字母並顯示直方圖。
    3. 推測可能的凱撒位移。
    4. 對每個候選位移解密並評分。
    5. 選出混合分數最高的位移作為最佳解。
    """
    user_input = input("Enter your text: ")

    # 統計字母出現次數
    result = count_letters(user_input)

    # 顯示直方圖
    print_histogram(result)

    # 根據最高頻字母找出可能的位移
    possible_k_values = list(range(26))

    if possible_k_values:
        print("\nPossible decryption shifts (Caesar):")
        print(possible_k_values)

        best_k = None
        best_score = -1.0

        # 逐一嘗試每個候選位移
        for k in possible_k_values:
            decrypted_text = decryption(user_input, k)

            # 計算各種分數
            chi2 = chi_square_score(decrypted_text)
            bg = bigram_score(decrypted_text)
            tg = trigram_score(decrypted_text)
            score = mixed_score(decrypted_text)

            # 印出評估結果
            print(
                f"shift k = {k:2d} | chi2 = {chi2:8.2f} | "
                f"bigram = {bg:.4f} | trigram = {tg:.4f} | "
                f"mixed = {score:.4f} | decrypted text: {decrypted_text}"
            )

            # 保留最高分的位移
            if score > best_score:
                best_score = score
                best_k = k

        # 輸出最佳解密結果
        if best_k is not None:
            print(f"\nBest shift by mixed score: k = {best_k} (score = {best_score:.4f})")
            print(f"decrypted text: {decryption(user_input, best_k)}")
    else:
        print("\nNo letters found.")

if __name__ == "__main__":
    main()