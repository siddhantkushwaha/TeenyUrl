import random
import string


def get_random_alias(n=7):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))


if __name__ == '__main__':
    random_alias = get_random_alias()
    print(random_alias)
