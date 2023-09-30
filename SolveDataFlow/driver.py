#!/usr/bin/env python3
import sys
import parser
import static_analysis as sa
from worklist import solve_worklist


def run_test():
    lines = sys.stdin.readlines()
    program, _ = parser.build_cfg(lines)
    result = sa.Liveness.run(program, solve_worklist)
    result.print()


if __name__ == "__main__":
    run_test()
