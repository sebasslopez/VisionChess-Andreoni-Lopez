from __future__ import annotations
from .Piece import Piece

from typing import TYPE_CHECKING
from ..Position import Position
from ..Color import Color
from .Pawn import Pawn
from .Rook import Rook

if TYPE_CHECKING:
    from chess.Board import Board


class King(Piece):
    def __init__(self, color: Color, position: Position):
        super().__init__(color, position)
        self.castlingPositions = []
        self.castlingMove = None

    def move(self, box, board):
        origin = self.position
        target = box.position
        if self.isCastlingMove(target):
            king_position, rook_position, rook_target = self.castlingMove
            rook_box = board.getBox(rook_position)
            king_box = board.getBox(king_position)
            rook_target_box = board.getBox(rook_target)
            if (rook_box is not None and king_box is not None and rook_target_box is not None and isinstance(rook_box.piece, Rook)):
                rook = rook_box.piece
                rook_box.clearPiece()
                king_box.setPiece(self)
                self.position = king_box.position
                rook_target_box.setPiece(rook)
                rook.position = rook_target_box.position
                self.hasMoved = True
                rook.hasMoved = True
                board.last_move = (self, origin, self.position)
            return
        super().move(box, board)

    def isCastlingMove(self, target: Position) -> bool:
        self.castlingMove = None
        for move in self.castlingPositions:
            if target.isTheSame(move[0]):
                self.castlingMove = move
                return True
        return False

    def getPossibleMoves(self, board: Board) -> list[Position]:
        moves: list[Position] = []
        dirs = [-1, 0, 1]
        OGpos = self.position.getTuple()
        pos = Position(OGpos[0], OGpos[1])
        for i in dirs:
            for j in dirs:
                pos = Position(OGpos[0] + i, OGpos[1] + j)
                box = board.getBox(pos)
                if box is None: continue
                if pos.isInside() and not pos.isTheSame(self.position) and (not self.check(pos, board, self.color)) and not self.isTeamMate(box.piece):
                    moves.append(pos)
        self.castlingPositions = self.getCastlingMoves(board)
        moves.extend(move[0] for move in self.castlingPositions)
        return moves

    def getCastlingMoves(self, board: Board) -> list[list[Position]]:
        moves = []
        for rook_column, king_column in ((0, 2), (7, 6)):
            rook_position = Position(self.position.row, rook_column)
            king_position = Position(self.position.row, king_column)
            rook_target = Position(self.position.row, 3 if rook_column == 0 else 5)
            if (not self.hasMoved and not self.check(self.position, board, self.color)
                    and self.canDoCastling(board, rook_position)
                    and not self.check(Position(self.position.row, (self.position.col + king_column) // 2), board, self.color)
                    and not self.check(king_position, board, self.color)):
                moves.append([king_position, rook_position, rook_target])
        return moves

    def isCheckMate(self, board: Board):
        return self.check(self.position, board, self.color) and not self.getPossibleMoves(board)

    def canDoCastling(self, board: Board, position: Position):
        rook_box = board.getBox(position)
        if rook_box is None or not isinstance(rook_box.piece, Rook) or rook_box.piece.hasMoved:
            return False
        step = 1 if position.col > self.position.col else -1
        return all(board.getBox(Position(self.position.row, col)).isEmpty() for col in range(self.position.col + step, position.col, step))

    def getBoxesBetween(self, board: Board):
        return []

    @staticmethod
    def check(position: Position, board: Board, color: Color) -> bool:
        for piece in board.getOpositePieces(color):
            if isinstance(piece, King):
                row, column = piece.position.getTuple()
                target_row, target_column = position.getTuple()
                if max(abs(row - target_row), abs(column - target_column)) == 1:
                    return True
            elif isinstance(piece, Pawn):
                direction = -1 if piece.color == Color.WHITE else 1
                row, column = piece.position.getTuple()
                target_row, target_column = position.getTuple()
                if target_row == row + direction and abs(target_column - column) == 1:
                    return True
            else:
                for pos in piece.getPossibleMoves(board):
                    if pos.isTheSame(position):
                        return True
        return False
