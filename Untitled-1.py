
import string

def count_letters(text):
    letter_counts = {char: 0 for char in string.ascii_uppercase}
    for char in text.upper():
        if char in letter_counts:
            letter_counts[char] += 1
    return letter_counts

def print_histogram(counts, symbol='*', show_zero=False):
    for letter, count in counts.items():
        if show_zero or count > 0:
            print(f"{letter}: {symbol * count}")

user_input = input("Enter your text: ")
result = count_letters(user_input)
print("Letter counts:")
for letter, count in result.items():
    print(f"{letter}: {count}")
print("Histogram:")
print_histogram(result)