import graphviz
import os

from app.parser.cfg import CFG
from app.parser.basic_blocks import BB
from app.custom_types import InstrNodeActual
from app.tokenizer import Tokenizer


class IRViz:
    def __init__(self, cfg: CFG, filename: str = None) -> None:
        self.cfg = cfg
        self.graph: graphviz.Digraph = graphviz.Digraph(name="CFG")
        self.filename = "graph" if filename is None else filename
        self.dir = "./ir_viz_tool/tests"

    def get_bb_instrs(self, bb: BB) -> str:
        instr_str: str = ""
        for instr in bb.get_instr_list():
            actual_instr: InstrNodeActual = self.cfg.get_actual_instr(instr)
            instr_str += f"{str(actual_instr)} | "

        return instr_str[:-2]

    def add_dom_edge(self, bb: BB) -> None:
        dom_bb: int = self.cfg.get_dom_predecessor(bb.bb_num)
        if dom_bb == -1:
            return
        self.graph.edge(f"BB{dom_bb}:b", f"BB{bb.bb_num}:b", label="dom", style="dotted")

    def add_pred_edge(self, bb: BB) -> None:
        pred_bb: list[int] = self.cfg.get_predecessors(bb.bb_num)
        if not pred_bb:
            return
        for pred in pred_bb:
            self.graph.edge(f"BB{pred}:s", f"BB{bb.bb_num}:n")

    def fmt_var_instr_map(self, bb: BB) -> str:
        res: str = ""
        var_instr_map: dict[int, int] = bb.get_var_instr_map()

        if bb.bb_num == 0:
            return res

        for var, instr_num in var_instr_map.items():
            res += f"{Tokenizer.id2string(var)}: {instr_num} | "

        return res[:-2]

    def generate_basic_blocks(self) -> None:
        def __create_basic_block(shape: str = "record") -> None:
            nonlocal name, label, var_instr_map
            label = f"<b>{name.upper()} | {{{label}}} | {{{var_instr_map}}}"
            self.graph.node(name=name, label=label, shape=shape)

        for bb in self.cfg.get_bb_map():
            label: str = self.get_bb_instrs(bb)
            name: str = f"BB{bb.bb_num}"
            var_instr_map: str = self.fmt_var_instr_map(bb)
            __create_basic_block()
            self.add_dom_edge(bb)
            self.add_pred_edge(bb)

    def render_graph(self):
        self.filename = os.path.splitext(self.filename)[0]
        self.graph.render(filename=f"{self.dir}/{self.filename}", format="png")

    def generate_graph(self) -> None:
        self.generate_basic_blocks()
        self.render_graph()
