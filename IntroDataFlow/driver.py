import sys

import lang
import todo

def test(case, args):
    if case == 0:
        print(VPL_mSort.ll2py(VPL_mSort.py2ll(args)))
    elif case == 1:
        print(VPL_mSort.size(VPL_mSort.py2ll(args)))
    elif case == 2:
        print(VPL_mSort.sorted(VPL_mSort.py2ll(args)))
    elif case == 3:
        print(VPL_mSort.sorted(VPL_mSort.py2ll(args)))
    elif case == 4:
        print(VPL_mSort.sum(VPL_mSort.py2ll(args)))
    elif case == 5:
        print(VPL_mSort.ll2py(VPL_mSort.mSort(VPL_mSort.py2ll(args))))
    elif case == 6:
        print(VPL_mSort.max(VPL_mSort.py2ll(args)))
    elif case == 7:
        print(VPL_mSort.get(VPL_mSort.py2ll(args[1:]), args[0]))
    else:
        print("Unknown case: ", case)

for line in sys.stdin:
    inps = [int(x) for x in list(line.split(" "))]
    case = inps[0]
    args = inps[1:]
    test(case, args)
