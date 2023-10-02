from typing import List, Set
from static_analysis import ConstraintEnv, Constraint


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

    def affected_constraints(s, c: Constraint):
        ids = s.dg.affects(c.id)
        cs = [s.csMap[id] for id in ids]
        return cs


def solve_worklist(constraints: List[Constraint], _env: ConstraintEnv) \
        -> ConstraintEnv:
    worklist = Worklist(constraints)
    env = _env.copy()
    while not worklist.empty:
        constr = worklist.extract()
        update = constr.eval(env)
        if update:
            affected = worklist.affected_constraints(constr)
            for c in affected:
                worklist.insert(c)
    return env
