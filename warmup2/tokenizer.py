from tokens import *
from error_handling import CustomSyntaxError


class store_curr_token:
    def __init__(self, generator):
        self._generator = generator

    def __iter__(self):
        return self

    def __next__(self):
        self.current = next(self._generator)
        return self.current

    def __call__(self, expr):
        self._generator = self._generator(expr)
        return self


@store_curr_token
def tokenize(expr):
    ptr = 0

    while ptr < len(expr):
        tok = ""

        while ptr < len(expr) and expr[ptr].isspace():
            ptr += 1

        if ptr == len(expr):
            raise CustomSyntaxError(message=f"Reached end before finding '{INPUT_END}'")

        if expr[ptr] in LETTER:
            while ptr < len(expr) and (expr[ptr] in LETTER or expr[ptr] in DIGIT):
                tok += expr[ptr]
                ptr += 1
            if tok in KEYWORDS:
                t_type = TokenType.KEYWORD
            else:
                t_type = TokenType.IDENTIFIER

        elif expr[ptr] in DIGIT:
            while ptr < len(expr) and expr[ptr] in DIGIT:
                tok += expr[ptr]
                ptr += 1
            t_type = TokenType.LITERAL

        elif expr[ptr] in OPERATORS:
            tok += expr[ptr]
            ptr += 1
            t_type = TokenType.OPERATOR

        elif expr[ptr] in SEPARATORS:
            tok += expr[ptr]
            ptr += 1
            t_type = TokenType.SEPARATOR

        elif expr[ptr] == "<":
            if ptr < len(expr) - 1 and expr[ptr+1] == "-":
                tok += "<-"
                ptr += 2
                t_type = TokenType.OPERATOR
            else:
                raise CustomSyntaxError(expected=f"- after <", found=expr[ptr], at=ptr)

        else:
            raise CustomSyntaxError(expected=f"{[e.value for e in TokenType]}", found=expr[ptr], at=ptr)

        yield t_type, tok, ptr
