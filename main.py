from app.tokenizer import Tokenizer
from app.parser.parser import Parser

# tokenizer = Tokenizer('test.txt')
# token = -1
# while(token != 30):
#     token = tokenizer.get_next()
#     value = list(tokenizer._token_map.keys())[list(tokenizer._token_map.values()).index(token)]
#     if value == 'identifier':
#         value = str(tokenizer.id) + ' ' + list(tokenizer._token_map.keys())[list(tokenizer._token_map.values()).index(tokenizer.id)]
#     elif value == 'number':
#         value = tokenizer.number
#     print(token, value)
if __name__ == '__main__':
    parser_obj = Parser("test.txt")
    parser_obj.parse_computation()
    parser_obj.cfg._instr_graph.debug()
    parser_obj.cfg.debug()
