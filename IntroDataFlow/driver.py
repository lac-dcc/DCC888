import sys
import todo
import parser
import staticanalysis as sa


def run_test():
    lines = sys.stdin.readlines()
    program, _ = parser.build_cfg(lines)
    result = sa.run_analysis_on_program(program, todo.ReachingDefinitions)
    result.print()


if __name__ == "__main__":
    run_test()
