'''
Transposition table algorithms
'''
import random
import math
import csv

################################# TRANSPOSITION TABLE #################################
node_count = 0
zobrist = [[[0]*9]*9]*2
table = {}

def initialize_keys():
    '''
    Generate Zobrist hash keys
    '''
    for p in range(0,2):
        for x in range(-4, 5):
            for z in range(-4, 5):
                zobrist[p][x + 4][z + 4] = random.getrandbits(64)- 2**63

def get_key(state):
    '''
    Get the state at the key
    '''
    key = 0
    for player in state:
        p = 0
        if player: p = 0
        else: p = 1

        for coord in state[player]:
            x = coord[0]
            z = coord[1]
            key ^= zobrist[p][x + 4][z + 4]

    return key

def output():
    '''
    Output file
    '''
    open('transposition_table.txt', 'w').close()
    w = csv.writer(open("transposition_table.txt", "w"))
    for key, val in table.items():
        w.writerow([key, val])

########################################################################################

############################# ALPHA-BETA + MOVE ORDER ##################################
# Depth-limited alphabeta search
def alphabeta(board, depth, maximizer, alpha, beta):
    tt_entry = {'move': None, 'value': None, 'flag': None, 'depth': None}
    key = get_key(board.deep_copy(True))
    
    # lookup
    if key in table and table[key]['depth'] >= depth:
        tt_entry = table[key]
        move, flag, value = tt_entry['move'], tt_entry['flag'], tt_entry['value']

        if flag == 'lower':
            return max(alpha, value), move
        elif flag == 'upper':
            return min(beta, value), move
    
    if board.query.check_win(maximizer):
        return math.inf if maximizer else -math.inf, -1
    elif depth == 0:
        return heuristic(board), -1

    if maximizer:
        score = -math.inf
        def shouldReplace(x): return x > score
    else:
        score = math.inf
        def shouldReplace(x): return x < score

    move = -1

    successors = list(board.moves(maximizer))
    successors = sorted(successors, key=lambda x: len(x[0]), reverse=True)

    for successor in successors:
        global node_count
        node_count = node_count + 1

        action = successor
        state = board.deep_copy()
        state.move(*action)

        temp = alphabeta(state, depth - 1, not maximizer, alpha, beta)[0]
        
        if shouldReplace(temp):
            score = temp
            move = action
        if maximizer:
            alpha = max(alpha, temp)
        else:
            beta = min(beta, temp)
        if alpha >= beta:
            break
    
    # store
    tt_entry['value'] = score
    tt_entry['move'] = move
    if score <= alpha:
        tt_entry['flag'] = 'upper'
    elif score >= beta:
        tt_entry['flag'] = 'lower'
    
    tt_entry['depth'] = depth

    table[key] = tt_entry
    return score, move

################################ PVS + MOVE ORDER ##################################
# Depth-limited principal variation search
def pvs(board, maximizer, alpha, beta, depth):
    tt_entry = {'move': None, 'value': None, 'flag': None, 'depth': None}
    
    key = get_key(board.deep_copy(True))
    
    # lookup
    if key in table and table[key]['depth'] >= depth:
        tt_entry = table[key]
        move, flag, value = tt_entry['move'], tt_entry['flag'], tt_entry['value']

        if flag == 'lower':
            return max(-alpha, value), move
        elif flag == 'upper':
            return min(-beta, value), move

    if board.query.check_win(maximizer):
        return math.inf if maximizer else -math.inf, -1
    elif depth == 0:
        return -heuristic(board), -1
    
    if maximizer:
        score = -math.inf
        def shouldReplace(x): return x > score
    else:
        score = math.inf
        def shouldReplace(x): return x < score
    
    move = -1
    
    successors = list(board.moves(maximizer))
    successors = sorted(successors, key=lambda x: len(x[0]), reverse=True)

    for idx, successor in enumerate(successors):
        global node_count
        node_count = node_count + 1

        action = successor
        child = board.deep_copy()
        child.move(*action)

        temp = 0
        if idx == 0:
            temp = -pvs(child, not maximizer, -beta, -alpha, depth - 1)[0]
        else:
            temp = -pvs(child, not maximizer, -alpha - 1, -alpha, depth - 1)[0]
            if alpha < score < beta:
                temp = -pvs(child, not maximizer, -beta, -score, depth - 1)[0]
        
        if shouldReplace(temp):
            score = temp
            move = action
        alpha = max(alpha, score)
        if alpha >= beta:
            break
    
    # store
    tt_entry['value'] = score
    tt_entry['move'] = move
    if score <= alpha:
        tt_entry['flag'] = 'upper'
    elif score >= beta:
        tt_entry['flag'] = 'lower'
    
    tt_entry['depth'] = depth

    table[key] = tt_entry
    return score, move

####################################### HEURISTIC ##########################################
def heuristic(board):
    center_proximity = board.query.center_proximity(False) - board.query.center_proximity(True)

    # cohesion
    cohesion = 0
    if abs(center_proximity) > 2:
        cohesion = len(list(board.query.populations(False))) - len(list(board.query.populations(True)))
    
    # number of marbles
    marbles = 0
    if abs(center_proximity) < 1.5:
        marbles = board.query.marbles(True, True) * 100 - board.query.marbles(False, True) * 100
    
    return center_proximity + cohesion + marbles