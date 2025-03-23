import pygame as py
import sys
import chess
from stockfish import Stockfish
import time

py.init()
py.mixer.init()
board = chess.Board()
stockfish = Stockfish(path="stockfish-windows-x86-64-avx2.exe")
# stockfish.set_skill_level(skill_level=1)
# stockfish.set_elo_rating(250)

SCREEN_WIDTH = 640
SCREEN_HEIGHT = 640
screen = py.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
py.display.set_caption("Chess Developed by Debjit Paul")
if True: # importing all the images and sounds
    WHITE_PAWN = py.image.load("imgs/Pieces/White Pieces/White Pawn.png").convert_alpha()
    WHITE_ROOK = py.image.load("imgs/Pieces/White Pieces/White Rook.png").convert_alpha()
    WHITE_KNIGHT = py.image.load("imgs/Pieces/White Pieces/White Knight.png").convert_alpha()
    WHITE_BISHOP = py.image.load("imgs/Pieces/White Pieces/White Bishop.png").convert_alpha()
    WHITE_QUEEN = py.image.load("imgs/Pieces/White Pieces/White Queen.png").convert_alpha()
    WHITE_KING = py.image.load("imgs/Pieces/White Pieces/White King.png").convert_alpha()

    BLACK_PAWN = py.image.load("imgs/Pieces/Black Pieces/Black Pawn.png").convert_alpha()
    BLACK_ROOK = py.image.load("imgs/Pieces/Black Pieces/Black Rook.png").convert_alpha()
    BLACK_KNIGHT = py.image.load("imgs/Pieces/Black Pieces/Black Knight.png").convert_alpha()
    BLACK_BISHOP = py.image.load("imgs/Pieces/Black Pieces/Black Bishop.png").convert_alpha()
    BLACK_QUEEN = py.image.load("imgs/Pieces/Black Pieces/Black Queen.png").convert_alpha()
    BLACK_KING = py.image.load("imgs/Pieces/Black Pieces/Black King.png").convert_alpha()

    LEGAL_MOVES = py.image.load("imgs/Legal Moves.png").convert_alpha()
    CAPTURABLE = py.image.load("imgs/Capturable.png")
    CAPTURABLE.set_alpha(100)
    CHECKMATE_SCREEN = py.image.load("imgs/Checkmate Screen.png")
    CHECKMATE_SCREEN.set_alpha(5)
    PAWN_PROMOTION_SCREEN = py.image.load("imgs/Pawn Promotion Screen.png")
    STAT_FONT = py.font.SysFont("comicsans", 50)
    CAPTURE = py.mixer.Sound("capture.mp3")
    MOVE = py.mixer.Sound("move-self.mp3")


White_pieces_cordinates = []
Black_pieces_cordinates = []
All_pieces_cordinates = {}
White_king_pos = []
Black_king_pos = []

PLayer = "White"
Selected = False
Clicked = False
Moved = False
First = True
Checkmate = False
PC_turn = False
start_time = None
moves = []

game_notation_to_coordinate_conversion = {
    "ranks":{
        "a": 0,
        "b": 80,
        "c": 160,
        "d": 240,
        "e": 320,
        "f": 400,
        "g": 480,
        "h": 560,
    },
    "files":{
        8 : 0,
        7 : 80,
        6 : 160,
        5 : 240,
        4 : 320,
        3 : 400,
        2 : 480,
        1 : 560,
    }
}

coordinate_to_game_notation_conversion = {
    "ranks":{
        range(0,80) : "a",
        range(80,160) : "b",
        range(160,240) : "c",
        range(240,320) : "d",
        range(320,400) : "e",
        range(400,480) : "f",
        range(480,560) : "g",
        range(560,640) : "h",
    },
    "files":{
        range(0,80) : 8,
        range(80,160) : 7,
        range(160,240) : 6,
        range(240,320) : 5,
        range(320,400) : 4,
        range(400,480) : 3,
        range(480,560) : 2,
        range(560,640) : 1,
    }
}

def get_game_notation(x, y):
    rank = None
    file = None
    for r in coordinate_to_game_notation_conversion["ranks"]:
        if x in r:
            rank = coordinate_to_game_notation_conversion["ranks"][r]
            break
    for f in coordinate_to_game_notation_conversion["files"]:
        if y in f:
            file = coordinate_to_game_notation_conversion["files"][f]
            break
    return rank, file

def Check(piece):
    rem = []
    opponent_pieces = Black_pieces if piece.color == "White" else White_pieces
    legal_moves, capturable = piece.legal_moves()
    
    # Remove the piece's current position from its team's coordinates
    piece.my_team_coordinates.remove((piece.rank, piece.file))

    for move in legal_moves:
        # Simulate the move
        piece.my_team_coordinates.append(move)
        if isinstance(piece, King):
            piece.king_pos.remove((piece.rank, piece.file))
            piece.king_pos.append(move)

        # Check for captures
        captured_piece = None
        if move in capturable:
            for capture_piece in opponent_pieces:
                if capture_piece.rank == move[0] and capture_piece.file == move[1]:
                    captured_piece = capture_piece
                    capture_piece.my_team_coordinates.remove(move)
                    opponent_pieces.remove(capture_piece)
                    break

        # Recalculate opponent influence
        opponent_influence = []
        for oppo_piece in opponent_pieces:
            piece_influ, _ = oppo_piece.legal_moves()
            opponent_influence.extend(piece_influ)

        # Check if the move leaves the king in check
        if piece.king_pos[0] in opponent_influence:
            rem.append(move)

        # Restore the capture piece
        if captured_piece:
            captured_piece.my_team_coordinates.append(move)
            opponent_pieces.append(captured_piece)

        # Undo the simulated move
        piece.my_team_coordinates.remove(move)
        if isinstance(piece, King):
            piece.king_pos.remove(move)
            piece.king_pos.append((piece.rank, piece.file))
    
    # Restore the piece's current position to its team's coordinates
    piece.my_team_coordinates.append((piece.rank, piece.file))
    
    # Remove illegal moves
    for rems in rem:
        if rems in legal_moves:
            legal_moves.remove(rems)
        if rems in capturable:
            capturable.remove(rems)
    
    return legal_moves, capturable


