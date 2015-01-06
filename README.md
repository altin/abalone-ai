A prototype written in Python of the two player strategic board game
[Abalone](https://en.wikipedia.org/wiki/Abalone_(board_game)).


Example use case
================

    from abalone.grid import AbaloneGrid
    from abalone.config import INITIAL_POSITIONS

    # Initialize the grid with the 'standard' opening
    grid = AbaloneGrid(INITIAL_POSITIONS['standard'])
    print(grid)

    # Get all the possible moves for the black player
    moves = grid.moves(grid.BLACK)
    print(list(moves))


Documentation
=============

Hexagonal grids
---------------

- [Hexagonal grids](http://www.redblobgames.com/grids/hexagons/)

Abalone playing agents
----------------------

- [Exploring Optimization Strategies in Board Game Abalone for Alpha-Beta
  Search](http://geneura.ugr.es/cig2012/papers/paper51.pdf)
- [Constructing an Abalone Game-Playing
  Agent](https://project.dke.maastrichtuniversity.nl/games/files/bsc/Lemmens_BSc-paper.pdf)
- [Implementing a Computer Player for Abalone using Alpha-Beta and Monte-Carlo
  Search](https://project.dke.maastrichtuniversity.nl/games/files/msc/pcreport.pdf)
- [Algorithmic Fun -
  Abalone](http://www.ist.tugraz.at/staff/aichholzer/research/rp/abalone/tele1-02_aich-abalone.pdf)
