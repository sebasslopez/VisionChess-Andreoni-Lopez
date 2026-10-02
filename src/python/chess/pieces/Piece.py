from __future__ import annotations
from abc import ABC, abstractmethod
import pygame
from utils.ResourceLocation import getImage
from typing import TYPE_CHECKING
from ..Position import Position
from ..Color import Color
if TYPE_CHECKING:
    from chess.Board import Board
    from ..Box import Box
    

class Piece(ABC):
    def __init__(self, color: Color, position: Position):
        self.color: Color = color
        self.position = position
        self.hasMoved = False
        self.isCaptured = False
    
    @abstractmethod
    def getPossibleMoves(self, board: Board) -> list[Position]:
        return []

    def isMoveValid(self, newPosition: Position, board: Board) -> bool:
        return newPosition in self.getPossibleMoves(board)
    
    def move(self, box: Box, board: Board):
        from .King import King
        if isinstance(box.piece, King):
            return
        origin = self.position
        target = box.position
        self.hasMoved = True
        if not box.isEmpty() and box.piece is not None:
            box.piece.capture(board)
        box.setPiece(self)
        self.position = target
        board.last_move = (self, origin, target)

    def capture(self,board: Board):
        self.isCaptured = True
        board.capturedPieces.append(self)

    def isTeamMate(self, otherPiece: "Piece | None") -> bool:
        if otherPiece is None: return False
        return self.color == otherPiece.color

    def getTexture(self) -> pygame.Surface:
        return getImage(f"{self.color.name.removeprefix("Color.").lower()}_{self.__class__.__name__.lower()}")

    def getOpositeColor(self) -> Color:
        return Color.WHITE if self.color == Color.BLACK else Color.BLACK
