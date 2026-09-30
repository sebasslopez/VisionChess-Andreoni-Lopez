from __future__ import annotations
from .Box import Box
from .Color import Color
from .Position import Position
import pygame
from .pieces.Pawn import Pawn
from .pieces.Bishop import Bishop
from .pieces.King import King
from .pieces.Queen import Queen
from .pieces.Knight import Knight
from .pieces.Rook import Rook
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .pieces.Piece import Piece

class Board:
    def __init__(self,flag:bool,board= ["."]*64):
        self.boxes:list[Box] = []
        self.Pieces:list[Piece] = []
        self.board:list[list[Box]] = self.createBoard(False)
        self.capturedPieces:list[Piece] = []
        self.isUpsideDown = False
        self.isSelected = False
        self.SelectedBox = None
        self.finished = False
        self.kings:list[King] = []
        self.kingsBox:list[Box] = self.getKings()
        if flag: self.previewBoard = self.copyBoard()
    

    def display(self,window: pygame.Surface):
        for b in self.previewBoard.boxes:
            b.display(window)

    def createBoard(self,flag:bool) -> list[list[Box]]:
        board:list[list[Box]] = []
        for i in range(0,8):
            row:list[Box] = []
            for j in range(0,8):
                p: Piece | None = Board.createPiece(i,j,flag)
                b: Box = Box(p,self.getBoxColor(i,j),Position(i,j))
                row.append(b)
                self.boxes.append(b)
                if p is not None: self.Pieces.append(p)
            board.append(row)
        return board

    @staticmethod
    def getBoxColor(row:int,column:int) -> Color:
        return Color.WHITE if ((row+column) % 2) == 0 else Color.BLACK

    def getBox(self,position: Position) -> Box | None:
        pos:tuple[int,int] = position.getTuple()
        if not position.isInside(): return None
        return self.board[pos[0]][pos[1]]

    def getOpositePieces(self,color:Color) -> list[Piece]:
        l:list[Piece] = []
        for p in self.Pieces:
            if p.color != color:
                l.append(p)
        return l
    


    @staticmethod
    def createPiece(row: int,column:int,flag:bool)-> Piece | None:
        return Board.getDefaulPieceByPos(row,column,Board.getColorByPos(row,column,flag))

    @staticmethod
    def getColorByPos(row: int,column:int,flag:bool) -> Color:
        if row * 8 + column <=32:
            return Color.WHITE if flag else Color.BLACK
        return Color.BLACK if flag else Color.WHITE

    @staticmethod
    def getDefaulPieceByPos(row: int,column:int,color:Color) -> Piece | None:
        if row == 1 or row == 6:
            return Pawn(color,Position(row,column))
        elif row == 0 or row == 7:
            if column == 0  or column == 7:
                return Rook(color,Position(row,column))
            elif column == 1 or column == 6:
                return Knight(color,Position(row,column))
            elif column == 2 or column == 5:
                return Bishop(color,Position(row,column))
            elif column == 3:
                return Queen(color,Position(row,column))
            else:
                return King(color,Position(row,column))
        return None

    def verifyClick(self,rect:tuple[int,int]):
        if self.finished: return
        b = self.getClickedBox(rect)
        if b is None: return
        if not self.isSelected:
            self.previewBoard = self.copyBoard()
            self.SelectedBox = b
            self.isSelected = True
            self.previewBoard.board = b.makePreviewBoard(self.previewBoard)
        else:
            if self.SelectedBox is None or self.SelectedBox.piece is None: return
            if (b.isEmpty() or (b.isoccupied() and not self.SelectedBox.piece.isTeamMate(b.piece))) and self.SelectedBox.piece.isMoveValid(b.position, self):
                self.SelectedBox.piece.move(b,self)
                self.SelectedBox.clearPiece()
                self.SelectedBox = None
                self.isSelected = False
                self.previewBoard = self.copyBoard()
                if self.checkFinished(): 
                    self.finished = True
                    print("JUEGO FINALIZADO!!!!!!!")
            elif b.piece is not None and b.isoccupied() and b.piece.isTeamMate(self.SelectedBox.piece):
                self.previewBoard = self.copyBoard()
                self.SelectedBox = b
                self.isSelected = True
                self.previewBoard.board = b.makePreviewBoard(self.previewBoard)


    def getKings(self):
        l: list[Box] = []
        for b in self.boxes:
            if isinstance(b.piece, King):
                l.append(b)
                self.kings.append(b.piece)
        return l

    def checkFinished(self):
        return self.kings[0].isCheckMate(self) or self.kings[1].isCheckMate(self) or self.londonBridgeFellDown() or self.checkQuantity()

    def londonBridgeFellDown(self):
        return self.kings[0].isCaptured or self.kings[1].isCaptured

    def checkQuantity(self):
        return not self.getOpositePieces(Color.WHITE) or not self.getOpositePieces(Color.BLACK)
    
    def copyBoard(self) -> Board:
        bor: Board = Board(False)
        bor.board = []
        bor.boxes = []
        bor.capturedPieces = []
        bor.Pieces = []
        for s in self.board:
            row: list[Box] = []
            for t in s:
                b = Box(t.piece,t.COLOROG,t.position)
                row.append(b)
                bor.boxes.append(b)
            bor.board.append(row)
        for s in self.Pieces:
                    bor.Pieces.append(s)
        for s in self.capturedPieces:
                    bor.capturedPieces.append(s)
        bor.isUpsideDown = self.isUpsideDown
        bor.isSelected = self.isSelected
        bor.SelectedBox = self.SelectedBox
        return bor
            

    def getClickedBox(self,rect:tuple[int,int])-> "Box | None":
        for b in self.boxes:
            if b.clickInside(rect):
                return b
        return None
                        