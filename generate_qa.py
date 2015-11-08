#! /usr/bin/env python
'''
generate question-answers for a chess configuration

question : .png image, question text , pgn of the game and fen of the board
answer : list of pieces, yes/no or numbers
'''

import chess, chess.pgn, os, sys, string
import itertools,random
from random import shuffle
from visualizer import *
from utils import *
from collections import defaultdict

### initalize
FIXED = 50
PREFIX = ''
PATH = 'output'
START = 5
MIDDLE = 30
END = 100

ANSWERS = {}
BOOL = {'yes' : True, 'no' : False, 'white' : True, 'black' : False}
COLOR = {'white' : True, 'black' : False}
INV_COLOR = { True : 'white', False : 'black'}
POLAR = ['yes','no']
PIECE_VAL = {1 : 1, 2 : 3 , 3: 3 , 4 : 5 , 5 : 9}
SIDES = ['black','white']
PIECES = ['pawn','knight','bishop','rook','queen','king']
Zcount = [str(i) for i in xrange(1,32)]

SQUARES = []
for y in list(xrange(1,9)):
	for x in string.lowercase[:8]:
		SQUARES.append((x,str(y)))

ID2SQUARE = dict(enumerate(SQUARES))

MOVES = []
for sq1 in ID2SQUARE:
	for sq2 in ID2SQUARE:
		if sq1 != sq2:
			MOVES.append(chess.Move(sq1,sq2).uci())

### question text for each q type
def t_is_attacked(side,piece,square):
	q_text = ['which piece is attacking {} {} at {}', 'what is the type of piece attacking {} {} at {}']
	return random.choice(q_text).format(side,piece, square)

def t_legal_move(move):
	q_text = ['is {} a legal move', 'can {} be made']
	return random.choice(q_text).format(move)

def t_existence(piece):
	q_text = ['is there any {} on the board', 'does any side have a {}']
	return random.choice(q_text).format(piece)

def t_existence_side(side,piece):
	q_text = ['is there a {} {} on the board', 'does {} have a {}']
	return random.choice(q_text).format(side,piece)

def t_count_board():
	q_text = ['how many pieces are on the board', 'how many pieces are there']
	return random.choice(q_text)

def t_count_all_pieces(side):
	q_text = ['what is the number of pieces {} has', 'how many pieces {} has']
	return random.choice(q_text).format(side)

def t_position(square):
	q_text = ['what piece is on {}', 'what is on {}']
	return random.choice(q_text).format("".join(square))

def t_attack(side,piece,square):

	q_text = ['does {} {} attacks {}'.format(side,piece,"".join(square)), 'is {} under attack by {} {}'.format("".join(square),side,piece)]
	return random.choice(q_text)

def t_check(side):
	q_text = ['is {} in check', 'is {} currently in check']
	return random.choice(q_text).format(side)

def t_material_count(side):
	q_text = ['what is the material count of {}', 'how many material points does {} have']
	return random.choice(q_text).format(side)

def t_material_adv():
	q_text = ['who has the material advantage?', 'whose material has more value']
	return random.choice(q_text)

def t_castle(side):
	q_text = ['can {} castle', 'is it ok for {} to castle']
	return random.choice(q_text).format(side)

def t_castling_rights(side):
	q_text = ['does {} has castling rights','can {} castle in future moves']
	return random.choice(q_text).format(side)

def t_stalemate():
	q_text = ['is this a stalemate','is the game stalemate','is the game over with a stalemate']
	return random.choice(q_text)

def t_checkmate():
	q_text = ['is this a checkmate','is the game over with a checkmate']
	return random.choice(q_text)

### util functions for boolean checks
def check_castling(board,side):

	if (chess.Move.from_uci("e1g1") in board.legal_moves and side == True) or (chess.Move.from_uci("e1c1") in board.legal_moves and side == True) or (chess.Move.from_uci("e8g8") in board.legal_moves and side == False) or (chess.Move.from_uci("e8c8") in board.legal_moves and side == False):
		return True
	return False