class Chess_Pieces():
    def __init__(self, color, rank, file):
        self.color = color
        self.file = file
        self.rank = rank
        self.my_team_coordinates = None
        self.opponent_team_coordinates = None
        self.first_move = True
        self.opponent = "Black" if self.color == "White" else "White"
        self.coordinate = (game_notation_to_coordinate_conversion["ranks"][self.rank], game_notation_to_coordinate_conversion["files"][self.file])
        self.selected = False
        if self.color == "White":
            White_pieces_cordinates.append((self.rank, self.file))
            self.king_pos = White_king_pos
            if isinstance(self, King):
                White_king_pos.append((self.rank, self.file))
                # print(self.king_pos)
        if self.color == "Black":
            Black_pieces_cordinates.append((self.rank, self.file))
            self.king_pos = Black_king_pos
            if isinstance(self, King):
                Black_king_pos.append((self.rank, self.file))
                # print(self.king_pos)

    def position_intializer(self):
        self.my_team_coordinates = White_pieces_cordinates if self.color == "White" else Black_pieces_cordinates
        self.opponent_team_coordinates = Black_pieces_cordinates if self.color == "White" else White_pieces_cordinates

    def move(self):
        global Selected, Clicked, Moved
        cursor_pos = py.mouse.get_pos()
        if py.mouse.get_pressed()[0]:
            x, y = self.coordinate
            if py.Rect(x, y, 80, 80).collidepoint(cursor_pos) or Selected:
                if not Selected or self.selected:
                    Selected = True
                    self.selected = True
                    self.coordinate = cursor_pos[0] - 40, cursor_pos[1] - 40
                    # self.temp_rank, self.temp_file = get_game_notation(cursor_pos[0], cursor_pos[1])
                    legal_moves, capturable = self.legal_moves()
                    # print(capturable)
                    # print(self.my_team_coordinates)
                    # print((self.rank, self.file))
                    legal_moves, capturable = Check(self)
                    for coordinate in legal_moves:
                        coordinate = (game_notation_to_coordinate_conversion["ranks"][coordinate[0]], game_notation_to_coordinate_conversion["files"][coordinate[1]])
                        screen.blit(LEGAL_MOVES, coordinate)
                    for coordinates in capturable:
                        coordinates = (game_notation_to_coordinate_conversion["ranks"][coordinates[0]], game_notation_to_coordinate_conversion["files"][coordinates[1]])
                        screen.blit(CAPTURABLE, coordinates)

                    Clicked = True
        else:
            self.coordinate = (game_notation_to_coordinate_conversion["ranks"][self.rank], game_notation_to_coordinate_conversion["files"][self.file])
            Selected = False
            self.selected = False
        Moved = True if Clicked else False
        Clicked = False
            
    def legal_move_validation(self):
        global Moved, PLayer, Checkmate, moves
        cursor_pos = py.mouse.get_pos()
        legal_moves, capturable = self.legal_moves()
        legal_moves, capturable = Check(self)
        rank, file = get_game_notation(cursor_pos[0], cursor_pos[1])

        
        if (rank, file) in legal_moves:
            # print("Yes")
            # print("Y")
            for event in py.event.get():
                if event.type == py.MOUSEBUTTONUP:

                    moves.append("".join((self.rank, str(self.file), rank, str(file))))
                    board.push_san("".join((self.rank, str(self.file), rank, str(file))))
                    print(board, "\n")
                    self.my_team_coordinates.remove((self.rank, self.file))
                    if (self.rank, self.file) in self.my_team_coordinates:
                        self.my_team_coordinates.remove((self.rank, self.file))

                    if isinstance(self, King):
                        self.king_pos.remove((self.rank, self.file))

                    self.rank, self.file = rank, file
                    self.coordinate = (game_notation_to_coordinate_conversion["ranks"][self.rank], game_notation_to_coordinate_conversion["files"][self.file])
                    self.my_team_coordinates.append((self.rank, self.file))
                    PLayer = "White" if PLayer == "Black" else "Black"
                    Opponent_pieces = White_pieces if self.color == "Black" else Black_pieces
                    if isinstance(self, King):
                        self.king_pos.append((self.rank, self.file))
                        if self.short_castle[0] and self.short_castle[1] == (rank, file):# Castling
                            self.short_castle_rook[0].my_team_coordinates.remove((self.short_castle_rook[0].rank, self.short_castle_rook[0].file))
                            self.short_castle_rook[0].rank, self.short_castle_rook[0].file = self.short_castle_rook[1]
                            self.short_castle_rook[0].coordinate = (game_notation_to_coordinate_conversion["ranks"][self.short_castle_rook[0].rank], game_notation_to_coordinate_conversion["files"][self.short_castle_rook[0].file])
                            self.short_castle_rook[0].my_team_coordinates.append((self.short_castle_rook[0].rank, self.short_castle_rook[0].file))
                        if self.long_castle[0] and self.long_castle[1] == (rank, file):
                            self.long_castle_rook[0].my_team_coordinates.remove((self.long_castle_rook[0].rank, self.long_castle_rook[0].file))
                            self.long_castle_rook[0].rank, self.long_castle_rook[0].file = self.long_castle_rook[1]
                            self.long_castle_rook[0].coordinate = (game_notation_to_coordinate_conversion["ranks"][self.long_castle_rook[0].rank], game_notation_to_coordinate_conversion["files"][self.long_castle_rook[0].file])
                            self.long_castle_rook[0].my_team_coordinates.append((self.long_castle_rook[0].rank, self.long_castle_rook[0].file))

                    for Pawns in Opponent_pieces:
                        if isinstance(Pawns, Pawn):
                            Pawns.en_passant = False
                    self.first_move = False
                    if (rank, file) in capturable:
                        CAPTURE.play()
                        for piece in Opponent_pieces:
                            if piece.rank == rank and piece.file == file:
                                Opponent_pieces.remove(piece)
                                self.opponent_team_coordinates.remove((rank, file))
                        if isinstance(self, Pawn):
                            if self.en_passant_eating_piece[0] and self.en_passant_eating_piece[1] == (rank, file):
                                Opponent_pieces.remove(self.en_passant_eating_piece[0])
                                self.opponent_team_coordinates.remove((self.en_passant_eating_piece[0].rank, self.en_passant_eating_piece[0].file))
                    else:
                        MOVE.play()
                    Possible_moves = []
                    for piece in Opponent_pieces:
                        moves, _ = piece.legal_moves()
                        moves, _ = Check(piece)
                        Possible_moves.extend(moves)
                    if Possible_moves == []:
                        Checkmate = True
            Moved = False

    def draw(self):
        screen.blit(self.image, self.coordinate)

