from app.tokenizer import Tokenizer
from app.parser.parser import Parser
from app.error_handling import CustomSyntaxError
from ir_viz_tool.ir_viz import IRViz

# tokenizer = Tokenizer('if_then.txt')
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
    import os

    include = [
            # "if_then.txt",
            # "copy_prop_test.txt",
            # "nested_if_then_else.txt",
            # "var_copy_prop.txt",
            # "subexpr_1.txt",
            "subexpr_if.txt",
            # "subexpr_if_2.txt",
            # "error_test.txt"
            ]

    dirpath = "./tests/"
    for file in os.listdir(dirpath):
        try:
            if (file in include or not include) and file.endswith(".txt"):
                print(file, "\n")
                parser_obj = Parser(dirpath+file)
                parser_obj.parse_computation()
                parser_obj.cfg._instr_graph.debug()
                parser_obj.cfg.debug()
                print(end="\n\n\n")
                ir_viz = IRViz(parser_obj.cfg, filename=file)
                ir_viz.generate_graph()
        except CustomSyntaxError as e:
            print(repr(e))
