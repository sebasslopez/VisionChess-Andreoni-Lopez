from __future__ import annotations
import pygame
from chess.Position import Position


class Screen:
    BOARD_MARGIN = 50

    def __init__(self, size: tuple[int, int], last_screen: Screen | None = None):
        self.screenSize = (size[0], size[1])
        self.last_screen = last_screen
        import VisionChess as VisionChest
        self.vision = VisionChest.VisionChess.getInstance()

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.KEYDOWN: self.handleKeyPress(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and pygame.mouse.get_pressed()[0]: self.handleMouseClick(event.pos)
        pass

    def display(self, window: pygame.Surface):
        window.fill((0, 0, 255))
        pass

    def update(self, window: pygame.Surface, size: tuple[int, int]):
        self.clear(window)
        self.display(window)
        pygame.display.flip()

    @staticmethod
    def clear(window: pygame.Surface):
        window.fill((0, 0, 0))

    def displayBoardCoordinates(self, window: pygame.Surface):
        font = pygame.font.Font(None, 40)
        for column in range(8):
            letter = font.render(chr(ord("a") + column), True, (255, 255, 255))
            x = Position.OFFSET_X + column * Position.getWidth() + Position.getWidth() // 2
            window.blit(letter, letter.get_rect(center=(x, self.BOARD_MARGIN // 2)))
        for row in range(8):
            number = font.render(str(8 - row), True, (255, 255, 255))
            y = Position.OFFSET_Y + row * Position.getWidth() + Position.getWidth() // 2
            window.blit(number, number.get_rect(center=(self.BOARD_MARGIN // 2, y)))

    def handleKeyPress(self, key: int):
        if key == pygame.K_ESCAPE and self.last_screen is not None: self.vision.stop()
        elif key == pygame.K_RIGHT:
            from gui.screen.menuScreen import menuScreen
            self.vision.setScreen(menuScreen(self.screenSize))
        pass

    def handleMouseClick(self, rect: tuple[int, int]):
        pass