class Pawn(Chess_Pieces):
    def __init__(self, color, rank, file):
        Chess_Pieces.__init__(self, color, rank, file)
        self.image = WHITE_PAWN if self.color == "White" else BLACK_PAWN
        self.en_passant = False
        self.en_passant_eating_piece = [None, None]
        self.promoted = False
        self.point = 1

    def legal_moves(self):
        legal_moves = []
        capturable = []
        All_pieces_cordinates = White_pieces_cordinates + Black_pieces_cordinates  # Combine all pieces' coordinates

        # Promotion
        if self.color == "White" and self.file == 8:
            self.promoted = True
        elif self.color == "Black" and self.file == 1:
            self.promoted = True

        # Pawn movement
        if self.color == "White":
            if (self.rank, self.file + 1) not in All_pieces_cordinates:
                legal_moves.append((self.rank, self.file + 1))
                if self.first_move and (self.rank, self.file + 2) not in All_pieces_cordinates:
                    legal_moves.append((self.rank, self.file + 2))
                    self.en_passant = True

            # En-passant capture for White pawns
            if self.file == 5:
                if (chr(ord(self.rank) + 1), self.file) in self.opponent_team_coordinates:
                    opponent_pawn = None
                    for piece in Black_pieces:
                        if isinstance(piece, Pawn) and piece.rank == chr(ord(self.rank) + 1) and piece.file == self.file:
                            opponent_pawn = piece
                            self.en_passant_eating_piece = [opponent_pawn, None]
                            break
                    if opponent_pawn and opponent_pawn.en_passant:
                        legal_moves.append((chr(ord(self.rank) + 1), self.file + 1))
                        capturable.append((chr(ord(self.rank) + 1), self.file + 1))
                        self.en_passant_eating_piece[1] = (chr(ord(self.rank) + 1), self.file + 1)

                if (chr(ord(self.rank) - 1), self.file) in self.opponent_team_coordinates:
                    opponent_pawn = None
                    for piece in Black_pieces:
                        if isinstance(piece, Pawn) and piece.rank == chr(ord(self.rank) - 1) and piece.file == self.file:
                            opponent_pawn = piece
                            self.en_passant_eating_piece = [opponent_pawn, None]
                            break
                    if opponent_pawn and opponent_pawn.en_passant:
                        legal_moves.append((chr(ord(self.rank) - 1), self.file + 1))
                        capturable.append((chr(ord(self.rank) - 1), self.file + 1))
                        self.en_passant_eating_piece[1] = (chr(ord(self.rank) - 1), self.file + 1)

            # Capturing moves
            if (chr(ord(self.rank) + 1), self.file + 1) in self.opponent_team_coordinates:
                legal_moves.append((chr(ord(self.rank) + 1), self.file + 1))
                capturable.append((chr(ord(self.rank) + 1), self.file + 1))
            if (chr(ord(self.rank) - 1), self.file + 1) in self.opponent_team_coordinates:
                legal_moves.append((chr(ord(self.rank) - 1), self.file + 1))
                capturable.append((chr(ord(self.rank) - 1), self.file + 1))


        elif self.color == "Black":
            if (self.rank, self.file - 1) not in All_pieces_cordinates:
                legal_moves.append((self.rank, self.file - 1))
                if self.first_move and (self.rank, self.file - 2) not in All_pieces_cordinates:
                    legal_moves.append((self.rank, self.file - 2))
                    self.en_passant = True  # Set en_passant for Black pawns

            # En-passant capture for Black pawns
            if self.file == 4:
                if (chr(ord(self.rank) + 1), self.file) in self.opponent_team_coordinates:
                    opponent_pawn = None
                    for piece in White_pieces:
                        if isinstance(piece, Pawn) and piece.rank == chr(ord(self.rank) + 1) and piece.file == self.file:
                            opponent_pawn = piece
                            break
                    if opponent_pawn and opponent_pawn.en_passant:
                        legal_moves.append((chr(ord(self.rank) + 1), self.file - 1))
                        capturable.append((chr(ord(self.rank) + 1), self.file - 1))

                if (chr(ord(self.rank) - 1), self.file) in self.opponent_team_coordinates:
                    opponent_pawn = None
                    for piece in White_pieces:
                        if isinstance(piece, Pawn) and piece.rank == chr(ord(self.rank) - 1) and piece.file == self.file:
                            opponent_pawn = piece
                            break
                    if opponent_pawn and opponent_pawn.en_passant:
                        legal_moves.append((chr(ord(self.rank) - 1), self.file - 1))
                        capturable.append((chr(ord(self.rank) - 1), self.file - 1))

            # Capturing moves
            if (chr(ord(self.rank) + 1), self.file - 1) in self.opponent_team_coordinates:
                legal_moves.append((chr(ord(self.rank) + 1), self.file - 1))
                capturable.append((chr(ord(self.rank) + 1), self.file - 1))
            if (chr(ord(self.rank) - 1), self.file - 1) in self.opponent_team_coordinates:
                legal_moves.append((chr(ord(self.rank) - 1), self.file - 1))
                capturable.append((chr(ord(self.rank) - 1), self.file - 1))

        return legal_moves, capturable

