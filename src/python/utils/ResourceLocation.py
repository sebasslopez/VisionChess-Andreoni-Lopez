import pygame

def getImage(path:str) -> pygame.Surface:
    try:
        img = pygame.image.load("../assets/textures/"+path+".png").convert_alpha()
    except FileNotFoundError:
        print("Could not found image in path:" + path+".png")
        return pygame.image.load("../assets/textures/missing.png").convert_alpha()
    return img