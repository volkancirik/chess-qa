import argparse

def get_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--seed', action='store', dest='seed',help='random seed, default = 0',type=int,default = 0)

    parser.add_argument('--q-type', action='store', dest='q_type',help='question types 0 checkmate 1 stalemate 2 castling rights 3 castle 4 material advantage 5 material count 6 check 7 attack 8 position 9 count all pieces 10 count pieces for side 11 existence of piece with side 12 existence of a piece 13 legal move 14 is attacked. use - for range ex 2-14 or',default = '2-14')

    parser.add_argument('--pgn-file', action='store', dest='pgn_file',help='input pgn file',default = 'data/chess.2014.blitz.pgn')

    parser.add_argument('--matches', action='store', dest='n_matches',help='# of matches to be read, -1 for all matches, default = 100',type=int,default = 100)

    parser.add_argument('--total-count', action='store', dest='total_count',help='total # of questions to generate',type=int, default = 100)

    parser.add_argument('--path', action='store', dest='path',help='folder to produce output into ',default = 'output')

    return parser
