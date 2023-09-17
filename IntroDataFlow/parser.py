"""
Parsing mechanism for .lang files
This module takes into account the language specification in lang.py
and implements a simple interpreter, as well as an exemplary Static
Analysis strategy. The most important functions are "run", which takes a
.lang file name and interprets the inheld program, as well as "run_analysis",
which takes both the .lang file name and the strategy class as input to
run an abstract interpretation of the program.
"""
import lang
from collections import deque
import json
from abc import ABC, abstractclassmethod
from typing import List, Set
from worklist import ConstraintEnv, Constraint, Equation, chaotic_iterations

# Navigation:
# - Parsing
# - Satic Analysis

# Parsing ---------------------------------------------------------------------

match_instruction = {
    "add": lang.Add,
    "mul": lang.Mul,
    "lth": lang.Lth,
    "geq": lang.Geq,
    "bt":  lang.Bt
}
rev_match_instruction = {
    lang.Add: "add",
    lang.Mul: "mul",
    lang.Lth: "lth",
    lang.Geq: "geq",
    lang.Bt:  "bt"
}


def parse_set(line):
    (s, var, value) = line.split(" ")
    return (var, int(value))


def is_bt(line):
    return line.split(" ")[0] == "bt"


def parse_binop(line):
    (dst, expr) = line.split(" = ")
    (opcode, var, value) = expr.split(" ")
    return (dst, opcode, var, value.strip())


def parse_bt(line):
    (_, cond, trueIndex, falseIndex) = line.split(" ")
    return (cond, int(trueIndex), int(falseIndex))


def btStack_points_to(bt, i):
    if len(bt) > 0:
        return bt[0].jump_to == i
    else:
        return False


def chain_instructions(i, lines, program, btStack):
    if i >= len(lines):
        return
    line = lines[i]
#    if line is "set":
#        (var, value) = parse_set(line)
#        env.set(var, value)
    if is_bt(line):
        (cond, trueIndex, falseIndex) = parse_bt(line)
        inst = lang.Bt(cond)
        inst.jump_to = falseIndex
        btStack.appendleft(inst)
        # btStack.appendleft((inst, falseIndex))

    else:
        (dst, opcode, src0, src1) = parse_binop(line)
        inst = match_instruction[opcode](dst, src0, src1)
        # tail may be bt, must deal with this case
    if btStack_points_to(btStack, i):
        btStack[0].set_true_dst(inst)
        inst.add_prev(btStack[0])
        btStack.popleft()
    else:
        if i > 0:
            tail = program[-1]
            tail.add_next(inst)
            inst.add_prev(tail)
    inst.index = i
    program.append(inst)
    chain_instructions(i+1, lines, program, btStack)


def pretty_print(program):
    print("----- Control Flow Graph -----")
    print("BB\t| index\t| instruction")
    _pretty_print(program[0], 0)


def _pretty_print(head, bb=0):
    while True:
        if type(head) == lang.Bt:
            print(f'{bb}\t| {head.index}\t| '
                  f'br {head.cond} {head.index+1} '
                  f'{head.jump_to}\n')
            _pretty_print(head.NEXTS[0], bb+1)
            _pretty_print(head.NEXTS[1], bb+2)
            break
        else:
            print(f'{bb}\t| {head.index}\t| '
                  f'{head.dst} = '
                  f'{rev_match_instruction[type(head)]} '
                  f'{head.src0} {head.src1}')
            if len(head.NEXTS) == 0:
                print("")
                break
            head = head.NEXTS[0]


def run(file_name):
    with open(file_name) as f:
        lines = f.readlines()
    (program, environment) = build_cfg(lines)
    interp(program[0], environment, "resulting environment")


def run_analysis(file_name, analysis):
    with open(file_name) as f:
        lines = f.readlines()
    (program, environment) = build_cfg(lines)
    result = analysis.run(program)
    return result


def build_cfg(lines):
    program = []
    btStack = deque()
    chain_instructions(0, lines[1:], program, btStack)
    envDict = json.loads(lines[0])
    environment = lang.Env()
    for (k, v) in envDict.items():
        environment.set(k, v)
    return (program, environment)


