import lang
from typing import List, Set
from static_analysis import ConstraintEnv, Constraint, Equation, \
    StaticAnalysis


class AdjacencyMatrix:
    """
    This NxN adjacency matrix represents a directed graph with N vertices.
    Each vertex in the graph has its own line. For each line, the N columns
    represent this vertex's neighbourhood.

    An arc from vertex 'a' to vertex 'b' is represented with -1 in M[a][b] and
    +1 in M[b][a]. Regardng this arc, 'a' and 'b' are called the "foot" and the
    "head", respectively. Thus, for each line, -1 represents "outgoing" edges,
    while +1 indicates "incoming" edges.

    All indexes start at 0.

    Given the cyclic graph G with vertices {1, 2, 3} and the edges
    {(1,2), (2,3), (3,1)}:

    >>> m = AdjacencyMatrix(3)
    >>> m.add_arc(0, 1)
    >>> m.add_arc(1, 2)
    >>> m.add_arc(2, 0)
    >>> print(str(m))
    [0, -1, 1]
    [1, 0, -1]
    [-1, 1, 0]
    """
    def __init__(s, size: int):
        matrix = []
        for n in range(size):
            row = [0 for i in range(size)]
            matrix.append(row)
        s.m = matrix
        s.len = n

    def add_arc(s, foot: int, head: int):
        s.m[foot][head] = -1
        s.m[head][foot] = 1

    def del_arc(s, foot: int, head: int):
        s.m[foot][head] = 0
        s.m[head][foot] = 0

    def __str__(s):
        out = ""
        for line in s.m:
            out += str(line) + '\n'
        return out.strip()

    def get(s, row: int, *cols: int):
        if len(cols) == 1:
            return s.m[row][cols[0]]
        else:
            return s.m[row]


class DependenceGraph:
    """
    The dependence graph tracks how each constraint affects and is affected by
    others. It consists of a directed graph whereby each vertex represents a
    constraint, and each arc represents an "affetcs" relationship. Therefore,
    given an arc (a,b), the "head" 'b' is affected by the "foot" 'a'. This
    means that 'b's equation utilizes 'a'.

    DependenceGraph utilizes an adjacency matrix for its in-memory
    representation. Since AdjacencyMatrix utilizes numerical indexes,
    DependenceGraph maps each constraint ID (e.g. "IN_1", "OUT_1") to its
    numerical index in the matrix. This frees the User to think only of
    constraint names when building the graph.

    >>> g = DependenceGraph(["x", "y", "z"])
    >>> g.add_dependence(foot="x", head="y")
    >>> g.add_dependence(foot="x", head="z")
    >>> g.print()
    """
    def __init__(s, constraintIds: List[str]):
        s.constraintIds = constraintIds
        s.adjm = AdjacencyMatrix(len(constraintIds))
        labels = dict()
        rlabels = dict()
        c = 0
        for i in constraintIds:
            labels[i] = c
            rlabels[c] = i
            c += 1
        s.labels = labels
        s.rlabels = rlabels

    def add_dependence(s, foot: str, head: str):
        foot_index = s.labels[foot]
        head_index = s.labels[head]
        s.adjm.add_arc(foot_index, head_index)

    def remove_dependence(s, foot: str, head: str):
        foot_index = s.labels[foot]
        head_index = s.labels[head]
        s.adjm.add_arc(foot_index, head_index)

    def print(s):
        for label in s.labels:
            affects = s.affects(label)
            affected_by = s.affected_by(label)
            print(f'label: {label}\n'
                  f'affects: {affects}\n'
                  f'affected by: {affected_by}')

    def affects(s, label: str) -> Set[str]:
        label_index = s.labels[label]
        row = s.adjm.get(label_index)
        nbs = []
        for i in range(len(row)):
            if row[i] == -1:
                nbs.append(s.rlabels[i])
        return set(nbs)

    def affected_by(s, label: str) -> Set[str]:
        label_index = s.labels[label]
        row = s.adjm.get(label_index)
        nbs = []
        for i in range(len(row)):
            if row[i] == 1:
                nbs.append(s.rlabels[i])
        return set(nbs)


class Worklist:
    def __init__(s, constraints: List[Constraint]):
        s.empty = False
        cIds = [c.id for c in constraints]
        s.dg = DependenceGraph(cIds)
        s.build_dependences(constraints)
        s.worklist = constraints
        s.csMap = dict()
        for c in constraints:
            s.csMap[c.id] = c

    def build_dependences(s, constraints: List[Constraint]):
        for c in constraints:
            uses = c.uses()
            for var in uses:
                s.dg.add_dependence(var, c.id)

    def insert(s, constraint: Constraint):
        s.worklist.append(constraint)

    def extract(s) -> Constraint:
        head = s.worklist.pop()
        if len(s.worklist) == 0:
            s.empty = True
        return head

    def empty(s) -> bool:
        pass

    def affected_constraints(s, c: Constraint):
        ids = s.dg.affects(c.id)
        cs = [s.csMap[id] for id in ids]
        return cs


def solve_worklist(constraints: List[Constraint], env: ConstraintEnv):
    worklist = Worklist(constraints)
    while not worklist.empty:
        constr = worklist.extract()
        update = constr.eval(env)
        if update:
            affected = worklist.affected_constraints(constr)
            for c in affected:
                worklist.insert(c)
    return env
