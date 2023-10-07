import lang
from parser import build_cfg
from abc import ABC, abstractclassmethod
from typing import List, Type, Callable
"""
Four data types have been defined to orient any Static Analysis
implementation.

- The StaticAnalysis base class represents the interface that static analysis
  strategies should follow. One example is provided with the Liveness class.

- ConstraintEnv

"""


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
    label: x
    affects: ['y', 'z']
    affected by: []
    label: y
    affects: []
    affected by: ['x']
    label: z
    affects: []
    affected by: ['x']

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
            affects = list(s.affects(label))
            affected_by = list(s.affected_by(label))
            affects.sort()
            affected_by.sort()
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


class ConstraintEnv:
    def __init__(s, env: dict):
        s.env = env

    def get(s, id: str) -> set:
        return s.env[id]

    def update(s, id: str, value: set):
        if s.env[id] == value:
            return False
        s.env[id] = value
        return True

    def __eq__(s, o) -> bool:
        return s.env == o.env

    def print(s):
        size = int(len(s.env)/2)
        for i in range(size):
            ordered_values = list(s.env[f'IN_{i}'])
            ordered_values.sort(key=lambda key: str(key))
            ordered_values = map(str, ordered_values)
            print(f'IN_{i}: {", ".join(ordered_values)}')
            ordered_values = list(s.env[f'OUT_{i}'])
            ordered_values.sort(key=lambda key: str(key))
            ordered_values = map(str, ordered_values)
            print(f'OUT_{i}: {", ".join(ordered_values)}')


class Constraint:
    """
    Constraints are named equations bound to a mutable environment. They
    represent data flow analysis constraints regarding IN and OUT sets.
    >>> env = ConstraintEnv({'x': {}, 'y':{4}, 'z': {2,3}})
    >>> x_eq = lambda: env.get('y') | env.get('z')
    >>> x = Constraint('x', x_eq)
    >>> _ = x.eval(env)
    >>> env.get('x') == {2, 3, 4}
    True

    Note that, while Equations return a resulting set based on its operations,
    Constraint objects actually update their environment, since a Constraint's
    value may influence others.
    """
    def __init__(s, id, eq):
        s.id = id
        s.eq = eq

    def eval(s, env):
        return env.update(s.id, s.eq())

    def __str__(s):
        return f'{s.id}: {str(s.eq)}'


class StaticAnalysis(ABC):
    @abstractclassmethod
    def IN(cls,
           program: List[lang.Inst],
           cEnv: ConstraintEnv,
           env: lang.Env) -> Callable:
        raise NotImplementedError

    @abstractclassmethod
    def OUT(cls,
            program: List[lang.Inst],
            cEnv: ConstraintEnv,
            env: lang.Env) -> Callable:
        raise NotImplementedError

    @classmethod
    def run(cls, program: List[lang.Inst], env: lang.Env) -> ConstraintEnv:
        cEnv = cls.build_constraint_env(program)
        constraints = cls.build_constraints(program, cEnv, env)
        cEnv = chaotic_iterations(constraints, cEnv)
        return cEnv

    @classmethod
    def build_constraint_env(cls, program: List[lang.Inst]) -> ConstraintEnv:
        env = dict()
        for i in range(len(program)):
            env[f'IN_{i}'] = set()
            env[f'OUT_{i}'] = set()
        return ConstraintEnv(env)

    @classmethod
    def build_constraints(cls, program: List[lang.Inst],
                          cEnv: ConstraintEnv,
                          env: lang.Env) -> List[Constraint]:
        constraints = []
        for instruction in program:
            _in = cls.IN(instruction, cEnv, env)
            constraints.append(
                Constraint(f'IN_{instruction.index}', _in)
            )
            _out = cls.OUT(instruction, cEnv, env)
            constraints.append(
                Constraint(f'OUT_{instruction.index}', _out)
            )
        return constraints

    # @classmethod
    # def definitions(cls, instruction):
    #     if type(instruction) == lang.Bt:
    #         return set()
    #     else:
    #         return set([instruction.definition()])

    # @classmethod
    # def vars(cls, instruction):
    #     if type(instruction) == lang.Bt:
    #         return set([instruction.cond])
    #     else:
    #         return set([*instruction.uses()])


def run_analysis_on_file(file_name: str, analysis: Type[StaticAnalysis]):
    with open(file_name) as f:
        lines = f.readlines()
    (program, environment) = build_cfg(lines)
    result = analysis.run(program, environment)
    return result


def run_analysis_on_program(program: List[lang.Inst],
                            env: lang.Env,
                            analysis: Type[StaticAnalysis]):
    result = analysis.run(program, env)
    return result


class Liveness(StaticAnalysis):
    """
    Returns the liveness analysis of a program.
    A variable is "alive" at a certain point in the code if it has been
    defined and there is at least one path from this point which leads to its
    current value being used. A variable "dies" if its value is reset.

    For each instruction
        p: v = E(s)

    The incoming and outgoing live variables are defined as:
        IN:  Union((OUT(p) - {v}), vars(E))
        OUT: Union(IN(ps)), ps in succ(p)

    (read more in https://homepages.dcc.ufmg.br/~fernando/classes/dcc888/ementa/slides/IntroDataFlow.pdf)

    >>> program_lines = [
    ... '{"a": 1, "b": 2}',
    ... 'x = add a b',
    ... 'y = add x a',
    ... 'b = add a x',
    ... ]
    >>> expected_result = ConstraintEnv({
    ... 'IN_0': {'a', 'b'},
    ... 'OUT_0': {'a', 'x'},
    ... 'IN_1': {'a', 'x'},
    ... 'OUT_1': {'a', 'x'},
    ... 'IN_2': {'a', 'x'},
    ... 'OUT_2': set(),
    ... })
    >>> program, env = build_cfg(program_lines)
    >>> result = Liveness.run(program, env)
    >>> result == expected_result
    True
    """

    @classmethod
    def IN(cls, instruction: lang.Inst,
           cEnv: ConstraintEnv,
           env: lang.Env) -> Callable:
        def _in():
            return (cEnv.get(f'OUT_{instruction.index}')
                    - instruction.definition()) \
                    | instruction.uses()
        return _in

    @classmethod
    def OUT(cls, instruction: lang.Inst,
            cEnv: ConstraintEnv,
            env: lang.Env) -> Callable:
        if len(instruction.NEXTS) == 0:
            return lambda: set()

        elif len(instruction.NEXTS) == 1:
            nxt = instruction.NEXTS[0]
            return lambda: cEnv.get(f'IN_{nxt.index}')

        else:
            first = instruction.NEXTS[0]
            second = instruction.NEXTS[1]
            return lambda: cEnv.get(f'IN_{first.index}') \
                | cEnv.get(f'IN_{second.index}')


def chaotic_iterations(constraints, env):
    while True:
        count = 0
        for i in range(1, len(constraints)+1):
            if not constraints[i-1].eval(env):
                count += 1
        if count == len(constraints):
            break
    return env
