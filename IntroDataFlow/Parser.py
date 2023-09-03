import lang
from collections import deque
import json
from abc import ABC, abstractclassmethod
from typing import List, Set

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


def points_to(bt, i):
    return bt.jump_number == i


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
        inst.jump_number = falseIndex
        btStack.appendleft(inst)
        # btStack.appendleft((inst, falseIndex))

    else:
        (dst, opcode, src0, src1) = parse_binop(line)
        inst = match_instruction[opcode](dst, src0, src1)
        # tail may be bt, must deal with this case
    if points_to(btStack[0], i):
        btStack[0].add_next(inst)
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
                  f'{head.jump_number}\n')
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
    (program, environment) = build_cfg(file_name)
    interp(program[0], environment, "resulting environment")


def run_analysis(file_name, analysis):
    (program, environment) = build_cfg(file_name)
    result = analysis.run(program)
    return result


def build_cfg(file_name):
    with open(file_name) as f:
        lines = f.readlines()
    program = []
    btStack = deque([(None, -1)])
    chain_instructions(0, lines[1:], program, btStack)
    # Pretty print it!
    pretty_print(program)
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

# Static Analysis --------------------------------------------------------------


class InstInOut:
    def __init__(s, instNum: int, inSet: Set[str], outSet: Set[str]):
        s.instNum   = instNum
        s.inSet     = inSet
        s.outSet    = outSet

    def __str__(s):
        return f'{s.instNum}\tIN: {s.inSet}\n\tOUT: {s.outSet}'

SAResult = List[InstInOut]

class StaticAnalysis(ABC):
    @abstractclassmethod
    def run(cls, program: List[lang.Inst]) -> SAResult:
        pass


class Liveness(StaticAnalysis):
    @classmethod
    def run(cls, program) -> SAResult:
        result = cls.IN(program[0])
        return result

    @classmethod
    def IN(cls, instruction):
        result, _out = cls.OUT(instruction)
        # _in = cls.OUT(instruction) - cls._v(instruction)
        _in = _out - cls._v(instruction)
        _in = _in | cls.vars(instruction)
        # instruction.IN = _in
        instInOut = InstInOut(instruction.index, _in, _out)
        print(instInOut)
        # return _in
        return [instInOut] + result

    @classmethod
    def OUT(cls, instruction):
        if len(instruction.NEXTS) == 0:
            # print(f'{instruction.index}\t|out: {set()}')
            return [], set()
        else:
            result = []
            out = set()
            for nxt in instruction.NEXTS:
                _result = cls.IN(nxt)
                _in = result[-1].inSet
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