def calculate_material(board,side):
	m = 0
	for piece in xrange(1,6):
		m += len(list(board.pieces(piece,side)))*PIECE_VAL[piece]
	return m

### boolean check for q types
def q_check(board,answer):

	if BOOL[answer] == board.is_check():
		return True
	return False

def q_material_count(board,side,answer):

	count = calculate_material(board,side)
	op_count = calculate_material(board,not(side))
	if count - op_count == int(answer):
		return True
	return False

def q_material_adv(board,answer):

	w = calculate_material(board,True)
	b = calculate_material(board,False)
	if w == b:
		return False
	if (w > b)  == BOOL[answer]:
		return True
	return False

def q_castle(board,side,answer):
	if board.has_castling_rights(COLOR[side]) == BOOL[answer] and (check_castling(board,COLOR[side]) == BOOL[answer]):
		return True
	return False

def q_castling_rights(board,side,answer):
	if board.has_castling_rights(COLOR[side]) == BOOL[answer]:
		return True
	return False

def q_stalemate(board, answer):
	if board.is_stalemate() == BOOL[answer]:
		return True
	return False

def q_checkmate(board, answer):
	if board.is_checkmate() == BOOL[answer]:
		return True
	return False

### generate positions for each q type
def g_is_attacked(q_type, games, total_count):

	answer_count = {}
	total = 0
	unique_answer = 0
	for a_s in SIDES:
		for a_p in PIECES:
			for s in SIDES:
				for p in PIECES:
					a = a_s + a_p
					answer_count[(a,s,p)] = 0
					unique_answer += 1

	count = total_count / unique_answer + FIXED
	qset = set()
	while total < total_count:
		shuffle(games)
		for j,game in enumerate(games):
			moves,i,board,node = ff_game(game,START,END)
			if i == 0:
				continue

			while node.variations:
				next_node = node.variation(0)
				moves.append(node.board().san(next_node.move))
				node = next_node
				board = node.board()

				i += 1

				attacked = []
				for attacked_piece in PIECES:
					for attacked_s in SIDES:
						attacked_side = BOOL[attacked_s]
						sq_list = list(board.pieces(PIECES.index(attacked_piece)+1,attacked_side))
						for attacked_sq in sq_list:
							attacked.append((not(attacked_side),attacked_piece,attacked_sq))
				shuffle(attacked)
				for (attacker_side,attacked_piece,attacked_sq) in attacked:
					attackers = list(board.attackers(attacker_side,attacked_sq))

				if len(attackers) == 0:
					continue
				for ind,att in enumerate(attackers):
					attacker_piece = board.piece_type_at(attackers[ind])
					a = INV_COLOR[attacker_side] + PIECES[attacker_piece-1]
					attacked_side = not(attacker_side)

					if len(attackers) == 1 and answer_count[(a,INV_COLOR[attacked_side],attacked_piece)] <= count and len(moves) > 1 and total < total_count and "".join(moves) not in qset:
						answer_count[(a,INV_COLOR[attacked_side],attacked_piece)] += 1
						write_qa(board,moves,q_type,a,total, QTEXT[q_type](INV_COLOR[attacked_side],attacked_piece,"".join(ID2SQUARE[attacked_sq])))
						total += 1
						print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
						qset.add("".join(moves))
						if total == total_count:
							return
						break

