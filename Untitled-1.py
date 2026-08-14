
import string

def count_letters(text):
    letter_counts = {char: 0 for char in string.ascii_uppercase}
    for char in text.upper():
        if char in letter_counts:
            letter_counts[char] += 1
    return letter_counts

def print_histogram(counts, ten_symbol="█", unit_symbol='*', show_zero=False):
    print("\nScaled Histogram ( █ = 10 units, * = 1 unit ):")
    print("-" * 50)
    for letter, count in counts.items():
        if show_zero or count > 0:
            ten_units = count // 10
            unit_units = count % 10
            print(f"{letter}: {ten_symbol * ten_units}{unit_symbol * unit_units}")
            

user_input = input("Enter your text: ")
result = count_letters(user_input)
print("Letter counts:")
for letter, count in result.items():
    print(f"{letter}: {count}")
print_histogram(result)