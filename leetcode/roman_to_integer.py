def romanToInt(s: str) -> int:
    roman_number = {
        "I": 1,
        "V": 5,
        "X": 10,
        "L": 50,
        "C": 100,
        "D": 500,
        "M": 1000
    }
    result = 0
    for i in range(len(s)-1):

        if s[i] in roman_number:
            if roman_number[s[i]] < roman_number[s[i+1]]:
                result -= roman_number[s[i]]
            else:
                result += roman_number[s[i]]

    result += roman_number[s[-1]]
    return int(result)
def main():
    print(romanToInt('LVIII'))


if __name__=='__main__':
   main()