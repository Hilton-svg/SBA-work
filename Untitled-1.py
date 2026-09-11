
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
    return [(ord('E') - ord(letter)) % 26
        for letter, count in counts.items()
        if count == max_count]

def decryption():
    

user_input = input("Enter your text: ")
result = count_letters(user_input)
print_histogram(result)

possible_k_values = displacement_searching(result)
if possible_k_values:
    print("\nPossible decryption shifts (Caesar):")
    print(possible_k_values)