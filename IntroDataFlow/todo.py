import lang
from parser import build_cfg
from typing import Callable
from static_analysis import ConstraintEnv, StaticAnalysis


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
    ... 'OUT_1': {(-1, 'b'), (0, 'x'), (1, 'a')},
    ... 'IN_2': {(-1, 'b'), (0, 'x'), (1, 'a')},
    ... 'OUT_2':{(0, 'x'), (1, 'a'), (2, 'b')},
    ... })
    >>> program, env = build_cfg(program_lines)
    >>> result = ReachingDefinitions.run(program)
    >>> result == expected_result
    True
    """

    @classmethod
    def IN(cls, instruction: lang.Inst,
           cEnv: ConstraintEnv,
           env: lang.Env) -> Callable:
        """
        TODO: implement the IN function given each constraint.
        An example for Liveness is implemented at static_analysis.py
        """
        raise NotImplementedError

    @classmethod
    def OUT(cls, instruction: lang.Inst,
            cEnv: ConstraintEnv,
            env: lang.Env) -> Callable:
        """
        TODO: implement the OUT function given each constraint.
        An example for Liveness is implemented at static_analysis.py
        """
        raise NotImplementedError
