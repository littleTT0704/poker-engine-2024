def calculate_differences(numbers):
    wins = 0
    for i in range(1, len(numbers)):
        difference = numbers[i] - numbers[i - 1]
        if difference >= 0:
            sign = 1
        else:
            sign = 0
        wins += sign
    
    return wins

l = [1,4,2,5,2,3,7,1]
print(calculate_differences(l))