class Rook(Chess_Pieces):#Castling
    def __init__(self, color, rank, file):
        Chess_Pieces.__init__(self, color, rank, file)
        self.image = WHITE_ROOK if self.color == "White" else BLACK_ROOK
        self.point = 5

    def legal_moves(self):
        legal_moves = []
        capturable = []
        for up_move in range(self.file + 1, 9):
            if (self.rank, up_move) in self.my_team_coordinates:
                break
            elif (self.rank, up_move) in self.opponent_team_coordinates:
                legal_moves.append((self.rank, up_move))
                capturable.append((self.rank, up_move))
                break
            else:
                legal_moves.append((self.rank, up_move))

        for down_move in range(self.file - 1, 0, -1):
            if (self.rank, down_move) in self.my_team_coordinates:
                break
            elif (self.rank, down_move) in self.opponent_team_coordinates:
                legal_moves.append((self.rank, down_move))
                capturable.append((self.rank, down_move))
                break
            else:
                legal_moves.append((self.rank, down_move))

        for left_move in range(ord(self.rank) + 1, 105):
            if (chr(left_move), self.file) in self.my_team_coordinates:
                break
            elif (chr(left_move), self.file) in self.opponent_team_coordinates:
                legal_moves.append((chr(left_move), self.file))
                capturable.append((chr(left_move), self.file))
                break
            else:
                legal_moves.append((chr(left_move), self.file))

        for right_move in range(ord(self.rank) - 1, 96, -1):
            if (chr(right_move), self.file) in self.my_team_coordinates:
                break
            elif (chr(right_move), self.file) in self.opponent_team_coordinates:
                legal_moves.append((chr(right_move), self.file))
                capturable.append((chr(right_move), self.file))
                break
            else:
                legal_moves.append((chr(right_move), self.file))
        
        
        return legal_moves, capturable

class Knight(Chess_Pieces):
    def __init__(self, color, rank, file):
        Chess_Pieces.__init__(self, color, rank, file)
        self.image = WHITE_KNIGHT if self.color == "White" else BLACK_KNIGHT
        self.point = 3

    def legal_moves(self):
        legal_moves = []
        capturable = []
        if not ord(self.rank) + 2 > 104 and not self.file - 1 < 1 and (chr(ord(self.rank) + 2), self.file - 1) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) + 2), self.file - 1))
            if (chr(ord(self.rank) + 2), self.file - 1) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) + 2), self.file - 1))

        if not ord(self.rank) + 2 > 104 and not self.file + 1 > 8 and (chr(ord(self.rank) + 2), self.file + 1) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) + 2), self.file + 1))
            if (chr(ord(self.rank) + 2), self.file + 1) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) + 2), self.file + 1))

        if not ord(self.rank) - 2 < 97 and not self.file - 1 < 1 and (chr(ord(self.rank) - 2), self.file - 1) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) - 2), self.file - 1))
            if (chr(ord(self.rank) - 2), self.file - 1) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) - 2), self.file - 1))

        if not ord(self.rank) - 2 < 97 and not self.file + 1 > 8 and (chr(ord(self.rank) - 2), self.file + 1) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) - 2), self.file + 1))
            if (chr(ord(self.rank) - 2), self.file + 1) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) - 2), self.file + 1))


        if not ord(self.rank) + 1 > 104 and not self.file - 2 < 1 and (chr(ord(self.rank) + 1), self.file - 2) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) + 1), self.file - 2))
            if (chr(ord(self.rank) + 1), self.file - 2) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) + 1), self.file - 2))

        if not ord(self.rank) + 1 > 104 and not self.file + 2 > 8 and (chr(ord(self.rank) + 1), self.file + 2) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) + 1), self.file + 2))
            if (chr(ord(self.rank) + 1), self.file + 2) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) + 1), self.file + 2))

        if not ord(self.rank) - 1 < 97 and not self.file - 2 < 1 and (chr(ord(self.rank) - 1), self.file - 2) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) - 1), self.file - 2))
            if (chr(ord(self.rank) - 1), self.file - 2) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) - 1), self.file - 2))

        if not ord(self.rank) - 1 < 97 and not self.file + 2 > 8 and (chr(ord(self.rank) - 1), self.file + 2) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) - 1), self.file + 2))
            if (chr(ord(self.rank) - 1), self.file + 2) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) - 1), self.file + 2))
        

        return legal_moves, capturable

