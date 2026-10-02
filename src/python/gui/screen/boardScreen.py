import pygame
from chess import Board as boar
from chess.Position import Position
from .screen import Screen


    
class boardScreen(Screen):
    def __init__(self, size:tuple[int,int]):
        super().__init__(size, None)
        Position.OFFSET_X = self.BOARD_MARGIN
        Position.OFFSET_Y = self.BOARD_MARGIN
        self.Board: boar.Board = boar.Board(True)

    def display(self, window: pygame.Surface):
        window.fill((0, 0, 0))
        self.Board.display(window)
        self.displayBoardCoordinates(window)

    def update(self, window: pygame.Surface,size:tuple[int,int]):
        super().clear(window)
        self.display(window)
        pygame.display.flip()

    def handleKeyPress(self,key: int):
        super().handleKeyPress(key)

    def handleMouseClick(self,rect:tuple[int,int]):
        self.Board.verifyClick(rect)
        pass
