#!/usr/bin/env python3
import sys
import parser
from ssa_form import PhiFunction
from todo import to_ssa


def print_inst(inst):
    if type(inst) is PhiFunction:
        print(f'{inst.dst} = phi({inst.srcs})')
    else:
        op = parser.rev_match_instruction[type(inst)]
        if op == 'bt':
            print(f'bt {inst.cond} {inst.jump_to}')
        else:
            print(f'{inst.dst} = {op} {inst.src0} {inst.src1}')


def run_test():
    lines = sys.stdin.readlines()
    program, env = parser.build_cfg(lines)
    ssa_program, env = to_ssa(program, env)
    i = 0
    for inst in ssa_program:
        print(i, end=': ')
        print_inst(inst)
        i += 1


if __name__ == "__main__":
    run_test()
