from ssa_form import DominanceGraph
from typing import List
import lang
import parser


class DJGraph(DominanceGraph):
    def compute_j_edges(s):
        pass

    def compute_dominance_frontiers(s):
        s.frontier = dict()
        for bb in s.bbs:
            s.frontier[bb.index] = []
        pass


def to_ssa(program: List[lang.Inst], env: lang.Env) -> \
        (List[lang.Inst], lang.Env):
    bbs = parser.to_basic_blocks(program)
    dj_graph = DJGraph(bbs, env)
    dj_graph.compute_dominance_graph()
    dj_graph.compute_j_edges()
    dj_graph.compute_dominance_frontier()
    dj_graph.insert_phi_functions()
    dj_graph.rename()
    return dj_graph.program(), dj_graph.env
