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
        moves:list[Position] = []
        dirsf = [1,-1,-2,2]
        dirsc = [-2,2,1,-1]
        OGpos = self.position.getTuple()
        pos = OGpos
        for i in range(0,2):
            for j in range(0,2):
                pos = Position(OGpos[0]+dirsf[j],OGpos[1]+dirsc[i])
                if pos.isInside():
                    box = board.getBox(pos)
                    if box is None: return moves
                    if box.isEmpty() or not self.isTeamMate(box.piece):
                        moves.append(pos)
        for i in range(2,4):
            for j in range(2,4):
                pos = Position(OGpos[0]+dirsf[j],OGpos[1]+dirsc[i])
                if pos.isInside():
                    box = board.getBox(pos)
                    if box is None: return moves
                    if box.isEmpty() or not self.isTeamMate(box.piece):
                        moves.append(pos)
        return moves