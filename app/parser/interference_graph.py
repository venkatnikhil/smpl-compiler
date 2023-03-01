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
import heapq


class InterferenceGraph:
    def __init__(self, cfg_map: dict[int, CFG], filename: str) -> None:
        self.interference_edges: dict[int, set[int]] = defaultdict(set)
        self.node_cost: dict[int, set[int]] = defaultdict(set)
        self.node_color: dict[int, int] = defaultdict(int)
        self.cfg_map: dict[int, CFG] = cfg_map
        self.cfg: CFG = cfg_map[0]
        self.all_colors: set[int] = set(range(1, 6))
        self.const_bb_instr: set[int] = set(self.cfg.const_bb.get_instr_list()).union({0, })
        self.graph = nx.Graph()
        self.filename = os.path.splitext(filename)[0]
        self.live_not_exclude: set[OpCodeEnum] = {OpCodeEnum.WRITE.value, OpCodeEnum.WRITE_NL.value,
                                                  OpCodeEnum.PHI.value, OpCodeEnum.BRA.value, OpCodeEnum.PARAM.value,
                                                  OpCodeEnum.RETURN.value, OpCodeEnum.END.value,
                                                  OpCodeEnum.STORE.value}.union(set(RELOP_TOKEN_OPCODE.values()))
        self.dead_code: set[int] = set()
        self.used_nodes: set[int] = set()
        self.coalesce_map: dict[int] = dict()
        self.old_ig = {}

    def create_interference_graph(self, live_range: set[int], bb: Optional[BB] = None) -> None:
        self.build_basic_interference_graph(live_range, bb)
        print('starting interference graph', self.interference_edges)
        self.old_ig = deepcopy(self.interference_edges)
        self.coalesce_phi()
        self.color_graph()

    def check_for_interference(self, node_1, node_2) -> bool:
        if node_1 not in self.interference_edges[node_2]:
            return True
        return False

    def coalesce_phi(self) -> None:
        cluster_set: list[list[int]] = self.get_clusters()
        for cluster in cluster_set:
            cur_coalesce = [cluster[0]]
            if cluster[1] in self.interference_edges \
                    and self.check_for_interference(cluster[0], cluster[1])\
                    and cluster[2] in self.interference_edges \
                    and self.check_for_interference(cluster[0], cluster[2]):
                if self.check_for_interference(cluster[1], cluster[2]):
                    cur_coalesce = cluster
                else:
                    cur_coalesce.append(cluster[1])

            elif cluster[2] in self.interference_edges and self.check_for_interference(cluster[0], cluster[2]):
                cur_coalesce.append(cluster[2])

            if len(cur_coalesce) > 1:
                self.coalesce_nodes(cur_coalesce)

    def coalesce_nodes(self, node_list: list[int]) -> None:
        print('coalesce', node_list)
        phi_node: int = node_list[0]
        for node in node_list[1:]:
            self.interference_edges[phi_node] = self.interference_edges[phi_node].union(self.interference_edges[node])
            self.node_cost[phi_node] = self.node_cost[phi_node].union(self.node_cost[node])
            del self.interference_edges[node]
            del self.node_cost[node]
            for key, value in self.interference_edges.items():
                if node in value:
                    self.interference_edges[key].remove(node)
                    self.interference_edges[key].add(phi_node)
            self.coalesce_map[node] = phi_node

    def get_clusters(self) -> list[list[int]]:
        cluster_set: list[list[int]] = []
        for instr_num, inter_set in self.interference_edges.items():
            instr: InstrNodeActual = self.cfg.get_instr(instr_num)
            if instr.opcode == OpCodeEnum.PHI.value and instr_num not in self.dead_code:
                cluster_set.append([instr_num, instr.left, instr.right])
        print('clusters:', cluster_set)
        return cluster_set

    def build_basic_interference_graph(self, live_range: set[int], bb: Optional[BB] = None) -> None:
        # set default bb to last bb
        if bb is None:
            bb = self.cfg.curr_bb
        elif bb.bot_live is not None and live_range == bb.bot_live:
            # return if live_range already calculated
            return

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
                self.build_basic_interference_graph(updated_live, parent_bb)

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
                    self.node_cost[instr.left].add(instr_num)
                if instr.right not in self.const_bb_instr:
                    bb.phi_live[1].add(instr.right)
                    self.node_cost[instr.right].add(instr_num)

            if instr_num in live_set:
                live_set.remove(instr_num)
                self.add_edges(instr_num, live_set)

            if instr.opcode in RELOP_TOKEN_OPCODE.values() or isinstance(instr, SingleOpInstrNode):
                live_set.add(instr.left)
                self.node_cost[instr.left].add(instr_num)
            elif instr.opcode == OpCodeEnum.PHI.value:
                continue
            elif isinstance(instr, OpInstrNode):
                if instr.left not in self.const_bb_instr:
                    live_set.add(instr.left)
                    self.node_cost[instr.left].add(instr_num)
                if instr.right not in self.const_bb_instr:
                    live_set.add(instr.right)
                    self.node_cost[instr.right].add(instr_num)

        return live_set

    def add_edges(self, src: int, dest: set[int]) -> None:
        self.interference_edges[src] = self.interference_edges[src].union(dest)
        for node in dest:
            self.interference_edges[node].add(src)

    def render_graph(self) -> None:
        self.graph.add_nodes_from(self.interference_edges.keys())
        for src, dest in self.interference_edges.items():
            self.graph.add_edges_from([(src, d) for d in dest])
        plt.figure(figsize=(10, 10))
        colors = [len(self.node_cost[i]) for i in list(self.graph)]
        maxval = max(colors)
        colors = list(map(lambda x: x/maxval, colors))
        nx.draw(self.graph, with_labels=True, node_color=colors, node_size=1000, cmap=plt.cm.get_cmap("coolwarm"), font_color="whitesmoke")
        # nx.draw(self.graph, pos=nx.spring_layout(self.graph), with_labels=True,
        #         node_color=["white"], node_size=1000)
        plt.savefig(f"./tests/ig/{self.filename}_graph.png")
        plt.show()

        self.graph = nx.Graph()
        self.graph.add_nodes_from(self.old_ig.keys())
        for src, dest in self.old_ig.items():
            self.graph.add_edges_from([(src, d) for d in dest])
        plt.figure(figsize=(10, 10))
        nx.draw(self.graph, with_labels=True, node_color=["white"], node_size=1000)
        # nx.draw(self.graph, pos=nx.spring_layout(self.graph), with_labels=True,
        #         node_color=["white"], node_size=1000)
        plt.savefig(f"./tests/ig/{self.filename}_old_graph.png")
        plt.show()

    def debug(self) -> None:
        import json

        def set_default(obj):
            if isinstance(obj, set):
                return list(obj)

        print(self.interference_edges)
        print(self.dead_code)
        # print(json.dumps(self.node_cost, indent=3, default=set_default))
        # print(set(self.interference_edges.keys()).difference(set(self.node_cost.keys())))
        # print(set(self.node_cost.keys()).difference(set(self.interference_edges.keys())))

    def get_adjacent_colors(self, node: int) -> set[int]:
        adj_colors: set[int] = set()
        for node in self.interference_edges[node]:
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
        self.heap = [(len(value), key) for key, value in self.node_cost.items()]
        heapq.heapify(self.heap)
