import pygame
from chess import Board as boar
from .screen import Screen


    
class boardScreen(Screen):
    def __init__(self, size:tuple[int,int], turns: bool = False):
        super().__init__(size, None)
        self.Board: boar.Board = boar.Board(True, turns=turns)

    def display(self, window: pygame.Surface):
        self.Board.display(window)
        pass

    def update(self, window: pygame.Surface,size:tuple[int,int]):
        super().clear(window)
        self.display(window)
        pygame.display.flip()

    def handleKeyPress(self,key: int):
        super().handleKeyPress(key)

    def handleMouseClick(self,rect:tuple[int,int]):
        self.Board.verifyClick(rect)
        pass
