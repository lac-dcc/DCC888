from ssa_form import DominanceGraph, PhiFunction
from typing import List
import lang
import parser


class DJGraph(DominanceGraph):
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
        for bb in s.bbs:
            nxts = bb.NEXTS
            for nxt in nxts:
                if bb.index not in s.get_dominator_indexes(nxt):
                    s.add_j_edge(bb, nxt)

    def add_j_edge(s, bb_tail: parser.BasicBlock, bb_head: parser.BasicBlock):
        s.j_edge_in[bb_head.index].append(bb_tail.index)
        s.j_edge_out[bb_tail.index].append(bb_head.index)

    def compute_dominance_frontiers(s):
        """
        TODO: use J-edges to compute the dominance frontier of all nodes in the
        Dominance Graph.
        """

        # TODO: optimize with piggybank and 'visited' markings
        for bb in s.bbs:
            s.dominance_frontier[bb.index] = set()
            subtree = s.dominance_graph(bb.index)
            for node_index in subtree.keys():
                if node_index in s.j_edge_out.keys():
                    target_indices = s.j_edge_out[node_index]
                    for target_index in target_indices:
                        if s.level[target_index] <= s.level[bb.index]:
                            s.dominance_frontier[bb.index].add(target_index)

    def insert_phi_functions(s):
        phi_nodes_indices = set()
        for values in s.dominance_frontier.values():
            if values != set():
                phi_nodes_indices.union(set((list(values))))

        for phi_node_index in phi_nodes_indices:
            used_vars = s.bbs[phi_node_index].uses()
            for used_var in used_vars:
                s._insert_phi(used_var, s.bbs[phi_node_index])

    # def insert_phi_functions(s):
        # defsites = dict()
        # phi_coverage = dict()
        # for bb in s.bbs:
        #     phi_coverage[bb.index] = set()
        #     defs = bb.definitions()
        #     for v in defs:
        #         if v in defsites.keys():
        #             defsites[v].append(bb)
        #         else:
        #             defsites[v] = [bb]
        # for var in defsites.keys():
        #     defining_nodes = defsites[var].copy()
        #     while len(defining_nodes) != 0:
        #         n = defining_nodes.pop()
        #         for frontier_node in s.frontier[n.index]:
        #             if var not in phi_coverage[n.index]:
        #                 s._insert_phi(var, frontier_node)
        #                 phi_coverage[n.index].add(var)

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
    dj_graph.compute_dominance_frontier()
    dj_graph.insert_phi_functions()
    # dj_graph.rename_variables()
    return dj_graph.rename_variables(), dj_graph.env
