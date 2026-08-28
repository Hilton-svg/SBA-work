
from collections import Counter
import string

def count_letters(text):
    counts = Counter(char for char in text.upper() if char in string.ascii_uppercase)
    return {char: counts.get(char, 0) for char in string.ascii_uppercase}

def print_histogram(counts, ten_symbol="█", unit_symbol='*', show_zero=False):
    print("\nScaled Histogram ( █ = 10 units, * = 1 unit ):")
    print("-" * 50)
    print("Letter counts:")
    for letter, count in counts.items():
        if show_zero or count > 0:
            ten_units = count // 10
            unit_units = count % 10
            bar = f"{ten_symbol * ten_units}{unit_symbol * unit_units}"
            print(f"{letter}: ({count})| {bar}")

def get_possible_k_values(counts):
    max_count = max(counts.values())
    if max_count == 0:
        return []
    

user_input = input("Enter your text: ")
result = count_letters(user_input)
print_histogram(result)
possible_k_values = get_possible_k_values(result)
if possible_k_values:
    print("\nPossible k values for scaling the histogram:")
    print(possible_k_values)