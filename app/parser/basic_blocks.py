from app.tokenizer import Tokenizer


class BB:
    def __init__(self, bb_num):
        self.bb_num = bb_num
        self._instr_list = []
        self._var_instr_map = dict()

    # TODO: add funcs to get references of vars and instrs

    def debug(self):
        print(repr(self))

    def update_instr_list(self, instr):
        self._instr_list.append(instr)

    def update_var_instr_map(self, key, value):
        self._var_instr_map[key] = value

    def get_instr_num(self, key):
        return self._var_instr_map[key]

    def check_instr_exists(self, key):
        return key in self._var_instr_map

    def __repr__(self):
        def __fmt_var_instr_map():
            temp = dict()

            for var, val in self._var_instr_map.items():
                if self.bb_num != 0:
                    temp[Tokenizer.id2string(var)] = f"({val})"
                else:
                    temp[f"#{var}"] = f"({val})"

            return temp

        def __fmt_instr_list():
            return [f"({val})" for val in self._instr_list]

        return ("BB%r<instrs: %r | var_instr: %s>" % (self.bb_num, __fmt_instr_list(), __fmt_var_instr_map())).\
            replace("'", "").replace('"', "")
