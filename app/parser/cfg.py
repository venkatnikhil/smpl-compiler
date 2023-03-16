from app.custom_types import InstrNodeType, InstrNodeActual
from app.parser.basic_blocks import BB
from app.parser.instr_graph import InstrGraph
from app.parser.instr_node import *
from app.tokens import OpCodeEnum, RELOP_TOKEN_OPCODE, TokenEnum
from typing import Optional, Union
from app.tokenizer import Tokenizer
from collections import deque


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
        self._excluded_instrs: set[OpCodeEnum] = set(RELOP_TOKEN_OPCODE.values()).union(
            {OpCodeEnum.PHI.value, OpCodeEnum.BRA.value, OpCodeEnum.CONST.value, OpCodeEnum.EMPTY.value,
             OpCodeEnum.READ.value, OpCodeEnum.WRITE.value, OpCodeEnum.WRITE_NL.value, OpCodeEnum.STORE.value,
             OpCodeEnum.KILL.value, OpCodeEnum.CALL.value, OpCodeEnum.PARAM.value, OpCodeEnum.RETURN.value})
        self._cleanup_list: set[OpCodeEnum] = {OpCodeEnum.KILL.value}
        self._phi_scope: list[tuple[int, TokenEnum]] = list()
        self.arr_map: dict[int, list[Union[int, list[int]]]] = dict()
        self.reg_traverse: list[int] = [0, 1]

        self.__initialize_cfg()

    def add_traverse_node(self, bb_num) -> None:
        self.reg_traverse.append(bb_num)

    def add_phi_scope(self, bb_num: int, bb_type: TokenEnum) -> None:
        self._phi_scope.append((bb_num, bb_type))

    def get_bb_map(self) -> list[BB]:
        return self._bb_map

    def get_dom_predecessor(self, bb: int) -> int:
        return self._dom_predecessors[bb]

    def get_predecessors(self, bb: int) -> list[int]:
        return self._predecessors[bb]

    def get_successors(self, bb: int) -> list[int]:
        return self._successors[bb]

    def remove_phi_scope(self) -> None:
        self._phi_scope.pop()

    def get_phi_scope(self) -> Optional[tuple[int, TokenEnum]]:
        if self._phi_scope:
            return self._phi_scope[-1]

    def create_phi_instr(self, ident: int, assignment: bool = False) -> Optional[int]:
        phi_scope: Optional[tuple[int, TokenEnum]] = self.get_phi_scope()

        phi_bb_num: int
        phi_bb_type: TokenEnum

        if not phi_scope:
            return

        phi_bb_num, phi_bb_type = phi_scope
        phi_bb: BB = self.get_bb_from_bb_num(phi_bb_num)

        if not assignment and phi_bb_type != TokenEnum.WHILE.value:
            return  # phis are only needed for IF in case of assignments

        if ident in phi_bb.get_var_instr_map():
            return  # phi would've already been created for the identifier if required

        phi_instr_num: int = self.build_instr_node(OpInstrNode, OpCodeEnum.PHI.value, bb=phi_bb_num, left=None,
                                                   right=None)

        # create phi instrs for all scopes above the current one
        self.remove_phi_scope()
        self.update_var_instr_map(phi_bb, ident, phi_instr_num)
        self.add_phi_scope(phi_scope[0], phi_scope[1])
        return phi_instr_num

    def create_kill_instr(self, arr_addr: int, is_assign: int) -> None:
        kill_scope: Optional[tuple[int, TokenEnum]] = self.get_phi_scope()

        if not kill_scope:
            return

        kill_bb_num: int
        kill_bb_num, _ = kill_scope
        kill_bb: BB = self.get_bb_from_bb_num(kill_bb_num)

        for instr_num in kill_bb.opcode_instr_order[OpCodeEnum.LOAD.value]:
            instr: InstrNodeActual = self._instr_graph.get_instr(instr_num)
            if instr.equals(opcode=OpCodeEnum.KILL.value, left=arr_addr, right=1):
                return
            elif instr.equals(opcode=OpCodeEnum.KILL.value, left=arr_addr, right=0):
                if is_assign == 1:
                    self.update_instr(instr_num, {"right": is_assign})
                    self.remove_phi_scope()
                    self.create_kill_instr(arr_addr, is_assign)
                    self.add_phi_scope(kill_scope[0], kill_scope[1])
                return

        # TODO: uncomment and use this instead of build_instr_node
        # kill_instr_num: int = self._instr_graph.build_instr_node(SingleOpInstrNode, OpCodeEnum.KILL.value,
        #                                                          instr_num=None, left=arr_addr)
        # kill_bb.update_opcode_instr_order(OpCodeEnum.KILL.value, kill_instr_num)
        kill_instr_num: int = self.build_instr_node(OpInstrNode, OpCodeEnum.KILL.value, kill_bb.bb_num,
                                                    left=arr_addr, right=is_assign)

        self.remove_phi_scope()
        self.create_kill_instr(arr_addr, is_assign)
        self.add_phi_scope(kill_scope[0], kill_scope[1])

    def update_var_instr_map(self, bb: BB, ident: int, instr_num: int) -> None:
        bb.update_var_instr_map(ident, instr_num)
        if bb is not self.const_bb:
            self.create_phi_instr(ident, assignment=True)  # we try to create phi instr for every assignment

    def __resolve_instr(self, bb: BB, ident: int, instr: InstrNodeActual, resolved_instr_num: int) -> None:
        # 1. update the var -> instr num map
        # 2. instr should be replaced by resolved_instr_num wherever used
        # 3. delete instr
        bb.update_var_instr_map(ident, resolved_instr_num)  # map ident to resolved instr num
        self.__update_resolved_instr(bb.bb_num, {instr.instr_num: resolved_instr_num})
        self.__delete_instr(bb, instr)

    def resolve_phi(self, bb_num: int) -> None:
        bb: BB = self.get_bb_from_bb_num(bb_num)
        var_instr_map: dict[int, int] = bb.get_var_instr_map()

        for ident, instr_num in var_instr_map.items():
            instr = self.get_instr(instr_num)
            if instr.opcode != OpCodeEnum.PHI.value:
                continue

            l_instr: Optional[int] = instr.left
            r_instr: Optional[int] = instr.right

            if l_instr is None:
                l_instr = self.get_var_instr_num(self._predecessors[bb_num][0], ident, {bb_num})
            if r_instr is None:
                r_instr = self.get_var_instr_num(self._predecessors[bb_num][1], ident, {bb_num})

            assert l_instr is not None or r_instr is not None, f"Error: All paths for {Tokenizer.id2string(ident)} " \
                                                               f"have value None"

            if l_instr == r_instr or l_instr is None or r_instr is None or r_instr == instr_num:
                # phi no longer required -> resolve and delete
                # possible cases -
                # 1. phi (x) (x)
                # 2. phi None (x) or phi (x) None
                # 3. (y) -> phi (x) (y) -- in case of while when r_instr is looped back to current phi
                resolved_instr_num: Optional[int] = l_instr if l_instr is not None else r_instr
            else:
                # TODO: is common subexpr required?
                resolved_instr_num: Optional[int] = self.__get_common_subexpr(bb, instr.opcode, instr_num, left=l_instr,
                                                                              right=r_instr)
                if resolved_instr_num is None:
                    self.update_instr(instr_num, {"left": l_instr, "right": r_instr})
                    continue

            self.__resolve_instr(bb, ident, instr, resolved_instr_num)

    def resolve_kill(self, bb_num: int) -> None:
        bb: BB = self.get_bb_from_bb_num(bb_num)
        instr_list: deque[int] = bb.get_instr_list()
        delete_list: list[InstrNodeActual] = []

        for instr_num in instr_list:
            instr: InstrNodeActual = self.get_instr(instr_num)
            if instr.opcode != OpCodeEnum.KILL.value:
                continue

            should_resolve: int = not instr.right

            if not should_resolve:
                continue

            delete_list.append(instr)
            # self.resolve_instr(bb, ident, instr, resolved_instr_num)
        for instr in delete_list:
            self.__delete_instr(bb, instr)
            self.__update_resolved_instr(bb.bb_num, {})

    def __update_resolved_instr(self, first_bb: int, update_map: dict[int, int]) -> None:
        stack: list[int] = [first_bb]
        visited_bb: set[int] = set()

        while stack:
            bb_num = stack.pop()
            if bb_num in visited_bb:
                continue

            visited_bb.add(bb_num)

            cur_bb: BB = self.get_bb_from_bb_num(bb_num)
            instr_remove_list: list[InstrNodeActual] = []
            update_from_join: bool = False

            for instr_num in cur_bb.get_instr_list():
                instr: InstrNodeActual = self.get_instr(instr_num)
                if instr.opcode in self._excluded_instrs and instr.opcode != OpCodeEnum.PHI.value \
                        and instr.opcode != OpCodeEnum.STORE.value:
                    if instr.opcode in RELOP_TOKEN_OPCODE.values() and instr.left in update_map:
                        instr.left = update_map[instr.left]
                    continue

                if instr.left in update_map:
                    instr.left = update_map[instr.left]
                if hasattr(instr, "right") and instr.right in update_map:
                    instr.right = update_map[instr.right]

                update_instr: Optional[int] = None
                if instr.opcode == OpCodeEnum.PHI.value:
                    if instr.left == instr.right and instr.left is not None:
                        update_instr = instr.left
                else:
                    kwargs = {"left": instr.left}
                    if hasattr(instr, "right"):
                        kwargs["right"] = instr.right
                    update_instr = self.__get_common_subexpr(cur_bb, instr.opcode, instr_num, **kwargs)
                if update_instr is not None:
                    update_from_join = True
                    update_map.update({instr_num: update_instr})  # common subexpr found; replace original instr
                    instr_remove_list.append(instr)

            for instr in instr_remove_list:
                self.__delete_instr(cur_bb, instr)

            var_instr_map: dict[int, int] = cur_bb.get_var_instr_map()
            keys = var_instr_map.keys()
            for key in keys:
                if var_instr_map[key] in update_map:
                    cur_bb.update_var_instr_map(key, update_map[var_instr_map[key]])

            if update_from_join:
                stack = [first_bb]
                visited_bb = set()
                continue

            for successor_bb_num in self._successors[bb_num]:
                stack.append(successor_bb_num)

    def __delete_instr(self, bb: BB, instr: InstrNodeActual) -> None:
        # Remove instr from bb list
        instr_num: int = instr.instr_num
        bb.remove_from_instr_list(instr_num)
        if instr.opcode not in self._excluded_instrs or instr.opcode == OpCodeEnum.KILL.value:
            bb.remove_from_opcode_instr_order(instr.opcode, instr_num)
        if len(bb.get_instr_list()) == 0:
            self.build_instr_node(EmptyInstrNode, OpCodeEnum.EMPTY.value, bb.bb_num)

    def get_bb_from_bb_num(self, bb_num: int) -> BB:
        return self._bb_map[bb_num]

    def __update_bb_map(self, bb_obj: BB) -> None:
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
        self.build_instr_node(AddrInstrNode, OpCodeEnum.CONST.value, val="BASE")
        bb1: int = self.create_bb([bb0], [])
        self.const_bb = self.get_bb_from_bb_num(bb0)

    def __get_arr_addr(self, elem_addr: int) -> int:
        adda_instr: InstrNodeActual = self._instr_graph.get_instr(elem_addr)
        arr_addr: InstrNodeActual = self._instr_graph.get_instr(adda_instr.right)
        return arr_addr.right

    # def __check_same_arr(self, elem_addr: int, arr_offset: int) -> bool:
    #     adda_instr: InstrNodeActual = self._instr_graph.get_instr(elem_addr)
    #     arr_addr: InstrNodeActual = self._instr_graph.get_instr(adda_instr.right)
    #     return arr_addr.right == arr_offset

    def __get_common_subexpr(self, bb: BB, opcode: OpCodeEnum, cur_instr_num: int = -1, **kwargs) -> Optional[int]:
        instrs: list[int] = bb.opcode_instr_order[opcode]

        if cur_instr_num in instrs:
            idx: int = instrs.index(cur_instr_num)
        else:
            idx: int = len(instrs)

        if idx != 0:

            if opcode == OpCodeEnum.LOAD.value:
                # DO NOT search for common subexpr AFTER current instr
                for instr in instrs[idx - 1::-1]:
                    cur_instr: InstrNodeActual = self._instr_graph.get_instr(instr)
                    if cur_instr.opcode == OpCodeEnum.LOAD.value and cur_instr.equals(opcode, **kwargs):
                        return instr
                    elif cur_instr.opcode == OpCodeEnum.STORE.value and self.__get_arr_addr(cur_instr.left) == \
                            self.__get_arr_addr(kwargs["left"]):
                        return None
                    elif cur_instr.opcode == OpCodeEnum.KILL.value and self.__get_arr_addr(kwargs["left"]) == \
                            cur_instr.left:
                        return None
            else:
                # DO NOT search for common subexpr AFTER current instr
                for instr in instrs[idx - 1::-1]:
                    if self._instr_graph.get_instr(instr).equals(opcode, **kwargs):
                        return instr

        dom_pred = self._dom_predecessors[bb.bb_num]
        if dom_pred == -1:
            return None

        return self.__get_common_subexpr(self.get_bb_from_bb_num(dom_pred), opcode, **kwargs)

    def build_instr_node(self, node_type: InstrNodeType, opcode: OpCodeEnum, bb: Optional[int] = None, **kwargs) -> int:
        if bb is None:
            bb = self.curr_bb
        else:
            bb = self.get_bb_from_bb_num(bb)

        if opcode not in self._excluded_instrs:
            existing_instr = self.__get_common_subexpr(bb, opcode, **kwargs)
            if existing_instr is not None:
                return existing_instr

        instr_num: Optional[int] = bb.get_first_instr_num()
        if instr_num is not None:  # there is at least 1 instr present in BB
            if not isinstance(self._instr_graph.get_instr(instr_num), EmptyInstrNode):
                instr_num = None  # first instr is not an Empty instr; create new instr node with new instr num
            else:
                bb.remove_empty_instr()  # first instr is Empty instr; create new instr node with **same** instr num

        instr_num: int = self._instr_graph.build_instr_node(node_type, opcode, instr_num, **kwargs)
        # TODO: REMOVE KILL
        bb.update_instr_list(instr_num, prepend=opcode == OpCodeEnum.PHI.value or opcode == OpCodeEnum.KILL.value)
        if opcode not in self._excluded_instrs or opcode in {OpCodeEnum.STORE.value, OpCodeEnum.KILL.value}:
            bb.update_opcode_instr_order(opcode, instr_num)
        return instr_num

    def get_var_instr_num(self, bb: Union[BB, int], ident: int, visited_bb: set[int]) -> Optional[int]:
        if isinstance(bb, int):
            bb = self.get_bb_from_bb_num(bb)
        if bb.bb_num in visited_bb:
            return

        visited_bb.add(bb.bb_num)
        if bb.check_instr_exists(ident):
            return bb.get_var_instr_num(ident)

        search_space: list[int] = self._predecessors[bb.bb_num]
        res: set[int] = set()
        for node in search_space:
            instr = self.get_var_instr_num(self._bb_map[node], ident, visited_bb)
            if instr is not None:
                res.add(instr)

        assert len(res) <= 1, f"2 different resolutions found for phi for ident: {Tokenizer.id2string(ident)}"
        if bb.bb_num == 0:
            print(f"Warning!: {Tokenizer.id2string(ident)} referenced before assignment!")
            return 0
        elif len(res) == 1:
            return res.pop()
        else:
            return

    def create_bb(self, predecessors: list[int], dom_predecessors: Optional[list[int]] = None) -> int:
        if dom_predecessors is None:
            dom_predecessors = predecessors

        new_bb: BB = BB(self.bb_num)
        self.curr_bb = new_bb
        self.__update_bb_map(self.curr_bb)
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

    def clean_instr(self, visited_set: set[int], bb=None) -> None:
        if not bb:
            bb = self.const_bb

        if bb.bb_num in visited_set:
            return

        visited_set.add(bb.bb_num)

        updated_instr_list: deque[int] = deque([])
        for instr_num in bb.get_instr_list():
            if self.get_instr(instr_num=instr_num).opcode not in self._cleanup_list:
                updated_instr_list.append(instr_num)
        bb.set_instr_list(updated_instr_list)

        for next_bb in self._successors[bb.bb_num]:
            self.clean_instr(visited_set, self.get_bb_from_bb_num(next_bb))

    def __get_non_empty_bb(self, bb_num: int, dead_code: set[int]) -> int:
        bb: BB = self.get_bb_from_bb_num(bb_num)
        branch_to: Optional[int] = None
        for instr_num in bb.get_instr_list():
            instr: InstrNodeActual = self.get_instr(instr_num)
            if instr.opcode != OpCodeEnum.EMPTY.value:
                    # and instr_num not in dead_code \
                    # and instr.opcode != OpCodeEnum.PHI.value:
                branch_to = instr_num
                break
        if branch_to is None:
            return self.__get_non_empty_bb(self._successors[bb_num][0], dead_code)
        return branch_to

    def update_branch_instrs(self, dead_code: set[int]) -> None:
        for bb in self._bb_map:
            instr: InstrNodeActual = self._instr_graph.get_instr(bb.get_last_instr_num())
            if instr.opcode == OpCodeEnum.BRA.value:
                instr.left = self.__get_non_empty_bb(instr.left, dead_code)
            elif instr.opcode in set(RELOP_TOKEN_OPCODE.values()):
                instr.right = self.__get_non_empty_bb(instr.right, dead_code)

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
