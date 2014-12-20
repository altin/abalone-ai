def split_when(func, iterable):
    alpha, beta = [], []
    iterable = list(iterable)
    while iterable:
        item = iterable.pop(0)
        if func(item):
            beta = [item] + iterable
            iterable = []
        else:
            alpha.append(item)
    return alpha, beta