def g_legal_move(q_type, games, total_count):

	total = 0
	unique_answer = 0
	answer_count = {}
	for a in POLAR:
		for m in MOVES:
			answer_count[(a,m)] = 0
			unique_answer += 1

	count = total_count / unique_answer + FIXED
	while total < total_count:
		shuffle(games)

		for j,game in enumerate(games):
			moves,i,board,node = ff_game(game,MIDDLE,END)
			if i == 0:
				continue

			squares = []
			for p in PIECES:
				for side in SIDES:
					s = BOOL[side]
					squares += list(board.pieces(PIECES.index(p)+1,s))
			a = 'yes'
			shuffle(squares)

			c_list = []
			for from_sq in squares:
				for to_sq in ID2SQUARE:
					if from_sq != to_sq:
						c_list.append("".join(ID2SQUARE[from_sq])+"".join(ID2SQUARE[to_sq]))
			shuffle(c_list)

			for candidate_move in c_list:
				if chess.Move.from_uci(candidate_move) in board.legal_moves and answer_count[(a,candidate_move)] < count and len(moves) > 0 and total < total_count :
					answer_count[(a,candidate_move)] += 1
					write_qa(board,moves,q_type,a,total, QTEXT[q_type](candidate_move))
					total += 1
					print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
					if total == total_count:
						return


			moves,i,board,node = ff_game(node,START,MIDDLE)
			a = 'no'

			c_list = []
			for from_sq in squares:
				for to_sq in ID2SQUARE:
					if from_sq != to_sq:
						c_list.append("".join(ID2SQUARE[from_sq])+"".join(ID2SQUARE[to_sq]))
			shuffle(c_list)
			for candidate_move in c_list:
				if chess.Move.from_uci(candidate_move) not in board.legal_moves and answer_count[(a,candidate_move)] < count and len(moves) > 2 and total < total_count :
					answer_count[('no',candidate_move)] += 1
					write_qa(board,moves,q_type,a,total, QTEXT[q_type](candidate_move))
					total += 1
					print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
					if total == total_count:
						return


def g_existence(q_type, games, total_count):

	answer_count = {}
	total = 0
	unique_answer = 0

	for p in PIECES:
		for a in POLAR:
			answer_count[(a,p)] = 0
			unique_answer += 1

	count = total_count / unique_answer + 10
	qset = set()
	while total <  total_count:
		shuffle(games)

		for p in PIECES:
			for j,game in enumerate(games):
				moves,i,board,node = ff_game(game,START,START+5)
				if i == 0:
					continue

				while node.variations:
					next_node = node.variation(0)
					moves.append(node.board().san(next_node.move))
					node = next_node
					board = node.board()

					i += 1

					c = 0
					for s in SIDES:
						side = BOOL[s]
						c += len(list(board.pieces(PIECES.index(p)+1,side)))

					a = 'no' if c == 0 else 'yes'
					if answer_count[(a,p)] < count and len(moves) > 1 and total < total_count and "".join(moves) not in qset:
						answer_count[(a,p)] += 1
						write_qa(board,moves,q_type,a,total, QTEXT[q_type](p))
						total += 1
						print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
						qset.add("".join(moves))
						if total == total_count:
							return
						break


def g_existence_side(q_type, games, total_count):

	answer_count = {}
	total = 0
	unique_answer = 0

	for s in SIDES:
		for p in PIECES:
			for a in POLAR:
				answer_count[(a,p,s)] = 0
				unique_answer += 1
	count = total_count / unique_answer + FIXED
	qset = set()
	while total < total_count:
		shuffle(games)

		for p in PIECES:
			for s in SIDES:
				for j,game in enumerate(games):

					moves,i,board,node = ff_game(game,START,END)
					if i == 0:
						continue

					while node.variations:
						next_node = node.variation(0)
						moves.append(node.board().san(next_node.move))
						node = next_node
						board = node.board()
						i += 1


						side = BOOL[s]
						c = len(list(board.pieces(PIECES.index(p)+1,side)))
						a = 'no' if c == 0 else 'yes'
 						if answer_count[(a,p,s)] < count and len(moves) > 1 and total < total_count and "".join(moves) not in qset:
							answer_count[(a,p,s)] += 1
							write_qa(board,moves,q_type,a,total,QTEXT[q_type](s,p))
							total += 1
							print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
							qset.add("".join(moves))
							if total == total_count:
								return
							break

