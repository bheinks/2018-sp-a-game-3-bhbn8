# This is where you build your AI for the Chess game.

import random
from time import sleep

# local imports
from joueur.base_ai import BaseAI
from games.chess.engine import Chess

# <<-- Creer-Merge: imports -->> - Code you add between this comment and the end comment will be preserved between Creer re-runs.
# you can add additional import(s) here
# <<-- /Creer-Merge: imports -->>

class AI(BaseAI):
    """ The basic AI functions that are the same between games. """

    def get_name(self):
        """ This is the name you send to the server so your AI will control the player named this string.

        Returns
            str: The name of your Player.
        """
        # <<-- Creer-Merge: get-name -->> - Code you add between this comment and the end comment will be preserved between Creer re-runs.
        return "Chess Python Player" # REPLACE THIS WITH YOUR TEAM NAME
        # <<-- /Creer-Merge: get-name -->>

    def start(self):
        """ This is called once the game starts and your AI knows its playerID and game. You can initialize your AI here.
        """
        # <<-- Creer-Merge: start -->> - Code you add between this comment and the end comment will be preserved between Creer re-runs.
        
        # our local board representation
        self.chess = Chess(self.game.fen)

        # represents whether or not we want minimax to return high or low
        self.color_code = 1 if self.player.color == "White" else -1

        # depth limit
        self.depth_limit = int(self.get_setting("depth_limit"))

        # <<-- /Creer-Merge: start -->>

    def game_updated(self):
        """ This is called every time the game's state updates, so if you are tracking anything you can update it here.
        """
        # <<-- Creer-Merge: game-updated -->> - Code you add between this comment and the end comment will be preserved between Creer re-runs.
        # replace with your game updated logic
        # <<-- /Creer-Merge: game-updated -->>

    def end(self, won, reason):
        """ This is called when the game ends, you can clean up your data and dump files here if need be.

        Args:
            won (bool): True means you won, False means you lost.
            reason (str): The human readable string explaining why you won or lost.
        """
        # <<-- Creer-Merge: end -->> - Code you add between this comment and the end comment will be preserved between Creer re-runs.
        # replace with your end logic
        # <<-- /Creer-Merge: end -->>
    def run_turn(self):
        """ This is called every time it is this AI.player's turn.

        Returns:
            bool: Represents if you want to end your turn. True means end your turn, False means to keep your turn going and re-call this function.
        """
        # <<-- Creer-Merge: runTurn -->> - Code you add between this comment and the end comment will be preserved between Creer re-runs.

        if len(self.game.moves) > 0:
            self.update_last_move()

        move = self.minimax_root(self.depth_limit, self.chess, True)
        self.chess.move(move)
        
        print("Best move: {}".format(move))
        self.chess.print()
        print()
        
        promotion = '' if not move.promotion else Chess.PIECE_MAP[self.chess.board[move.m_to].type]

        for piece in self.player.pieces:
            if ''.join((piece.file, str(piece.rank))) == Chess.get_san(move.m_from):
                piece.move(*tuple(Chess.get_san(move.m_to)), promotionType=promotion)

        return True  # to signify we are done with our turn.

        # <<-- /Creer-Merge: runTurn -->>

    # <<-- Creer-Merge: functions -->> - Code you add between this comment and the end comment will be preserved between Creer re-runs.

    def update_last_move(self):
        move = self.game.moves[-1]
        fr_from = move.from_file + str(move.from_rank)
        fr_to = move.to_file + str(move.to_rank)
        self.chess.move(self.chess.get_enemy_move(fr_from, fr_to))

    def minimax_root(self, depth, game, is_max_player):
        moves = game.generate_moves()
        random.shuffle(moves)
        best_value = -9999
        best_move = None

        for move in moves:
            game.move(move)
            value = self.minimax(depth-1, game, not is_max_player)
            game.undo()

            if value >= best_value:
                best_value = value
                best_move = move

        return best_move

    def minimax(self, depth, game, is_max_player):
        if not depth:
            return game.value * self.color_code

        if game.in_draw():
            return 0

        moves = game.generate_moves()
        random.shuffle(moves)

        if is_max_player:
            best_value = -9999

            for move in moves:
                game.move(move)
                best_value = max(best_value, self.minimax(depth-1, game, not is_max_player))
                game.undo()

            return best_value
        else:
            best_value = 9999

            for move in moves:
                game.move(move)
                best_value = min(best_value, self.minimax(depth-1, game, not is_max_player))
                game.undo()

            return best_value

    def print_current_board(self):
        """Prints the current board using pretty ASCII art
        Note: you can delete this function if you wish
        """

        # iterate through the range in reverse order
        for r in range(9, -2, -1):
            output = ""
            if r == 9 or r == 0:
                # then the top or bottom of the board
                output = "   +------------------------+"
            elif r == -1:
                # then show the ranks
                output = "     a  b  c  d  e  f  g  h"
            else:  # board
                output = " " + str(r) + " |"
                # fill in all the files with pieces at the current rank
                for file_offset in range(0, 8):
                    # start at a, with with file offset increasing the char
                    f = chr(ord("a") + file_offset)
                    current_piece = None
                    for piece in self.game.pieces:
                        if piece.file == f and piece.rank == r:
                            # then we found the piece at (file, rank)
                            current_piece = piece
                            break

                    code = "."  # default "no piece"
                    if current_piece:
                        # the code will be the first character of their type
                        # e.g. 'Q' for "Queen"
                        code = current_piece.type[0]

                        if current_piece.type == "Knight":
                            # 'K' is for "King", we use 'N' for "Knights"
                            code = "N"

                        if current_piece.owner.id == "1":
                            # the second player (black) is lower case.
                            # Otherwise it's uppercase already
                            code = code.lower()

                    output += " " + code + " "

                output += "|"
            print(output)

    # <<-- /Creer-Merge: functions -->>