def interp(instruction, environment, title):
    """
    This function evaluates a program until there is no more instructions to
    evaluate.
    """
    if instruction:
        instruction.eval(environment)
        interp(instruction.get_next(), environment, title)
    else:
        print(f'-------- {title} --------')
        environment.dump()


# Static Analysis -------------------------------------------------------------
"""
Three data types have been defined to orient any Static Analysis
implementation.

- First, the IN/OUT sets of each instruction are represented
  through a single InstInOut object, which also contains the instruction's
  index as means of identification.

- The SAResult type indicates what should be returned by Static Analysis
  algorithms, which is a list of InstInOut. It is implemented as an ordered
  list by index, which relieves any analysis implementation from this concern.

- The StaticAnalysis type represent a Static Analysis strategy. Any
  implementation should inherit from this class and implement its "run"
  interface.
"""


class InstInOut:
    def __init__(s, instNum: int, inSet: Set[str], outSet: Set[str]):
        s.index = instNum
        s.inSet = inSet
        s.outSet = outSet

    def __str__(s):
        return f'{s.index}\tIN: {s.inSet}\n\tOUT: {s.outSet}'

    def __eq__(self, o):
        if self.inSet != o.inSet:
            return False
        if self.outSet != o.outSet:
            return False
        return True


class SAResult(List):
    def __init__(self, iterable):
        super().__init__(iterable)

    def append(s, item: InstInOut):
        super().append(item)
        super().sort(key=lambda x: x.index)

    def __eq__(self, o):
        for i in range(len(self)):
            if self[i] != o[i]:
                return False
        return True

    def print(s):
        for i in s:
            print(i)


class StaticAnalysis(ABC):
    @abstractclassmethod
    def run(cls, program: List[lang.Inst]) -> SAResult:
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
    >>> expected_result = SAResult([
    ... InstInOut(0, set(['a', 'b']), set(['a', 'x'])),
    ... InstInOut(1, set(['a', 'x']), set(['a', 'x'])),
    ... InstInOut(2, set(['a', 'x']), set()),
    ... InstInOut(3, set(['a', 'x']), set()),
    ... ])
    >>> program, env = build_cfg(program_lines)
    >>> result = Liveness.run(program)
    >>> result == expected_result
    True
    """
    @classmethod
    def run(cls, program: List[lang.Inst]) -> SAResult:
        # result = cls.IN(program[0])
        constraints = cls.build_constraints(program)
        [print(str(c)) for c in constraints]
        env = cls.build_constraint_env(program)
        chaotic_iterations(constraints, env)
        return env

    @classmethod
    def v_equation(cls, instruction: lang.Inst) -> Equation:
        v = cls._v(instruction)
        if len(v) > 0:
            v = [str(i) for i in v]
            v = ",".join(v)
            return Equation('set', f'{v}')
        else:
            return Equation('empty')

    @classmethod
    def vs_equation(cls, instruction: lang.Inst) -> Equation:
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
            _in = Equation(
                Equation(
                    Equation(f'OUT_{instruction.index}'),
                    'minus',
                    cls.v_equation(instruction)
                ),
                'union',
                cls.vs_equation(instruction)
            )
            constraints.append(
                Constraint(f'IN_{instruction.index}', _in)
            )

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
        result, _out = cls.OUT(instruction)
        _in = _out - cls._v(instruction)
        _in = _in | cls.vars(instruction)
        instInOut = InstInOut(instruction.index, _in, _out)
        # return [instInOut] + result
        result.append(instInOut)
        return result

    @classmethod
    def OUT(cls, instruction):
        if len(instruction.NEXTS) == 0:
            # print(f'{instruction.index}\t|out: {set()}')
            return SAResult([]), set()
        else:
            result = SAResult([])
            out = set()
            for nxt in instruction.NEXTS:
                _result = cls.IN(nxt)
                if len(_result) == 0:
                    continue
                _in = _result[0].inSet
                result += _result
                out = out | _in
            # print(f'{instruction.index}\t|out: {out}')
            # instruction.OUT = out
            return result, out

    @classmethod
    def _v(cls, instruction):
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
