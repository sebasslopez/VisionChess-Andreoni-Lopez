from __future__ import annotations
from chess.pieces.Piece import Piece
from chess.Color import Color
from chess.Position import Position
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from chess.Board import Board
import pygame



class Box:
    def __init__(self,piece:Piece | None, color: Color, position: Position):
        self.piece = piece
        self.COLOROG = color
        self.colorAC = color
        self.position = position
        pass

    def display(self,window:pygame.Surface):
        window.fill(self.getColor(),self.position.getBoundingBox())
        if self.piece is not None:         
            window.blit(pygame.transform.scale(self.piece.getTexture(),(self.position.getWidth(),self.position.getWidth())),self.position.getBoundingBox())
    
    def isoccupied(self) -> bool:
        return self.piece is not None

    def isEmpty(self) -> bool:
        return not self.isoccupied()

    def clearPiece(self):
        self.colorAC = self.COLOROG
        self.piece = None

    def setPiece(self, piece: Piece):
        self.clearPiece()
        self.piece = piece

    def getColor(self):
        if self.colorAC == Color.WHITE:
            return 200,200,200
        elif self.colorAC == Color.BLACK:
            return 50,50,50
        elif self.colorAC == Color.GREEN:
            return 0,255,0
        elif self.colorAC == Color.BLUE:
            return 0,0,255
        elif self.colorAC == Color.RED:
            return 255,0,0
        return 123,23,85

    def clickInside(self,rect:tuple[int,int]) -> bool:
        r = self.position.getBoundingBox()
        return r[0] <= rect[0] <= r[0] + r[2] and r[1] <= rect[1] <= r[1] + r[3]

    def makePreviewBoard(self,board:Board) -> list[list["Box"]] :
        if self.piece is None: return board.board
        for pos in self.piece.getPossibleMoves(board):
            box = board.board[pos.getTuple()[0]][pos.getTuple()[1]]
            if box.isEmpty():
                box.colorAC = Color.GREEN
            elif not self.piece.isTeamMate(box.piece):
                box.colorAC = Color.RED
        return board.board
