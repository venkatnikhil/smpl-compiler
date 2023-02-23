from app.tokens import OpCodeEnum
from typing import Optional
from app.tokenizer import Tokenizer


class ConstInstrNode:
    def __init__(self, instr_num: int, val: int) -> None:
        self.opcode: OpCodeEnum = OpCodeEnum.CONST.value
        self.val: int = val
        self.instr_num: int = instr_num

    def debug(self) -> None:
        print(repr(self))

    def equals(self, opcode: OpCodeEnum, val: int) -> bool:
        return self.opcode == opcode and self.val == val

    def __repr__(self) -> str:
        return "%r: ConstInstrNode <%s, #%r>" % (self.instr_num, self.opcode, self.val)

    def __str__(self) -> str:
        return "%s: %s #%s" % (self.instr_num, self.opcode, self.val)


class AddrInstrNode:
    def __init__(self, instr_num: int, val: str) -> None:
        self.opcode: OpCodeEnum = OpCodeEnum.CONST.value
        self.val: str = val
        self.instr_num: int = instr_num

    def debug(self) -> None:
        print(repr(self))

    def equals(self, opcode: OpCodeEnum, val: str) -> bool:
        return self.opcode == opcode and self.val == val

    def __repr__(self) -> str:
        return "%r: AddrInstrNode <%s, #%s>" % (self.instr_num, self.opcode, self.val)

    def __str__(self) -> str:
        return "%s: %s #%s" % (self.instr_num, self.opcode, self.val)


class ZeroOpInstrNode:
    def __init__(self, opcode: OpCodeEnum, instr_num: int) -> None:
        self.opcode: OpCodeEnum = opcode
        self.instr_num: int = instr_num

    def debug(self) -> None:
        print(repr(self))

    def equals(self, opcode: OpCodeEnum) -> bool:
        return self.opcode == opcode

    def __repr__(self) -> str:
        return "%r: ZeroOpInstrNode <%s>" % (self.instr_num, self.opcode)

    def __str__(self) -> str:
        return "%s: %s" % (self.instr_num, self.opcode)


class OpInstrNode:
    def __init__(self, opcode: OpCodeEnum, instr_num: int, left: Optional[int], right: Optional[int]) -> None:
        self.opcode: OpCodeEnum = opcode
        self.left: Optional[int] = left
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
        return "%r: OpInstrNode <%s, (%r), (%s)>" % (self.instr_num, self.opcode, self.left, self.right)

    def __str__(self) -> str:
        return "%s: %s (%s) (%s)" % (self.instr_num, self.opcode, self.left, self.right)


class EmptyInstrNode:
    def __init__(self, instr_num: int) -> None:
        self.opcode: OpCodeEnum = OpCodeEnum.EMPTY.value
        self.instr_num: int = instr_num

    def debug(self) -> None:
        print(repr(self))

    def __repr__(self) -> str:
        return "%r: EmptyInstrNode <%s>" % (self.instr_num, self.opcode)

    def __str__(self) -> str:
        return "%s: %s" % (self.instr_num, self.opcode.replace("<", "\\<").replace(">", "\\>"))


class SingleOpInstrNode:
    def __init__(self, opcode: OpCodeEnum, instr_num: int, left: int) -> None:
        self.opcode: OpCodeEnum = opcode
        self.left: int = left
        self.instr_num: int = instr_num

    def debug(self) -> None:
        print(repr(self))

    def equals(self, opcode: str, left: int) -> bool:
        return self.opcode == opcode and self.left == left

    def update_instr(self, change_dict: dict[str, int]) -> None:
        assert "opcode" not in change_dict, "cannot change opcode of an instr"

        for attr, val in change_dict.items():
            assert hasattr(self, attr), f"instr has no attribute named: {attr}"
            setattr(self, attr, val)

    def __repr__(self) -> str:
        if self.opcode == OpCodeEnum.CALL.value:
            return "%r: SingleOpInstrNode <%s, %s>" % (self.instr_num, self.opcode, Tokenizer.id2string(self.left))
        return "%r: SingleOpInstrNode <%s, (%r)>" % (self.instr_num, self.opcode, self.left)

    def __str__(self) -> str:
        if self.opcode == OpCodeEnum.CALL.value:
            return "%s: %s %s" % (self.instr_num, self.opcode, Tokenizer.id2string(self.left))
        return "%s: %s (%s)" % (self.instr_num, self.opcode, self.left)
