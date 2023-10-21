import lang
import parser
from typing import List


class Phi(lang.Inst):
    def __init(s, dst, srcs):
        s.dst = dst
        s.srcs = srcs
        super().__init__()

    def definition(s):
        return set([s.dst])

    def uses(s):
        return set(s.srcs)


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
        phi_coverage = dict()
        for bb in s.bbs:
            phi_coverage[bb.index] = set()
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
                    if var not in phi_coverage[n.index]:
                        s._insert_phi(var, frontier_node)
                        phi_coverage[n.index].add(var)
        # s._update_jumps(bb)
        pass

    def _insert_phi(var, bb):
        preds = [var for ps in bb.PREVS]
        phi = Phi(var, preds)
        leader = bb.instructions[0]
        # update instruction chain
        bb.instructions = [phi] + bb.instructions

    def rename(s):
        pass

    def program(s):
        last_index = 0
        for bb in s.bbs:
            for inst in bb.instructions:
                inst.index = last_index
                last_index += 1
        for bb in s.bbs:
            last_instruction = bb.instructions[-1]
            # update instruction chaining
            if type(last_instruction) is not lang.Bt:
                continue
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
