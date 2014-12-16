from collections import namedtuple
import itertools
from functools import wraps


HexBase = namedtuple('Hex', ('x', 'z'))


class Hex(HexBase):
    @property
    def y(self):
        return -self.x + self.z

    def neighbours(self):
        for x, z in itertools.permutations((-1, 0, 1), 2):
            yield Hex(self.x + x, self.z + z)

    def distance(self, hex):
        return (abs(self.x - hex.x) +
                abs(self.y - hex.y) +
                abs(self.z - hex.z)) / 2

    def is_adjacent(self, hex):
        return self.distance(hex) == 1


class HexGroup(tuple):
    MAX_LENGTH = 3

    def is_valid(self):
        return 1 <= len(self) <= self.MAX_LENGTH


def queryset(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        return HexQuerySet(result)
    return wrapper


class HexQuerySet(dict):
    def __init__(self, states):
        for hex, state in states:
            self[hex] = state

    @queryset
    def neighbours(self, hex):
        hex = Hex(*hex)
        return ((neighbour, self[neighbour]) for neighbour in hex.neighbours()
                if neighbour in self)

    @queryset
    def by_state(self, state):
        return ((hex, s) for (hex, s) in self.items() if s == state)

    @queryset
    def not_empty(self):
        return ((hex, s) for (hex, s) in self.items() if s is not None)

    @queryset
    def by_axis(self, x=None, y=None, z=None):
        for hex, state in self.items():
            if all((x is None or hex.x == x,
                    y is None or hex.y == y,
                    z is None or hex.z == z)):
                yield hex, state


class BaseGrid(dict):
    BLACK = True
    WHITE = False
    REPR = {
        BLACK: '@',
        WHITE: 'O',
        None: '.',
    }

    def __init__(self, r):
        self.radius = r
        for x in self.axis_range():
            for z in self.axis_range(x):
                self[Hex(x, z)] = None

    @property
    def query(self):
        return HexQuerySet(self.items())

    def axis_range(self, v=0):
        r = self.radius
        start = max(-r+v, -r)
        stop = min(r+v, r)
        return range(start+1, stop)

    def groups(self, state, lengths=None):
        if lengths is None:
            lengths = [1, 2, 3]
        groups = set()
        for axis, row in itertools.product(('x', 'y', 'z'), self.axis_range()):
            conseq = self.query.by_state(state).by_axis(**{axis: row}).keys()
            groups.update(conseq)
        return groups

    def __repr__(self):
        board = ((self.REPR[self[(x, z)]] for x in self.axis_range(z))
                 for z in self.axis_range())
        board = (' '.join(row).center(self.radius*4) for row in board)
        return '\n'.join(reversed(list(board)))
