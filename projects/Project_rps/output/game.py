import random

def play():
    choices = ['rock', 'paper', 'scissors']
    print("Welcome to Rock-Paper-Scissors!")
    print("Type 'quit' to stop playing.")

    user_score = 0
    cpu_score = 0

    while True:
        user_choice = input("\nEnter rock, paper, or scissors: ").lower()
        if user_choice == 'quit':
            break
        if user_choice not in choices:
            print("Invalid choice, try again.")
            continue

        cpu_choice = random.choice(choices)
        print(f"Computer chose: {cpu_choice}")

        if user_choice == cpu_choice:
            print("It's a tie!")
        elif (user_choice == 'rock' and cpu_choice == 'scissors') or \
             (user_choice == 'paper' and cpu_choice == 'rock') or \
             (user_choice == 'scissors' and cpu_choice == 'paper'):
            print("You win!")
            user_score += 1
        else:
            print("Computer wins!")
            cpu_score += 1

        print(f"Score -> You: {user_score} | Computer: {cpu_score}")

    print("\nFinal Score")
    print(f"You: {user_score} | Computer: {cpu_score}")
    print("Thanks for playing!")

if __name__ == "__main__":
    play()
