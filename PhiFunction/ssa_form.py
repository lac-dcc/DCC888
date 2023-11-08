import lang
import parser
from typing import List, Set


class PhiFunction(lang.Inst):
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
        s.immediate_dominance = dict()
        s.dominators = dict()
        s.level = dict()
        s.path = dict()
        for bb in s.bbs:
            s.immediate_dominance[bb.index] = set()
            s.dominators[bb.index] = []
            s.level[bb.index] = 0
            s.path[bb.index] = []

    def flow_graph(s):
        fg = dict()
        for bb in s.bbs:
            fg[bb.index] = [nxt.index for nxt in bb.NEXTS]
        return fg

    def _dominance_graph(s, root: int, dg: dict) -> dict:
        children = s.immediate_dominance[root]
        dg[root] = children
        for child in children:
            s._dominance_graph(child, dg)

    def dominance_graph(s, root: int = 0) -> dict:
        dg = dict()
        s._dominance_graph(root, dg)
        return dg

    def find_common_ancestor(s, bb_indices: Set[int]) \
            -> int:
        paths = [s.path[i] for i in bb_indices]
        j = 0
        min_len = min([len(path) for path in paths])
        for j in range(min_len):
            for i in range(1, len(paths)):
                if paths[i-1][j] != paths[i][j]:
                    return paths[i][j-1]
        return 0

    def get_immediate_dominance(s, block_index: int):
        return s.immediate_dominance[block_index]

    def get_dominator_indexes(s, bb_index: int):
        return s.dominators[bb_index]

    def compute_dominance_graph(s):
        # for each child c of current v:
        # if v is the only parent of c, c dominates v
        # if v_0, v_1, ... are parents of c, ther earliest common parent
        # dominates c.
        parents = [s.bbs[0]]
        s.path[s.bbs[0].index] = [0]
        visited = []
        s.level[0] = 0
        while True:
            next_parents = []
            for parent in parents:
                if parent.index in visited:
                    continue
                visited.append(parent.index)
                children = parent.NEXTS
                for child in children:
                    parents = child.PREVS
                    s.path[child.index] = \
                        s.path[parents[0].index] + [child.index]
                    if len(parents) == 1:
                        dominator_index = parent.index
                    else:
                        parent_indices = [bb.index for bb in parents]
                        dominator_index = \
                            s.find_common_ancestor(parent_indices)
                    s.level[child.index] = s.level[dominator_index]+1
                    s.immediate_dominance[dominator_index].add(child.index)
                    s.dominators[child.index] = \
                        s.dominators[dominator_index] + [dominator_index]
                    next_parents.append(child)
            if len(visited) == len(s.bbs):
                break
            parents = next_parents

    def rename_variables(s):
        var_stack = dict()
        var_count = dict()

        def assert_in_stack(var):
            if var not in var_stack.keys():
                var_stack[var] = [0]

        def assert_count(var):
            if var not in var_count.keys():
                var_count[var] = 0

        def replace_use(var, inst):
            top = var_stack[var][-1]
            if issubclass(type(inst), lang.BinOp):
                if inst.src0 == var:
                    inst.src0 = f'{var}_{top}'
                if inst.src1 == var:
                    inst.src1 = f'{var}_{top}'
            else:
                inst.cond = f'{var}_{top}'

        def replace_phi_use(var, block_index, inst):
            for i in range(len(inst.srcs)):
                if type(inst.srcs[i]) is tuple \
                        and inst.srcs[i][1] == block_index:
                    inst.srcs[i] = var

        def replace_definition(var, inst):
            top = var_stack[var][-1]
            inst.dst = f'{var}_{top}'

        def find_latest(root_var, block_index):
            bb = s.bbs[block_index]
            latest = 0
            for definition in bb.definitions():
                root, var_index = definition.split('_')
                if root == root_var and int(var_index) > int(latest):
                    latest = var_index
            return f'{root_var}_{latest}'

        for inst in s.prog:
            if type(inst) is not PhiFunction:
                for var in inst.uses():
                    assert_in_stack(var)
                    replace_use(var, inst)
            for var in inst.definition():
                assert_in_stack(var)
                assert_count(var)
                i = var_count[var]
                var_stack[var].append(i)
                replace_definition(var, inst)
                var_count[var] += 1
        for inst in s.prog:
            if type(inst) is not PhiFunction:
                continue
            for (root_var, block_index) in inst.uses():
                var = find_latest(root_var, block_index)
                replace_phi_use(var, block_index, inst)

    def reindex_program(s):
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
        s.prog = prog
