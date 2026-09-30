
from collections import Counter
import string

def count_letters(text):
    counts = Counter(text.upper())
    return {char: counts[char] for char in string.ascii_uppercase}

def print_histogram(counts, ten_symbol="█", unit_symbol='*', show_zero=True):
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

user_input = input("Enter your text: ")
result = count_letters(user_input)
print_histogram(result)

possible_k_values = displacement_searching(result)
if possible_k_values:
    print("\nPossible decryption shifts (Caesar):")
    print(possible_k_values)
    for k in possible_k_values:
        decrypted_text = decryption(user_input, k)
        print(f"shift k = {k:2d} | decrypted text: {decrypted_text}")
else:
    print("\nNo letters found.")