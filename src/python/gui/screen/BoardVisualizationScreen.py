import pygame
from chess import Board as boar
from chess.Position import Position
from .screen import Screen
from vision.Vision import Vision


class BoardVisualizationScreen(Screen):
    def __init__(self, size: tuple[int, int]):
        super().__init__(size, None)
        Position.OFFSET_X = self.BOARD_MARGIN
        Position.OFFSET_Y = self.BOARD_MARGIN
        self.vision = Vision()
        self.board: boar.Board | None = None
        self.loading_dots = 1
        self.loading_tick = 0

    @staticmethod
    def rotateBoard(board: str) -> str:
        if board == "" or len(board) != 64:
            return ""
        rows = [board[index:index + 8] for index in range(0, 64, 8)]
        return "".join(rows[7 - column][row] for row in range(8) for column in range(8))

    def getDetectedBoard(self) -> str:
        return self.rotateBoard(self.vision.detect())

    def display(self, window: pygame.Surface):
        window.fill((0, 0, 0))
        detected_board = self.getDetectedBoard()
        if self.board is None and len(detected_board) == 64:
            self.board = boar.Board(False, detected_board, turns=False)
        elif self.board is not None and len(detected_board) == 64:
            self.board.updateBoard(detected_board)
        if self.board is not None:
            self.board.display(window)
        else:
            font = pygame.font.Font(None, 48)
            text = font.render("Cargando" + "." * self.loading_dots, True, (255, 255, 255))
            text_rect = text.get_rect(center=window.get_rect().center)
            window.blit(text, text_rect)
            self.loading_tick += 1
            if self.loading_tick >= 5:
                self.loading_tick = 0
                self.loading_dots = self.loading_dots % 3 + 1
        self.displayBoardCoordinates(window)

    def update(self, window: pygame.Surface, size: tuple[int, int]):
        super().clear(window)
        self.display(window)
        pygame.display.flip()

    def handleKeyPress(self, key: int):
        if key == pygame.K_r:
            self.vision.reset()
            self.board = None
            self.loading_dots = 1
            self.loading_tick = 0
            return
        super().handleKeyPress(key)
