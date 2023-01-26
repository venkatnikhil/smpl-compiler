from enum import Enum


class TokenType(Enum):
    IDENTIFIER = 'IDENTIFIER'
    KEYWORD = 'KEYWORD'
    SEPARATOR = 'SEPARATOR'
    OPERATOR = 'OPERATOR'
    LITERAL = 'LITERAL'


DIGIT = {str(i) for i in range(0, 10)}
LETTER = {chr(i) for i in range(ord("a"), ord("z") + 1)}

ASSIGN_OP = "<-"
PLUS = "+"
MINUS = "-"
MULTIPLY = "*"
DIVIDE = "/"

INPUT_START = "computation"
VAR_DECL = "var"

OPEN_PAREN = "("
CLOSE_PAREN = ")"
STMT_END = ";"
INPUT_END = "."


OPERATORS = {ASSIGN_OP, PLUS, MINUS, MULTIPLY, DIVIDE}
KEYWORDS = {INPUT_START, VAR_DECL}
SEPARATORS = {STMT_END, OPEN_PAREN, CLOSE_PAREN, INPUT_END}
