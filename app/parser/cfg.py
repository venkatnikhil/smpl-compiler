from app.custom_types import InstrNodeType, InstrNodeActual
from app.parser.basic_blocks import BB
from app.parser.instr_graph import InstrGraph
from app.parser.instr_node import OpInstrNode, EmptyInstrNode
from app.tokens import OpCodeEnum, RELOP_TOKEN_OPCODE, TokenEnum
from typing import Optional, Union
from app.tokenizer import Tokenizer


class CFG:
    def __init__(self) -> None:
        self.const_bb: Optional[BB] = None
        self._instr_graph: InstrGraph = InstrGraph()
        self.bb_num: int = 0
        self.curr_bb: Optional[BB] = None
        self._predecessors: list[list[int]] = list()
        self._successors: list[list[int]] = list()
        self._dom_predecessors: list[int] = list()
        self._bb_map: list[BB] = list()
        self.declared_vars: set[int] = set()
        self.excluded_instrs: set[OpCodeEnum] = {RELOP_TOKEN_OPCODE.values()}.union(
            {OpCodeEnum.PHI.value, OpCodeEnum.BRA.value, OpCodeEnum.CONST.value, OpCodeEnum.EMPTY.value})
        self._phi_scope: list[tuple[int, TokenEnum]] = list()

        self.__initialize_cfg()

    def add_phi_scope(self, bb_num: int, bb_type: TokenEnum) -> None:
        self._phi_scope.append((bb_num, bb_type))

    def remove_phi_scope(self) -> None:
        self._phi_scope.pop()

    def get_phi_scope(self) -> Optional[tuple[int, TokenEnum]]:
        if self._phi_scope:
            return self._phi_scope[-1]
        return None

    def create_phi(self, ident: int, instr_num: int, assignment: bool = False) -> None:
        phi_scope: Optional[tuple[int, TokenEnum]] = self.get_phi_scope()

        if phi_scope:
            phi_bb_num: int = phi_scope[0]
            phi_bb: BB = self.get_bb(phi_bb_num)
            # print(phi_bb_num, phi_scope[1])
            is_while: bool = True if phi_scope[1] == TokenEnum.WHILE.value else False

            if assignment and not is_while:
                phi_instr_num: int = self.build_instr_node(OpInstrNode, OpCodeEnum.PHI.value, bb=phi_bb_num, left=None,
                                                           right=None)
                self.remove_phi_scope()
                self.update_var_instr_map(phi_bb, ident, phi_instr_num)
                self.add_phi_scope(phi_scope[0], phi_scope[1])

            # TODO: Resolve the similar case of while
            # if assignment and is_while:
            #     phi_instr_num: int = self.build_instr_node(OpInstrNode, OpCodeEnum.PHI.value, bb=phi_bb_num, left=None,
            #                                                right=None)
            #     phi_bb.update_var_instr_map(ident, phi_instr_num)

    def update_var_instr_map(self, bb: BB, ident: int, instr_num: int, assign: bool = False) -> None:
        bb.update_var_instr_map(ident, instr_num)
        self.create_phi(ident, instr_num, assignment=assign)

    def resolve_phi(self, bb_num: int) -> None:
        bb = self.get_bb(bb_num)
        var_instr_map = bb.get_var_instr_map()
        for ident, instr_num in var_instr_map.items():
            instr = self.get_instr(instr_num)
            if instr.opcode == OpCodeEnum.PHI.value:
                l_instr = instr.left
                r_instr = instr.right
                if l_instr is None:
                    l_instr = self.get_var_instr_num(self._predecessors[bb_num][0], ident, set())
                if r_instr is None:
                    r_instr = self.get_var_instr_num(self._predecessors[bb_num][1], ident, set())

                if l_instr == r_instr:
                    # TODO: propagate the new instr_num for ident to successors in case of while
                    bb.update_var_instr_map(ident, l_instr)
                else:
                    self.update_instr(instr_num, {"left": l_instr, "right": r_instr})

                if self.get_phi_scope() is not None and self.get_phi_scope()[0] is TokenEnum.WHILE.value:
                    # TODO: resolve the changed instructions in the successors for the case of while
                    continue

    def get_bb(self, bb_num: int) -> BB:
        return self._bb_map[bb_num]

    def update_bb_map(self, bb_obj: BB) -> None:
        self._bb_map.append(bb_obj)

    def update_predecessors(self, bb_num: int, other: list[int]) -> None:
        if len(self._predecessors) == bb_num:
            self._predecessors.append([])
        self._predecessors[bb_num].extend(other)

    def update_successors(self, bb_num: int, other: list[int]) -> None:
        if len(self._successors) == bb_num:
            self._successors.append([])
        self._successors[bb_num].extend(other)

    def update_dom_predecessors(self, bb_num: int, other: list[int]) -> None:
        if len(self._dom_predecessors) == bb_num:
            self._dom_predecessors.append(-1)
        self._dom_predecessors[bb_num] = other[0] if other else -1

    def __initialize_cfg(self) -> None:
        bb0: int = self.create_bb([])
        bb1: int = self.create_bb([bb0], [])
        self.const_bb = self.get_bb(bb0)

    def get_common_subexpr(self, bb: BB, opcode: OpCodeEnum, **kwargs) -> Optional[int]:
        instrs: list[int] = bb.opcode_instr_order[opcode]

        for instr in instrs:
            if self._instr_graph.get_instr(instr).equals(opcode, **kwargs):
                return instr

        dom_pred = self._dom_predecessors[bb.bb_num]
        if dom_pred == -1:
            return None

        return self.get_common_subexpr(self.get_bb(dom_pred), opcode, **kwargs)

    def build_instr_node(self, node_type: InstrNodeType, opcode: OpCodeEnum, bb: Optional[int] = None, **kwargs) -> int:
        if bb is None:
            bb = self.curr_bb
        else:
            bb = self.get_bb(bb)

        if opcode not in self.excluded_instrs:
            existing_instr = self.get_common_subexpr(bb, opcode, **kwargs)
            if existing_instr is not None:
                return existing_instr

        instr_num: Optional[int] = bb.get_first_instr_num()
        if instr_num is not None:  # there is at least 1 instr present in BB
            if not isinstance(self._instr_graph.get_instr(instr_num), EmptyInstrNode):
                instr_num = None  # first instr is not an Empty instr; create new instr node with new instr num
            else:
                bb.remove_empty_instr()  # first instr is Empty instr; create new instr node with **same** instr num
        instr_num: int = self._instr_graph.build_instr_node(node_type, opcode, instr_num, **kwargs)
        bb.update_instr_list(instr_num, is_phi=opcode == OpCodeEnum.PHI.value)
        bb.update_opcode_instr_order(opcode, instr_num)
        return instr_num

    def get_var_instr_num(self, bb: Union[BB, int], ident: int, visited_bb: set[int]) -> Optional[int]:
        if isinstance(bb, int):
            bb = self.get_bb(bb)
        if bb.bb_num in visited_bb:
            return
        visited_bb.add(bb.bb_num)
        if bb.check_instr_exists(ident):
            return bb.get_var_instr_num(ident)

        search_space: list[int] = self._predecessors[bb.bb_num]
        # res: list[int] = list()
        res: set[int] = set()
        for node in search_space:
            instr = self.get_var_instr_num(self._bb_map[node], ident, visited_bb)
            if instr is not None:
                res.add(instr)

        assert len(res) <= 1, f"2 different resolutions found for phi for ident: {Tokenizer.id2string(ident)}"
        # instr_num: Optional[int] = None
        if bb.bb_num == 0:
            print(f"Warning!: {Tokenizer.id2string(ident)} referenced before assignment!")
            return 0
        else:
            return res.pop()

        # if len(res) > 1 and res[0] != res[1]:
        #     instr_num = self.build_instr_node(OpInstrNode, OpCodeEnum.PHI.value, bb=bb.bb_num, left=res[0],
        #                                       right=res[1])
        #     self.update_var_instr_map(bb, ident, instr_num)
        # elif len(set(res)) == 1:
        #     instr_num = res[0]
        # elif bb.bb_num == 0:
        #     print(f"Warning!: {Tokenizer.id2string(ident)} referenced before assignment!")
        #     instr_num = 0  # uninitialized vars

        # return instr_num

    def create_bb(self, predecessors: list[int], dom_predecessors: Optional[list[int]] = None) -> int:
        if dom_predecessors is None:
            dom_predecessors = predecessors

        new_bb: BB = BB(self.bb_num)
        self.curr_bb = new_bb
        self.update_bb_map(self.curr_bb)
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

    def update_branch_instrs(self) -> None:
        for bb in self._bb_map:
            instr: InstrNodeActual = self._instr_graph.get_instr(bb.get_last_instr_num())
            if instr.opcode == OpCodeEnum.BRA.value:
                instr.left = self.get_bb(instr.left).get_first_instr_num()

    def debug(self) -> None:
        for bb in self._bb_map:
            bb.debug()
        print("\nPredecessors:")
        for bb_num, bb_list in enumerate(self._predecessors):
            print(f"BB{bb_num}: {bb_list}")

        print("\nSuccessors:")
        for bb_num, bb_list in enumerate(self._successors):
            print(f"BB{bb_num}: {bb_list}")

        print("\nDom Predecessors:")
        for bb_num, bb in enumerate(self._dom_predecessors):
            print(f"BB{bb_num}: {bb}")
