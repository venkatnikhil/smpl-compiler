from app.custom_types import InstrNodeType, InstrNodeActual
from app.parser.basic_blocks import BB
from app.parser.instr_graph import InstrGraph
from app.parser.instr_node import OpInstrNode, EmptyInstrNode
from app.tokens import OpCodeEnum
from typing import Optional


class CFG:
    def __init__(self) -> None:
        self.const_bb: Optional[BB] = None
        self._instr_graph: InstrGraph = InstrGraph()
        self.bb_num: int = 0
        self.curr_bb: Optional[BB] = None
        self._predecessors: dict[int, list[int]] = dict()
        self._successors: dict[int, list[int]] = dict()
        self._dom_predecessors: dict[int, list[int]] = dict()
        self._bb_map: dict[int, BB] = dict()
        self.__initialize_cfg()

    def get_bb(self, bb_num: int) -> BB:
        return self._bb_map[bb_num]

    def update_bb_map(self, bb_num: int, bb_obj: BB) -> None:
        self._bb_map[bb_num] = bb_obj

    def update_predecessors(self, bb_num: int, other: list[int]) -> None:
        if bb_num not in self._predecessors:
            self._predecessors[bb_num] = []
        self._predecessors[bb_num].extend(other)

    def update_successors(self, bb_num: int, other: list[int]) -> None:
        if bb_num not in self._successors:
            self._successors[bb_num] = []
        self._successors[bb_num].extend(other)

    def update_dom_predecessors(self, bb_num: int, other: list[int]) -> None:
        if bb_num not in self._dom_predecessors:
            self._dom_predecessors[bb_num] = []
        self._dom_predecessors[bb_num].extend(other)

    def __initialize_cfg(self) -> None:
        bb0: int = self.create_bb([])
        bb1: int = self.create_bb([bb0], [])
        self.const_bb = self.get_bb(bb0)

    def build_instr_node(self, node_type: InstrNodeType, opcode: OpCodeEnum, bb: Optional[BB] = None, **kwargs) -> int:
        if bb is None:
            bb = self.curr_bb
        instr_num: Optional[int] = bb.get_first_instr_num()
        if instr_num is not None:
            if not isinstance(self._instr_graph.get_instr(instr_num), EmptyInstrNode):
                instr_num = None
            else:
                bb.remove_empty_instr()
        instr_num: int = self._instr_graph.build_instr_node(node_type, opcode, instr_num, **kwargs)
        bb.update_instr_list(instr_num)
        return instr_num

    def get_var_instr_num(self, bb: BB, ident: int) -> int:
        if bb.check_instr_exists(ident):
            return bb.get_var_instr_num(ident)

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

    def create_bb(self, predecessors: list[int], dom_predecessors: Optional[list[int]] = None) -> int:
        if dom_predecessors is None:
            dom_predecessors = predecessors

        new_bb: BB = BB(self.bb_num)
        self.curr_bb = new_bb
        self.update_bb_map(self.bb_num, self.curr_bb)
        self.update_predecessors(self.bb_num, predecessors)
        self.update_dom_predecessors(self.bb_num, dom_predecessors)
        self.update_successors(self.bb_num, [])
        self.build_instr_node(EmptyInstrNode, OpCodeEnum.EMPTY.value)

        for parent in predecessors:
            self.update_successors(parent, [self.bb_num])

        self.bb_num += 1
        return self.curr_bb.bb_num

    def get_instr(self, instr_num: int) -> InstrNodeActual:
        return self._instr_graph.get_instr(instr_num)

    def update_instr(self, instr_num: int, change_dict: dict[str, int]) -> None:
        instr = self._instr_graph.get_instr(instr_num)
        assert isinstance(instr, OpInstrNode), "can only update OpInstrNode"
        instr.update_instr(change_dict)

    def debug(self) -> None:
        for bb in self._bb_map.values():
            bb.debug()
        print("\nPredecessors:")
        for bb_num, bb_list in self._predecessors.items():
            print(f"BB{bb_num}: {bb_list}")

        print("\nSuccessors:")
        for bb_num, bb_list in self._successors.items():
            print(f"BB{bb_num}: {bb_list}")

        print("\nDom Predecessors:")
        for bb_num, bb_list in self._dom_predecessors.items():
            print(f"BB{bb_num}: {bb_list}")
