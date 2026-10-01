import pygame
from chess import Board as boar
from .screen import Screen
from ...vision.Vision import Vision


class BoardVisualizationScreen(Screen):
    def __init__(self, size: tuple[int, int]):
        super().__init__(size, None)  # self.vision = Vision()  # self.Board: boar.Board = boar.Board(False,self.vision.detect())

    def display(self, window: pygame.Surface):
        # self.Board.display(window)
        pass

    def update(self, window: pygame.Surface, size: tuple[int, int]):
        super().clear(window)
        self.display(window)
        pygame.display.flip()

    def handleKeyPress(self, key: int):
        super().handleKeyPress(key)

    def handleMouseClick(self, rect: tuple[int, int]):
        # self.Board.verifyClick(rect)
        pass