def g_count_board(q_type, games, total_count):

	answer_count = defaultdict(lambda: total_count)
	total = 0
	unique_answer = 0

	for c in xrange(2,32):
		answer_count[c] = 0
		unique_answer += 1

	count = total_count / unique_answer + FIXED
	qset = set()
	while total < total_count:

		shuffle(games)

		for j,game in enumerate(games):

			moves,i,board,node = ff_game(game,START,END)
			if i == 0:
				continue

			while node.variations:
				next_node = node.variation(0)
				moves.append(node.board().san(next_node.move))
				node = next_node
				board = node.board()
				i += 1

				c = 0
				for s in SIDES:
					side = BOOL[s]
					for piece in xrange(6):
						c += len(list(board.pieces(piece+1,side)))

				if answer_count[c] < count and len(moves) > 1 and total < total_count and "".join(moves) not in qset:
					answer_count[c] += 1
					write_qa(board,moves,q_type,str(c),total, QTEXT[q_type]())
					total += 1
					print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)

					qset.add("".join(moves))
					if total == total_count:
						return
					break


def g_count_all_pieces(q_type, games, total_count):

	total = 0
	unique_answer = 0

	answer_count = defaultdict(lambda: total_count)
	for s in SIDES:
		for c in xrange(1,16):
			answer_count[(s,c)] = 0
			unique_answer += 1
	count = total_count / unique_answer + FIXED
	qset = set()
	while total < total_count:
		shuffle(games)
		for s in SIDES:
			for j,game in enumerate(games):
				moves,i,board,node = ff_game(game,START,END)

				side = BOOL[s]
				while node.variations:
					next_node = node.variation(0)
					moves.append(node.board().san(next_node.move))
					node = next_node
					board = node.board()
					i += 1
					c = 0
					for piece in xrange(6):
						c += len(list(board.pieces(piece+1,side)))

					if answer_count[(s,c)] < count and len(moves) > 1 and total < total_count and "".join(moves) not in qset:
						answer_count[(s,c)] += 1
						write_qa(board,moves,q_type,str(c),total, QTEXT[q_type](s))
						total += 1
						print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
						qset.add("".join(moves))
						if total == total_count:
							return
						break


def g_position(q_type, games, total_count):

	answer_count = {}
	total = 0
	unique_answer = 0
	for s in SIDES:
		for p in PIECES:
			for square in SQUARES:
				answer_count[(s,p,square)] = 0
				unique_answer += 1
	count = total_count / unique_answer + FIXED
	qset = set()
	while total < total_count:
		shuffle(games)
		for s in SIDES:
			for p in PIECES:
				for j,game in enumerate(games):
					moves,i,board,node = ff_game(game,START,END)
					if i == 0:
						continue

					while node.variations:
						next_node = node.variation(0)
						moves.append(node.board().san(next_node.move))
						node = next_node
						board = node.board()

						i += 1

						side = BOOL[s]
						list_piece = list( board.pieces(PIECES.index(p) + 1,side))
						if len(list_piece) > 1:
							square = random.choice(list_piece)
							sq = ID2SQUARE[square]
							if answer_count[s,p,sq] < count and len(moves) > 1 and total < total_count and "".join(moves) not in qset:
								answer_count[(s,p,sq)] += 1
								write_qa(board,moves,q_type,s+p,total, QTEXT[q_type](sq))
								total += 1
								print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
								qset.add("".join(moves))
								if total == total_count:
									return
								break

