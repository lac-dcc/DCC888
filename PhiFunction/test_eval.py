import parser
import ssa_form
import solution


def getprog(progname):
    with open(f"programs/{progname}.lang") as f:
        lines = f.readlines()
    return parser.build_cfg(lines)


origprog, origenv = getprog("big_branch")
parser.interp(origprog[0], origenv, "solution in original form")
prog, env = getprog("big_branch")
sol, solenv = solution.to_ssa(prog, env)
parser.interp(sol[0], solenv, "solution in ssa_form")
