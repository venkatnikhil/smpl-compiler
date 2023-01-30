class ConstInstrNode:
    def __init__(self, opcode, instr_num, val):
        self.opcode = opcode
        self.val = val
        self.instr_num = instr_num

    def debug(self):
        print(repr(self))

    def __repr__(self):
        return "ConstInstrNode<(%r), %s, #%r>" % (self.instr_num, self.opcode, self.val)


class OpInstrNode:
    def __init__(self, opcode, instr_num, left, right):
        self.opcode = opcode
        self.left = left
        self.right = right
        self.instr_num = instr_num

    def debug(self):
        print(repr(self))

    def __repr__(self):
        return "OpInstrNode<(%r), %s, (%r), (%r)>" % (self.instr_num, self.opcode, self.left, self.right)
