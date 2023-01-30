from app.parser.instr_node import ConstInstrNode, OpInstrNode


class InstrGraph:
    def __init__(self):
        self._instr_map = dict()
        self._curr_instr = 1

    def build_instr_node(self, node_type, opcode, **kwargs):
        if node_type is ConstInstrNode:
            node = ConstInstrNode(opcode=opcode, instr_num=self._curr_instr, val=kwargs["val"])
        elif node_type is OpInstrNode:
            node = OpInstrNode(opcode=opcode, instr_num=self._curr_instr, left=kwargs["left"], right=kwargs["right"])

        self._instr_map[self._curr_instr] = node
        self._curr_instr += 1
        return self._curr_instr - 1

    def debug(self):
        for node in self._instr_map.values():
            node.debug()
