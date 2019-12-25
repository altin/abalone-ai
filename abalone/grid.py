"""
Handles the representation of hexes (tiles), hex groups and board grids and also
implements all the legal movements logic.
"""
import math
import random
import itertools as it
from numbers import Number
from operator import itemgetter
from functools import wraps
from collections import namedtuple

from . import config
from .utils import split_when

class IllegalMove(Exception):
    pass

HexBase = namedtuple('Hex', ('x', 'z'))

class Hex(HexBase):
    """
    Representation of a hex or tile on the grid.
    """

    directions = [(_x, _z) for _x, _z in  # Collide with attrs
                  it.permutations((-1, 0, 1), 2)]

    @property
    def y(self):
        return -self.x - self.z

    def __add__(self, other):
        return Hex(*[s + o for s, o in zip(self, other)])

    def __rmul__(self, other):
        return self.__mul__(other)

    def __mul__(self, other):
        if isinstance(other, Number):
            return Hex(*[other*axis for axis in self])
        return super(Hex, self).__mul__(other)

    def __neg__(self):
        return Hex(*[-axis for axis in self])

    def neighbours(self):
        """
        Returns an iterator with all the surrounding Hexes.
        """
        for x, z in self.directions:
            yield Hex(x=self.x + x, z=self.z + z)

    def distance(self, hex):
        """
        Returns the moving distance from the specified Hex.
        """
        return (abs(self.x - hex.x) +
                abs(self.y - hex.y) +
                abs(self.z - hex.z)) / 2

    def is_adjacent(self, hex):
        """
        Returns wether the other Hex is adjacent to this.
        """
        return self.distance(hex) == 1

    def direction(self, hex):
        """
        Returns the direction from this Hex to the other.
        """
        return (hex.x - self.x, hex.z - self.z)


class HexBlock(tuple):
    def __new__(cls, *args):
        return super(HexBlock, cls).__new__(cls, *args)

    def is_valid(self):
        """
        Returns wether this HexBlock is valid:
            - it must have a valid length.
            - all the hexes must be adjacent to one another.
            - all the hexes must be aligned in the same direction.
        """
        return all((
            # Must have a valid length
            len(self) in config.GROUP_LENGTHS,
            # Must be adjacent to one another
            all((a.is_adjacent(b) for a, b in zip(self, self[1:]))),
            # Must be in the same direction
            len(set((a.direction(b) for a, b in zip(self, self[1:])))) <= 1
        ))

    @property
    def directions(self):
        """
        Returns the directions of alignment of this HexBlock:
            - all possible directions if the block is a single hex.
            - the two directions of alignement if it's made from more that one
            hex.
        """
        if len(self) == 1:
            for direction in Hex.directions:
                yield direction
        else:
            transition = zip(self, self[1:])
            for a, b in transition:
                yield a.direction(b)
                yield b.direction(a)

    def strength(self, direction):
        """
        Returns the strength of push in a given direction: the amount of hexes
        aligned in that direction
        """
        return len(self) if direction in self.directions else 1

    def sorted(self, direction):
        """
        Returns an HexBlock sorted in the specified direction.
        """
        axis = next((pos for axis, pos in enumerate(direction)))
        return HexBlock(sorted(self, key=itemgetter(axis)))


