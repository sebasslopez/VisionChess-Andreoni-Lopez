import pygame
from gui.screen.screen import Screen


class menuScreen(Screen):
    def __init__(self,size:tuple[int,int]):
        super().__init__(size, None)
        

    def handle_event(self, event: pygame.event.Event):
        pass

    def display(self, window: pygame.Surface):
        window.fill((0, 255, 255))
        pass

    def update(self, window: pygame.Surface,size:tuple[int,int]):
        super().clear(window)
        self.display(window)
        pygame.display.flip()

    def handleKeyPress(self,key: int):
        if key == pygame.K_ESCAPE and self.vision.getScreen is not None: self.vision.setScreen(menuScreen(self.screenSize))
        elif key == pygame.K_LEFT and self.vision.getScreen is not None: self.vision.setScreen(Screen(self.screenSize))
        super().handleKeyPress(key)