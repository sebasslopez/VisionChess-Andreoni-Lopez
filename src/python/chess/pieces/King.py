from __future__ import annotations
from .Piece import Piece
from typing import TYPE_CHECKING
from ..Position import Position
from ..Color import Color

if TYPE_CHECKING:
    from chess.Board import Board


class King(Piece):
    def __init__(self, color: Color, position: Position):
        super().__init__(color, position)

    def getPossibleMoves(self, board: Board) -> list[Position]:
        moves: list[Position] = []
        row, col = self.position.getTuple()
        for row_step in (-1, 0, 1):
            for col_step in (-1, 0, 1):
                if row_step == 0 and col_step == 0:
                    continue
                position = Position(row + row_step, col + col_step)
                box = board.getBox(position)
                if box is not None and (box.isEmpty() or not self.isTeamMate(box.piece)):
                    moves.append(position)
        moves.extend(board.getCastlingMoves(self))
        return moves

    def getSafeMoves(self, board: Board) -> list[Position]:
        return board.getLegalMoves(self)

    def isCheckMate(self, board: Board):
        return board.isInCheck(self.color) and not self.getSafeMoves(board)

    def canDoCastling(self, board: Board, position: Position):
        return position in board.getCastlingMoves(self)

    def getBoxesBetween(self, board: Board):
        return []

    @staticmethod
    def check(position: Position, board: Board, color: Color) -> bool:
        enemy = Color.WHITE if color == Color.BLACK else Color.BLACK
        return board.isSquareAttacked(position, enemy)
