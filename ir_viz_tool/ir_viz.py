import graphviz
import os

from app.parser.cfg import CFG
from app.parser.basic_blocks import BB
from app.custom_types import InstrNodeActual
from app.tokenizer import Tokenizer
from app.tokens import RELOP_TOKEN_OPCODE, OpCodeEnum


colors = ["lightcoral", "grey67", "royalblue4"]
c = 0

BR_INSTRS = set(RELOP_TOKEN_OPCODE.values()).union({OpCodeEnum.BRA.value})


class IRViz:
    def __init__(self, cfg_map: dict[int, CFG], reg_cfg_map: dict[int, dict[int, list[str]]],
                 dead_code_map: dict[int, set[int]], filename: str = None) -> None:
        self.cfg_map: dict[int, CFG] = cfg_map
        self.cfg: CFG
        self.graph: graphviz.Digraph = graphviz.Digraph(name="CFG", graph_attr={"ranksep": "0.75", "nodesep": "0.5"})
        self.filename: str = "graph" if filename is None else filename
        self.dir: str = "./tests/ir"
        self.call_instrs: dict[str, str] = dict()
        self.reg_cfg_map = reg_cfg_map
        self.dead_code_map = dead_code_map

    def get_bb_instrs(self, bb: BB) -> str:
        def strike(text: str) -> str:
            return ''.join([u'\u0336{}'.format(c) for c in text])

        instr_str: str = ""
        for instr in bb.get_instr_list():
            actual_instr: InstrNodeActual = self.cfg.get_instr(instr)
            if actual_instr.opcode != OpCodeEnum.CALL.value:
                if instr in self.dead_code:
                    instr_str += f"{strike(str(actual_instr))} | "
                else:
                    instr_str += f"{str(actual_instr)} | "
            else:
                instr_str += f"<{actual_instr.instr_num}>{str(actual_instr)} | "
                self.call_instrs[f"{self.key}BB{bb.bb_num}:{actual_instr.instr_num}"] = \
                    f"{Tokenizer.id2string(actual_instr.left)}_BB0"

        return instr_str[:-2]

    def add_dom_edge(self, bb: BB) -> None:
        dom_bb: int = self.cfg.get_dom_predecessor(bb.bb_num)
        if dom_bb == -1:
            return
        self.sub_graph.edge(f"{self.key}BB{dom_bb}:b", f"{self.key}BB{bb.bb_num}:b", label="dom", style="dotted")

    def add_pred_edge(self, bb: BB) -> None:
        global c

        bb_first_instr_num: int = bb.get_first_instr_num()
        pred_bb: list[int] = self.cfg.get_predecessors(bb.bb_num)
        if not pred_bb:
            return
        for pred in pred_bb:
            instr: InstrNodeActual = self.cfg.get_instr(self.cfg.get_bb_from_bb_num(pred).get_last_instr_num())
            instr_num: int = -1
            if instr.opcode in BR_INSTRS:
                if instr.opcode == OpCodeEnum.BRA.value:
                    instr_num = instr.left
                else:
                    instr_num = instr.right
            if instr_num == bb_first_instr_num:
                self.sub_graph.edge(f"{self.key}BB{pred}:s", f"{self.key}BB{bb.bb_num}:n", color=colors[c % 3],
                                    label="br", style="bold")
            else:
                self.sub_graph.edge(f"{self.key}BB{pred}:s", f"{self.key}BB{bb.bb_num}:n", color=colors[c % 3])

            c += 1

    def fmt_var_instr_map(self, bb: BB) -> str:
        res: str = ""
        var_instr_map: dict[int, int] = bb.get_var_instr_map()

        if bb.bb_num == 0:
            return res

        for var, instr_num in var_instr_map.items():
            res += f"{Tokenizer.id2string(var)}: {instr_num} | "

        return res[:-2]

    def get_live_range(self, bb: BB) -> str:
        if bb is self.cfg.const_bb:
            return ""
        return f"top: {list(bb.top_live)} | bot: {list(bb.bot_live)}"

    def get_reg_instrs(self, bb_num: int) -> str:
        repl = "\<-"
        instr_str: str = ""
        for instr in self.reg_cfg[bb_num]:
            instr_str += f"{instr.replace('<-', repl)} | "

        return instr_str[:-2]

    def generate_basic_blocks(self) -> None:
        def __create_basic_block(shape: str = "record") -> None:
            nonlocal name, label, var_instr_map, live_range
            label = f"<b>{name} | {{{label}}} | {{{var_instr_map}}} | {{{live_range}}} | {{{reg_instrs}}}"
            self.sub_graph.node(name=name, label=label, shape=shape, ordering="out")

        for bb in self.cfg.get_bb_map():
            label: str = self.get_bb_instrs(bb)
            name: str = f"{self.key}BB{bb.bb_num}"
            var_instr_map: str = self.fmt_var_instr_map(bb)
            live_range: str = self.get_live_range(bb)
            reg_instrs: str = self.get_reg_instrs(bb.bb_num)
            __create_basic_block()
            self.add_dom_edge(bb)
            self.add_pred_edge(bb)

    def render_graph(self):
        self.filename = os.path.splitext(self.filename)[0]
        self.graph.render(filename=f"{self.dir}/{self.filename}", format="png")

    def generate_graph(self) -> None:
        for key, cfg in self.cfg_map.items():
            self.cfg = cfg
            self.reg_cfg = self.reg_cfg_map[key]
            self.dead_code = self.dead_code_map[key]
            self.key = f"{Tokenizer.id2string(key)}_" if key != 0 else ""
            with self.graph.subgraph(name=f"cluster_{self.key}") as self.sub_graph:
                self.sub_graph.attr(label=self.key[:-1] if self.key else "main")
                self.generate_basic_blocks()

        for key, val in self.call_instrs.items():
            self.graph.edge(f"{key}:_", f"{val}:n", label="call", style="dotted")

        self.render_graph()
