#!/usr/bin/env python3
import sys
import parser
from ssa_form import PhiFunction
from solution import to_ssa


def print_program(program):
    for inst in program:
        print(inst.index, end=': ')
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
    print_program(ssa_program)


if __name__ == "__main__":
    run_test()
