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

    def getPossibleMoves(self, board: Board) -> list["Position"]:
        moves:list["Position"] = []
        dirs = [1,-1]
        dirr = dirs[self.color.value - 1]
        OGpos = self.position.getTuple()
        pos = Position(OGpos[0] + dirr, OGpos[1])
        box = board.getBox(pos)
        if box is None: return moves
        if pos.isInside() and box.isEmpty():
            moves.append(pos)
            for i in dirs:
                pos = Position(OGpos[0] + dirr, OGpos[1])
                box = board.getBox(pos)
                if box is None: return moves
                if pos.isInside() and box.isoccupied() and not self.isTeamMate(box.piece):
                    moves.append(pos)
            pos = Position(OGpos[0] + dirr * 2, OGpos[1])
            box = board.getBox(pos)
            if box is None: return moves
            if pos.isInside() and box.isEmpty() and not self.hasMoved:
                moves.append(pos)
        else:
            for i in dirs:
                pos = Position(OGpos[0] + dirr, OGpos[1] + i)
                box = board.getBox(pos)
                if box is None: return moves
                if pos.isInside() and box.isoccupied() and not self.isTeamMate(box.piece):
                    moves.append(pos)
        return moves