class Bishop(Chess_Pieces):
    def __init__(self, color, rank, file):
        Chess_Pieces.__init__(self, color, rank, file)
        self.image = WHITE_BISHOP if self.color == "White" else BLACK_BISHOP
        self.score = 3

    def legal_moves(self):
        legal_moves = []
        capturable = []
        for rank in range(ord(self.rank) + 1, 105):
            if (chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)) in self.my_team_coordinates or ((rank - 96) + self.file - (ord(self.rank) - 96)) > 8 or ((rank - 96) + self.file - (ord(self.rank) - 96)) < 1:
                break
            elif (chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)) in self.opponent_team_coordinates:
                legal_moves.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))
                capturable.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))
                break
            else:
                legal_moves.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))

        for rank in range(ord(self.rank) - 1, 96, -1):
            if (chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)) in self.my_team_coordinates or ((rank - 96) + self.file - (ord(self.rank) - 96)) > 8 or ((rank - 96) + self.file - (ord(self.rank) - 96)) < 1:
                break
            elif (chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)) in self.opponent_team_coordinates:
                legal_moves.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))
                capturable.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))
                break
            else:
                legal_moves.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))

        for rank in range(ord(self.rank) - 1, 96, -1):
            if (chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))) in self.my_team_coordinates or ((105 - rank) + self.file - (105 - ord(self.rank))) > 8 or ((105 - rank) + self.file - (105 - ord(self.rank))) < 1:
                break
            elif (chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))) in self.opponent_team_coordinates:
                legal_moves.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))
                capturable.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))
                break
            else:
                legal_moves.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))

        for rank in range(ord(self.rank) + 1, 105):
            if (chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))) in self.my_team_coordinates or ((105 - rank) + self.file - (105 - ord(self.rank))) > 8 or ((105 - rank) + self.file - (105 - ord(self.rank))) < 1:
                break
            elif (chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))) in self.opponent_team_coordinates:
                legal_moves.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))
                capturable.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))
                break
            else:
                legal_moves.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))
        

        return legal_moves, capturable

class Queen(Chess_Pieces):
    def __init__(self, color, rank, file):
        Chess_Pieces.__init__(self, color, rank, file)
        self.image = WHITE_QUEEN if self.color == "White" else BLACK_QUEEN
        self.score = 9

    def legal_moves(self):
        legal_moves = []
        capturable = []
        if True: # Straight Moves
            for up_move in range(self.file + 1, 9):
                if (self.rank, up_move) in self.my_team_coordinates:
                    break
                elif (self.rank, up_move) in self.opponent_team_coordinates:
                    legal_moves.append((self.rank, up_move))
                    capturable.append((self.rank, up_move))
                    break
                else:
                    legal_moves.append((self.rank, up_move))

            for down_move in range(self.file - 1, 0, -1):
                if (self.rank, down_move) in self.my_team_coordinates:
                    break
                elif (self.rank, down_move) in self.opponent_team_coordinates:
                    legal_moves.append((self.rank, down_move))
                    capturable.append((self.rank, down_move))
                    break
                else:
                    legal_moves.append((self.rank, down_move))

            for left_move in range(ord(self.rank) + 1, 105):
                if (chr(left_move), self.file) in self.my_team_coordinates:
                    break
                elif (chr(left_move), self.file) in self.opponent_team_coordinates:
                    legal_moves.append((chr(left_move), self.file))
                    capturable.append((chr(left_move), self.file))
                    break
                else:
                    legal_moves.append((chr(left_move), self.file))

            for right_move in range(ord(self.rank) - 1, 96, -1):
                if (chr(right_move), self.file) in self.my_team_coordinates:
                    break
                elif (chr(right_move), self.file) in self.opponent_team_coordinates:
                    legal_moves.append((chr(right_move), self.file))
                    capturable.append((chr(right_move), self.file))
                    break
                else:
                    legal_moves.append((chr(right_move), self.file))
        if True: # Diagonal Moves
            for rank in range(ord(self.rank) + 1, 105):
                if (chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)) in self.my_team_coordinates or ((rank - 96) + self.file - (ord(self.rank) - 96)) > 8 or ((rank - 96) + self.file - (ord(self.rank) - 96)) < 1:
                    break
                elif (chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)) in self.opponent_team_coordinates:
                    legal_moves.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))
                    capturable.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))
                    break
                else:
                    legal_moves.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))

            for rank in range(ord(self.rank) - 1, 96, -1):
                if (chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)) in self.my_team_coordinates or ((rank - 96) + self.file - (ord(self.rank) - 96)) > 8 or ((rank - 96) + self.file - (ord(self.rank) - 96)) < 1:
                    break
                elif (chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)) in self.opponent_team_coordinates:
                    legal_moves.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))
                    capturable.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))
                    break
                else:
                    legal_moves.append((chr(rank), (rank - 96) + self.file - (ord(self.rank) - 96)))

            for rank in range(ord(self.rank) - 1, 96, -1):
                if (chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))) in self.my_team_coordinates or ((105 - rank) + self.file - (105 - ord(self.rank))) > 8 or ((105 - rank) + self.file - (105 - ord(self.rank))) < 1:
                    break
                elif (chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))) in self.opponent_team_coordinates:
                    legal_moves.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))
                    capturable.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))
                    break
                else:
                    legal_moves.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))

            for rank in range(ord(self.rank) + 1, 105):
                if (chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))) in self.my_team_coordinates or ((105 - rank) + self.file - (105 - ord(self.rank))) > 8 or ((105 - rank) + self.file - (105 - ord(self.rank))) < 1:
                    break
                elif (chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))) in self.opponent_team_coordinates:
                    legal_moves.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))
                    capturable.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))
                    break
                else:
                    legal_moves.append((chr(rank), (105 - rank) + self.file - (105 - ord(self.rank))))
        

        return legal_moves, capturable

