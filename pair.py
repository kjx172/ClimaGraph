import random

#random number
target = random.randint(1, 100)

#get user input
num_guesses = 6

while num_guesses != 0:
    try:
        guess = int(input("Enter a number 1 - 100: "))

        if guess > 100 or guess < 1:
            print("please enter a number within the range")
            continue
        
        if guess == target:
            print(f"Number found: {guess}")
            break

        elif guess < target:
            print("target number is higher")

        elif guess > target:
            print("target number is lower")

        num_guesses -= 1

    except:
        print("Incorrect input, please enter a number")


if num_guesses == 0:
    print(f"Ran out of guesses, the target number was {target}")

