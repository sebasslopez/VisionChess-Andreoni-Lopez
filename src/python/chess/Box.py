from __future__ import annotations
from chess.pieces.Piece import Piece
from chess.Color import Color
from chess.Position import Position
from typing import TYPE_CHECKING
import pygame

if TYPE_CHECKING:
    from chess.Board import Board


class Box:
    def __init__(self, piece: Piece | None, color: Color, position: Position):
        self.piece = piece
        self.COLOROG = color
        self.colorAC = color
        self.position = position

    def display(self, window: pygame.Surface):
        window.fill(self.getColor(), self.position.getBoundingBox())
        if self.piece is not None:
            texture = pygame.transform.scale(self.piece.getTexture(), (self.position.getWidth(), self.position.getWidth()))
            window.blit(texture, self.position.getBoundingBox())

    def isoccupied(self) -> bool:
        return self.piece is not None

    def isEmpty(self) -> bool:
        return self.piece is None

    def clearPiece(self):
        self.colorAC = self.COLOROG
        self.piece = None

    def setPiece(self, piece: Piece):
        self.clearPiece()
        self.piece = piece

    def getColor(self):
        colors = {
            Color.WHITE: (200, 200, 200),
            Color.BLACK: (50, 50, 50),
            Color.GREEN: (0, 255, 0),
            Color.BLUE: (0, 0, 255),
            Color.RED: (255, 0, 0),
        }
        return colors.get(self.colorAC, (123, 23, 85))

    def clickInside(self, rect: tuple[int, int]) -> bool:
        x, y, width, height = self.position.getBoundingBox()
        return x <= rect[0] < width and y <= rect[1] < height

    def makePreviewBoard(self, board: Board) -> list[list[Box]]:
        if self.piece is None:
            return board.board
        source = board.getBox(self.piece.position)
        if source is None or source.piece is None:
            return board.board
        for position in board.getLegalMoves(source.piece):
            target = board.getBox(position)
            if target is None:
                continue
            target.colorAC = Color.RED if target.isoccupied() else Color.GREEN
        return board.board