class King(Chess_Pieces):
    def __init__(self, color, rank, file):
        Chess_Pieces.__init__(self, color, rank, file)
        self.image = WHITE_KING if self.color == "White" else BLACK_KING
        self.score = 100
        self.short_castle = [False, None]
        self.long_castle = [False, None]
        self.short_castle_rook = [None, None]
        self.long_castle_rook = [None, None]

    def legal_moves(self):
        legal_moves = []
        capturable = []
        if not ord(self.rank) + 1 > 104 and not self.file - 1 < 1 and (chr(ord(self.rank) + 1), self.file - 1) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) + 1), self.file - 1))
            if (chr(ord(self.rank) + 1), self.file - 1) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) + 1), self.file - 1))
                
        if not ord(self.rank) + 1 > 104 and not self.file + 1 > 8 and (chr(ord(self.rank) + 1), self.file + 1) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) + 1), self.file + 1))
            if (chr(ord(self.rank) + 1), self.file + 1) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) + 1), self.file + 1))
                
        if not ord(self.rank) - 1 < 97 and not self.file - 1 < 1 and (chr(ord(self.rank) - 1), self.file - 1) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) - 1), self.file - 1))
            if (chr(ord(self.rank) - 1), self.file - 1) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) - 1), self.file - 1))
                
        if not ord(self.rank) - 1 < 97 and not self.file + 1 > 8 and (chr(ord(self.rank) - 1), self.file + 1) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) - 1), self.file + 1))
            if (chr(ord(self.rank) - 1), self.file + 1) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) - 1), self.file + 1))
                
        if not ord(self.rank) + 1 > 104 and (chr(ord(self.rank) + 1), self.file) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) + 1), self.file))
            if (chr(ord(self.rank) + 1), self.file) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) + 1), self.file))
                
        if not ord(self.rank) - 1 < 97 and (chr(ord(self.rank) - 1), self.file) not in self.my_team_coordinates:
            legal_moves.append((chr(ord(self.rank) - 1), self.file))
            if (chr(ord(self.rank) - 1), self.file) in self.opponent_team_coordinates:
                capturable.append((chr(ord(self.rank) - 1), self.file))
                
        if not self.file + 1 > 8 and (self.rank, self.file + 1) not in self.my_team_coordinates:
            legal_moves.append((self.rank, self.file + 1))
            if (self.rank, self.file + 1) in self.opponent_team_coordinates:
                capturable.append((self.rank, self.file + 1))
                
        if not self.file - 1 < 1 and (self.rank, self.file - 1) not in self.my_team_coordinates:
            legal_moves.append((self.rank, self.file - 1))
            if (self.rank, self.file - 1) in self.opponent_team_coordinates:
                capturable.append((self.rank, self.file - 1))
        
        Opponent_pieces = White_pieces if self.color == "Black" else Black_pieces
        if self.first_move:
            opponent_influence = [] 
            if self.color == "White":
                # print("0")
                for rook in White_pieces:
                    if isinstance(rook, Rook) and rook.rank == "h" and rook.first_move:
                        # print("1")
                        opponent_influence = []
                        for oppo_piece in Opponent_pieces:
                            if not (isinstance(oppo_piece, King) and oppo_piece.first_move):
                                # print("2")
                                opponent_legal_moves, _ = oppo_piece.legal_moves()
                                opponent_influence.extend(opponent_legal_moves)
                        # print(opponent_influence)
                        # print(self.king_pos)
                        if not (("e", 1) in opponent_influence or (("f", 1) in opponent_influence or ("f", 1) in self.my_team_coordinates) or (("g", 1) in opponent_influence or ("g", 1) in self.my_team_coordinates) or ("h", 1) in opponent_influence):
                            # print("Appended")
                            legal_moves.append(("g", 1))
                            self.short_castle = [True, ("g", 1)]
                            self.short_castle_rook = [rook, ("f", 1)]
                            break
                        else:
                            # print("Not Appended")
                            self.short_castle = [False, None]
                            self.short_castle_rook = [None, None]
                    else:
                        self.short_castle = [False, None]
                        self.short_castle_rook = [None, None]

                    if isinstance(rook, Rook) and rook.rank == "a" and rook.first_move:
                        # print("1")
                        opponent_influence = []
                        for oppo_piece in Opponent_pieces:
                            if not (isinstance(oppo_piece, King) and oppo_piece.first_move):
                                # print("2")
                                opponent_legal_moves, _ = oppo_piece.legal_moves()
                                opponent_influence.extend(opponent_legal_moves)
                        if not (("e", 1) in opponent_influence or (("d", 1) in opponent_influence or ("d", 1) in self.my_team_coordinates) or (("c", 1) in opponent_influence or ("c", 1) in self.my_team_coordinates) or (("b", 1) in opponent_influence or ("b", 1) in self.my_team_coordinates) or ("a", 1) in opponent_influence):
                            # print("Appended")
                            legal_moves.append(("c", 1))
                            self.long_castle = [True, ("c", 1)]
                            self.long_castle_rook = [rook, ("d", 1)]
                            break
                        else:
                            self.long_castle = [False, None]
                            self.long_castle_rook = [None, None]
                    else:
                        self.long_castle = [False, None]
                        self.long_castle_rook = [None, None]
            if self.color == "Black":
                for rook in Black_pieces:
                    if isinstance(rook, Rook) and rook.rank == "h" and rook.first_move:
                        opponent_influence = []
                        for oppo_piece in Opponent_pieces:
                            if not (isinstance(oppo_piece, King) and oppo_piece.first_move):
                                opponent_legal_moves, _ = oppo_piece.legal_moves()
                                opponent_influence.extend(opponent_legal_moves)
                        if not (("e", 8) in opponent_influence or (("f", 8) in opponent_influence or ("f", 8) in self.my_team_coordinates) or (("g", 8) in opponent_influence or ("g", 8) in self.my_team_coordinates) or ("h", 8) in opponent_influence):
                            legal_moves.append(("g", 8))
                            self.short_castle = [True, ("g", 8)]
                            self.short_castle_rook = [rook, ("f", 8)]
                        else:
                            self.short_castle = [False, None]
                            self.short_castle_rook = [None, None]
                        break
                    else:
                        self.short_castle = [False, None]
                        self.short_castle_rook = [None, None]
                    if isinstance(rook, Rook) and rook.rank == "a" and rook.first_move:
                        opponent_influence = []
                        for oppo_piece in Opponent_pieces:
                            if not (isinstance(oppo_piece, King) and oppo_piece.first_move):
                                opponent_legal_moves, _ = oppo_piece.legal_moves()
                                opponent_influence.extend(opponent_legal_moves)
                        if not (("e", 8) in opponent_influence or (("d", 8) in opponent_influence or ("d", 8) in self.my_team_coordinates) or (("c", 8) in opponent_influence or ("c", 8) in self.my_team_coordinates) or (("b", 8) in opponent_influence or ("b", 8) in self.my_team_coordinates) or ("a", 8) in opponent_influence):
                            legal_moves.append(("c", 8))
                            self.long_castle = [True, ("c", 8)]
                            self.long_castle_rook = [rook, ("d", 8)]
                        else:
                            self.long_castle = [False, None]
                            self.long_castle_rook = [None, None]
                        break
                    else:
                        self.long_castle = [False, None]
                        self.long_castle_rook = [None, None]

        return legal_moves, capturable


