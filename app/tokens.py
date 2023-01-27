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
    'end of file': 255
}

EOF = list(DEFAULT_TOKENS.keys())[-1]