import pygame
from pathlib import Path


TEXTURES_DIR = Path(__file__).resolve().parents[2] / "assets" / "textures"

def getImage(path:str) -> pygame.Surface:
    image_path = TEXTURES_DIR / (path + ".png")
    try:
        img = pygame.image.load(str(image_path)).convert_alpha()
    except FileNotFoundError:
        print("Could not find image in path: " + str(image_path))
        return pygame.image.load(str(TEXTURES_DIR / "missing.png")).convert_alpha()
    return img
