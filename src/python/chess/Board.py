from __future__ import annotations

from .Box import Box
from .Color import Color
from .Position import Position
import pygame
from .pieces.Pawn import Pawn
from .pieces.Bishop import Bishop
from .pieces.King import King
from .pieces.Queen import Queen
from .pieces.Knight import Knight
from .pieces.Rook import Rook
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .pieces.Piece import Piece


class Board:
    def __init__(self, canPlay: bool, uDown: bool = False, board=None, turns: bool = False):
        if board is None: board = ["rnbqkbnrpppppppp................................PPPPPPPPRNBQKBNR"]
        self.lastUpdate = board
        self.initial = board
        self.boxes: list[Box] = []
        self.Pieces: list[Piece] = []
        self.capturedPieces: list[Piece] = []
        self.isUpsideDown = uDown
        self.turnsEnabled = turns
        self.currentTurn = Color.WHITE
        self.enPassantTarget: Position | None = None
        self.enPassantPawn: Piece | None = None
        self.isSelected = False
        self.selectedBox = None
        self.finished = False
        self.board: list[list[Box]] = self.createBoard(uDown)
        self.kings: list[King] = []
        self.kingsBox: list[Box] = self.getKings()
        self.markedKingBoxes: list[Box] = []
        if canPlay:
            self.previewBoard = self.copyBoard()

    def display(self, window: pygame.Surface):
        for box in self.previewBoard.boxes:
            box.display(window)

    def createBoard(self, upside_down: bool) -> list[list[Box]]:
        value = self.initial[0] if isinstance(self.initial, list) else self.initial
        if upside_down:
            value = value[::-1]
        board: list[list[Box]] = []
        for index, char in enumerate(value):
            position = Position.getFromIndex(index)
            piece = self.getGetPieceByChar(char, position)
            box = Box(piece, self.getBoxColor(position), position)
            self.boxes.append(box)
            if piece is not None:
                self.Pieces.append(piece)
            if index % 8 == 0:
                board.append([])
            board[-1].append(box)
        return board

    @staticmethod
    def getBoxColor(position: Position) -> Color:
        return Color.WHITE if (position.row + position.col) % 2 == 0 else Color.BLACK

    def getBox(self, position: Position) -> Box | None:
        if not position.isInside():
            return None
        return self.board[position.row][position.col]

    def getOppositePieces(self, color: Color) -> list[Piece]:
        return [piece for piece in self.Pieces if not piece.isCaptured and piece.color != color]

    @staticmethod
    def getGetPieceByChar(char: str, position: Position) -> Piece | None:
        pieces = {'r': (Rook, Color.BLACK), 'R': (Rook, Color.WHITE), 'n': (Knight, Color.BLACK), 'N': (Knight, Color.WHITE), 'b': (Bishop, Color.BLACK), 'B': (Bishop, Color.WHITE), 'q': (Queen, Color.BLACK), 'Q': (Queen, Color.WHITE), 'k': (King, Color.BLACK), 'K': (King, Color.WHITE), 'p': (Pawn, Color.BLACK), 'P': (Pawn, Color.WHITE), }
        piece_type, color = pieces.get(char, (None, None))
        return piece_type(color, position) if piece_type is not None else None

    def getPawnStartRow(self, color: Color) -> int:
        if self.isUpsideDown:
            return 1 if color == Color.WHITE else 6
        return 6 if color == Color.WHITE else 1

    def getKingHomeRow(self, color: Color) -> int:
        if self.isUpsideDown:
            return 0 if color == Color.WHITE else 7
        return 7 if color == Color.WHITE else 0

    def verifyClick(self, rect: tuple[int, int]):
        if self.finished:
            return
        box = self.getClickedBox(rect)
        if box is None:
            return
        if not self.isSelected:
            if box.piece is None or (self.turnsEnabled and box.piece.color != self.currentTurn):
                return
            self.selectedBox = box
            self.isSelected = True
            self.updatePreview()
            return
        if box.piece is not None and box.piece.color == self.selectedBox.piece.color:
            self.selectedBox = box
            self.updatePreview()
            return
        if self.selectedBox.piece is not None and self.isLegalMove(self.selectedBox.piece, box.position):
            self.movePiece(self.selectedBox.piece, box.position)
            if self.turnsEnabled:
                self.currentTurn = Color.BLACK if self.currentTurn == Color.WHITE else Color.WHITE
            self.selectedBox = None
            self.isSelected = False
            self.markKings()
            self.previewBoard = self.copyBoard()
            if self.checkFinished():
                self.finished = True

    def updatePreview(self):
        self.previewBoard = self.copyBoard()
        selected = self.previewBoard.getBox(self.selectedBox.position)
        if selected is not None:
            self.previewBoard.board = selected.makePreviewBoard(self.previewBoard)

    def getKings(self):
        self.kings = [box.piece for box in self.boxes if isinstance(box.piece, King)]
        return [box for box in self.boxes if isinstance(box.piece, King)]

    def isSquareAttacked(self, position: Position, by_color: Color) -> bool:
        for piece in self.Pieces:
            if piece.isCaptured or piece.color != by_color:
                continue
            row, col = piece.position.getTuple()
            target_row, target_col = position.getTuple()
            if isinstance(piece, Pawn):
                direction = 1 if piece.color == Color.BLACK else -1
                if target_row == row + direction and abs(target_col - col) == 1:
                    return True
            elif isinstance(piece, Knight):
                if (abs(target_row - row), abs(target_col - col)) in ((1, 2), (2, 1)):
                    return True
            elif isinstance(piece, King):
                if max(abs(target_row - row), abs(target_col - col)) == 1:
                    return True
            else:
                row_step = target_row - row
                col_step = target_col - col
                if isinstance(piece, Rook) and row_step != 0 and col_step != 0:
                    continue
                if isinstance(piece, Bishop) and abs(row_step) != abs(col_step):
                    continue
                if isinstance(piece, Queen) and not (row_step == 0 or col_step == 0 or abs(row_step) == abs(col_step)):
                    continue
                if row_step == 0 and col_step == 0:
                    continue
                row_step = 0 if row_step == 0 else row_step // abs(row_step)
                col_step = 0 if col_step == 0 else col_step // abs(col_step)
                current = Position(row + row_step, col + col_step)
                blocked = False
                while current != position:
                    if self.getBox(current).isoccupied():
                        blocked = True
                        break
                    current = Position(current.row + row_step, current.col + col_step)
                if not blocked:
                    return True
        return False

    def isInCheck(self, color: Color) -> bool:
        king = next((piece for piece in self.kings if not piece.isCaptured and piece.color == color), None)
        return king is not None and self.isSquareAttacked(king.position, Color.WHITE if color == Color.BLACK else Color.BLACK)

    def getCastlingMoves(self, king: King) -> list[Position]:
        if king.hasMoved or king.position.col != 4 or king.position.row != self.getKingHomeRow(king.color) or self.isInCheck(king.color):
            return []
        row = king.position.row
        enemy = Color.WHITE if king.color == Color.BLACK else Color.BLACK
        moves = []
        for rook_col, target_col, between_cols in ((7, 6, (5, 6)), (0, 2, (1, 2, 3))):
            rook_box = self.getBox(Position(row, rook_col))
            if not isinstance(rook_box.piece if rook_box else None, Rook):
                continue
            rook = rook_box.piece
            if rook.color != king.color or rook.hasMoved:
                continue
            if any(self.getBox(Position(row, col)).isoccupied() for col in between_cols):
                continue
            transit_cols = (5, 6) if target_col == 6 else (3, 2)
            if any(self.isSquareAttacked(Position(row, col), enemy) for col in transit_cols):
                continue
            moves.append(Position(row, target_col))
        return moves

    def getLegalMoves(self, piece: Piece) -> list[Position]:
        if piece not in self.Pieces or piece.isCaptured:
            return []
        legal = []
        for position in piece.getPossibleMoves(self):
            target = self.getBox(position)
            if target is not None and isinstance(target.piece, King):
                continue
            simulated = self.copyBoard()
            simulated_piece = simulated.getBox(piece.position).piece
            simulated._executeMove(simulated_piece, position)
            if not simulated.isInCheck(piece.color):
                legal.append(position)
        return legal

    def isLegalMove(self, piece: Piece, position: Position) -> bool:
        return position in self.getLegalMoves(piece)

    def _executeMove(self, piece: Piece, destination: Position):
        source = self.getBox(piece.position)
        target = self.getBox(destination)
        if source is None or target is None:
            return
        source_position = Position(piece.position.row, piece.position.col)
        old_target = target.piece
        is_en_passant = isinstance(piece, Pawn) and self.enPassantTarget == destination and target.isEmpty()
        if is_en_passant:
            captured = self.getBox(Position(source_position.row, destination.col))
            if captured is not None and captured.piece is not None:
                captured.piece.capture(self)
                captured.clearPiece()
        elif old_target is not None:
            old_target.capture(self)
        source.clearPiece()
        target.setPiece(piece)
        piece.position = Position(destination.row, destination.col)
        piece.hasMoved = True
        if isinstance(piece, King) and abs(destination.col - source_position.col) == 2:
            rook_col = 7 if destination.col == 6 else 0
            rook_target_col = 5 if destination.col == 6 else 3
            rook_box = self.getBox(Position(source_position.row, rook_col))
            rook_target = self.getBox(Position(source_position.row, rook_target_col))
            if rook_box is not None and rook_target is not None and rook_box.piece is not None:
                rook = rook_box.piece
                rook_box.clearPiece()
                rook_target.setPiece(rook)
                rook.position = Position(source_position.row, rook_target_col)
                rook.hasMoved = True
        self.enPassantTarget = None
        self.enPassantPawn = None
        if isinstance(piece, Pawn) and abs(destination.row - source_position.row) == 2:
            self.enPassantTarget = Position((destination.row + source_position.row) // 2, destination.col)
            self.enPassantPawn = piece
        if isinstance(piece, Pawn) and destination.row in (0, 7):
            promoted = Queen(piece.color, Position(destination.row, destination.col))
            promoted.hasMoved = True
            target.setPiece(promoted)
            if piece in self.Pieces:
                self.Pieces.remove(piece)
            self.Pieces.append(promoted)

    def movePiece(self, piece: Piece, destination: Position):
        self._executeMove(piece, destination)
        self.getKings()

    def checkFinished(self):
        if len(self.kings) < 2:
            return True
        if self.turnsEnabled:
            return self.isCheckMate(self.currentTurn) or not any(self.getLegalMoves(piece) for piece in self.Pieces if piece.color == self.currentTurn and not piece.isCaptured)
        return any(self.isCheckMate(color) or not any(self.getLegalMoves(piece) for piece in self.Pieces if piece.color == color and not piece.isCaptured) for color in (Color.WHITE, Color.BLACK))

    def isCheckMate(self, color: Color):
        return self.isInCheck(color) and not any(self.getLegalMoves(piece) for piece in self.Pieces if piece.color == color)

    def londonBridgeFellDown(self):
        return any(king.isCaptured for king in self.kings)

    def checkQuantity(self):
        return not any(piece.color == Color.WHITE and not piece.isCaptured for piece in self.Pieces) or not any(piece.color == Color.BLACK and not piece.isCaptured for piece in self.Pieces)

    def markKings(self):
        for box in self.boxes:
            box.colorAC = box.COLOROG
        self.markedKingBoxes.clear()
        for king in self.kings:
            if not king.isCaptured and self.isInCheck(king.color):
                box = self.getBox(king.position)
                if box is not None:
                    box.colorAC = Color.RED
                    self.markedKingBoxes.append(box)

    def copyBoard(self) -> Board:
        copied = Board(False, self.isUpsideDown)
        copied.initial = self.initial
        copied.lastUpdate = self.lastUpdate
        copied.board = []
        copied.boxes = []
        copied.Pieces = []
        copied.capturedPieces = []
        piece_map = {}
        for row in self.board:
            copied_row = []
            for original_box in row:
                original_piece = original_box.piece
                copied_piece = None
                if original_piece is not None:
                    key = id(original_piece)
                    if key not in piece_map:
                        copied_piece = type(original_piece)(original_piece.color, Position(original_piece.position.row, original_piece.position.col))
                        copied_piece.hasMoved = original_piece.hasMoved
                        copied_piece.isCaptured = original_piece.isCaptured
                        piece_map[key] = copied_piece
                        copied.Pieces.append(copied_piece)
                    else:
                        copied_piece = piece_map[key]
                position = Position(original_box.position.row, original_box.position.col)
                copied_box = Box(copied_piece, original_box.COLOROG, position)
                copied_box.colorAC = original_box.colorAC
                copied_row.append(copied_box)
                copied.boxes.append(copied_box)
            copied.board.append(copied_row)
        for original_piece in self.capturedPieces:
            copied_piece = piece_map.get(id(original_piece))
            if copied_piece is None:
                copied_piece = type(original_piece)(original_piece.color, Position(original_piece.position.row, original_piece.position.col))
                copied_piece.hasMoved = original_piece.hasMoved
                copied_piece.isCaptured = True
            copied.capturedPieces.append(copied_piece)
        copied.enPassantTarget = None if self.enPassantTarget is None else Position(self.enPassantTarget.row, self.enPassantTarget.col)
        copied.enPassantPawn = piece_map.get(id(self.enPassantPawn)) if self.enPassantPawn is not None else None
        copied.kingsBox = copied.getKings()
        copied.markedKingBoxes = []
        for original_box in self.markedKingBoxes:
            copied_box = copied.getBox(original_box.position)
            if copied_box is not None:
                copied.markedKingBoxes.append(copied_box)
        copied.isSelected = self.isSelected
        copied.selectedBox = None
        copied.finished = self.finished
        copied.turnsEnabled = self.turnsEnabled
        copied.currentTurn = self.currentTurn
        return copied

    def getClickedBox(self, rect: tuple[int, int]) -> Box | None:
        return next((box for box in self.boxes if box.clickInside(rect)), None)
