import random


def generate_if_stmt():
    pass


def generate_rand_expr():
    exp = ""
    op = ["+", "-", "/", "*"]
    count = 0
    max_count = 50

    def generate_expr(add_op=False):
        nonlocal exp, count

        exp += " " * random.randint(0, 10)
        if add_op:
            exp += str(random.choice(op))
        nest = random.randint(0, 1)
        if nest:
            count += 1
            exp += "("
            generate_expr()
            exp += ")"
        else:
            exp += str(random.randint(1, 10))
            opd = random.randint(0, 5)
            for _ in range(opd):
                exp += str(random.choice(op))
                exp += str(random.randint(1, 10))
        if count < max_count and random.randint(0, 1):
            generate_expr(True)

    generate_expr()
    return exp+"."
