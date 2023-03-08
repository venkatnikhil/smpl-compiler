from collections import defaultdict
from typing import Optional
from app.parser.basic_blocks import BB
from app.parser.interference_graph import InterferenceGraph
from app.parser.cfg import CFG
from app.custom_types import InstrNodeActual
from app.parser.instr_node import *
from copy import deepcopy
from collections import OrderedDict


import os
import heapq

from app.tokens import RELOP_TOKEN_OPCODE


class RegisterAllocation:
    instr_fmt: str = "{l_reg} <- {opcode} {left} {right}"

    def __init__(self, cfg_map: dict[int, CFG], filename: str) -> None:
        self.node_color_map: dict[int, dict[int, int]] = dict()
        self.cfg_map: dict[int, CFG] = cfg_map
        self.all_colors: set[int] = set(range(1, 6))
        self.cfg_ig_map: dict[int, InterferenceGraph] = dict()
        self.filename: str = os.path.splitext(filename)[0]
        self.reg_cfg_map: OrderedDict[int, OrderedDict[int, list[str]]] = OrderedDict()

    def allocate_registers(self) -> None:
        for id, cur_cfg in self.cfg_map.items():
            self.node_color: dict[int, int] = defaultdict(int)
            self.cfg = cur_cfg
            self.interference_graph: InterferenceGraph = InterferenceGraph(self.cfg)
            self.interference_graph.create_interference_graph()
            # self.cfg.update_branch_instrs(self.interference_graph.dead_code)
            self.color_graph()
            # TODO: uncomment these
            self.interference_graph.render_graph(filename=self.filename, debug=False, node_color=self.node_color)
            self.interference_graph.render_graph(filename=f"{self.filename}_old", debug=True)

            self.reg_cfg_map[id] = OrderedDict()
            self.allocate(self.reg_cfg_map[id], set(), list())
            self.node_color_map[id] = deepcopy(self.node_color)
            self.resolve_return(self.reg_cfg_map[id], max(self.node_color.values()))

        for id, cur_cfg in self.cfg_map.items():
            self.cfg = cur_cfg
            self.resolve_calls(self.reg_cfg_map[id], max(self.node_color_map[id].values()))

        self.instr_num: int = 1
        for id, cfg in self.reg_cfg_map.items():
            for bb_num in range(len(cfg)):
                self.number_instrs(cfg[bb_num])

        for id, cfg in self.reg_cfg_map.items():
            self.cfg = self.cfg_map[id]
            self.cur_reg_cfg = cfg
            for bb_num in range(len(cfg)):
                self.update_branch_instr(cfg[bb_num])

        self.write_to_file()

    def update_branch_instr(self, instr_list: list[str]) -> None:

        for i in range(len(instr_list)):
            instr = instr_list[i].strip().split()
            if instr[1] in RELOP_TOKEN_OPCODE.values():
                if instr[3].isdigit():
                    instr[3] = self.get_reg_instr_num(int(instr[3])).rstrip(":")
                    instr_list[i] = " ".join(instr)
            elif instr[1] == OpCodeEnum.BRA.value:
                if instr[2].isdigit():
                    instr[2] = self.get_reg_instr_num(int(instr[2])).rstrip(":")
                    instr_list[i] = " ".join(instr)
                elif not instr[2].startswith('R'):
                    func_id: int = Tokenizer.string2id(instr[2])
                    parent_cfg = self.cfg
                    parent_reg_cfg = self.cur_reg_cfg
                    self.cfg = self.cfg_map[func_id]
                    self.cur_reg_cfg = self.reg_cfg_map[func_id]
                    instr[2] = self.get_reg_instr_num(0).rstrip(":")
                    self.cfg = parent_cfg
                    self.cur_reg_cfg = parent_reg_cfg
                    instr_list[i] = " ".join(instr)
                    instr_list[i - 1] = instr_list[i - 1].format(func_return=('#' + str(int(instr[0].rstrip(':')) + 1)))

    def get_reg_instr_num(self, bb_num: int):
        if len(self.cur_reg_cfg[bb_num]) > 0:
            return self.cur_reg_cfg[bb_num][0].strip().split()[0]

        return self.get_reg_instr_num(self.cfg.get_successors(bb_num)[0])

    def number_instrs(self, instr_list: list[str]) -> None:
        instr_to_remove: list[int] = []
        for i in range(len(instr_list)):
            if instr_list[i].startswith("R0"):
                instr_to_remove.append(i)
            else:
                instr_list[i] = f"{self.instr_num}: {instr_list[i]}"
                self.instr_num += 1

        for idx in instr_to_remove[::-1]:
            instr_list.pop(idx)

    def resolve_return(self, reg_dict: dict[int, list[str]], max_reg: int) -> None:
        for bb_num, instr_list in reg_dict.items():
            idx_instr_map: dict[int, list[str]] = dict()
            for idx, instr in enumerate(instr_list):
                instr_vals = instr.strip().split(' ')
                new_instrs = []
                if instr_vals[0] == 'return':
                    if len(instr_vals) > 1 and instr_vals[1] != "R1":
                        new_instrs.append(f"move R1 <- {instr_vals[1]}")
                    new_instrs.append(f"bra R{max_reg + 1}")
                    idx_instr_map[idx] = new_instrs

            for key in sorted(idx_instr_map.keys(), reverse=True):
                new_instrs = idx_instr_map[key]
                instr_list[key] = new_instrs[0]
                if len(new_instrs) > 1:
                    instr_list.insert(key + 1, new_instrs[1])

    def resolve_calls(self, reg_dict: dict[int, list[str]], max_reg: int) -> None:
        for bb_num, instr_list in reg_dict.items():
            moves_after_call: list[str] = []
            moves_before_call: list[str] = []
            moves_before_call_param: list[str] = []
            idx_instr_map: dict[int, list[str]] = dict()
            param_num = 1
            for idx, instr in enumerate(instr_list):
                instr_vals = instr.strip().split(' ')
                new_instrs = []
                if len(instr_vals) > 3 and instr_vals[2] == 'call':
                    param_num = 1

                    # save registers
                    func_reg: int = max(self.node_color_map[int(instr_vals[3])].values())
                    reg: int = max(func_reg + 1, max_reg) + 1
                    for before_instr in range(1, func_reg + 2):
                        new_instrs.append(f"move R{reg} <- R{before_instr}")
                        reg += 1

                    # assign param vals to registers
                    new_instrs.extend(moves_before_call_param)
                    new_instrs.append(f"move R{func_reg + 1} <- {{func_return}}")
                    new_instrs.append(f"bra {Tokenizer.id2string(int(instr_vals[3]))}")

                    # restore registers
                    reg: int = max(func_reg + 1, max_reg) + 1
                    for after_instr in moves_after_call:
                        new_instrs.append(after_instr.format(reg=reg))
                        reg += 1
                    for after_instr in range(1, func_reg + 2):
                        new_instrs.append(f"move R{after_instr} <- R{reg}")
                        reg += 1

                    # assign returned values to register
                    if instr_vals[0] != "R0" and instr_vals[0] != "R1":
                        new_instrs.append(f"move {instr_vals[0]} <- R1")

                    idx_instr_map[idx] = new_instrs
                    moves_after_call = []
                    moves_before_call = []
                elif len(instr_vals) > 3 and instr_vals[2] == 'param':
                    color = self.node_color[int(instr_vals[3])]
                    # get register num or const val
                    if color != 0:
                        reg_val = f"R{self.node_color[int(instr_vals[3])]}"
                    else:
                        reg_val = f"#{self.cfg.get_instr(int(instr_vals[3])).val}"
                    if instr_vals[0] == "R0":
                        # append save and restore register moves
                        # moves_after_call.append(f"move R{param_num} <- R{{reg}}")
                        # moves_before_call.append(f"move R{{reg}} <- R{param_num}")
                        if f"R{param_num}" != reg_val:
                            # append param vals to registers moves
                            moves_before_call_param.append(f"move R{param_num} <- {reg_val}")
                        param_num += 1
                    # const bb param
                    else:
                        idx_instr_map[idx] = [f"R0 <- param #{instr_vals[3]}"]
                else:
                    param_num = 1

            for key in sorted(idx_instr_map.keys(), reverse=True):
                new_instrs = idx_instr_map[key]
                instr_list[key] = new_instrs[0]
                if len(new_instrs) > 1:
                    for i in range(1, len(new_instrs)):
                        instr_list.insert(key + i, new_instrs[i])

    def allocate(self, reg_dict: dict[int, list[str]], visited: set[int], phi_list: list[str],
                 bb: Optional[BB] = None) -> None:
        # set default bb to last bb
        if bb is None:
            bb = self.cfg.curr_bb

        if bb.bb_num in visited:
            return

        visited.add(bb.bb_num)

        reg_dict[bb.bb_num], left_phi, right_phi = self.create_reg_instr(bb, phi_list)

        # recursively call predecessors
        pred_bb: list[int] = self.cfg.get_predecessors(bb.bb_num)
        for i in range(len(pred_bb)):
            parent_bb: BB = self.cfg.get_bb_from_bb_num(pred_bb[i])
            # if parent_bb != self.cfg.const_bb:
            phi_list: list[str] = left_phi if parent_bb.bb_num == pred_bb[0] else right_phi
            self.allocate(reg_dict, visited, phi_list, parent_bb)

    def create_reg_instr(self, bb: BB, phi_list: list[str]) -> tuple[list[str], list[str], list[str]]:
        reg_instr_list: list[str] = []
        left_phi: list[str] = []
        right_phi: list[str] = []
        branch_instrs: list[str] = []

        for instr_num in bb.get_instr_list():
            instr: InstrNodeActual = self.cfg.get_instr(instr_num)
            node: str = self.get_register_node(instr_num)

            if isinstance(instr, ConstInstrNode) or isinstance(instr, AddrInstrNode):
                continue

            if instr.opcode == OpCodeEnum.END.value:
                reg_instr_list.append("end")
                continue

            left: str = ""
            right: str = ""

            if isinstance(instr, ZeroOpInstrNode) or isinstance(instr, EmptyInstrNode) \
                    or instr_num in self.interference_graph.dead_code:
                if instr.opcode in {OpCodeEnum.RETURN.value, OpCodeEnum.WRITE_NL.value}:
                    reg_instr_list.append(f"{instr.opcode}")
                elif instr.opcode == OpCodeEnum.READ.value:
                    reg_instr_list.append(self.instr_fmt.format(l_reg=node, opcode=instr.opcode, left=left, right=right))
                continue

            if instr.opcode == OpCodeEnum.CALL.value:
                left = str(instr.left)
            elif instr.opcode == OpCodeEnum.PARAM.value:
                left = f"{instr.left}"
            else:
                left: str = self.get_register_node(instr.left)

                if isinstance(instr, OpInstrNode):
                    right = self.get_register_node(instr.right)

                if instr.opcode == OpCodeEnum.PHI.value:
                    if node != left:
                        left_phi.append(f"move {node} <- {left}")
                    if node != right:
                        right_phi.append(f"move {node} <- {right}")
                    continue

                if instr.opcode == OpCodeEnum.BRA.value or instr.opcode in set(RELOP_TOKEN_OPCODE.values()):
                    if instr.opcode == OpCodeEnum.BRA.value:
                        left = str(instr.left)
                    else:
                        right = str(instr.right)
                    branch_instrs.append(f"{instr.opcode} {left} {right}")
                    continue

            if instr.opcode in {OpCodeEnum.RETURN.value, OpCodeEnum.STORE.value, OpCodeEnum.WRITE.value}:
                reg_instr_list.append(f"{instr.opcode} {left}")
            else:
                reg_instr_list.append(self.instr_fmt.format(
                    l_reg=node,
                    opcode=instr.opcode,
                    left=left,
                    right=right
                ))

        if phi_list:
            print(phi_list)
        for phi_instr in phi_list:
            reg_instr_list.append(phi_instr)

        for br_instr in branch_instrs:
            reg_instr_list.append(br_instr)

        return reg_instr_list, left_phi, right_phi

    def get_register_node(self, instr_num: int) -> str:
        if instr_num not in self.node_color:
            if instr_num in self.interference_graph.coalesce_map:
                return f"R{str(self.node_color[self.interference_graph.coalesce_map[instr_num]])}"
            elif instr_num in self.interference_graph.const_bb_instr:
                instr: InstrNodeActual = self.cfg.get_instr(instr_num)
                if isinstance(instr, SingleOpInstrNode):
                    return f"#{self.cfg.get_instr(instr_num).left}"
                return f"#{self.cfg.get_instr(instr_num).val}"
        return f"R{self.node_color[instr_num]}"

    def get_adjacent_colors(self, node: int) -> set[int]:
        adj_colors: set[int] = set()
        for node in self.interference_graph.interference_edges[node]:
            if self.node_color[node] != 0:
                adj_colors.add(self.node_color[node])
        return adj_colors

    def color_node(self, node: int) -> int:
        adj_colors: set[int] = self.get_adjacent_colors(node)
        available_colors: set[int] = self.all_colors.difference(adj_colors)
        if available_colors:
            return min(available_colors)  # assign smallest available color
        else:
            new_max_val: int = max(self.all_colors) + 1
            self.all_colors.add(new_max_val + 1)
            return new_max_val

    def color_param_nodes(self):
        count: int = 1
        for instr_num in self.cfg.const_bb.get_instr_list():
            instr: InstrNodeActual = self.cfg.get_instr(instr_num)
            if instr.opcode == OpCodeEnum.PARAM.value:
                self.node_color[instr_num] = count
                count += 1

    def color_graph(self) -> None:
        self.get_cost_heap()

        import json

        self.color_param_nodes()

        def __color():
            while self.heap:
                node = heapq.heappop(self.heap)
                if self.heap:
                    __color()
                self.node_color[node[1]] = self.color_node(node[1])

        __color()

        print(json.dumps(self.node_color, indent=2))

    def get_cost_heap(self) -> None:
        self.heap = [(len(value), key) for key, value in self.interference_graph.node_cost.items()]
        heapq.heapify(self.heap)

    def debug(self) -> None:
        self.interference_graph.debug()
        # with open(f'./tests/reg_alloc/{self.filename}.txt', "a") as f:
        for id in self.cfg_map.keys():
            print(f'For cfg {id}\n')
            for bb_node, instrs in sorted(self.reg_cfg_map[id].items()):
                print('For BB ', bb_node)
                for instr in instrs:
                    print('\t', instr)
                print()
            print(f"Max reg for {id}: {max(self.node_color_map[id].values())}")

    def write_to_file(self) -> None:
        with open(f'./tests/reg_alloc/{self.filename}.txt', "a+") as f:
            for idx, reg_cfg in self.reg_cfg_map.items():
                cfg_name: str = "main" if idx == 0 else Tokenizer.id2string(idx)
                f.write(f"{cfg_name}_cfg:\n")
                for bb_num in range(len(reg_cfg)):
                    f.write(f"{cfg_name}_BB{bb_num}:\n")
                    for instr in reg_cfg[bb_num]:
                        f.write(f"\t{instr}\n")
                    f.write("\n")
                f.write("\n")
