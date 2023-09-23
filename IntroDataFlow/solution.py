import lang
from parser import build_cfg
from static_analysis import ConstraintEnv, Constraint, Equation, \
    StaticAnalysis, chaotic_iterations

from typing import List


class ReachingDefinitions(StaticAnalysis):
    """
    Returns the Reaching Definitions analysis of a program.
    The definition of a variable reaches a program point if said variable has
    been defined prior and does not "die" via a new assignment along the way.

    For each instruction
        p: v = E(s)

    The incoming and outgoing reaching definitions are deined as:
        IN:  Union(OUT(ps), ps in succ(p)
        OUT: Union(IN(p) - {definitions(v)}, {(p, v)})

    (read more in https://homepages.dcc.ufmg.br/~fernando/classes/dcc888/ementa/slides/IntroDataFlow.pdf)

    Since the program starts with a set environment, definitions from said
    environment are said to come from instruction -1.

    >>> program_lines = [
    ... '{"a": 1, "b": 2}',
    ... 'x = add a b',
    ... 'a = add x a',
    ... 'b = add a x',
    ... ]
    >>> expected_result = ConstraintEnv({
    ... 'IN_0': {(-1, 'a'), (-1, 'b')},
    ... 'OUT_0': {(-1, 'a'), (-1, 'b'), (0, 'x')},
    ... 'IN_1': {(-1, 'a'), (-1, 'b'), (0, 'x')},
    ... 'OUT_1': {(1, 'a'), (-1, 'b'), (0, 'x')},
    ... 'IN_2': {(1, 'a'), (-1, 'b'), (0, 'x')},
    ... 'OUT_2':{(1, 'a'), (1, 'b'), (0, 'x')},
    ... })
    >>> program, env = build_cfg(program_lines)
    >>> result = ReachingDefinitions.run(program)
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
    def IN(cls, instruction: lang.Inst) -> Equation:
        eq = Equation('set', set())
        for pred in instruction.PREVS:
            _eq = Equation(eq, 'union', Equation(f'OUT_{pred.index}'))
            eq = _eq
        return eq

    @classmethod
    def OUT(cls, instruction: lang.Inst) -> Equation:
        _defs = cls.definitions(instruction)
        defs = []
        for d in _defs:
            defs.append((instruction.index, d))
        _out = Equation(
            Equation(
                Equation(f'IN_{instruction.index}'),
                'minus',
                cls.definitions_equation(instruction)
            ),
            'union',
            Equation('set', set(defs))
        )
        return _out

    @classmethod
    def definitions_equation(cls, instruction: lang.Inst) -> Equation:
        v = cls.definitions(instruction)
        return Equation('set', v)

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
