class ConstraintEnv:
    def __init__(s, env: dict):
        s.env = env

    def get(s, id: str) -> set:
        return s.env[id]

    def update(s, id: str, value: set):
        if s.env[id] == value:
            return False
        s.env[id] = value
        return True


class Equation:
    """
    Equations represent generic set operations which can be recursively
    combined.
    >>> env = ConstraintEnv({'x': {'1','2','3'}, 'y':{'4'}})
    >>> x = Equation('x')
    >>> y = Equation('y')
    >>> eq1 = Equation(x, 'union', y)
    >>> eq2 = Equation(eq1, 'minus', Equation('set', '2,3'))
    >>> eq2.solve(env) == {'1', '4'}
    True

    Note that Equations do no have special meaning in the context of data flow
    analysis. Use the Constraint API to represent data flow equations.
    """

    def __init__(self, left, op="", right=None):
        self.left = left
        self.op = op
        self.right = right

    def solve(s, env: ConstraintEnv):
        if s.left == "empty":
            return set()
        elif s.left == "set":
            return set(s.op.split(','))
        elif s.op == "":
            return env.get(s.left)
        else:
            return s.opTable.get(s.op)(s.left, s.right, env)

    def Union(left, right, env: ConstraintEnv):
        return left.solve(env) | right.solve(env)

    def Minus(left, right, env: ConstraintEnv):
        return left.solve(env) - right.solve(env)

    def Inter(left, right, env: ConstraintEnv):
        return left.solve(env).intersection(right.solve(env))

    opTable = {
        "union": Union,
        "minus": Minus,
        "inter": Inter,
    }


class Constraint:
    """
    Constraints are named equations bound to a mutable environment. They
    represent data flow analysis constraints regarding IN and OUT sets.
    >>> env = ConstraintEnv({'x': {}, 'y':{4}, 'z': {2,3}})
    >>> x = Constraint('x', Equation(Equation('y'), 'union', Equation('z')))
    >>> x.eval(env)
    >>> env.get('x') == {2, 3, 4}
    True

    Note that, while Equations return a resulting set based on its operations,
    Constraint objects actually update their environment, since a Constraint's
    value may influence others.
    """
    def __init__(s, id, eq):
        s.id = id
        s.eq = eq

    def eval(s, env):
        return env.update(s.id, s.eq.solve(env))


_env = dict()
for i in range(1, 7):
    _env[f'IN_{i}'] = set()
    _env[f'OUT_{i}'] = set()

env = ConstraintEnv(_env)
constraints = [
    Constraint('IN_1', Equation('set', '')),
    Constraint('IN_2',
                Equation(Equation('OUT_1'), 'union', Equation('OUT_3'))),
    Constraint('IN_3', Equation('OUT_2')),
    Constraint('IN_4',
                Equation(Equation('OUT_1'), 'union', Equation('OUT_5'))),
    Constraint('IN_5', Equation('OUT_4')),
    Constraint('IN_6',
                Equation(Equation('OUT_2'), 'union', Equation('OUT_4'))),
    Constraint('OUT_1', Equation('IN_1')),
    Constraint('OUT_2', Equation('IN_2')),
    Constraint(
        'OUT_3',
        Equation(
            Equation(Equation('IN_3'), 'minus', Equation('set', '3, 5, 6')),
            'union',
            Equation('set', '3')
        )
    ),
    Constraint('OUT_4', Equation('IN_4')),
    Constraint(
        'OUT_5',
        Equation(
            Equation(Equation('IN_5'), 'minus', Equation('set', '3, 5, 6')),
            'union',
            Equation('set', '5')
        )
    ),
    Constraint(
        'OUT_6',
        Equation(
            Equation(Equation('IN_6'), 'minus', Equation('set', '3, 5, 6')),
            'union',
            Equation('set', '6')
        )
    ),
]


def chaotic_iterations(constraints, env):
    while True:
        count = 0
        for i in range(1, len(constraints)+1):
            if not constraints[i-1].eval(env):
                count += 1
        if count == len(constraints):
            break
    print(env.env)


# chaotic_iterations(constraints, env)
