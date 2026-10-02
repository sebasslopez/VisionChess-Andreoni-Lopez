from __future__ import annotations
from .Piece import Piece

from typing import TYPE_CHECKING
from ..Position import Position
from ..Color import Color
if TYPE_CHECKING:
    from chess.Board import Board

class Rook(Piece):
    def __init__(self, color: Color, position: Position):
            super().__init__(color, position)
    
    def getPossibleMoves(self, board: Board) -> list[Position]:
        moves:list[Position] = []
        dirs = [1,-1]
        OGpos = self.position.getTuple()
        for i in dirs:
            pos = Position(OGpos[0]+i,OGpos[1])
            box = board.getBox(pos)
            while box is not None and pos.isInside() and box.isEmpty():
                moves.append(pos)
                pos = Position(pos.row+i,OGpos[1])
                box = board.getBox(pos)
            if box is not None and not self.isTeamMate(box.piece):
                 moves.append(pos)
        for i in dirs:
                    pos = Position(OGpos[0],OGpos[1]+i)
                    box = board.getBox(pos)
                    while box is not None and pos.isInside() and box.isEmpty():
                        moves.append(pos)
                        pos = Position(OGpos[0], pos.col+i)
                        box = board.getBox(pos)
                    if box is not None and not self.isTeamMate(box.piece):
                         moves.append(pos)
        return moves