def g_attack(q_type, games, total_count):

	answer_count = {}
	total = 0
	unique_answer = 0
	for a in POLAR:
		for s in SIDES:
			for p in PIECES:
				for square in SQUARES:
					answer_count[(a,s,p,square)] = 0
					unique_answer += 1
	count = total_count / unique_answer + FIXED
	qset = set()
	while total < total_count:

		shuffle(games)

		for s in SIDES:
			for p in PIECES[1:]:
				for j,game in enumerate(games):
					moves,i,board,node = ff_game(game,START,END)
					if i == 0:
						continue

					while node.variations:
						next_node = node.variation(0)
						moves.append(node.board().san(next_node.move))
						node = next_node
						board = node.board()
						i += 1


						side = BOOL[s]
						list_piece = list( board.pieces(PIECES.index(p) + 1,side))
						if len(list_piece) <= 0:
							continue

						piece = random.choice(list_piece)
						sq_list = list(board.attacks(piece))
						if len(sq_list) <= 0:
							continue
						square = random.choice(sq_list)

						sq = ID2SQUARE[square]
						a = 'yes'
						if answer_count[a,s,p,sq] < count and len(moves) > 1 and total < total_count and "".join(moves) not in qset:
							sq = ID2SQUARE[square]
							answer_count[(a,s,p,sq)] += 1
							write_qa(board,moves,q_type,a,total, QTEXT[q_type](s,p,sq))
							total += 1
							print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)

							qset.add("".join(moves))
							if total == total_count:
								return
							break

						square = random.choice(xrange(64))
						a = 'no'
						if square not in set(sq_list) and answer_count[a,s,p,sq] < count and len(moves) > 1 and total < total_count and "".join(moves) not in qset:
							sq = ID2SQUARE[square]
							answer_count[(a,s,p,sq)] += 1
							write_qa(board,moves,q_type,a,total, QTEXT[q_type](s,p,sq))
							total += 1
							print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
							qset.add("".join(moves))
							if total == total_count:
								return
							break

def g_check(q_type, games, total_count):

	answer_count = {}
	unique_answer = 0
	total = 0
	for a in POLAR:
		for s in SIDES:
			answer_count[(a,s)] = 0
			unique_answer += 1
	count = total_count / unique_answer + 1

	qset = set()
	while total < total_count:
		shuffle(games)
		for side in SIDES:
			for j,game in enumerate(games):
				moves,i,board,node = ff_game(game,MIDDLE, END)
				if i == 0:
					continue

				while node.variations:
					next_node = node.variation(0)
					moves.append(node.board().san(next_node.move))
					node = next_node
					board = node.board()
					i += 1

					answer = 'no'
					turn  = False
					if i%2 == 0:
						turn = True

					if q_check(board,answer) and BOOL[side] == turn and answer_count[(answer,side)] < count and len(moves) > 1 and total < total_count and "".join(moves) not in qset:
						answer_count[(answer,side)] += 1
						write_qa(board,moves,q_type,answer,total, QTEXT[q_type](side))
						total += 1
						print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
						qset.add("".join(moves))
						if total == total_count:
							return
						break

					answer = 'yes'
					if q_check(board,answer) and BOOL[side] == turn and answer_count[(answer,side)] < count and len(moves) > 1 and total < total_count and "".join(moves) not in qset:
						answer_count[(answer,side)] += 1
						write_qa(board,moves,q_type,answer,total, QTEXT[q_type](side))
						total += 1
						print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
						qset.add("".join(moves))
						if total == total_count:
							return
						break
def g_material_count(q_type, games, total_count):

	answer_count = {}
	unique_answer = 0
	total = 0
	for a in Zcount:
		for s in SIDES:
			answer_count[(a,s)] = 0
			unique_answer +=1
	count = total_count / unique_answer + FIXED

	qset = set()
	while total <  total_count:
		shuffle(games)
		for answer in Zcount:
			for side in SIDES:
				for j,game in enumerate(games):
					if answer_count[(answer,side)] >= count:
						break
					moves,i,board,node = ff_game(game,START,END)
					if i == 0:
						continue

					k = 0
					while node.variations:
						next_node = node.variation(0)
						moves.append(node.board().san(next_node.move))
						node = next_node
						board = node.board()

						k += 1
						i += 1

						if q_material_count(board,BOOL[side],answer) and len(moves) > 1 and total < total_count and "".join(moves) not in qset:
							answer_count[(answer,side)] += 1
							write_qa(board,moves,q_type,answer,total, QTEXT[q_type](side))
							qset.add("".join(moves))
							total += 1
							print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
							if total == total_count:
								return
							break


