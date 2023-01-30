from app.parser.instr_node import ConstInstrNode, OpInstrNode
from app.custom_types import InstrNodeType


class InstrGraph:
    def __init__(self) -> None:
        self._instr_map: dict[int, InstrNodeType] = dict()
        self._curr_instr: int = 1

    def build_instr_node(self, node_type: InstrNodeType, opcode: str, **kwargs):
        if node_type is ConstInstrNode:
            node = ConstInstrNode(opcode=opcode, instr_num=self._curr_instr, val=kwargs["val"])  # TODO: REMOVE opcode
        elif node_type is OpInstrNode:
            node = OpInstrNode(opcode=opcode, instr_num=self._curr_instr, left=kwargs["left"], right=kwargs["right"])

        self._instr_map[self._curr_instr] = node  # instr num to **actual** instr node map
        self._curr_instr += 1
        return self._curr_instr - 1

    def debug(self) -> None:
        for node in self._instr_map.values():
            node.debug()
