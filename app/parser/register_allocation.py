from collections import defaultdict
from typing import Optional
from app.parser.basic_blocks import BB
from app.parser.interference_graph import InterferenceGraph
from app.parser.cfg import CFG
from app.custom_types import InstrNodeActual
from app.parser.instr_node import *
from copy import deepcopy


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
        self.reg_cfg: dict[int, dict[int, list[str]]] = dict()

    def allocate_registers(self) -> None:
        for id, cur_cfg in self.cfg_map.items():
            self.node_color: dict[int, int] = defaultdict(int)
            self.cfg = cur_cfg
            self.interference_graph: InterferenceGraph = InterferenceGraph(self.cfg)
            self.interference_graph.create_interference_graph()
            # self.cfg.update_branch_instrs(self.interference_graph.dead_code)
            self.color_graph()
            # self.interference_graph.render_graph(filename=self.filename, debug=False, node_color=self.node_color)
            # self.interference_graph.render_graph(filename=f"{self.filename}_old", debug=True)

            self.reg_cfg[id] = dict()
            self.allocate(self.reg_cfg[id], set(), list())
            self.node_color_map[id] = deepcopy(self.node_color)

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

            if isinstance(instr, ZeroOpInstrNode) or isinstance(instr, EmptyInstrNode) \
                    or instr_num in self.interference_graph.dead_code:
                continue

            left: str = ""
            right: str = ""
            if instr.opcode == OpCodeEnum.CALL.value:
                left = str(instr.left)
            elif instr.opcode == OpCodeEnum.PARAM.value:
                left = f"#{instr.left}"
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
                    branch_instrs.append(self.instr_fmt.format(l_reg=node, opcode=instr.opcode, left=left, right=right))
                    continue

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

    def color_graph(self) -> None:
        self.get_cost_heap()

        import json

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
        for id in self.cfg_map.keys():
            print(f'For cfg {id}\n')
            for bb_node, instrs in sorted(self.reg_cfg[id].items()):
                print('For BB ', bb_node)
                for instr in instrs:
                    print('\t', instr)
                print()
            print(f"Max reg for {id}: {max(self.node_color_map[id].values())}")