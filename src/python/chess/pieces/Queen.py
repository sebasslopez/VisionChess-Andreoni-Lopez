from __future__ import annotations
from .Piece import Piece
from typing import TYPE_CHECKING
from ..Position import Position
from ..Color import Color

if TYPE_CHECKING:
    from chess.Board import Board


class Queen(Piece):
    def __init__(self, color: Color, position: Position):
        super().__init__(color, position)

    def getPossibleMoves(self, board: Board) -> list[Position]:
        moves: list[Position] = []
        row, col = self.position.getTuple()
        directions = (
            (1, 0), (-1, 0), (0, 1), (0, -1),
            (1, 1), (1, -1), (-1, 1), (-1, -1),
        )
        for row_step, col_step in directions:
            current_row = row + row_step
            current_col = col + col_step
            while 0 <= current_row < 8 and 0 <= current_col < 8:
                position = Position(current_row, current_col)
                box = board.getBox(position)
                if box is None:
                    break
                if box.isEmpty():
                    moves.append(position)
                else:
                    if not self.isTeamMate(box.piece):
                        moves.append(position)
                    break
                current_row += row_step
                current_col += col_step
        return moves
