import lang
import parser
from typing import List


class Phi(lang.Inst):
    def __init__(s, dst, srcs):
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

    def _insert_phi(s, var, bb):
        preds = [var for ps in bb.PREVS]
        phi = Phi(var, preds)
        # update instruction chain
        leader = bb.instructions[0]
        for prev in leader.PREVS:
            phi.add_prev(prev)
            for i in range(len(prev.NEXTS)):
                if prev.NEXTS[i] == leader:
                    prev.NEXTS[i] = phi
                    break
        phi.add_next(leader)
        leader.PREVS = [phi]
        bb.instructions = [phi] + bb.instructions

    def rename(s):
        pass

    def program(s):
        last_index = 0
        # update instruction indices
        for bb in s.bbs:
            for inst in bb.instructions:
                inst.index = last_index
                last_index += 1
        # update branch jump addresses
        for bb in s.bbs:
            last_instruction = bb.instructions[-1]
            if type(last_instruction) is not lang.Bt:
                continue
            next_leaders = [n.leader() for n in bb.NEXTS]
            for leader in next_leaders:
                if leader != last_instruction.index+1:
                    last_instruction.jump_to = leader
        # concatenate basic blocks
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
