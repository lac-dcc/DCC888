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
import json

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


class BasicBlock:
    def __init__(s, instructions):
        s.instructions = instructions
        s.NEXTS = []
        s.PREVS = []

    def add_next(s, nxt):
        s.NEXTS.append(nxt)

    def add_previous(s, prev):
        s.PREVS.append(prev)


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
    (_, cond, trueIndex) = line.split(" ")
    return (cond, int(trueIndex))


def btStack_points_to(bt, i):
    if len(bt) > 0:
        return bt[0].jump_false == i
    else:
        return False


def chain_instructions(i, lines, program, btList, instruction_table):
    if i >= len(lines):
        return
    line = lines[i]
#    if line is "set":
#        (var, value) = parse_set(line)
#        env.set(var, value)
    if is_bt(line):
        (cond, trueIndex) = parse_bt(line)
        inst = lang.Bt(cond)
        inst.jump_to = trueIndex
        btList.append(inst)
        # btStack.appendleft((inst, falseIndex))

    else:
        (dst, opcode, src0, src1) = parse_binop(line)
        inst = match_instruction[opcode](dst, src0, src1)
        # tail may be bt, must deal with this case
    # if btStack_points_to(btStack, i):
    #     btStack[0].set_false_dst(inst)
    #     inst.add_prev(btStack[0])
    #     btStack.popleft()
    if i > 0:
        tail = program[-1]
        tail.add_next(inst)
        inst.add_prev(tail)
    inst.index = i
    instruction_table[i] = inst
    program.append(inst)
    chain_instructions(i+1, lines, program, btList, instruction_table)


def resolve_bts(btList, instruction_table):
    for bt in btList:
        bt.set_true_dst(instruction_table[bt.jump_to])


def pretty_print(program):
    print("----- Control Flow Graph -----")
    print("BB\t| index\t| instruction")
    _pretty_print(program[0], 0)


def _pretty_print(head, bb=0):
    while True:
        if head is lang.Bt:
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


def build_cfg(lines):
    program = []
    btList = []
    instruction_table = dict()
    chain_instructions(0, lines[1:], program, btList, instruction_table)
    resolve_bts(btList, instruction_table)
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


def to_basic_blocks(program):
    leaders = [0]
    bbs = []
    for i in range(len(program)):
        if type(program[i]) is lang.Bt:
            leaders.append(i+1)
            leaders.append(program[i].jump_to)
    bb_map = dict()

    for i in range(len(leaders)):
        begin = leaders[i]
        if i == len(leaders)-1:
            bb = BasicBlock(program[begin:])
        else:
            end = leaders[i+1]
            bb = BasicBlock(program[begin:end])
        bb_map[leaders[i]] = bb
        bbs.append(bb)

    for i in range(len(leaders)-1):
        current_bb = bbs[i]
        last_inst = current_bb.instructions[-1]
        continue_target_leader = leaders[i+1]
        continue_target = bb_map[continue_target_leader]
        current_bb.add_next(continue_target)
        bb_map[continue_target_leader].add_previous(current_bb)

        if type(last_inst) is not lang.Bt:
            continue
        jump_target_leader = last_inst.jump_to
        jump_target = bb_map[jump_target_leader]
        current_bb.add_next(jump_target)
        bb_map[jump_target_leader].add_previous(current_bb)

    return bbs


def bb_to_ssa(bb, environment):
    pass


def to_ssa(program, environment):
    count = dict()
    stack = dict()
    for var in environment.definitions():
        count[var] = 0
        stack[var] = [0]

    bbs = to_basic_blocks(program)
    ssa_program = []
    ssa_environment = lang.Env()
    for bb in bbs:
        ssa_bb, ssa_environment = bb_to_ssa(bb, ssa_environment)
    return (ssa_program, ssa_environment)
