from app.parser.basic_blocks import BB
from app.parser.instr_graph import InstrGraph
from app.parser.instr_node import OpInstrNode
from app.tokens import OpCodeEnum


class CFG:
    def __init__(self):
        self.const_bb = None
        self._instr_graph = InstrGraph()
        self.bb_num = 2
        self.curr_bb = None
        self._predecessors = dict()
        self._successors = dict()
        self._dom_predecessors = dict()
        self._bb_map = dict()
        self.initialize_cfg()

    def get_bb(self, bb_num):
        return self._bb_map[bb_num]

    def initialize_cfg(self):
        bb0 = BB(0)
        bb1 = BB(1)
        self._bb_map.update({
            0: bb0,
            1: bb1
        })
        self.curr_bb = bb1
        self._predecessors[bb1.bb_num] = [bb0.bb_num]
        self._successors[bb0.bb_num] = [bb1.bb_num]
        self.const_bb = bb0

    def build_instr_node(self, node_type, opcode, bb=None, **kwargs):
        if bb is None:
            bb = self.curr_bb
        instr_num = self._instr_graph.build_instr_node(node_type, opcode, **kwargs)
        bb.update_instr_list(instr_num)
        return instr_num

    def get_var_instr_num(self, bb, ident):
        if bb.check_instr_exists(ident):
            return bb.get_instr_num(ident)

        search_space = self._predecessors[bb.bb_num]
        res = set()
        for node in search_space:
            res.add(self.get_var_instr_num(self._bb_map[node], ident))

        res = list(res)
        if len(res) > 1:
            instr_num = self.build_instr_node(OpInstrNode, OpCodeEnum.PHI.value, bb=bb, left=res[0], right=res[1])
        else:
            instr_num = res[0]

        return instr_num

    def debug(self):
        for bb in self._bb_map.values():
            bb.debug()