White_pieces = [Pawn("White", "a", 2),Pawn("White", "b", 2),Pawn("White", "c", 2),Pawn("White", "d", 2),Pawn("White", "e", 2),Pawn("White", "f", 2),Pawn("White", "g", 2),Pawn("White", "h", 2), Rook("White", "a", 1),Rook("White", "h", 1), Knight("White", "b", 1),Knight("White", "g", 1), Bishop("White", "c", 1),Bishop("White", "f", 1), Queen("White", "d", 1), King("White", "e", 1)]
for piece in White_pieces:
    piece.position_intializer()

Black_pieces = [Pawn("Black", "a", 7),Pawn("Black", "b", 7),Pawn("Black", "c", 7),Pawn("Black", "d", 7),Pawn("Black", "e", 7),Pawn("Black", "f", 7),Pawn("Black", "g", 7),Pawn("Black", "h", 7), Rook("Black", "a", 8),Rook("Black", "h", 8), Knight("Black", "b", 8),Knight("Black", "g", 8), Bishop("Black", "c", 8),Bishop("Black", "f", 8), Queen("Black", "d", 8), King("Black", "e", 8)]
for piece in Black_pieces:
    piece.position_intializer()

def Draw_Board():
    box_color_interchange = 0
    for file in range(0,640,80):
        for row in range(0,640,80):
            box = py.Rect(file, row, 80, 80)
            if box_color_interchange == 0:
                r, g, b = 120, 80, 70
                box_color_interchange = 1
            elif box_color_interchange == 1:
                r, g, b = 180, 140, 130
                box_color_interchange = 0
            py.draw.rect(screen, (r, g, b), box)
        if box_color_interchange == 0:
            box_color_interchange = 1
        elif box_color_interchange == 1:
            box_color_interchange = 0

def Update_coordinate_and_draw(pieces):
        for piece in pieces:
            piece.move()
            piece.draw()

def Pawn_promotion(piece):
    Promotion_screen_not_selected = True
    New_Queen = py.Rect(220, 220, 85, 85)
    New_Rook = py.Rect(350, 220, 85, 85)
    New_Bishop = py.Rect(220, 330, 85, 85)
    New_Knight = py.Rect(350, 330, 85, 85)
    while Promotion_screen_not_selected:
        pos = py.mouse.get_pos()
        screen.blit(CHECKMATE_SCREEN, (0, 0))
        screen.blit(PAWN_PROMOTION_SCREEN, (SCREEN_WIDTH - PAWN_PROMOTION_SCREEN.get_width() - (SCREEN_WIDTH - PAWN_PROMOTION_SCREEN.get_width())/2, SCREEN_HEIGHT - PAWN_PROMOTION_SCREEN.get_height() - (SCREEN_HEIGHT - PAWN_PROMOTION_SCREEN.get_height())/2))
        piece_color = piece.color# (219, 216)
# (347, 217)
# (218, 326)
# (349, 326)
        if piece_color == "White":
            screen.blit(WHITE_QUEEN, (220, 220))
            screen.blit(WHITE_ROOK, (350, 220))
            screen.blit(WHITE_BISHOP, (220, 330))
            screen.blit(WHITE_KNIGHT, (350, 330))
        elif piece_color == "Black":
            screen.blit(BLACK_QUEEN, (220, 220))
            screen.blit(BLACK_ROOK, (350, 220))
            screen.blit(BLACK_BISHOP, (220, 330))
            screen.blit(BLACK_KNIGHT, (350, 330))
        
        py.display.update()
        for event in py.event.get():
            if event.type == py.QUIT:
                play = False
                py.quit()
                sys.exit()
            if event.type == py.MOUSEBUTTONDOWN:
                if New_Queen.collidepoint(pos):
                    Promotion_screen_not_selected = False
                    New_Piece = Queen(piece_color, piece.rank, piece.file)
                    New_Piece.my_team_coordinates = piece.my_team_coordinates
                    New_Piece.opponent_team_coordinates = piece.opponent_team_coordinates
                    return New_Piece
                if New_Rook.collidepoint(pos):
                    Promotion_screen_not_selected = False
                    New_Piece = Rook(piece_color, piece.rank, piece.file)
                    New_Piece.my_team_coordinates = piece.my_team_coordinates
                    New_Piece.opponent_team_coordinates = piece.opponent_team_coordinates
                    return New_Piece
                if New_Bishop.collidepoint(pos):
                    Promotion_screen_not_selected = False
                    New_Piece = Bishop(piece_color, piece.rank, piece.file)
                    New_Piece.my_team_coordinates = piece.my_team_coordinates
                    New_Piece.opponent_team_coordinates = piece.opponent_team_coordinates
                    return New_Piece
                if New_Knight.collidepoint(pos):
                    Promotion_screen_not_selected = False
                    New_Piece = Knight(piece_color, piece.rank, piece.file)
                    New_Piece.my_team_coordinates = piece.my_team_coordinates
                    New_Piece.opponent_team_coordinates = piece.opponent_team_coordinates
                    return New_Piece
             
