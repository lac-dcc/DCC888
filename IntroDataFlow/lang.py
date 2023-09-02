"""
Introduction to Data-Flow Analysis.

This file contains the implementation of a simple interpreter of low-level
instructions. The interpreter takes a program, represented as its first
instruction, plus an environment, which is a stack of bindings. Bindings are
pairs of variable names and values. New bindings are added to the stack whenever
new variables are defined. Bindings are never removed from the stack. In this
way, we can inspect the history of state transformations caused by the
interpretation of a program.

This file uses doctests all over. To test it, just run python 3 as follows:
"python3 -m doctest main.py". The program uses syntax that is excluive of
Python 3. It will not work with standard Python 2.

Example:
    TODO: add another test here!

    env = {a:3, b:3}
    x = add a b
    y = mul x x
"""

from collections import deque
import json

class Env:
    """
    A table that associates variables with values. The environment is
    implemented as a stack, so that previous bindings of a variable V remain
    available in the environment if V is overassigned.

    Example:
        >>> e = Env()
        >>> e.set("a", 2)
        >>> e.set("a", 3)
        >>> e.get("a")
        3

        >>> e = Env()
        >>> e.set("a1", 3)
        >>> e.set("a0", 2)
        >>> e.get_first(['a2', 'a0', 'a1'])
        2

        >>> e = Env({"b": 5})
        >>> e.set("a", 2)
        >>> e.get("a") + e.get("b")
        7
    """
    def __init__(s, initial_args={}):
        s.env = deque()
        for var, value in initial_args.items():
            s.env.appendleft((var, value))

    def get(s, var):
        """
        Finds the first occurrence of variable 'var' in the environment stack,
        and returns the value associated with it.
        """
        return s.get_or_raise(lambda var_name: var_name == var)

    def get_first(s, vars):
        """
        Finds the first occurrence of any variable in the iterator 'vars'.
        It then returns the  value associated with that occurrence. This method
        is useful to implement phi-functions: when evaluating an instruction
        such as 'x = phi(x0, x1)', we can look for either 'x0' or 'x1' in the
        environment. The last assigned variable will be the first that we shall
        find on the stack.
        """
        return s.get_or_raise(lambda var_name: var_name in vars)

    def get_or_raise(self, pred):
        """
        This method is an auxiliary routine used within both 'get' and
        'get_first'. It takes the predicate with the condition used to find the
        correct binding.
        """
        val = next((value for (e_var, value) in self.env if pred(e_var)), None)
        if val != None:
            return val
        else:
            raise LookupError(f"Absent key {val}")

    def set(s, var, value):
        """
        This method adds 'var' to the environment, by placing the binding
        '(var, value)' onto the top of the environment stack.
        """
        s.env.appendleft((var, value))

    def dump(s):
        """
        Prints the contents of the environment. This method is mostly used for
        debugging purposes.
        """
        for (var, value) in s.env:
            print(f"{var}: {value}")

class Inst:
    """
    The representation of instructions. All that an instruction has, that is
    common among all the instructions, is the next_inst attribute. This
    attribute determines the next instruction that will be fetched after this
    instruction runs.
    """
    def __init__(s):
        s.NEXTS = []
        s.PREVS = []
        s.IN = set()
        s.OUT = set()
    def add_next(s, next_inst):
        s.NEXTS.append(next_inst)
    def add_prev(s, prev_inst):
        s.PREVS.append(prev_inst)
    def get_next(s):
        if len(s.NEXTS) > 0:
            return s.NEXTS[0]
        else:
            return None

class BinOp(Inst):
    """
    The general class of binary instructions. These instructions define a
    value, and use two values. As such, it contains a routine to extract the
    defined value, and the list of used values.
    """
    def __init__(s, dst, src0, src1):
        s.dst = dst
        s.src0 = src0
        s.src1 = src1
        super().__init__()
    def definition(s):
        return s.dst
    def uses(s):
        return [s.src0, s.src1]


class Add(BinOp):
    """
    Example:
        >>> a = Add("a", "b0", "b1")
        >>> e = Env({"b0":2, "b1":3})
        >>> a.eval(e)
        >>> e.get("a")
        5

        >>> a = Add("a", "b0", "b1")
        >>> a.get_next() == None
        True
    """
    def eval(s, env):
        env.set(s.dst, env.get(s.src0) + env.get(s.src1))

class Mul(BinOp):
    """
    Example:
        >>> a = Mul("a", "b0", "b1")
        >>> e = Env({"b0":2, "b1":3})
        >>> a.eval(e)
        >>> e.get("a")
        6
    """
    def eval(s, env):
        env.set(s.dst, env.get(s.src0) * env.get(s.src1))

class Lth(BinOp):
    """
    Example:
        >>> a = Lth("a", "b0", "b1")
        >>> e = Env({"b0":2, "b1":3})
        >>> a.eval(e)
        >>> e.get("a")
        True
    """
    def eval(s, env):
        env.set(s.dst, env.get(s.src0) < env.get(s.src1))

class Geq(BinOp):
    """
    Example:
        >>> a = Geq("a", "b0", "b1")
        >>> e = Env({"b0":2, "b1":3})
        >>> a.eval(e)
        >>> e.get("a")
        False
    """
    def eval(s, env):
        env.set(s.dst, env.get(s.src0) >= env.get(s.src1))

class Bt(Inst):
    """
    This is a Branch-If-True instruction, which diverts the control flow to the
    'true_dst' if the predicate 'pred' is true, and to the 'false_dst'
    otherwise.

    Example:
        TODO: add a test here!
    """
    def __init__(s, cond, true_dst=None, false_dst=None):
        s.cond = cond
        s.true_dst = true_dst
        s.false_dst = false_dst
        super().__init__()
    def definition(s):
        return None
    def uses(s):
        return [s.cond]
    def set_true_dst(s, true_dst):
        s.true_dst = true_dst
    def set_false_dst(s, false_dst):
        s.false_dst = false_dst
    def eval(s, env):
        """
        The evaluation of the condition sets the next_iter to the instruction.
        This value determines which successor instruction is to be evaluated.
        Any values greater than 0 are evaluated as True, while 0 corresponds to
        False.
        """
        if env.get(s.cond):
            s.next_iter = 0
        else:
            s.next_iter = 1
    def get_next(s):
        return s.NEXTS[s.next_iter]
