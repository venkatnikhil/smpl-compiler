from app.tokens import OpCodeEnum
from typing import Optional


class ConstInstrNode:
    def __init__(self, instr_num: int, val: int) -> None:
        self.opcode: OpCodeEnum = OpCodeEnum.CONST.value
        self.val: int = val
        self.instr_num: int = instr_num

    def debug(self) -> None:
        print(repr(self))

    def equals(self, opcode: OpCodeEnum, val: int) -> bool:
        return self.val == val

    def __repr__(self) -> str:
        return "ConstInstrNode<(%r), %s, #%r>" % (self.instr_num, self.opcode, self.val)


class OpInstrNode:
    def __init__(self, opcode: OpCodeEnum, instr_num: int, left: int, right: Optional[int]) -> None:
        self.opcode: OpCodeEnum = opcode
        self.left: int = left
        self.right: Optional[int] = right
        self.instr_num: int = instr_num

    def debug(self) -> None:
        print(repr(self))

    def equals(self, opcode: str, left: int, right: int) -> bool:
        return self.opcode == opcode and self.left == left and self.right == right

    def update_instr(self, change_dict: dict[str, int]) -> None:
        assert "opcode" not in change_dict, "cannot change opcode of an instr"

        for attr, val in change_dict.items():
            assert hasattr(self, attr), f"instr has no attribute named: {attr}"
            setattr(self, attr, val)

    def __repr__(self) -> str:
        return "OpInstrNode<(%r), %s, (%r), (%r)>" % (self.instr_num, self.opcode, self.left, self.right)


class EmptyInstrNode:
    def __init__(self, instr_num: int) -> None:
        self.opcode: OpCodeEnum = OpCodeEnum.EMPTY.value
        self.instr_num: int = instr_num

    def debug(self) -> None:
        print(repr(self))

    def __repr__(self) -> str:
        return "EmptyInstrNode<(%r), %s>" % (self.instr_num, self.opcode)
