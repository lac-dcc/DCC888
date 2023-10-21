import lang
import parser
from typing import List


class DominanceGraph:
    def __init__(s, basic_blocks: List[parser.BasicBlock],
                 env: lang.Env):
        s.bbs = basic_blocks
        s.env = env
        s.frontier = dict()
        for bb in s.bbs:
            s.frontier[bb.index] = []

    def compute_dominance_frontier(s):
        pass

    def insert_phi_functions(s):
        defsites = dict()
        for bb in s.bbs:
            defs = bb.definitions()
            for v in defs:
                if v in defsites.keys():
                    defsites[v].append(bb)
                else:
                    defsites[v] = [bb]
        for var in defsites.keys():
            defining_nodes = defsites[var].copy()
            while len(defining_nodes) != 0:
                n = defining_nodes.pop()
                for frontier_node in s.frontier[n.index]:
                    if var not in n.phi_coverage():
                        s._insert_phi(var, frontier_node)
        # s._update_jumps(bb)
        pass

    def rename(s):
        pass

    def program(s):
        prog = []
        for bb in s.bbs:
            prog += bb.instructions
        return prog


def to_ssa(program: List[lang.Inst], env: lang.Env) -> \
        (List[lang.Inst], lang.Env):
    bbs = parser.to_basic_blocks(program)
    dominance_graph = DominanceGraph(bbs, env)
    dominance_graph.compute_dominance_frontier()
    dominance_graph.insert_phi_functions()
    dominance_graph.rename()
    return dominance_graph.program(), dominance_graph.env
