import random
import string


def get_random_string(length=10):
    """Generates 10 random ascii lowercase letters."""
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))
