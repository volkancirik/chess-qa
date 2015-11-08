#! /usr/bin/env python
'''Code to draw chess board and pieces.

FEN notation to describe the arrangement of peices on a chess board.

White pieces are coded: K, Q, B, N, R, P, for king, queen, bishop,
rook knight, pawn. Black pieces use lowercase k, q, b, n, r, p. Blank
squares are noted with digits, and the "/" separates ranks.

As an example, the game starts at:

rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR

See: http://en.wikipedia.org/wiki/Forsyth-Edwards_Notation
'''
import re, string
from PIL import Image,ImageDraw,ImageFont

class BadChessboard(ValueError):
	pass
	
def remove_move(fen):
	'''
	removes latest move
	'''
	return fen.split()[0]

def expand_blanks(fen):
	'''Expand the digits in an FEN string into spaces
	
	>>> expand_blanks("rk4q3")
	'rk	   q   '
	'''
	fen = remove_move(fen)
	def expand(match):
		return ' ' * int(match.group(0))
	return re.compile(r'\d').sub(expand, fen)
	
def check_valid(expanded_fen):
	'''Asserts an expanded FEN string is valid'''

	match = re.compile(r'([KQBNRPkqbnrp ]{8}/){8}$').match
	if not match(expanded_fen + '/'):
		raise BadChessboard()
	
def expand_fen(fen):
	'''Preprocesses a fen string into an internal format.
	
	Each square on the chessboard is represented by a single 
	character in the output string. The rank separator characters
	are removed. Invalid inputs raise a BadChessboard error.
	'''
	expanded = expand_blanks(fen)
	check_valid(expanded)
	return expanded.replace('/', '')
	
def draw_board(n=8, sq_size=(20, 20)):
	'''Return an image of a chessboard.
	
	The board has n x n squares each of the supplied size.'''
	from itertools import cycle
	def square(i, j):
		return i * sq_size[0], j * sq_size[1]
	opaque_grey_background = 160, 240
	board = Image.new('LA', square(n, n), opaque_grey_background) 
#	board = Image.new('LA', square(n, n))


	draw_square = ImageDraw.Draw(board).rectangle
	whites = ((square(i, j), square(i + 1, j + 1))
			  for i_start, j in zip(cycle((0, 1)), range(n))
			  for i in range(i_start, n, 2))
	for white_square in whites:
		draw_square(white_square, fill='white')
	return board
	
class DrawChessPosition(object):
	'''Chess position renderer.
	
	Create an instance of this class, then call 
	'''
	def __init__(self):
		'''Initialise, preloading pieces and creating a blank board.''' 
		self.n = 8
		self.create_pieces()
		self.create_blank_board()
	
	def create_pieces(self):
		'''Load the chess pieces from disk.
		
		Also extracts and caches the alpha masks for these pieces. 
		'''
		whites = 'KQBNRP'
		piece_images = dict(
			zip(whites, (Image.open('pieces/w%s.png' % p) for p in whites)))
		blacks = 'kqbnrp'
		piece_images.update(dict(
			zip(blacks, (Image.open('pieces/%s.png' % p) for p in blacks))))
		piece_sizes = set(piece.size for piece in piece_images.values())
		# Sanity check: the pieces should all be the same size
		assert len(piece_sizes) == 1
		self.piece_w, self.piece_h = piece_sizes.pop()
		self.piece_images = piece_images
		self.piece_masks = dict((pc, img.split()[3]) for pc, img in
								 self.piece_images.iteritems())
	
	def create_blank_board(self):
		'''Pre-render a blank board.'''
		self.board = draw_board(sq_size=(self.piece_w, self.piece_h))
	
	def point(self, i, j):
		'''Return the top left of the square at (i, j).'''
		w, h = self.piece_w, self.piece_h
		return i * h, j * w
	
	def square(self, i, j):
		'''Return the square at (i, j).'''
		t, l = self.point(i, j)
		b, r = self.point(i + 1, j + 1)
		return t, l, b, r
	
	def draw(self, fen):
		'''Return an image depicting the input position.
		
		fen - the first record of a FEN chess position.
		Clients are responsible for resizing this image and saving it,
		if required.
		'''
		board = self.board.copy()
		pieces = expand_fen(fen)
		images, masks, n = self.piece_images, self.piece_masks, self.n
		pts = (self.point(i, j) for j in range(n) for i in range(n))
		def not_blank(pt_pc):
			return pt_pc[1] != ' '
		for pt, piece in filter(not_blank, zip(pts, pieces)):
			board.paste(images[piece], pt, masks[piece])

		d = ImageDraw.Draw(board)
		font = ImageFont.truetype("arial.ttf",11)
		x = string.lowercase[:8]
		for i in xrange(0,8):
			d.text( ( 45 + i*50, 388) , x[i] , fill = (0,256), font = font)
			d.text( (1, 350 - i*50) , str(i+1) , fill = (0,256), font = font)

		return board
