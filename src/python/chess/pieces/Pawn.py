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

    def move(self, box, board):
        origin = self.position
        target = box.position
        if box.isEmpty() and abs(target.col - origin.col) == 1:
            adjacent = board.getBox(Position(origin.row, target.col))
            last_move = board.last_move
            if (adjacent is not None and isinstance(adjacent.piece, Pawn) and last_move is not None and last_move[0] is adjacent.piece and abs(last_move[1].row - last_move[2].row) == 2):
                adjacent.piece.capture(board)
                adjacent.clearPiece()
        super().move(box, board)
        if target.row in (0, 7):
            from .Queen import Queen
            promoted = Queen(self.color, target)
            promoted.hasMoved = True
            box.setPiece(promoted)
            board.Pieces.remove(self)
            board.Pieces.append(promoted)

    def getPossibleMoves(self, board: Board) -> list["Position"]:
        moves: list["Position"] = []
        dirr = -1 if self.color == Color.WHITE else 1
        OGpos = self.position.getTuple()
        pos = Position(OGpos[0] + dirr, OGpos[1])
        box = board.getBox(pos)
        if box is not None and box.isEmpty():
            moves.append(pos)
            pos = Position(OGpos[0] + dirr * 2, OGpos[1])
            box = board.getBox(pos)
            initial_row = 6 if self.color == Color.WHITE else 1
            if box is not None and box.isEmpty() and not self.hasMoved and OGpos[0] == initial_row:
                moves.append(pos)
        for i in (-1, 1):
            pos = Position(OGpos[0] + dirr, OGpos[1] + i)
            box = board.getBox(pos)
            if box is not None and box.isoccupied() and not self.isTeamMate(box.piece):
                moves.append(pos)
            elif box is not None and box.isEmpty():
                adjacent = board.getBox(Position(OGpos[0], OGpos[1] + i))
                last_move = board.last_move
                if (adjacent is not None and adjacent.piece is not None and isinstance(adjacent.piece, Pawn) and last_move is not None and last_move[0] is adjacent.piece and abs(last_move[1].row - last_move[2].row) == 2):
                    moves.append(pos)
        return moves
