from collections import namedtuple
import itertools
from functools import wraps

from . import config


HexBase = namedtuple('HexBase', ('x', 'z'))


class Hex(HexBase):
    @property
    def y(self):
        return -self.x - self.z

    def __repr__(self):
        return 'Hex(x={self.x}, y={self.y}, z={self.z})'.format(self=self)

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
    def is_valid(self):
        return len(self) in config.GROUP_LENGTHS


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
        return ((hex, s) for (hex, s) in self.iteritems() if s == state)

    @queryset
    def not_empty(self):
        return ((hex, s) for (hex, s) in self.iteritems() if s is not None)

    @queryset
    def by_axis(self, x=None, y=None, z=None):
        for hex, state in self.iteritems():
            if all((x is None or hex.x == x,
                    y is None or hex.y == y,
                    z is None or hex.z == z)):
                yield hex, state

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

    def axial_supporters(self, hex):
        """
        Returns three sets (one per axis) with the hexes that support (are
        directly conected and not too far away) this hex.
        """
        for axis in 'x', 'y', 'z':
            fix = getattr(hex, axis)
            in_line = self.by_axis(**{axis: fix})
            in_line_pops = in_line.populations(self[hex])
            # Only one inline-population should fulfill this
            supporters = next((pop for pop in in_line_pops if hex in pop))
            # +1 because we want to exclude the ones that are
            # max(GROUP_LENGTHS) away and include the hex itself
            supporters = set((sup for sup in supporters
                              if hex.distance(sup)+1 in config.GROUP_LENGTHS))
            yield supporters

    def blocks(self, hex, lengths=None):
        """
        Returns a set of all the possible blocks in which this hex could be
        moved.
        """
        if lengths is None:
            lengths = config.GROUP_LENGTHS
        blocks = set()
        for supporters in self.axial_supporters(hex):
            for length in lengths:
                for comb in itertools.combinations(supporters, length):
                    state = ((h, self[hex]) for h in comb)
                    if hex in comb and HexQuerySet(state).are_connected():
                        blocks.add(comb)
        return blocks


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

    def groups(self, state, lengths=None):
        if lengths is None:
            lengths = config.GROUP_LENGTHS
        groups = set()
        for axis, row in itertools.product(('x', 'y', 'z'), self.axis_range()):
            conseq = self.query.by_state(state).by_axis(**{axis: row}).keys()
            groups.update(conseq)
        return groups

    def __repr__(self):
        board = ((self.REPR[self[(x, z)]] for x in self.axis_range(z))
                 for z in self.axis_range())
        board = (' '.join(row).center(self.radius*4) for row in board)
        return '\n'.join(list(board))