def main():
    global All_pieces_cordinates, PC_turn, Checkmate, PLayer, start_time, moves
    play = True

    while play:
        if not Checkmate:
            All_pieces_cordinates = []
            Draw_Board()
            Update_coordinate_and_draw(White_pieces)
            Update_coordinate_and_draw(Black_pieces)
            All_pieces_cordinates.extend(White_pieces_cordinates)
            All_pieces_cordinates.extend(Black_pieces_cordinates)
            if PLayer == "White":
                PC_turn = False
                for piece in White_pieces:
                    if piece.selected:
                        piece.legal_move_validation()
                        if isinstance(piece, Pawn) and piece.promoted:
                            Promoted_piece = Pawn_promotion(piece)
                            White_pieces.remove(piece)
                            White_pieces.append(Promoted_piece)
                            break
            if PLayer == "Black":
                PC_turn = True
                stockfish.set_fen_position(board.fen())
                # best_move = stockfish.get_top_moves(1)[0]["Move"]
                # stockfish.set_skill_level(0)
                # stockfish.set_elo_rating(1350)
                best_move = stockfish.get_best_move_time(1000)
                for piece in Black_pieces:
                    if piece.rank == best_move[0] and str(piece.file) == best_move[1]:
                        board.push_san(best_move)
                        moves.append(best_move)
                        print(board, "\n")
                        stockfish.set_fen_position(board.fen())
                        # print(stockfish.get_top_moves(1)[0]["Move"])
                        piece.my_team_coordinates.remove((piece.rank, piece.file))
                        if (piece.rank, piece.file) in piece.my_team_coordinates:
                            piece.my_team_coordinates.remove((piece.rank, piece.file))

                        if isinstance(piece, King):
                            piece.king_pos.remove((piece.rank, piece.file))

                        piece.rank, piece.file = best_move[2], int(best_move[3])
                        piece.coordinate = (game_notation_to_coordinate_conversion["ranks"][piece.rank], game_notation_to_coordinate_conversion["files"][piece.file])
                        piece.my_team_coordinates.append((piece.rank, piece.file))
                        if isinstance(piece, King):
                            piece.king_pos.append((piece.rank, piece.file))
                            if piece.short_castle[0] and piece.short_castle[1] == (best_move[2], int(best_move[3])):# Castling
                                piece.short_castle_rook[0].my_team_coordinates.remove((piece.short_castle_rook[0].rank, piece.short_castle_rook[0].file))
                                piece.short_castle_rook[0].rank, piece.short_castle_rook[0].file = piece.short_castle_rook[1]
                                piece.short_castle_rook[0].coordinate = (game_notation_to_coordinate_conversion["ranks"][piece.short_castle_rook[0].rank], game_notation_to_coordinate_conversion["files"][piece.short_castle_rook[0].file])
                                piece.short_castle_rook[0].my_team_coordinates.append((piece.short_castle_rook[0].rank, piece.short_castle_rook[0].file))
                            if piece.long_castle[0] and piece.long_castle[1] == (best_move[2], int(best_move[3])):
                                piece.long_castle_rook[0].my_team_coordinates.remove((piece.long_castle_rook[0].rank, piece.long_castle_rook[0].file))
                                piece.long_castle_rook[0].rank, piece.long_castle_rook[0].file = piece.long_castle_rook[1]
                                piece.long_castle_rook[0].coordinate = (game_notation_to_coordinate_conversion["ranks"][piece.long_castle_rook[0].rank], game_notation_to_coordinate_conversion["files"][piece.long_castle_rook[0].file])
                                piece.long_castle_rook[0].my_team_coordinates.append((piece.long_castle_rook[0].rank, piece.long_castle_rook[0].file))

                        for Pawns in White_pieces:
                            if isinstance(Pawns, Pawn):
                                Pawns.en_passant = False
                        piece.first_move = False
                        if (best_move[2], int(best_move[3])) in piece.opponent_team_coordinates:
                            CAPTURE.play()
                            for opp_piece in White_pieces:
                                if opp_piece.rank == best_move[2] and opp_piece.file == int(best_move[3]):
                                    White_pieces.remove(opp_piece)
                                    White_pieces_cordinates.remove((best_move[2], int(best_move[3])))
                            if isinstance(piece, Pawn):
                                if piece.en_passant_eating_piece[0] and piece.en_passant_eating_piece[1] == (best_move[2], int(best_move[3])):
                                    White_pieces.remove(piece.en_passant_eating_piece[0])
                                    piece.opponent_team_coordinates.remove((piece.en_passant_eating_piece[0].rank, piece.en_passant_eating_piece[0].file))
                        else:
                            MOVE.play()
                        Possible_moves = []
                        for piece in White_pieces:
                            moves, _ = piece.legal_moves()
                            moves, _ = Check(piece)
                            Possible_moves.extend(moves)
                        # print(Possible_moves)

                        # start_time = time.time()
                py.display.update()
                if Possible_moves == []:
                    start_time = time.time()
                PLayer = "White" if PLayer == "Black" else "Black"
            
            if start_time:# here
                time_elapsed = time.time() - start_time
                if time_elapsed > 0.1:
                    Checkmate = True

        else:
            screen.blit(CHECKMATE_SCREEN, (0,0))
            Checkmate_Show = STAT_FONT.render("Checkmate!!!", 1, (0,0,0))
            screen.blit(Checkmate_Show, (SCREEN_WIDTH - Checkmate_Show.get_width() - (SCREEN_WIDTH - Checkmate_Show.get_width())/2, SCREEN_HEIGHT - Checkmate_Show.get_height() - (SCREEN_HEIGHT - Checkmate_Show.get_height())/2))
        py.display.update()
        for event in py.event.get():
            if event.type == py.QUIT:
                play = False
                py.quit()
                # sys.exit()

if __name__ == "__main__":
    main()
    

    