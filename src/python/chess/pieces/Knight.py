from __future__ import annotations
from .Piece import Piece
from typing import TYPE_CHECKING
from ..Position import Position
from ..Color import Color

if TYPE_CHECKING:
    from chess.Board import Board


class Knight(Piece):
    def __init__(self, color: Color, position: Position):
        super().__init__(color, position)

    def getPossibleMoves(self, board: Board) -> list[Position]:
        moves: list[Position] = []
        row, col = self.position.getTuple()
        for row_step, col_step in (
            (1, 2), (1, -2), (-1, 2), (-1, -2),
            (2, 1), (2, -1), (-2, 1), (-2, -1),
        ):
            position = Position(row + row_step, col + col_step)
            box = board.getBox(position)
            if box is not None and (box.isEmpty() or not self.isTeamMate(box.piece)):
                moves.append(position)
        return moves
