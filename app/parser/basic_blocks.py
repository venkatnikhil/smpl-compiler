from app.tokenizer import Tokenizer
from typing import Optional


class BB:
    def __init__(self, bb_num: int) -> None:
        self.bb_num: int = bb_num
        self._instr_list: list[int] = []
        self._var_instr_map: dict[int, int] = dict()

    def debug(self) -> None:
        print(repr(self))

    def update_instr_list(self, instr: int) -> None:
        # TODO: should we check if instr_num is already in the list? check copy_prop_test for info subexpr elimination
        self._instr_list.append(instr)

    def update_var_instr_map(self, ident: int, instr_num: int) -> None:
        self._var_instr_map[ident] = instr_num

    def get_var_instr_num(self, key: int) -> int:
        return self._var_instr_map[key]

    def check_instr_exists(self, key: int) -> bool:
        return key in self._var_instr_map

    def get_first_instr_num(self) -> Optional[int]:
        return self._instr_list[0] if self._instr_list else None

    def remove_empty_instr(self) -> None:
        assert len(self._instr_list) == 1, "BB instr has more than 1 instrs"
        self._instr_list.pop()

    def __repr__(self) -> str:
        def __fmt_var_instr_map() -> dict[str, str]:
            temp = dict()

            for var, val in self._var_instr_map.items():
                if self.bb_num != 0:  # const bb
                    temp[Tokenizer.id2string(var)] = f"({val})"
                else:
                    temp[f"#{var}"] = f"({val})"

            return temp

        def __fmt_instr_list() -> list[str]:
            return [f"({val})" for val in self._instr_list]

        return ("BB%r<instrs: %r | var_instr: %s>" % (self.bb_num, __fmt_instr_list(), __fmt_var_instr_map())).\
            replace("'", "").replace('"', "")
