from __future__ import annotations
from .Piece import Piece
from typing import TYPE_CHECKING
from ..Position import Position
from ..Color import Color

if TYPE_CHECKING:
    from chess.Board import Board


class Pawn(Piece):
    def __init__(self, color: Color, position: Position):
        super().__init__(color, position)

    def getPossibleMoves(self, board: Board) -> list[Position]:
        moves: list[Position] = []
        direction = 1 if self.color == Color.BLACK else -1
        row, col = self.position.getTuple()
        forward = Position(row + direction, col)
        forward_box = board.getBox(forward)

        if forward_box is not None and forward_box.isEmpty():
            moves.append(forward)
            double = Position(row + direction * 2, col)
            double_box = board.getBox(double)
            if row == board.getPawnStartRow(self.color) and not self.hasMoved and double_box is not None and double_box.isEmpty():
                moves.append(double)

        for side in (-1, 1):
            target = Position(row + direction, col + side)
            target_box = board.getBox(target)
            if target_box is not None and target_box.isoccupied() and not self.isTeamMate(target_box.piece):
                moves.append(target)
            elif target_box is not None and board.enPassantTarget == target:
                moves.append(target)

        return moves
