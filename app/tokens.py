from enum import Enum


DIGIT = {str(i) for i in range(0, 10)}
LETTER = {chr(i) for i in range(ord("a"), ord("z") + 1)}.union({chr(i) for i in range(ord("A"), ord("Z") + 1)})

MULTI_OPERATOR_START = {'=', '!', '>', '<'}

TYPE_KEYWORD = 'keyword'
TYPE_IDENTIFIER = 'identifier'
TYPE_NUMBER = 'number'

DEFAULT_TOKENS = {
    '': 0,
    '*': 1,
    '/': 2,
    '+': 11,
    '-': 12,
    '==': 20,
    '!=': 21,
    '<': 22,
    '>=': 23,
    '<=': 24,
    '>': 25,
    '.': 30,
    ',': 31,
    '[': 32,
    ']': 34,
    ')': 35,
    '<-': 40,
    'then': 41,
    'do': 42,
    '(': 50,
    'number': 60,
    'identifier': 61,
    ';': 70,
    '}': 80,
    'od': 81,
    'fi': 82,
    'else': 90,
    'let': 100,
    'call': 101,
    'if': 102,
    'while': 103,
    'return': 104,
    'var': 110,
    'array': 111,
    'void': 112,
    'function': 113,
    'procedure': 114,
    '{': 150,
    'main': 200,
    'InputNum': 201,
    'OutputNum': 202,
    'OutputNewLine': 203,
    'end of file': 255
}

END_OF_FILE = list(DEFAULT_TOKENS.keys())[-1]


class TokenEnum(Enum):
    TIMES = 1
    DIV = 2
    PLUS = 11
    MINUS = 12
    EQL = 20
    NEQ = 21
    LSS = 22
    GEQ = 23
    LEQ = 24
    GTR = 25
    PERIOD = 30
    COMMA = 31
    OPEN_BRACKET = 32
    CLOSE_BRACKET = 34
    CLOSE_PAREN = 35
    BECOMES = 40
    THEN = 41
    DO = 42
    OPEN_PAREN = 50
    NUMBER = 60
    IDENTIFIER = 61
    SEMI = 70
    END = 80
    OD = 81
    FI = 82
    ELSE = 90
    LET = 100
    CALL = 101
    IF = 102
    WHILE = 103
    RETURN = 104
    VAR = 110
    ARR = 111
    VOID = 112
    FUNC = 113
    PROC = 114
    BEGIN = 150
    MAIN = 200
    READ = 201
    WRITE = 202
    WRITE_NL = 203
    EOF = 255
    ERROR = 0


class OpCodeEnum(Enum):
    CONST = "const"
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    CMP = "cmp"
    ADDA = "adda"
    LOAD = "load"
    STORE = "store"
    PHI = "phi"
    END = "end"
    BRA = "bra"
    BNE = "bne"
    BEQ = "beq"
    BLE = "ble"
    BLT = "blt"
    BGE = "bge"
    BGT = "bgt"
    READ = "read"
    WRITE = "write"
    WRITE_NL = "writeNL"
    EMPTY = "<empty>"
    KILL = "kill"


RELOP_TOKEN_OPCODE = {
    TokenEnum.EQL.value: OpCodeEnum.BNE.value,
    TokenEnum.NEQ.value: OpCodeEnum.BEQ.value,
    TokenEnum.LSS.value: OpCodeEnum.BGE.value,
    TokenEnum.GEQ.value: OpCodeEnum.BLT.value,
    TokenEnum.LEQ.value: OpCodeEnum.BGT.value,
    TokenEnum.GTR.value: OpCodeEnum.BLE.value
}
