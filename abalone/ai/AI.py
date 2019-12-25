import math
from collections import deque

node_count = 0

############################# MIN-MAX ##################################
# Depth-limited Minimax search
def minimax(board, depth, maximizer):
    if board.query.check_win(not maximizer):
        return -math.inf if maximizer else math.inf, -1
    elif depth == 0:
        return heuristic(board), -1

    if maximizer:
        score = -math.inf
        def shouldReplace(x): return x > score
    else:
        score = math.inf
        def shouldReplace(x): return x < score

    move = -1

    successors = board.moves(maximizer)

    for successor in successors:
        global node_count
        node_count = node_count + 1

        action = successor
        state = board.deep_copy()
        state.move(*action)

        temp = minimax(state, depth - 1, not maximizer)[0]
        if shouldReplace(temp):
            score = temp
            move = action

    return score, move

############################# ALPHA-BETA ##################################
# Depth-limited alphabeta search
def alphabeta(board, depth, maximizer, alpha, beta):
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

    return score, move

############################# PVS (Move Ordering) ############################
# Depth-limited principal variation search
def pvs(board, maximizer, alpha, beta, depth):
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
    #ordered_successors = deque([])
    
    # # Order nodes based on sumito moves
    # for successor in successors:
    #     old = board.deep_copy() # Prior board
        
    #     block = successor[0]
    #     direction = successor[1]
    #     new = board.deep_copy() # New board
    #     new.move(block, direction)

    #     old_m = old.query.marbles(not maximizer)
    #     new_m = new.query.marbles(not maximizer)

    #     if old_m != new_m:
    #         ordered_successors.appendleft(successor)
    #     else:
    #         ordered_successors.append(successor)

    #ordered_successors = sorted(ordered_successors, key=lambda x: len(x[0]), reverse=True)


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
    if abs(center_proximity) < 1.8:
        marbles = board.query.marbles(True, True) * 100 - board.query.marbles(False, True) * 100
    
    return center_proximity + cohesion + marbles