from tokens import *
from tokenizer import tokenize
from error_handling import CustomSyntaxError


def store(ident, val):
    symbol_table[ident] = val


def lookup(ident):
    rt_val = symbol_table.get(ident, None)
    if rt_val is None:
        raise CustomSyntaxError(message=f"var {ident} referenced before assignment")
    return rt_val


def parse_factor():
    t_type, t_val, t_idx = sym.current
    if t_val == OPEN_PAREN:
        next(sym)
        rt_val = parse_expression()
        if sym.current[1] != CLOSE_PAREN:
            raise CustomSyntaxError(expected=CLOSE_PAREN, found=sym.current[1], at=sym.current[2])
    elif t_type == TokenType.LITERAL:
        rt_val = int(t_val)
    elif t_type == TokenType.IDENTIFIER:
        rt_val = lookup(t_val)
    else:
        raise CustomSyntaxError(expected=f"{OPEN_PAREN} or {TokenType.LITERAL} or {TokenType.IDENTIFIER}",
                                found=t_val, at=t_idx)

    next(sym)
    return rt_val


def parse_term():
    f = parse_factor()
    while sym.current[1] == MULTIPLY or sym.current[1] == DIVIDE:
        op = sym.current[1]
        next(sym)
        if op == MULTIPLY:
            f *= parse_factor()
        else:
            f2 = parse_factor()
            if f2 == 0:
                raise CustomSyntaxError(message="Division by zero!")
            f /= f2

    return f


def parse_expression():
    t = parse_term()
    while sym.current[1] == PLUS or sym.current[1] == MINUS:
        op = sym.current[1]
        next(sym)
        if op == PLUS:
            t += parse_term()
        else:
            t -= parse_term()

    return t


def parse_computation():
    next(sym)
    if sym.current[1] != INPUT_START:
        raise CustomSyntaxError(expected=INPUT_START, found=sym.current[1], at=sym.current[2])

    next(sym)
    while sym.current[1] == VAR_DECL:
        next(sym)
        if sym.current[0] != TokenType.IDENTIFIER:
            raise CustomSyntaxError(expected=TokenType.IDENTIFIER,
                                    found=f"token type: {sym.current[0]} token val: {sym.current[1]}",
                                    at=sym.current[2])
        id = sym.current[1]
        next(sym)
        if sym.current[1] != ASSIGN_OP:
            raise CustomSyntaxError(expected=ASSIGN_OP, found=sym.current[1], at=sym.current[2])

        next(sym)
        val = parse_expression()
        if sym.current[1] != STMT_END:
            raise CustomSyntaxError(expected=STMT_END, found=sym.current[1], at=sym.current[2])

        store(id, val)
        next(sym)

    while sym.current:
        val = parse_expression()
        if sym.current[1] == STMT_END or sym.current[1] == INPUT_END:
            print(val)
            if sym.current[1] == INPUT_END:
                print("##### parsing complete. exiting... #####")
                break
            next(sym)


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2 or not sys.argv[1]:
        expr = input('Enter expression: ')
    else:
        expr = sys.argv[1]

    sym = tokenize(expr)
    symbol_table = dict()

    try:
        parse_computation()
    except StopIteration:
        print(repr(CustomSyntaxError(message="Invalid input")))
    except CustomSyntaxError as e:
        print(repr(e))
