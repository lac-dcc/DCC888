import lang
from parser import build_cfg
from typing import List, Callable
from static_analysis import ConstraintEnv, Constraint, \
    StaticAnalysis, chaotic_iterations


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
    >>> result.print()
    >>> result == expected_result
    True
    """

    @classmethod
    def run(cls, program: List[lang.Inst]) -> ConstraintEnv:
        env = cls.build_constraint_env(program)
        constraints = cls.build_constraints(program, env)
        env = chaotic_iterations(constraints, env)
        return env

    @classmethod
    def build_constraint_env(cls, program: List[lang.Inst]) -> ConstraintEnv:
        env = dict()
        for i in range(len(program)):
            env[f'IN_{i}'] = set()
            env[f'OUT_{i}'] = set()
        return ConstraintEnv(env)

    @classmethod
    def build_constraints(cls, program: List[lang.Inst], env: ConstraintEnv) \
            -> List[Constraint]:
        constraints = []
        for instruction in program:
            _in = cls.IN(instruction, env)
            constraints.append(
                Constraint(f'IN_{instruction.index}', _in)
            )
            _out = cls.OUT(instruction, env)
            constraints.append(
                Constraint(f'OUT_{instruction.index}', _out)
            )
        return constraints

    @classmethod
    def IN(cls, instruction: lang.Inst, env: ConstraintEnv) -> Callable:
        def _in():
            res = set()
            for pred in instruction.PREVS:
                res = res | env.get(f'OUT_{pred.index}')
            return res

        return _in

    @classmethod
    def OUT(cls, instruction: lang.Inst, env: ConstraintEnv) -> Callable:
        _defs = cls.definitions(instruction)
        defs = []
        for d in _defs:
            defs.append((instruction.index, d))

        return lambda: (env.get(f'IN_{instruction.index}') - _defs) \
            | set(defs)

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
