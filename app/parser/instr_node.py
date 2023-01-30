from app.tokens import OpCodeEnum


class ConstInstrNode:
    def __init__(self, instr_num: int, val: int) -> None:
        self.opcode: str = OpCodeEnum.CONST.value
        self.val: int = val
        self.instr_num: int = instr_num

    def debug(self) -> None:
        print(repr(self))

    def __repr__(self) -> str:
        return "ConstInstrNode<(%r), %s, #%r>" % (self.instr_num, self.opcode, self.val)


class OpInstrNode:
    def __init__(self, opcode: str, instr_num: int, left: int, right: int) -> None:
        self.opcode: str = opcode
        self.left: int = left
        self.right: int = right
        self.instr_num: int = instr_num

    def debug(self) -> None:
        print(repr(self))

    def __repr__(self) -> str:
        return "OpInstrNode<(%r), %s, (%r), (%r)>" % (self.instr_num, self.opcode, self.left, self.right)
