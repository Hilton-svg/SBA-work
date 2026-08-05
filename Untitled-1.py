
import string

message = input("Enter your text: ").upper()
number_of_each_words = {char: 0 for char in string.ascii_uppercase}
for char in message:
    if char in number_of_each_words:
        number_of_each_words[char] += 1