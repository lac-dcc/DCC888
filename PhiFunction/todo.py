from ssa_form import DominanceGraph
from typing import List
import lang
import parser


class DJGraph(DominanceGraph):
    def __init__(s, basic_blocks: List[parser.BasicBlock],
                 env: lang.Env):
        s.j_edge_in = dict()
        s.dominance_frontier = dict()
        super.__init__(s, basic_blocks, env)

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
        for bb in s.bbs:
            nxts = bb.NEXTS
            for nxt in nxts:
                if bb.index not in s.get_dominator_indexes(nxt):
                    s.add_j_edge(bb, nxt)

    def add_j_edge(s, bb_tail: parser.BasicBlock, bb_head: parser.BasicBlock):
        if bb_head.index in s.j_edge_in.keys():
            s.j_edge_in[bb_head.index].append(bb_tail.index)
        else:
            s.j_edge_in[bb_head.index] = [bb_tail.index]

    def compute_dominance_frontiers(s):
        """
        TODO: use J-edges to compute the dominance frontier of all nodes in the
        Dominance Graph.
        """
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
