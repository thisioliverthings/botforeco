import random

generated_numbers = set()

def generate_account_number():
    while True:
        account_number = ''.join(random.choices('0123456789', k=8))
        if account_number not in generated_numbers:
            generated_numbers.add(account_number)
            return account_number