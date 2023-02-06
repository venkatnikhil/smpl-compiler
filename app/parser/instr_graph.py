from app.parser.instr_node import ConstInstrNode, OpInstrNode, EmptyInstrNode, SingleOpInstrNode
from app.custom_types import InstrNodeActual, InstrNodeType
from typing import Optional
from app.tokens import OpCodeEnum


class InstrGraph:
    def __init__(self) -> None:
        self._instr_map: list[InstrNodeActual] = [ConstInstrNode(0, 0)]
        self._curr_instr: int = 1

    def build_instr_node(self, node_type: InstrNodeType, opcode: OpCodeEnum, instr_num: Optional[int], **kwargs):
        provided = instr_num
        if instr_num is None:
            instr_num = self._curr_instr

        node: Optional[InstrNodeActual] = None

        if node_type is ConstInstrNode:
            node = ConstInstrNode(instr_num=instr_num, val=kwargs["val"])
        elif node_type is OpInstrNode:
            node = OpInstrNode(opcode=opcode, instr_num=instr_num, left=kwargs["left"], right=kwargs["right"])
        elif node_type is EmptyInstrNode:
            node = EmptyInstrNode(instr_num=instr_num)
        elif node_type is SingleOpInstrNode:
            node = SingleOpInstrNode(opcode=opcode, instr_num=instr_num, left=kwargs["left"])

        if len(self._instr_map) == instr_num:
            self._instr_map.append(node)
        else:
            self._instr_map[instr_num] = node  # instr num to **actual** instr node map

        if provided is None:
            self._curr_instr += 1

        return instr_num

    def get_instr(self, instr_num: int) -> InstrNodeActual:
        return self._instr_map[instr_num]

    def debug(self) -> None:
        for node in self._instr_map:
            node.debug()
