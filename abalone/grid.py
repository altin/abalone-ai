from collections import namedtuple
import itertools
from functools import wraps

from . import config


HexBase = namedtuple('HexBase', ('x', 'z'))


class Hex(HexBase):
    directions = [(x, -x-z, z) for x, z in
                  itertools.permutations((-1, 0, 1), 2)]

    def __new__(cls, x=None, y=None, z=None):
        if x is None:
            x = y-z
        elif y is None:
            y = -x-z
        elif z is None:
            z = -x-y
        return super(cls, Hex).__new__(cls, x, z)

    @property
    def y(self):
        return -self.x - self.z

    def __repr__(self):
        return 'Hex(x={self.x}, y={self.y}, z={self.z})'.format(self=self)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z

    def neighbours(self):
        for x, y, z in self.directions:
            yield Hex(self.x + x, self.z + z)

    def distance(self, hex):
        return (abs(self.x - hex.x) +
                abs(self.y - hex.y) +
                abs(self.z - hex.z)) / 2

    def is_adjacent(self, hex):
        return self.distance(hex) == 1

    def direction(self, hex):
        return (hex.x - self.x, hex.y - self.y, hex.z - self.z)


def queryset(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        results = func(self, *args, **kwargs)
        results = ((hex, self[hex]) for hex in results)
        return HexQuerySet(results)
    return wrapper


class HexQuerySet(dict):
    def __init__(self, states):
        for hex, state in states:
            self[hex] = state

    @queryset
    def neighbours(self, hex):
        hex = Hex(*hex)
        return (neighbour for neighbour in hex.neighbours()
                if neighbour in self)

    @queryset
    def by_state(self, state):
        return (hex for (hex, s) in self.iteritems() if s == state)

    @queryset
    def not_empty(self):
        return (hex for (hex, s) in self.iteritems() if s is not None)

    @queryset
    def by_axis(self, x=None, y=None, z=None):
        for hex, state in self.iteritems():
            if all((x is None or hex.x == x,
                    y is None or hex.y == y,
                    z is None or hex.z == z)):
                yield hex

    @queryset
    def by_vector(self, hex, direction, distance):
        moves = ((axis*step for axis in direction) for step in range(distance))
        places = ((b+c for b, c in zip(hex, move)) for move in moves)
        places = {Hex(*list(place)) for place in places}
        return set(self.keys()) & places

    def populations(self, state):
        """
        Returns sets of interconnected hexes.
        """
        unchecked = set(self.by_state(state).keys())
        while unchecked:
            neighbours = {unchecked.pop()}
            group = set()
            while neighbours:
                hex = neighbours.pop()
                unchecked.discard(hex)
                group.add(hex)
                neighbours.update(set(hex.neighbours()) & unchecked)
            yield group

    @queryset
    def population(self, hex):
        return next((pop for pop in self.populations(self[hex]) if hex in pop))

    def are_connected(self):
        """
        Returns wether the current QS hexes are all connected or not.
        """
        # Check that all hexes are or white or black
        states = set(self.values())
        if len(states) != 1 or states == {None}:
            return False
        populations = self.populations(states.pop())
        return len(list(populations)) == 1

    def hex_blocks(self, hex, lengths=None):
        """
        Returns all the possible blocks in which this hex could be moved.
        """
        if lengths is None:
            lengths = config.GROUP_LENGTHS

        blocks = set()
        population = self.population(hex)
        neighbours = population.neighbours(hex)
        directions = (hex.direction(n) for n in neighbours)
        directions = itertools.chain(directions, [(0, 0, 0)])
        for direction, distance in itertools.product(directions, lengths):
            block = population.by_vector(hex, direction, distance)
            block = tuple(sorted(block.keys()))
            blocks.add(block)
        return blocks

    def blocks(self, state, lengths=None):
        return {self.hex_blocks(hex, lengths) for hex in self.by_state(state)}


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
        return HexQuerySet(self.iteritems())

    def axis_range(self, v=0):
        r = self.radius
        start = max(-r-v, -r)
        stop = min(r-v, r)
        return range(start+1, stop)

    def __repr__(self):
        board = ((self.REPR[self[(x, z)]] for x in self.axis_range(z))
                 for z in self.axis_range())
        board = (' '.join(row).center(self.radius*4) for row in board)
        return '\n'.join(list(board))