def queryset(func):
    """
    Returns a HexQuerySet object from an iterator of Hexes.
    """
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
        """
        Returns the neightbours of an Hex.
        """
        return (neighbour for neighbour in hex.neighbours()
                if neighbour in self)

    @queryset
    def by_state(self, state):
        """
        Filters the queryset by state (player colour).
        """
        return (hex for (hex, s) in self.items() if s == state)

    @queryset
    def not_empty(self):
        """
        Filters out all empty hexes.
        """
        return (hex for (hex, s) in self.items() if s is not None)

    @queryset
    def by_axis(self, x=None, z=None):
        """
        Returns hexes on the specified axises.
        """
        for hex, state in self.items():
            if all((x is None or hex.x == x, z is None or hex.z == z)):
                yield hex

    @queryset
    def by_vector(self, hex, direction, distance):
        """
        Returns all the hexes in some direction and until some distance
        beginning on the specified hex.
        """
        moves = ((axis*step for axis in direction) for step in range(distance))
        places = (hex + move for move in moves)
        return set(self.keys()) & set(places)

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
        """
        Returns the set of interconnected hexes where the specified hex lies.
        """
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
        directions = it.chain(directions, [(0, 0, 0)])

        for direction, distance in it.product(directions, lengths):
            block = population.by_vector(hex, direction, distance)
            block = HexBlock(block.keys())

            # Sort blocks to ensure adjacency
            if all(hex[1] == block[0][1] for hex in block):
                block = HexBlock(tuple(sorted(block, key=itemgetter(0))))
            else:
                block = HexBlock(tuple(sorted(block,key=itemgetter(1))))

            blocks.add(block)
        return blocks

    def blocks(self, state, lengths=None):
        """
        Returns all the possible blocks which could be legally moved.
        """
        return {HexBlock(block) for hex in self.by_state(state)
                for block in self.hex_blocks(hex, lengths)}

    @queryset
    def move(self, block, direction):
        """
        Attempts to move the given block in the given direction rising and
        IllegalMove exception if it is not possible because:
            - the specified block isn't correct.
            - the specified direction isn't correct.
            - there is not place enough to move the marbles.
            - enemy is stronger.
            - some marbles would commit suicide.
        """
        if direction not in Hex.directions:
            raise IllegalMove("Incorrect direction")

        if not block.is_valid():
            raise IllegalMove("Incorrect block.")

        # Reorder the block
        block = block.sorted(direction)

        state = self[block[0]]

        # Get the pushing strength
        strength = block.strength(direction)

        # Get the mirror of the block in that direction
        mirror = (hex + strength*Hex(*direction) for hex in block)

        # Split the mirror at the first non-enemy marble
        enemies, others = split_when(lambda h: self.get(h, None) != (not state), mirror)

        # There must be less enemy marbles that own ones
        if not len(block) > len(enemies):
            raise IllegalMove("Enemy is stronger.")

        new_block = set((hex + Hex(*direction) for hex in block))
        
        if direction not in block.directions:
            # Broadside mvoe
            # Disallow broadside moves if any destination hexes are non-empty
            if any((hex in self and self[hex] is not None for hex in new_block)):
                raise IllegalMove("No place enough to move enemy marbles")
        else:
            # Straight/side move
            # Get the first hex position in the direction the block is heading to
            diff = list(new_block.difference(block))
            if diff[0] in others:
                # Disallow straight/side moves if the first destination hex is own marble
                if self.get(diff[0]) is not None:
                    raise IllegalMove("Straight/Side: Attacking own marble.")
            elif diff[0] in enemies:
                # Sumito move
                # Clear all the own and enemy marbles
                for hex in it.chain(block, enemies):
                    self[hex] = None

                new_enemies = [(hex + direction, not state) for hex in enemies
                            if hex + direction in self]
                self.update(new_enemies)
        
        # Clear all the own marbles
        for hex in block:
            self[hex] = None
        
        new_block = [(hex + direction, state) for hex in block]
        if any((hex not in self for hex, state in new_block)):
            raise IllegalMove("Attempting to move off the grid.")
        self.update(new_block)
        return self.keys()

    def marbles(self, state, length=False):
        """
        Returns the number of marbles for a given player.
        """
        marbles = {k: v for k, v in self.items() if v == state}
        if length:
            return len(marbles)
        return marbles
    
    def check_win(self, state):
        """
        Checks if the game is over (opposing player has lost >= GAME_OVER marbles)
        """
        if len(self.marbles(not state)) <= config.GAME_OVER:
            return True
        return False
    
    def center_proximity(self, state):
        """
        Returns the mean distance from each marble to 
        the origin of the grid, for a given player.
        """
        center = Hex(0,0)

        distance = -math.inf
        marbles = self.marbles(state)
        for marble in marbles.keys():
            if distance == -math.inf:
                distance = marble.distance(center)
            else:
                distance += marble.distance(center)
        
        return distance / len(marbles)
    
    def mean_position(self, state):
        """
        Returns the mean position of a player.
        """
        pops = list(self.populations(state))
        avg_hex = -math.inf

        for pop in pops:
            length = len(pop)
            d_avg = sum(d for d, _ in pop) / length
            r_avg = sum(r for _, r in pop) / length
            avg_hex = Hex(d_avg, r_avg)
        
        return avg_hex
    
    def chase(self, state):
        # get current mean pos
        avg = self.mean_position(state)

        # get smallest pop of other player
        pops = list(self.populations(not state))
        pops = sorted(pops, key=lambda x: len(x))
        pop = [pops[0]]
        avg_other = Hex(0,0)

        # calculate position of smallest pop
        for block in pop:
            length = len(block)
            d_avg = sum(d for d, _ in block) / length
            r_avg = sum(r for _, r in block) / length
            avg_other = Hex(d_avg, r_avg)
        
        return avg.distance(avg_other)
    






class BaseGrid(dict):
    BLACK = config.BLACK
    WHITE = config.WHITE
    REPR = {
        BLACK: 'B',
        WHITE: 'W',
        None: '.',
    }

    def __init__(self, r):
        self.radius = r
        for x in self.axis_range():
            for z in self.axis_range(x):
                self[Hex(x=x, z=z)] = None

    @property
    def query(self):
        return HexQuerySet(self.items())

    def axis_range(self, v=0):
        """
        Returns the position range in the specified axis.
        """
        r = self.radius
        start = max(-r-v, -r)
        stop = min(r-v, r)
        return range(start+1, stop)

    @property
    def display(self):
        board = ((self.REPR[self[(x, z)]] for x in self.axis_range(z))
                 for z in self.axis_range())
        board = (' '.join(row).center(self.radius*4) for row in board)
        return '\n'.join(list(board))
    
    def deep_copy(self,raw=False):
        copy = {
                config.WHITE: [(k[0], k[1]) for k, v in self.items() if v == config.WHITE],
                config.BLACK: [(k[0], k[1]) for k, v in self.items() if v == config.BLACK],
        }
        if raw == True:
            return copy
        return AbaloneGrid(copy)

    def move(self, block, direction):
        """
        Attempts to move some block in some direction rising an IllegalMove
        exception if that movement is illegal.
        """
        for block, state in self.query.move(block, direction).items():
            self[block] = state

    def moves(self, state, rnd=False, seed=None):
        """
        Returns all the possible moves for some player.
        """
        lengths = config.GROUP_LENGTHS
        if rnd:
            lengths = random.randrange(lengths[0], lengths[1])
            lengths = range(lengths, lengths + 1)
        if seed:
            if seed.__class__.__name__ == 'method':
                random.seed = seed
            else:
                random.seed(seed)
        
        blocks = list(self.query.blocks(state, lengths))
        for block in blocks:
            for direction in Hex.directions:
                try:
                    self.query.move(block, direction)
                except IllegalMove:
                    pass
                else:
                    yield block, direction





class AbaloneGrid(BaseGrid):
    def __init__(self, initial_position):
        super(AbaloneGrid, self).__init__(config.GRID_RADIUS)
        positions = {position: state
                     for state, positions in initial_position.items()
                     for position in positions}
        self.update(positions)
