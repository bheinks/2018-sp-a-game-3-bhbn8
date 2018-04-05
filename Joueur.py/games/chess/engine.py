import copy

# local imports
from games.chess.constants import *
#from constants import *


class Chess:
    # map piece types for framework
    PIECE_MAP = {
        PAWN: "Pawn",
        KNIGHT: "Knight",
        BISHOP: "Bishop",
        ROOK: "Rook",
        QUEEN: "Queen",
        KING: "King"
    }

    def __init__(self, fen=DEFAULT_FEN):
        self.board = [None] * 128
        self.kings = {WHITE: EMPTY, BLACK: EMPTY}
        self.castling = {WHITE: 0, BLACK: 0}
        self.history = []
        #self.value = 0

        self.load(fen)

    def get_value(self):
        value = 0

        for square in SQUARES:
            value += self.get_piece_value(square.value)

        return value

    def copy(self):
        new = copy.copy(self)
        new.kings = {WHITE: self.kings[WHITE], BLACK: self.kings[BLACK]}
        new.castling = {WHITE: self.castling[WHITE], BLACK: self.castling[BLACK]}

        return new

    def load(self, fen):
        tokens = fen.split()
        square = 0

        for piece in tokens[0]:
            if piece == '/':
                square += 8
            elif piece.isdigit():
                square += int(piece)
            else:
                color = WHITE if piece.isupper() else BLACK
                piece = Piece(piece.lower(), color)
                self.place_piece(piece, Chess.get_san(square))
                #self.value += Chess.get_piece_value(color, piece.type, square)
                square += 1

        self.turn = tokens[1]

        if 'K' in tokens[2]:
            self.castling[WHITE] |= KSIDE_CASTLE
        if 'Q' in tokens[2]:
            self.castling[WHITE] |= QSIDE_CASTLE
        if 'k' in tokens[2]:
            self.castling[BLACK] |= KSIDE_CASTLE
        if 'q' in tokens[2]:
            self.castling[BLACK] |= QSIDE_CASTLE

        self.ep_square = EMPTY if tokens[3] == '-' else SQUARES[tokens[3]].value
        self.half_moves = int(tokens[4])
        self.move_number = int(tokens[5])

    def generate_fen(self):
        empty = 0
        fen = ""

        i = SQUARES.a8.value - 1
        while i <= SQUARES.h1.value:
            i += 1

            if not self.board[i]:
                empty += 1
            else:
                if empty > 0:
                    fen += str(empty)
                    empty = 0
                
                type = self.board[i].type
                color = self.board[i].color

                fen += type.upper() if color == WHITE else type

            if (i+1) & 0x88:
                if empty > 0:
                    fen += str(empty)

                if i != SQUARES.h1.value:
                    fen += '/'

                empty = 0
                i += 8

        # add castling permissions
        cflags = ''
        if self.castling[WHITE] & KSIDE_CASTLE:
            cflags += 'K'
        if self.castling[WHITE] & QSIDE_CASTLE:
            cflags += 'Q'
        if self.castling[BLACK] & KSIDE_CASTLE:
            cflags += 'k'
        if self.castling[BLACK] & QSIDE_CASTLE:
            cflags += 'q'

        # if castling flag is empty, replace with dash
        cflags = cflags or '-'

        epflags = '-' if self.ep_square == EMPTY else Chess.get_san(self.ep_square)

        return ' '.join(
            [fen, self.turn, cflags, epflags, str(self.half_moves), str(self.move_number)])
    
    def get_piece(square):
        return self.board[SQUARES[square].value]

    def place_piece(self, piece, square):
        sq = SQUARES[square].value
        self.board[sq] = piece

        if piece.type == KING:
            self.kings[piece.color] = sq

    def print(self):
        print("   +" + '-'*24 + '+')

        i = SQUARES.a8.value - 1
        while i <= SQUARES.h1.value:
            i += 1

            if Chess.get_file(i) == 0:
                print(" {} |".format("87654321"[Chess.get_rank(i)]), end='')

            if not self.board[i]:
                print(" . ", end='')
            else:
                type = self.board[i].type
                color = self.board[i].color

                print(' ' + (type.upper() if color == WHITE else type) + ' ', end='')

            if (i+1) & 0x88:
                print('|')
                i += 8

        print("   +" + '-'*24 + '+')
        print("     " + "  ".join(list("abcdefgh")))

    def generate_moves(self, legal=True, single_square=""):
        def add_move(m_from, m_to, flags):
            moves = []

            if ((Chess.get_rank(m_to) == RANK_8 or Chess.get_rank(m_to) == RANK_1) and
                    self.board[m_from].type == PAWN):
                for piece in [QUEEN, ROOK, BISHOP, KNIGHT]:
                    moves.append(Move(self.board, self.turn, m_from, m_to, flags, piece))
            else:
                moves.append(Move(self.board, self.turn, m_from, m_to, flags))

            return moves

        moves = []
        us = self.turn
        them = Chess.swap_color(us)
        second_rank = {'b': RANK_7, 'w': RANK_2}

        i = SQUARES.a8.value - 1
        last_sq = SQUARES.h1.value

        # if we're only exploring the moves for a single square
        if single_square:
            i = last_sq = SQUARES[single_square].value - 1

        while i <= last_sq:
            i += 1
            # if we ran off the end of the board
            if i & 0x88:
                i += 7
                continue

            piece = self.board[i]
            # if empty square or enemy piece
            if not piece or piece.color != us:
                continue

            if piece.type == PAWN:
                # single square non-capture
                square = i + PAWN_OFFSETS[us][0]

                # if square is empty
                if not self.board[square]:
                    moves += add_move(i, square, NORMAL)

                    # double square
                    square = i + PAWN_OFFSETS[us][1]

                    if second_rank[us] == Chess.get_rank(i) and not self.board[square]:
                        moves += add_move(i, square, BIG_PAWN)

                # pawn captures
                for j in range(2, 4):
                    square = i + PAWN_OFFSETS[us][j]

                    # if end of board
                    if square & 0x88:
                        continue

                    # if square is occupied by enemy piece
                    if self.board[square] and self.board[square].color == them:
                        moves += add_move(i, square, CAPTURE)
                    # if capture square is en passant square
                    elif square == self.ep_square:
                        moves += add_move(i, square, EP_CAPTURE)
            else:
                for offset in PIECE_OFFSETS[piece.type]:
                    square = i

                    while True:
                        square += offset

                        # break if end of board
                        if square & 0x88:
                            break

                        if not self.board[square]:
                            moves += add_move(i, square, NORMAL)
                        else:
                            if self.board[square].color == them:
                                moves += add_move(i, square, CAPTURE)

                            break

                        # break if knight or king
                        if piece.type in ['n', 'k']:
                            break

        if not single_square or last_sq == self.kings[us]:
            # kingside castling
            if self.castling[us] & KSIDE_CASTLE:
                castling_from = self.kings[us]
                castling_to = castling_from + 2

                # if the path is clear, we're not in check and won't be in check
                if (not self.board[castling_from+1] and
                        not self.board[castling_to] and
                        not self.attacked(them, self.kings[us]) and
                        not self.attacked(them, castling_from+1) and
                        not self.attacked(them, castling_to)):
                    moves += add_move(self.kings[us], castling_to, KSIDE_CASTLE)

            # queenside castling
            if self.castling[us] & QSIDE_CASTLE:
                castling_from = self.kings[us]
                castling_to = castling_from - 2

                # if the path is clear, we're not in check and won't be in check
                if (not self.board[castling_from-1] and
                        not self.board[castling_from-2] and
                        not self.board[castling_from-3] and
                        not self.attacked(them, self.kings[us]) and
                        not self.attacked(them, castling_from-1) and
                        not self.attacked(them, castling_to)):
                    moves += add_move(self.kings[us], castling_to, QSIDE_CASTLE)

        # if we're allowing illegal moves
        if not legal:
            return moves

        # filter out illegal moves
        legal_moves = []
        for move in moves:
            self.move(move)

            if not self.king_attacked(us):
                legal_moves.append(move)

            self.undo()

        return legal_moves

    def attacked(self, color, square):
        i = SQUARES.a8.value - 1
        while i <= SQUARES.h1.value:
            i += 1

            # if we ran off the end of the board
            if i & 0x88:
                i += 7
                continue
            
            # if empty square or wrong color
            if not self.board[i] or self.board[i].color != color:
                continue

            piece = self.board[i]
            difference = i - square
            index = difference + 119

            if ATTACKS[index] & (1 << SHIFTS[piece.type]):
                if piece.type == PAWN:
                    if difference > 0:
                        if piece.color == WHITE:
                            return True
                    else:
                        if piece.color == BLACK:
                            return True
                    continue

                # if knight or king
                if piece.type in ['n', 'k']:
                    return True

                offset = RAYS[index]
                j = i + offset

                blocked = False
                while j != square:
                    if self.board[j]:
                        blocked = True
                        break
                    j += offset

                if not blocked:
                    return True

        return False

    def king_attacked(self, color):
        return self.attacked(Chess.swap_color(color), self.kings[color])

    def in_check(self):
        return self.king_attacked(self.turn)

    def in_checkmate(self):
        return self.in_check() and not self.generate_moves()

    def in_stalemate(self):
        return not self.in_check() and not self.generate_moves()

    def insufficient_material(self):
        pieces = {}
        bishops = []
        num_pieces = 0
        sq_color = 0

        i = SQUARES.a8.value - 1
        while i <= SQUARES.h1.value:
            i += 1
            sq_color = (sq_color + 1) % 2

            if i & 0x88:
                i += 7
                continue

            piece = self.board[i]

            if piece:
                pieces[piece.type] = pieces.get(piece.type, 0) + 1

                if piece.type == BISHOP:
                    bishops.append(sq_color)

                num_pieces += 1

        # K vs. K
        if num_pieces == 2:
            return True
        # K vs. KN or K vs. KB
        elif num_pieces == 3 and (pieces.get(BISHOP, 0) == 1 or pieces.get(KNIGHT, 0) == 1):
            return True
        # KB vs. KB where any number of bishops are all the same color
        elif num_pieces == (pieces.get(BISHOP, 0)+2):
            b_sum = sum(bishops)

            if sum == 0 or sum == len(bishops):
                return True

        return False

    def in_threefold_repetition(self):
        # if we don't have enough moves to determine repetition
        if len(self.history) < 8:
            return False

        # if there's been a capture, promotion or pawn movement in the past 8 moves
        for _, move in self.history[-8:]:
            if move.captured or move.promotion or move.piece == PAWN:
                return False

        # if each player's past 2 pairs of moves are not equal
        for i, j in zip(range(-8, -4), range(-4, 0)):
            if self.history[i][1] != self.history[j][1]:
                return False

        return True

    def in_draw(self):
        return (self.half_moves >= 100 or
                self.in_threefold_repetition() or
                self.insufficient_material())# or
                #self.in_stalemate())

    def game_over(self):
        return self.half_moves >= 50 or self.in_checkmate() or self.in_draw()

    def move(self, move):
        us = self.turn
        them = Chess.swap_color(us)
        self.snapshot(move)

        # if capture, subtract value of piece
        #self.value -= Chess.PIECE_VALUES[them].get(move.captured, 0)
        #self.value -= Chess.get_piece_value(them, move.captured, move.m_to)

        self.board[move.m_to] = self.board[move.m_from]
        self.board[move.m_from] = None

        # if en passant capture, remove the captured pawn
        if move.flags & EP_CAPTURE:
            if self.turn == BLACK:
                self.board[move.m_to-16] = None
            else:
                self.board[move.m_to+16] = None

        # if pawn promotion, replace with new piece
        if move.flags & PROMOTION:
            #self.value -= Chess.PIECE_VALUES[self.turn]['p']
            #self.value += Chess.PIECE_VALUES[self.turn][move.promotion]

            self.board[move.m_to] = Piece(move.promotion, us)

        # if we moved the king
        if self.board[move.m_to].type == KING:
            self.kings[self.board[move.m_to].color] = move.m_to

            # if we castled, move the rook next to the king
            if move.flags & KSIDE_CASTLE:
                castling_to = move.m_to - 1
                castling_from = move.m_to + 1

                self.board[castling_to] = self.board[castling_from]
                self.board[castling_from] = None
            elif move.flags & QSIDE_CASTLE:
                castling_to = move.m_to + 1
                castling_from = move.m_to - 2

                self.board[castling_to] = self.board[castling_from]
                self.board[castling_from] = None

            # remove castling permissions
            self.castling[us] = 0

        # remove castling permissions if we move a rook
        if self.castling[us]:
            for rook in ROOKS[us]:
                if move.m_from == rook["square"] and self.castling[us] & rook["flag"]:
                    self.castling[us] ^= rook["flag"]
                    break

        # remove castling permissions if we capture a rook
        if self.castling[them]:
            for rook in ROOKS[them]:
                if move.m_to == rook["square"] and self.castling[them] & rook["flag"]:
                    self.castling[them] ^= rook["flag"]
                    break

        # if big pawn move, update the en passant square
        if move.flags & BIG_PAWN:
            if self.turn == BLACK:
                self.ep_square = move.m_to - 16
            else:
                self.ep_square = move.m_to + 16
        else:
            self.ep_square = EMPTY

        # reset the 50 move counter if a pawn is moved or a piece is captured
        if move.piece == PAWN or move.flags & (CAPTURE | EP_CAPTURE):
            self.half_moves = 0
        else:
            self.half_moves += 1

        if self.turn == BLACK:
            self.move_number += 1

        self.turn = Chess.swap_color(self.turn)

    def undo(self):
        try:
            old, move = self.history.pop()
        # stack is empty
        except IndexError:
            return None

        self.kings = old.kings
        self.turn = old.turn
        self.castling = old.castling
        self.ep_square = old.ep_square
        self.half_moves = old.half_moves
        self.move_number = old.move_number
        #self.value = old.value

        us = self.turn
        them = Chess.swap_color(us)

        self.board[move.m_from] = self.board[move.m_to]
        self.board[move.m_from].type = move.piece # undo any promotions
        self.board[move.m_to] = None

        if move.flags & CAPTURE:
            self.board[move.m_to] = Piece(move.captured, them)
        elif move.flags & EP_CAPTURE:
            index = 0

            if us == BLACK:
                index = move.m_to - 16
            else:
                index = move.m_to + 16

            self.board[index] = Piece(PAWN, them)

        if move.flags & (KSIDE_CASTLE | QSIDE_CASTLE):
            castling_to = castling_from = 0

            if move.flags & KSIDE_CASTLE:
                castling_to = move.m_to + 1
                castling_from = move.m_to -1
            elif move.flags & QSIDE_CASTLE:
                castling_to = move.m_to - 2
                castling_from = move.m_to + 1

            self.board[castling_to] = self.board[castling_from]
            self.board[castling_from] = None

        return move

    def snapshot(self, move):
        self.history.append((self.copy(), move))

    # utility functions

    @staticmethod
    def get_san(i):
        return "abcdefgh"[Chess.get_file(i)] + "87654321"[Chess.get_rank(i)]

    @staticmethod
    def get_file(i):
        return i & 15

    @staticmethod
    def get_rank(i):
        return i >> 4

    @staticmethod
    def swap_color(color):
        return WHITE if color == BLACK else BLACK

    def get_enemy_move(self, fr_from, fr_to):
        matching_move = None

        for move in self.generate_moves():
            if (Chess.get_san(move.m_from) == fr_from and
                    Chess.get_san(move.m_to) == fr_to):
                matching_move = move
                break

        return matching_move

    def get_piece_value(self, square):
        piece = self.board[square]

        if not piece:
            return 0

        color = piece.color
        type = piece.type

        # add material and PST heuristic value
        value = PIECE_VALUES[type] + PST_VALUES[color][type][square]

        return value if color == WHITE else -value


class Piece:
    def __init__(self, type, color):
        self.type = type
        self.color = color


class Move:
    def __init__(self, board, color, m_from, m_to, flags, promotion=''):
        self.color = color
        self.m_from = m_from
        self.m_to = m_to
        self.flags = flags
        self.promotion = promotion
        self.piece = board[m_from].type
        self.captured = ''
        
        if promotion:
            self.flags |= PROMOTION

        if board[m_to]:
            self.captured = board[m_to].type
        elif flags & EP_CAPTURE:
            self.captured = PAWN

    def __eq__(self, other):
        return self.m_from == other.m_from and self.m_to == other.m_to

    def __str__(self):
        return "{} {} from {} to {}".format(
            self.color,
            self.piece,
            Chess.get_san(self.m_from),
            Chess.get_san(self.m_to))

    def __repr__(self):
        return self.__str__()
