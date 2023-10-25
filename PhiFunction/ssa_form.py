import lang
import parser
from typing import List, Set


class Phi(lang.Inst):
    def __init__(s, dst, srcs):
        s.dst = dst
        s.srcs = srcs
        super().__init__()

    def definition(s):
        return set([s.dst])

    def uses(s):
        return set(s.srcs)


class DJGraph:
    def __init__(s, basic_blocks: List[parser.BasicBlock],
                 env: lang.Env):
        s.bbs = basic_blocks
        s.env = env
        s.dominance = dict()
        s.dominators = dict()
        s.level = dict()
        s.path = dict()
        for bb in s.bbs:
            s.dominance[bb.index] = set()
            s.dominators[bb.index] = set()
            s.level[bb.index] = 0
            s.path[bb.index] = []

    def find_common_ancestor(s, bbs: Set[parser.BasicBlock]) \
            -> parser.BasicBlock:
        indexes = [bb.index for bb in bbs]
        paths = [s.path[i] for i in indexes]
        print(paths)
        j = 0
        min_len = min([len(path) for path in paths])
        for j in range(min_len):
            for i in range(1, len(paths)):
                if paths[i-1][j] != paths[i][j]:
                    return s.bbs[paths[i][j-1]]
        return s.bbs[0]

    def compute_dominance_graph(s):
        # for each child c of current v:
        # if v is the only parent of c, c dominates v
        # if v_0, v_1, ... are parents of c, ther earliest common parent
        # dominates c.
        parents = [s.bbs[0]]
        s.path[s.bbs[0].index] = [0]
        visited = []
        level = 0
        while True:
            for parent in parents:
                if parent.index in visited:
                    continue
                s.level[parent.index] = level
                visited.append(parent.index)
                children = parent.NEXTS
                for child in children:
                    print(f'child: {child.index}, {child}')
                    parents = child.PREVS
                    print(f'{parents}')
                    s.path[child.index] = \
                        s.path[parents[0].index] + [child.index]
                    if len(parents) == 1:
                        dominator = parent
                    else:
                        print(f'found dominator: {dominator.index}')
                        dominator = s.find_common_ancestor(parents)
                    s.dominance[dominator.index].add(child.index)
                    s.dominators[child.index].add(dominator.index)
            if len(visited) == len(s.bbs):
                break
            parents = children
            level += 1

    def compute_j_edges(s):
        pass

    def compute_dominance_frontiers(s):
        s.frontier = dict()
        for bb in s.bbs:
            s.frontier[bb.index] = []
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

    def rename_variables(s):
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
    dj_graph = DJGraph(bbs, env)
    dj_graph.compute_dominance_graph()
    dj_graph.compute_j_edges()
    dj_graph.compute_dominance_frontier()
    dj_graph.insert_phi_functions()
    dj_graph.rename()
    return dj_graph.program(), dj_graph.env
