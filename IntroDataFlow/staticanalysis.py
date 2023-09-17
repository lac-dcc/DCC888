import lang
from abc import ABC, abstractclassmethod
from typing import List
"""
Four data types have been defined to orient any Static Analysis
implementation.

- The StaticAnalysis base class represents the interface that static analysis
  strategies should follow. One example is provided with the Liveness class.

- ConstraintEnv

"""


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


class Equation:
    """
    Equations represent generic set operations which can be recursively
    combined.
    >>> env = ConstraintEnv({'x': {'1','2','3'}, 'y':{'4'}})
    >>> x = Equation('x')
    >>> y = Equation('y')
    >>> eq1 = Equation(x, 'union', y)
    >>> eq2 = Equation(eq1, 'minus', Equation('set', '2,3'))
    >>> eq2.solve(env) == {'1', '4'}
    True

    Note that Equations do no have special meaning in the context of data flow
    analysis. Use the Constraint API to represent data flow equations.
    """

    def __init__(s, left, op="", right=None):
        s.left = left
        s.op = op
        s.right = right

    def __str__(s):
        if s.op is None:
            return f'{str(s.left)}'
        elif s.right is None:
            return f'{str(s.left)} {s.op}'
        else:
            return f'{str(s.left)} {s.op} {str(s.right)}'

    def solve(s, env: ConstraintEnv):
        if s.left == "empty":
            return set()
        elif s.left == "set":
            return set(s.op.split(','))
        elif s.op == "":
            return env.get(s.left)
        else:
            return s.opTable.get(s.op)(s.left, s.right, env)

    def Union(left, right, env: ConstraintEnv):
        return left.solve(env) | right.solve(env)

    def Minus(left, right, env: ConstraintEnv):
        return left.solve(env) - right.solve(env)

    def Inter(left, right, env: ConstraintEnv):
        return left.solve(env).intersection(right.solve(env))

    opTable = {
        "union": Union,
        "minus": Minus,
        "inter": Inter,
    }


class Constraint:
    """
    Constraints are named equations bound to a mutable environment. They
    represent data flow analysis constraints regarding IN and OUT sets.
    >>> env = ConstraintEnv({'x': {}, 'y':{4}, 'z': {2,3}})
    >>> x = Constraint('x', Equation(Equation('y'), 'union', Equation('z')))
    >>> x.eval(env)
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
        return env.update(s.id, s.eq.solve(env))

    def __str__(s):
        return f'{s.id}: {str(s.eq)}'


class StaticAnalysis(ABC):
    @abstractclassmethod
    def run(cls, program: List[lang.Inst]) -> ConstraintEnv:
        raise NotImplementedError


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
    >>> result = Liveness.run(program)
    >>> result == expected_result
    True
    """
    @classmethod
    def run(cls, program: List[lang.Inst]) -> ConstraintEnv:
        constraints = cls.build_constraints(program)
        env = cls.build_constraint_env(program)
        env = chaotic_iterations(constraints, env)
        return env

    @classmethod
    def definitions_equation(cls, instruction: lang.Inst) -> Equation:
        v = cls.definitions(instruction)
        if len(v) > 0:
            v = [str(i) for i in v]
            v = ",".join(v)
            return Equation('set', f'{v}')
        else:
            return Equation('empty')

    @classmethod
    def vars_equation(cls, instruction: lang.Inst) -> Equation:
        vs = cls.vars(instruction)
        if len(vs) > 0:
            vs = [str(i) for i in vs]
            vs = ",".join(vs)
            return Equation('set', f'{vs}')
        return Equation('empty')

    @classmethod
    def build_constraints(cls, program: List[lang.Inst]) -> List[Constraint]:
        constraints = []
        for instruction in program:
            _in = cls.IN(instruction)
            constraints.append(
                Constraint(f'IN_{instruction.index}', _in)
            )
            _out = cls.OUT(instruction)
            constraints.append(
                Constraint(f'OUT_{instruction.index}', _out)
            )
        return constraints

    @classmethod
    def build_constraint_env(cls, program: List[lang.Inst]) -> ConstraintEnv:
        env = dict()
        for i in range(len(program)):
            env[f'IN_{i}'] = set()
            env[f'OUT_{i}'] = set()
        return ConstraintEnv(env)

    @classmethod
    def IN(cls, instruction):
        _in = Equation(
            Equation(
                Equation(f'OUT_{instruction.index}'),
                'minus',
                cls.definitions_equation(instruction)
            ),
            'union',
            cls.vars_equation(instruction)
        )
        return _in

    @classmethod
    def OUT(cls, instruction):
        if len(instruction.NEXTS) == 0:
            _out = Equation('empty')

        elif len(instruction.NEXTS) == 1:
            nxt = instruction.NEXTS[0]
            _out = Equation(f'IN_{nxt.index}')

        else:
            first = instruction.NEXTS[0]
            second = instruction.NEXTS[1]
            _out = Equation(
                Equation(f'IN_{first.index}'),
                'union',
                Equation(f'IN_{second.index}')
            )
        return _out

    @classmethod
    def definitions(cls, instruction):
        if type(instruction) == lang.Bt:
            return set()
        else:
            return set([instruction.definition()])

    @classmethod
    def vars(cls, instruction):
        if type(instruction) == lang.Bt:
            return set([instruction.cond])
        else:
            return set([*instruction.uses()])


def chaotic_iterations(constraints, env):
    while True:
        count = 0
        for i in range(1, len(constraints)+1):
            if not constraints[i-1].eval(env):
                count += 1
        if count == len(constraints):
            break
    return env
