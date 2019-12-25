import math
import random

class Node:
    """ A node in the game tree. Note wins is always from the viewpoint of playerJustMoved.
        Crashes if state not specified.
    """
    def __init__(self, move = None, parent = None, state = None, player = None):
        self.move = move # the move that got us to this node - "None" for the root node
        self.parentNode = parent # "None" for the root node
        self.childNodes = []
        self.wins = 0
        self.visits = 0
        self.playerJustMoved = player # the only part of the state that the Node needs later
        self.untriedMoves = list(state.moves(self.playerJustMoved)) # future child nodes
        
    def UCTSelectChild(self):
        """ Use the UCB1 formula to select a child node. Often a constant UCTK is applied so we have
            lambda c: c.wins/c.visits + UCTK * sqrt(2*log(self.visits)/c.visits to vary the amount of
            exploration versus exploitation.
        """
        s = sorted(self.childNodes, key = lambda c: c.wins/c.visits + math.sqrt(2*math.log(self.visits)/c.visits))[-1]
        return s
    
    def AddChild(self, m, s):
        """ Remove m from untriedMoves and add a new child node for this move.
            Return the added child node
        """
        n = Node(move = m, parent = self, state = s)
        self.untriedMoves.remove(m)
        self.childNodes.append(n)
        return n
    
    def Update(self, result):
        """ Update this node - one additional visit and result additional wins. result must be from the viewpoint of playerJustmoved.
        """
        self.visits += 1
        self.wins += result

    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.wins) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "]"

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
            s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for _ in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
            s += str(c) + "\n"
        return s

def UCT(rootstate, itermax, player, verbose = False):
    """ Conduct a UCT search for itermax iterations starting from rootstate.
        Return the best move from the rootstate.
        Assumes 2 alternating players (player 1 starts), with game results in the range [0.0, 1.0]."""

    rootnode = Node(state = rootstate, player = player)

    for sim in range(itermax):
        print("Simulation ", sim + 1, "...")
        node = rootnode
        state = rootstate.deep_copy()

        # Select
        while node.untriedMoves == [] and node.childNodes != []: # node is fully expanded and non-terminal
            node = node.UCTSelectChild()
            state.move(*node.move)
            # node.playerJustMoved = not node.playerJustMoved

        # Expand
        if node.untriedMoves != []: # if we can expand (i.e. state/node is non-terminal)
            m = random.choice(node.untriedMoves) 
            state.move(*m)
            # node.playerJustMoved = not node.playerJustMoved
            node = node.AddChild(m, state) # add child and descend tree

        # Rollout - this can often be made orders of magnitude quicker using a state.GetRandomMove() function
        while state.query.check_win(node.playerJustMoved) == False: # while state is non-terminal
            state.move(*random.choice(list(state.moves(node.playerJustMoved, rnd=True))))
            # node.playerJustMoved = not node.playerJustMoved

        # Backpropagate
        while node != None: # backpropagate from the expanded node and work back to the root node
            status = 0
            if state.query.check_win(node.playerJustMoved):
                status = 1.0
            else:
                status = 0.0

            node.Update(status) # state is terminal. Update node with result from POV of node.playerJustMoved
            node = node.parentNode
    
    return sorted(rootnode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited