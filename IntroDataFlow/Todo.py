import lang
from typing import List
from Parser import SAResult, StaticAnalysis


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

    Since the program starts with a set environment, definitions from said
    environment are said to come from instruction -1.

    >>> program_lines = [
    ... '{"a": 1, "b": 2}',
    ... 'x = add a b',
    ... 'a = add x a',
    ... 'b = add a x',
    ... ]
    >>> expected_result = SAResult([
    ...     InstInOut(0,
    ...         set([(-1, 'a'), (-1, 'b')]),
    ...         set([(-1, 'a'), (-1, 'b'), (0, 'x')])
    ...     ),
    ...     InstInOut(1,
    ...         set([(-1, 'a'), (-1, 'b'), (0, 'x')]),
    ...         set([(1, 'a'), (-1, 'b'), (0, 'x')])
    ...     )),
    ...     InstInOut(2,
    ...         set([(1, 'a'), (-1, 'b'), (0, 'x')])
    ...         set([(1, 'a'), (1, 'b'), (0, 'x')])
    ...     )),
    ... ])
    >>> program, env = build_cfg(program_lines)
    >>> result = Liveness.run(program)
    >>> result == expected_result
    True
    """

    @classmethod
    def run(cls, program: List[lang.Inst]) -> SAResult:
        """
        TODO: Implement reaching definitions here.
        you may implement any auxiliary class methods.
        as long as 'run' returns an SAResult value.
        """
        raise NotImplementedError