def g_material_adv(q_type, games, total_count):

	answer_count = { 'white' : 0, 'black' : 0}
	total = 0
	unique_answer = 2
	count = total_count / unique_answer + 1
	while total < total_count:
		shuffle(games)

		for answer in SIDES:
			for j,game in enumerate(games):
				if answer_count[answer] >= count:
					break
				moves,i,board,node = ff_game(game,START,MIDDLE)
				if i == 0:
					continue

				if q_material_adv(board,answer) and len(moves) > 1 and total < total_count:
					answer_count[answer] += 1
					write_qa(board,moves,q_type,answer,total, QTEXT[q_type]())
					total += 1
					print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
					if total == total_count:
						return


def g_castle(q_type, games, total_count):

	answer_count = { ('white','yes') : 0, ('black','yes') : 0, ('white','no') : 0, ('black','no') : 0}
	total = 0
	unique_answer = 4
	count = total_count / unique_answer + 1
	while total < total_count:
		shuffle(games)

		for side in SIDES:
			for answer in POLAR:
				for j,game in enumerate(games):
					if answer_count[(side,answer)] >= count:
						break

					moves,i,board,node = ff_game(game,START,MIDDLE)
					if i == 0:
						continue

					if q_castle(board,side,answer) and len(moves) > 1 and total < total_count:
						answer_count[(side,answer)] += 1
						write_qa(board,moves,q_type,answer,total, QTEXT[q_type](side))
						total += 1
						print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
						if total == total_count:
							return


def g_castling_rights(q_type, games, total_count):

	answer_count = { ('white','yes') : 0, ('black','yes') : 0, ('white','no') : 0, ('black','no') : 0}
	total = 0
	unique_answer = 4
	count = total_count / unique_answer + 1 + 1
	while total < total_count:
		shuffle(games)
		for side in SIDES:
			for answer in POLAR:
				for j,game in enumerate(games):
					if answer_count[(side,answer)] >= count:
						break

					moves,i,board,node = ff_game(game,START,MIDDLE)
					if i == 0:
						continue
					if q_castling_rights(board,side,answer) and len(moves) > 1 and total < total_count:
						answer_count[(side,answer)] += 1
						write_qa(board,moves,q_type,answer,total, QTEXT[q_type](side))
						total += 1
						print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
						if total == total_count:
							return


def g_stalemate(q_type, games, total_count):

	answer_count = {'yes' : 0, 'no' : 0}
	total = 0
	unique_answer = 2
	count = total_count / unique_answer + 1 
	while total < total_count:

		shuffle(games)
		for j,game in enumerate(games):

			moves,i,board,node = ff_game(game,MIDDLE,END)
			if i == 0:
				continue

			answer = 'no'
			if q_stalemate(board,answer) and answer_count[answer] < count and len(moves) > 1 and total < total_count:
				answer_count[answer] += 1
				write_qa(board,moves,q_type,answer,total,QTEXT[q_type]())
				total += 1
				print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
				if total == total_count:
					return


			k = 0
			while node.variations:
				next_node = node.variation(0)
				moves.append(node.board().san(next_node.move))
				node = next_node
				k += 1
				i += 1

			if k == 0:
				continue

			node = next_node
			board = node.board()
			answer = 'yes'

			if q_stalemate(board,answer) and answer_count[answer] < count and len(moves) > 1 and total < total_count:
				answer_count[answer] += 1
				write_qa(board,moves,q_type,answer,total,QTEXT[q_type]())
				total += 1
				print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
				if total == total_count:
					return


