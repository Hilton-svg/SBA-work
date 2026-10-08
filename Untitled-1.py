import string
from collections import Counter

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
COMMON_BIGRAMS = set(
    "th he in er an re nd at on nt ha es st en ed to it ou ea hi is "
    "or ti as te et ng of al de se le sa si ar ve ra ld ur".split()
)

def count_letters(text):
    counts = Counter(text.upper())
    return {char: counts[char] for char in string.ascii_uppercase}

def chi_square_score(text):
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

def extract_letters(text):
    return [c.lower() for c in text if ('a' <= c <= 'z') or ('A' <= c <= 'Z')]

def bigram_score(text):
    letters = extract_letters(text)
    if len(letters) < 2:
        return 0.0
    bigrams = [''.join(letters[i:i + 2]) for i in range(len(letters) - 1)]
    hits = sum(1 for bg in bigrams if bg in COMMON_BIGRAMS)
    return hits / len(bigrams)

def mixed_score(text, chi_weight=0.5, bigram_weight=0.5):
    counts = count_letters(text)
    total = sum(counts.values())
    if total == 0:
        return -1.0

    chi2 = chi_square_score(text)
    chi_score = 1.0 / (1.0 + chi2 / total)
    bg_score = bigram_score(text)
    return chi_weight * chi_score + bigram_weight * bg_score

def print_histogram(counts, ten_symbol="█", unit_symbol='*', show_zero=False):
    print(f"\nScaled Histogram ( {ten_symbol} = 10 units, {unit_symbol} = 1 unit ):")
    print("-" * 50)
    print("Letter counts:")
    for letter, count in counts.items():
        if show_zero or count > 0:
            bar = ten_symbol * (count // 10) + unit_symbol * (count % 10)
            print(f"{letter}: ({count})| {bar}")

def displacement_searching(counts):
    max_count = max(counts.values())
    if max_count == 0:
        return []
    return [(ord(letter) - ord('E')) % 26
        for letter, count in counts.items()
        if count == max_count]

def decryption(cipher_text, k):
    decryption_text = []
    for char in cipher_text:
        if char.isupper():
            decrypted_char = chr((ord(char) - ord('A') - k) % 26 + ord('A'))
            decryption_text.append(decrypted_char)
        elif char.islower():
            decrypted_char = chr((ord(char) - ord('a') - k) % 26 + ord('a'))
            decryption_text.append(decrypted_char)
        else:
            decryption_text.append(char)
    return "".join(decryption_text)

# ==================== 主程式流程 (Main Flow) ====================

def main():
    user_input = input("Enter your text: ")
    result = count_letters(user_input)
    print_histogram(result)

    possible_k_values = displacement_searching(result)
    if possible_k_values:
        print("\nPossible decryption shifts (Caesar):")
        print(possible_k_values)

        best_k = None
        best_score = -1.0

        for k in possible_k_values:
            decrypted_text = decryption(user_input, k)
            chi2 = chi_square_score(decrypted_text)
            bg = bigram_score(decrypted_text)
            score = mixed_score(decrypted_text)
            print(
                f"shift k = {k:2d} | chi2 = {chi2:8.2f} | "
                f"bigram = {bg:.4f} | mixed = {score:.4f} | "
                f"decrypted text: {decrypted_text}"
            )

            if score > best_score:
                best_score = score
                best_k = k

        if best_k is not None:
            print(f"\nBest shift by mixed score: k = {best_k} (score = {best_score:.4f})")
            print(f"decrypted text: {decryption(user_input, best_k)}")
    else:
        print("\nNo letters found.")

if __name__ == "__main__":
    main()