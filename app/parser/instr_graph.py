from app.parser.instr_node import ConstInstrNode, OpInstrNode, EmptyInstrNode, SingleOpInstrNode
from app.custom_types import InstrNodeActual, InstrNodeType
from typing import Optional
from app.tokens import OpCodeEnum


class InstrGraph:
    def __init__(self) -> None:
        self._instr_map: list[InstrNodeActual] = [EmptyInstrNode(0)]
        self._curr_instr: int = 1

    def check_if_instr_exists(self, node_type: InstrNodeType, opcode: OpCodeEnum, instr_num: int, **kwargs) -> int:
        # TODO: update logic
        if node_type is EmptyInstrNode or (instr_num is not None and isinstance(self._instr_map[instr_num],
                                                                                EmptyInstrNode)):
            return -1

        for node in self._instr_map:
            if isinstance(node, node_type):
                if node.equals(opcode, **kwargs):
                    return node.instr_num

        return -1

    def build_instr_node(self, node_type: InstrNodeType, opcode: OpCodeEnum, instr_num: Optional[int], **kwargs):
        provided = instr_num
        if instr_num is None:
            instr_num = self._curr_instr

        node: Optional[InstrNodeActual] = None

        # TODO:
        # what happens if there is an exisiting instr same as the instr to be built (suppose cmp a < 1)
        # 1. do we create another instr node?
        # 2. do we reuse the previous one? if yes, is the prev instr added to the current bb instr_list?
        existing_instr = self.check_if_instr_exists(node_type, opcode, provided, **kwargs)
        if existing_instr != -1:
            return existing_instr

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
