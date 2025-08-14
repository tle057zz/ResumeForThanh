import simpleaudio as sa
import time
import numpy as np
import os
def clear():
    os.system('clear')  # Windows: 'cls', macOS/Linux: 'clear'

# Morse Code Dictionary
MORSE_CODE_DICT = {
    'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..',
    'E': '.',  'F': '..-.', 'G': '--.',  'H': '....',
    'I': '..', 'J': '.---', 'K': '-.-',  'L': '.-..',
    'M': '--', 'N': '-.',   'O': '---',  'P': '.--.',
    'Q': '--.-','R': '.-.', 'S': '...',  'T': '-',
    'U': '..-','V': '...-', 'W': '.--',  'X': '-..-',
    'Y': '-.--','Z': '--..',
    '1': '.----', '2': '..---','3': '...--','4': '....-','5': '.....',
    '6': '-....', '7': '--...','8': '---..','9': '----.','0': '-----',
    ',': '--..--', '.': '.-.-.-','?': '..--..','/': '-..-.',
    '-': '-....-','(': '-.--.', ')': '-.--.-',' ': '/'
}

# Audio tone settings
SAMPLE_RATE = 44100
FREQ = 800  # Hz
DOT_DURATION = 0.1   # seconds
DASH_DURATION = DOT_DURATION * 3
SYMBOL_SPACE = 0.1
LETTER_SPACE = 0.3
WORD_SPACE = 0.7

def generate_tone(duration):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), False)
    tone = np.sin(FREQ * t * 2 * np.pi)
    audio = (tone * 32767).astype(np.int16)
    return sa.play_buffer(audio, 1, 2, SAMPLE_RATE)

def text_to_morse(text):
    morse = ''
    for char in text.upper():
        morse += MORSE_CODE_DICT.get(char, '') + ' '
    return morse.strip()

def play_morse(morse_code):
    for symbol in morse_code:
        if symbol == '.':
            generate_tone(DOT_DURATION).wait_done()
        elif symbol == '-':
            generate_tone(DASH_DURATION).wait_done()
        elif symbol == ' ':
            time.sleep(LETTER_SPACE)
        elif symbol == '/':
            time.sleep(WORD_SPACE)
        time.sleep(SYMBOL_SPACE)
from IPython.display import clear_output
import os

def clear_screen():
    # Check the operating system name
    if os.name == 'nt':  # 'nt' for Windows
        _ = os.system('cls')
    else:  # 'posix' for Unix-like systems (macOS, Linux)
        _ = os.system('clear')

# Call the function to clear the screen
clear_screen()
if __name__ == "__main__":
    while True:
        clear_screen()
        message = input("Enter your message: ")
        morse = text_to_morse(message)
        print("Morse Code:", morse)
        print("Playing audio...")
        play_morse(morse)
        print("\033c", end="")