def g_checkmate(q_type, games, total_count):

	answer_count = {'yes' : 0, 'no' : 0}
	total = 0
	unique_answer = 2
	count = total_count / unique_answer  + 1

	qset = set()
	while total < total_count:
		shuffle(games)
		for j,game in enumerate(games):
			moves,i,board,node = ff_game(game,MIDDLE,END)

			if i == 0:
				continue

			if q_checkmate(board,'no') and answer_count['no'] < count and len(moves) > 1 and total < total_count:
				answer_count['no'] += 1
				write_qa(board,moves,q_type,'no',total,QTEXT[q_type]())
				total += 1
				print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
				if total == total_count:
					return


			k = 0
			while node.variations:
				next_node = node.variation(0)
				moves.append(node.board().san(next_node.move))
				node = next_node
				k += 1
				i += 1

			if k == 0:
				continue

			node = next_node
			board = node.board()

			if q_checkmate(board,'yes') and answer_count['yes'] < count and len(moves) > 1 and total < total_count:
				answer_count['yes'] += 1
				write_qa(board,moves,q_type,'yes',total,QTEXT[q_type]())
				total += 1
				print "{}/{} generated for type {}. answer type per question {}".format(total,total_count,q_type, unique_answer)
				if total == total_count:
					return


### fast-forward game for a number of steps
def ff_game(game,start,end):

	moves = []
	node = game
	nmoves = random.randint(start,end)

	i = 0
	while node.variations:
		i += 1
		next_node = node.variation(0)
		board = node.board()
		moves.append(node.board().san(next_node.move))
		node = next_node
		if i == nmoves:
			break

	board = node.board()
	if i == 0:
		return moves,0,board,node
	node = next_node
	return moves,i,board,node

### write question data into files
def write_qa(board,m,q,a,c, q_text, meta = ''):

	fen = board.fen()
	renderer = DrawChessPosition()
	board_image = renderer.draw(fen)

	f_name = "q"+str(q)+"_"+str(c)
	board_image.save(PREFIX+f_name+'.png')

	moves = " ".join(m)
	moves = moves[:-1] if moves[-1] == "#" else moves

	print >> open(PREFIX+f_name+'.txt','w'), "\t".join([q_text,moves,fen,a])
#	print >> open(PREFIX+f_name+'.fen','w'), fen ## if you want to print FEN too, uncomment

CHECK = { 0 : q_checkmate, 1 : q_stalemate, 2 : q_castling_rights, 3 : q_castle, 4 : q_material_adv, 5 : q_material_count, 6 : q_check}
QTEXT = { 0 : t_checkmate, 1 : t_stalemate, 2 : t_castling_rights, 3 : t_castle, 4 : t_material_adv, 5 : t_material_count, 6: t_check, 7 : t_attack, 8 : t_position, 9 : t_count_all_pieces, 10 : t_count_board , 11 : t_existence_side, 12 : t_existence, 13 : t_legal_move, 14 : t_is_attacked}
GENERATE = { 0 : g_checkmate, 1: g_stalemate, 2 : g_castling_rights, 3 : g_castle, 4 : g_material_adv, 5 : g_material_count , 6: g_check, 7 : g_attack, 8 : g_position , 9 : g_count_all_pieces, 10 : g_count_board , 11 : g_existence_side, 12 : g_existence, 13 : g_legal_move, 14 : g_is_attacked}

def read_games(pgn_file, n_matches):

	pgn = open(pgn_file)
	g_count = 0
	games = []
	while pgn.tell() != os.fstat(pgn.fileno()).st_size:
		game = chess.pgn.read_game(pgn)
		games.append(game)
		g_count += 1
		if g_count == n_matches:
			break
	print >> sys.stderr, "Total ",g_count,"games has been read"
	return games

if __name__ == "__main__":
	random.seed(0)
	parser = get_parser()
	p = parser.parse_args()
	random.seed(p.seed)

	games = read_games(p.pgn_file, p.n_matches)
	PATH = p.path
	if len(p.q_type.split('-')) == 2:
		st = int(p.q_type.split('-')[0])
		end = int(p.q_type.split('-')[1])+1

	else:
		st = int(p.q_type)
		end = int(p.q_type) +1

	for q_type in xrange(st,end):

		PREFIX = PATH + '/' + str(q_type) + '/'

		os.system('rm -rf '+PREFIX)
		os.system('mkdir -p '+PREFIX)
		GENERATE[q_type](q_type,games, p.total_count)
		print >> sys.stderr, "DONE!",q_type
