from app.custom_types import InstrNodeType
from app.parser.basic_blocks import BB
from app.parser.instr_graph import InstrGraph
from app.parser.instr_node import OpInstrNode
from app.tokens import OpCodeEnum
from typing import Optional


class CFG:
    def __init__(self) -> None:
        self.const_bb: Optional[BB] = None
        self._instr_graph: InstrGraph = InstrGraph()
        self.bb_num: int = 2
        self.curr_bb: Optional[BB] = None
        self._predecessors: dict[int, list[int]] = dict()
        self._successors: dict[int, list[int]] = dict()
        self._dom_predecessors: dict[int, list[int]] = dict()
        self._bb_map: dict[int, BB] = dict()
        self.initialize_cfg()

    def get_bb(self, bb_num: int) -> BB:
        return self._bb_map[bb_num]

    def update_bb_map(self, bb_num: int, bb_obj: BB) -> None:
        self._bb_map[bb_num] = bb_obj

    def update_predecessors(self, bb_num: int, other: int) -> None:
        if bb_num not in self._predecessors:
            self._predecessors[bb_num] = []
        self._predecessors[bb_num].append(other)

    def update_successors(self, bb_num: int, other: int) -> None:
        if bb_num not in self._successors:
            self._successors[bb_num] = []
        self._successors[bb_num].append(other)

    def update_dom_predecessors(self, bb_num: int, other: int) -> None:
        if bb_num not in self._dom_predecessors:
            self._dom_predecessors[bb_num] = []
        self._dom_predecessors[bb_num].append(other)

    def initialize_cfg(self) -> None:
        bb0: BB = BB(0)
        bb1: BB = BB(1)
        self.update_bb_map(0, bb0)
        self.update_bb_map(1, bb1)
        self.update_predecessors(bb1.bb_num, bb0.bb_num)
        self.update_successors(bb0.bb_num, bb1.bb_num)
        self.curr_bb = bb1
        self.const_bb = bb0

    def build_instr_node(self, node_type: InstrNodeType, opcode: str, bb: Optional[BB] = None, **kwargs) -> int:
        if bb is None:
            bb = self.curr_bb
        instr_num: int = self._instr_graph.build_instr_node(node_type, opcode, **kwargs)
        bb.update_instr_list(instr_num)
        return instr_num

    def get_var_instr_num(self, bb: BB, ident: int) -> int:
        if bb.check_instr_exists(ident):
            return bb.get_instr_num(ident)

        search_space: list[int] = self._predecessors[bb.bb_num]
        res: set[int] = set()
        for node in search_space:
            res.add(self.get_var_instr_num(self._bb_map[node], ident))

        res: list[int] = list(res)
        if len(res) > 1:
            instr_num = self.build_instr_node(OpInstrNode, OpCodeEnum.PHI.value, bb=bb, left=res[0], right=res[1])
        else:
            instr_num = res[0]

        return instr_num

    def debug(self) -> None:
        for bb in self._bb_map.values():
            bb.debug()
