class RestrictionEnv:
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
    >>> env = RestrictionEnv({'x': {'1','2','3'}, 'y':{'4'}})
    >>> x = Equation('x')
    >>> y = Equation('y')
    >>> eq1 = Equation(x, 'union', y)
    >>> eq2 = Equation(eq1, 'minus', Equation('set', '2,3'))
    >>> eq2.solve(env) == {'1', '4'}
    True
    """

    def __init__(self, left, op="", right=None):
        self.left = left
        self.op = op
        self.right = right

    def solve(s, env: RestrictionEnv):
        if s.left == "set":
            return set(s.op.split(','))
        elif s.op == "":
            return env.get(s.left)
        else:
            return s.opTable.get(s.op)(s.left, s.right, env)

    def Union(left, right, env: RestrictionEnv):
        return left.solve(env) | right.solve(env)

    def Minus(left, right, env: RestrictionEnv):
        return left.solve(env) - right.solve(env)

    def Inter(left, right, env: RestrictionEnv):
        return left.solve(env).intersection(right.solve(env))

    opTable = {
        "union": Union,
        "minus": Minus,
        "inter": Inter,
    }


class Restriction:
    """
    >>> env = RestrictionEnv({'x': {}, 'y':{4}, 'z': {2,3}})
    >>> x = Restriction('x', Equation(Equation('y'), 'union', Equation('z')))
    >>> x.eval(env)
    >>> env.get('x') == {2, 3, 4}
    True
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

env = RestrictionEnv(_env)
restrictions = [
    Restriction('IN_1', Equation('set', '')),
    Restriction('IN_2',
                Equation(Equation('OUT_1'), 'union', Equation('OUT_3'))),
    Restriction('IN_3', Equation('OUT_2')),
    Restriction('IN_4',
                Equation(Equation('OUT_1'), 'union', Equation('OUT_5'))),
    Restriction('IN_5', Equation('OUT_4')),
    Restriction('IN_6',
                Equation(Equation('OUT_2'), 'union', Equation('OUT_4'))),
    Restriction('OUT_1', Equation('IN_1')),
    Restriction('OUT_2', Equation('IN_2')),
    Restriction(
        'OUT_3',
        Equation(
            Equation(Equation('IN_3'), 'minus', Equation('set', '3, 5, 6')),
            'union',
            Equation('set', '3')
        )
    ),
    Restriction('OUT_4', Equation('IN_4')),
    Restriction(
        'OUT_5',
        Equation(
            Equation(Equation('IN_5'), 'minus', Equation('set', '3, 5, 6')),
            'union',
            Equation('set', '5')
        )
    ),
    Restriction(
        'OUT_6',
        Equation(
            Equation(Equation('IN_6'), 'minus', Equation('set', '3, 5, 6')),
            'union',
            Equation('set', '6')
        )
    ),
]


def chaotic_iterations(restrictions, env):
    while True:
        count = 0
        for i in range(1, len(restrictions)+1):
            if not restrictions[i-1].eval(env):
                count += 1
        if count == len(restrictions):
            break
    print(env.env)


chaotic_iterations(restrictions, env)


# def build_restrictions(program):
#     restrictions_list = []
#     for instruction in program:
#         restriction_name = f'IN_{str(instruction.index)}'
