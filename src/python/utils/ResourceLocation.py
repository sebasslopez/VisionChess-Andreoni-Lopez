from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

import pygame


ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
TEXTURES_DIR = ASSETS_DIR / "textures"
SPRITES_DIR = TEXTURES_DIR / "sprites"
MODEL_TEXTURES_DIR = TEXTURES_DIR / "models"
MODELS_DIR = ASSETS_DIR / "models"
ResourceType = Literal["sprites", "models", "model"]


def _resource_path(resource: str | Path) -> str:
    """Normaliza una ruta con o sin namespace ``chess:``."""
    value = str(resource).replace("\\", "/").strip("/")
    if ":" in value:
        value = value.split(":", 1)[1]
    return value.removesuffix(".png").removesuffix(".json").strip("/")


def _asset_path(resource: str | Path, resource_type: ResourceType) -> Path:
    value = _resource_path(resource)

    if resource_type == "sprites":
        for prefix in ("textures/sprites/", "sprites/", "item/pieces/"):
            if value.startswith(prefix):
                value = value[len(prefix):]
                break
        return SPRITES_DIR / f"{value}.png"

    if resource_type == "models":
        for prefix in ("textures/models/", "models/"):
            if value.startswith(prefix):
                value = value[len(prefix):]
                break
        return MODEL_TEXTURES_DIR / f"{value}.png"

    for prefix in ("models/", "model/"):
        if value.startswith(prefix):
            value = value[len(prefix):]
            break
    return MODELS_DIR / f"{value}.json"


def getResourcePath(resource: str | Path, resource_type: ResourceType) -> Path:
    """Devuelve la ruta de un sprite, textura de modelo o modelo JSON."""
    return _asset_path(resource, resource_type)


def getImage(path: str | Path, resource_type: ResourceType | None = None) -> pygame.Surface:
    """Carga una imagen desde ``sprites`` o ``textures/models``.

    Ejemplos válidos: ``white_pawn``, ``sprites/white_pawn`` y
    ``chess:models/bishop_white``. Si no se indica el tipo, se infiere de la
    ruta y se usa ``sprites`` por compatibilidad con las piezas actuales.
    """
    normalized = _resource_path(path)
    if resource_type is None:
        resource_type = "models" if normalized.startswith(("models/", "textures/models/")) else "sprites"

    image_path = _asset_path(path, resource_type)
    try:
        return pygame.image.load(str(image_path)).convert_alpha()
    except FileNotFoundError:
        missing_path = SPRITES_DIR / "missing.png"
        print(f"Could not find image in path: {image_path}")
        return pygame.image.load(str(missing_path)).convert_alpha()


def getTexture(path: str | Path, resource_type: ResourceType = "sprites") -> pygame.Surface:
    """Alias explícito para obtener un sprite o una textura de modelo."""
    return getImage(path, resource_type)


def getModel(path: str | Path) -> dict[str, Any]:
    """Carga un modelo JSON desde ``assets/models`` o ``assets/models/custom``."""
    model_path = _asset_path(path, "model")
    try:
        with model_path.open("r", encoding="utf-8") as model_file:
            return json.load(model_file)
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Could not find model in path: {model_path}") from error
