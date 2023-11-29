from typing import List
from static_analysis import ConstraintEnv, Constraint, DependenceGraph


class Worklist:
    """
    The Worklist is the main data structure used by worklist algorithms.
    It represents which constraints remain to be solved.

    There are two fundamental operations regarding this structure:
    insert and extract.

    - "insert" adds constraints to the worklist, the result being a new
    *ordered* worklist. The ordering defines how efficient the worklist
    algorithm works. For this class insert needs not to return a new
    object, but keep itself ordered.

    - "extract" pops the first constraint from the ordered worklist.

    TODO: implement the Worklist data structure. You may create any
    auxiliary methods as necessary, but the current interface must be
    implemented.
    """

    def __init__(s, constraints: List[Constraint]):
        """
        TODO: given a set of constraints, implement a functioning Worklist.
        HINT: keep a DependenceGraph object (from static_analysis) to keep
        track of how constraints affect each other.
        """
        pass

    def insert(s, constraint: Constraint):
        """
        TODO: add new constraints to the active worklist.
        """
        pass

    def extract(s) -> Constraint:
        """
        TODO: pop the fist constraint in the ordered worklist.
        """

    def affected_constraints(s, c: Constraint):
        """
        TODO: return a collection of the Constraints that are affected by 'c'.
        """
        pass

    def empty(s) -> bool:
        """
        TODO: let the caller know if the implemented worklist is empty
        """
        pass


def solve_worklist(constraints: List[Constraint], _env: ConstraintEnv) \
        -> ConstraintEnv:
    worklist = Worklist(constraints)
    env = _env.copy()
    while not worklist.empty():
        constr = worklist.extract()
        update = constr.eval(env)
        if update:
            affected = worklist.affected_constraints(constr)
            for c in affected:
                worklist.insert(c)
    return env
