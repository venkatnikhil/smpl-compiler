from app.parser.cfg import CFG
from app.parser.basic_blocks import BB
from typing import Optional
from app.custom_types import InstrNodeActual
from app.tokens import OpCodeEnum, RELOP_TOKEN_OPCODE
from app.parser.instr_node import *
from collections import defaultdict
from copy import deepcopy

import os
import networkx as nx
import matplotlib.pyplot as plt


class InterferenceGraph:
    def __init__(self, cfg_map: dict[int, CFG], filename: str) -> None:
        self.interference_edges: dict[int, set[int]] = defaultdict(set)
        self.cfg_map: dict[int, CFG] = cfg_map
        self.cfg: CFG = cfg_map[0]
        self.const_bb_instr: set[int] = set(self.cfg.const_bb.get_instr_list()).union({0,})
        self.graph = nx.Graph()
        self.filename = os.path.splitext(filename)[0]
        self.live_not_exclude: set[OpCodeEnum] = {OpCodeEnum.WRITE.value, OpCodeEnum.WRITE_NL.value,
                                                  OpCodeEnum.PHI.value, OpCodeEnum.BRA.value, OpCodeEnum.PARAM.value,
                                                  OpCodeEnum.RETURN.value, OpCodeEnum.END.value,
                                                  OpCodeEnum.STORE.value}.union(set(RELOP_TOKEN_OPCODE.values()))
        self.dead_code: set[int] = set()
        self.clusters: list[list[int]] = []
        self.used_nodes: set[int] = set()

    def build_interference_graph(self, live_range: set[int], bb: Optional[BB] = None) -> None:
        # set default bb to last bb
        if bb is None:
            bb = self.cfg.curr_bb
        elif bb.bot_live is not None and live_range == bb.bot_live:
            print(bb.bb_num)
            # return if live_range already calculated
            return
        print(bb.bb_num)

        # calculate the live ranges
        if bb.bot_live is None:
            bb.bot_live = set()
        bb.bot_live = bb.bot_live.union(live_range)
        live_range = self.calculate_top_and_bot(bb)

        # return if live_range already calculated
        if bb.top_live is not None and live_range == bb.top_live:
            return

        # update the top_live of the bb
        bb.top_live = live_range

        # recursively call predecessors
        pred_bb: list[int] = self.cfg.get_predecessors(bb.bb_num)
        for i in range(len(pred_bb)):
            updated_live: set[int] = live_range.union(bb.phi_live[i])
            parent_bb:BB = self.cfg.get_bb_from_bb_num(pred_bb[i])
            if parent_bb != self.cfg.const_bb:
                self.build_interference_graph(updated_live, parent_bb)

    def calculate_top_and_bot(self, bb: BB) -> set[int]:
        live_set: set[int] = deepcopy(bb.bot_live)

        for instr_num in reversed(bb.get_instr_list()):
            instr: InstrNodeActual = self.cfg.get_instr(instr_num)

            if instr_num not in live_set and instr.opcode not in self.live_not_exclude:
                self.dead_code.add(instr_num)
                continue

            if isinstance(instr, ZeroOpInstrNode) or instr.opcode == OpCodeEnum.BRA.value:
                live_set.discard(instr_num)
                continue

            if instr.opcode == OpCodeEnum.PHI.value:
                if instr.left not in self.const_bb_instr:
                    bb.phi_live[0].add(instr.left)
                if instr.right not in self.const_bb_instr:
                    bb.phi_live[1].add(instr.right)

                curr_cluster: list[int] = list(filter(lambda x: (x not in self.used_nodes) and
                                                                (x not in self.const_bb_instr), [instr_num, instr.left,
                                                                                                 instr.right]))
                if curr_cluster:
                    self.clusters.append(curr_cluster)
                self.used_nodes = self.used_nodes.union({instr_num, instr.left, instr.right})

            if instr_num in live_set:
                live_set.remove(instr_num)
                self.add_edges(instr_num, live_set)

            if instr.opcode in RELOP_TOKEN_OPCODE.values() or isinstance(instr, SingleOpInstrNode):
                live_set.add(instr.left)
            elif instr.opcode == OpCodeEnum.PHI.value:
                continue
            elif isinstance(instr, OpInstrNode):
                if instr.left not in self.const_bb_instr:
                    live_set.add(instr.left)
                if instr.right not in self.const_bb_instr:
                    live_set.add(instr.right)

        return live_set

    def add_edges(self, src: int, dest: set[int]) -> None:
        self.interference_edges[src] = self.interference_edges[src].union(dest)
        for node in dest:
            self.interference_edges[node].add(src)

    def add_rem_nodes_to_clusters(self) -> None:
        for node in self.interference_edges.keys():
            if node not in self.used_nodes:
                self.used_nodes.add(node)
                self.clusters.append([node])

    def render_graph(self) -> None:
        self.add_rem_nodes_to_clusters()
        self.graph.add_nodes_from(self.interference_edges.keys())
        for src, dest in self.interference_edges.items():
            self.graph.add_edges_from([(src, d) for d in dest])
        plt.figure(figsize=(20, 20))
        nx.draw(self.graph, with_labels=True, node_color=["white"], node_size=1000)
        print(self.clusters)
        # nx.draw(self.graph, pos=nx.spring_layout(self.graph), with_labels=True,
        #         node_color=["white"], node_size=1000)
        plt.savefig(f"/Users/himanshushah/UCI/q2/smpl-compiler/tests/ig/{self.filename}_graph.png")
        plt.show()

    def debug(self) -> None:
        print(self.interference_edges)
        print(self.dead_code)
