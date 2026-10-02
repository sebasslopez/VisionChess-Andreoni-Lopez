import pygame
from gui.screen.screen import Screen
from gui.screen.boardScreen import boardScreen
from gui.screen.BoardVisualizationScreen import BoardVisualizationScreen


class VisionChess:
    instance: "VisionChess | None" = None

    def __init__(self):
        VisionChess.instance = self
        self.screenSize = (900, 900)
        pygame.init()
        self.screenwindow: pygame.Surface | None = pygame.display.set_mode(self.screenSize, pygame.SCALED)
        self.clock: pygame.time.Clock | None = pygame.time.Clock()
        self.screen = BoardVisualizationScreen(self.screenSize)
        pygame.display.set_caption("VisionChess")
        self.running = True
        self.run()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                update: bool = False
                if event.type == pygame.QUIT:
                    self.stop()
                if event.type == pygame.WINDOWRESIZED:
                    update = True
                if self.screen is not None:
                    self.screen.handle_event(event)
                    if update and self.screenwindow is not None:
                        self.screen.update(self.screenwindow, self.screenSize)
            if self.screenwindow is not None and self.screen is not None:
                self.screen.display(self.screenwindow)
            pygame.display.flip()
            if self.clock is not None: self.clock.tick(60)
        pygame.quit()

    def setScreen(self, new_screen: Screen | None):
        self.screen = new_screen

    def getScreen(self) -> Screen | None:
        return self.screen

    @staticmethod
    def getInstance() -> "VisionChess":
        if VisionChess.instance is None:
            return VisionChess()
        return VisionChess.instance

    def stop(self):
        self.running = False
        pygame.quit()


if __name__ == "__main__":
    VisionChess()
