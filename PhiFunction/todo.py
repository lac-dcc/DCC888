from ssa_form import DominanceGraph, PhiFunction
from typing import List
import lang
import parser


class DJGraph(DominanceGraph):
    """
    The DJGraph class extends the DominanceGraph defined in ssa_form.py.
    The base class operates on Basic Blocks:

        >>> program = [
        ...     '{"zero": 0, "one": 1, "true": true}',
        ...     'a = add zero one',
        ...     'bt true 3',
        ...     'a = add a one',
        ...     'a = add a one',
        ... ]
        >>> prog, env = parser.build_cfg(program)
        >>> bbs = parser.to_basic_blocks(prog)

    Basic Blocks (BBs) are indexed according to the order their leaders appear
    in the program.
        >>> [bb.index for bb in bbs]
        [0, 1, 2]

    DominanceGraph always uses the indices to operate on the
    blocks:

        >>> dg = DominanceGraph(bbs, env)
        >>> dg.flow_graph()
        {0: [1, 2], 1: [2], 2: []}
        >>> dg.compute_dominance_graph()
        >>> dg.dominance_graph()
        {0: {1, 2}, 1: set(), 2: set()}

    This means that BB 0 leads to BBs 1 and 2, BB 1 leads
    to BB 2, and BB 2 is the final block and leads nowhere. Also, BB
    0 dominates BBs 1 and 2, while BBs 1 and 2 are the leaves of the dominance
    tree.

    The whole API is based on such indices, and BBs are never passed directly
    as parameters:
        >>> dg.dominance_graph(root=1)
        {1: set()}

    DominanceGraph stores information about its structure:
        >>> dg.get_immediate_domain_indices(index=0)
        {1, 2}
        >>> dg.get_dominator_indices(index=1)
        {0}

    Instead of interacting directly with BasicBlock objects, you may use
    DominanceGraph:
        >>> dg.get_NEXTS_indices(index=0)
        {1, 2}
        >>> dg.get_PREVS_indices(index=2)
        {0, 1}

    """
    def __init__(s, basic_blocks: List[parser.BasicBlock],
                 env: lang.Env):
        super().__init__(basic_blocks, env)
        s.j_edge_in = dict()
        s.j_edge_out = dict()
        s.dominance_frontier = dict()
        for bb in s.bbs:
            s.j_edge_in[bb.index] = []
            s.j_edge_out[bb.index] = []

    def compute_j_edges(s):
        """
        Taken from "A Linear Time Algorithm for Placing phi-Nodes":

            An edge x->y in a flowgraph is named a join edge (or J-edge) if
            x !sdom y. Furthermore, y is named a join node.

        TODO: implement the method for computing J-edges.

        Note that J-edges are represented in the 's.j_edge_in' dictionary.
        Representing J-edges from the side of the receiver falls in accordance
        with how J-edges are utilized when computing Dominance Frontiers.
        """
        raise NotImplementedError

    def add_j_edge(s, bb_tail: parser.BasicBlock, bb_head: parser.BasicBlock):
        s.j_edge_in[bb_head.index].append(bb_tail.index)
        s.j_edge_out[bb_tail.index].append(bb_head.index)

    def compute_dominance_frontiers(s):
        """
        TODO: use J-edges to compute the dominance frontier of all nodes in the
        Dominance Graph.
        """
        raise NotImplementedError

    def insert_phi_functions(s):
        phi_nodes_indices = set()
        for values in s.dominance_frontier.values():
            if values != set():
                phi_nodes_indices.union(set((list(values))))

        for phi_node_index in phi_nodes_indices:
            used_vars = list(s.bbs[phi_node_index].uses())
            used_vars.sort()
            for used_var in used_vars:
                s._insert_phi(used_var, s.bbs[phi_node_index])

    def _insert_phi(s, var, bb):
        preds = [(var, ps.index) for ps in bb.PREVS]
        phi = PhiFunction(var, preds)
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


def to_ssa(program: List[lang.Inst], env: lang.Env) -> \
        (List[lang.Inst], lang.Env):
    bbs = parser.to_basic_blocks(program)
    dj_graph = DJGraph(bbs, env)
    dj_graph.compute_dominance_graph()
    dj_graph.compute_j_edges()
    dj_graph.compute_dominance_frontiers()
    dj_graph.insert_phi_functions()
    dj_graph.reindex_program()
    dj_graph.rename_variables()
    return dj_graph.prog, dj_graph.env
