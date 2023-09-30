#!/usr/bin/env python3
import sys
import parser
import static_analysis as sa
import worklist


def run_test():
    lines = sys.stdin.readlines()
    program, _ = parser.build_cfg(lines)
    cs = sa.Liveness.build_constraints(program)
    env = sa.Liveness.build_constraint_env(program)
    sol = worklist.solve_worklist(cs, env)
    sol.print()


if __name__ == "__main__":
    run_test()
