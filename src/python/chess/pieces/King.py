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
        moves:list[Position] = []
        dirs = [-1,0,1]
        OGpos = self.position.getTuple()
        pos = Position(OGpos[0],OGpos[1])
        for i in dirs:
             for j in dirs:
                pos = Position(OGpos[0]+i,OGpos[1]+j)
                box = board.getBox(pos)
                if box is None: return moves
                if pos.isInside() and not pos.isTheSame(self.position) and (not self.check(pos,board,self.color)) and not self.isTeamMate(box.piece):
                    moves.append(pos)
        return moves

    def isCheckMate(self,board: Board):
        return self.check(self.position,board,self.color) and not self.getPossibleMoves(board)

    @staticmethod
    def check(position:Position,board: Board,color:Color) -> bool:
        for piece in board.getOpositePieces(color):
             for pos in piece.getPossibleMoves(board):
                if pos.isTheSame(position):
                    return True
        return False

    