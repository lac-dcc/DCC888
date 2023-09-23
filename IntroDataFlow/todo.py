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
        """
        TODO: given a program, run through its instructions and create IN and
        OUT constraints for Reaching Definitions. Then, use chaotic iterations
        to solve said constraints.
        You may implement any auxiliary class methods,
        as long as 'run' returns the correct ConstraintEnv.

        The building blocks for the implementation are provided in the
        staticanalysis module: Equation, Constraint, ConstraintEnv,
        chaotic_iterations.

        Use the Liveness implementation found in static_analysis.py
        as an example.
        """
        raise NotImplementedError
