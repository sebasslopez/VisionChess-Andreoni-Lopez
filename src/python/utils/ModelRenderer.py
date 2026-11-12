from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np
import pygame

from .ResourceLocation import getModel, getTexture


@dataclass(frozen=True)
class _Face:
    points: tuple[tuple[float, float, float], ...]
    uv: tuple[tuple[float, float], ...]
    uv_rotation: int
    shade: float
    depth: float


class ModelRenderer:
    """Renderizador 3D simple para los modelos JSON de las piezas."""

    _face_axes = {
        "north": (("z", 0), ("x", 1), ("y", 1)),
        "south": (("z", 1), ("x", -1), ("y", 1)),
        "west": (("x", 0), ("z", -1), ("y", 1)),
        "east": (("x", 1), ("z", 1), ("y", 1)),
        "down": (("y", 0), ("x", 1), ("z", -1)),
        "up": (("y", 1), ("x", 1), ("z", 1)),
    }
    def __init__(self, square_size: int = 100):
        self.square_size = square_size
        self._model_cache: dict[str, dict[str, Any]] = {}
        self._face_geometry_cache: dict[str, list[_Face]] = {}
        self._texture_cache: dict[str, pygame.Surface] = {}
        self._texture_data_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        self._color_cache: dict[tuple[str, tuple[float, float, float, float]], tuple[int, int, int]] = {}
        self._render_cache_key = None
        self._render_cache_surface: pygame.Surface | None = None
        self.camera_yaw = 0.7853981634
        self.camera_elevation = 0.45
        self.camera_zoom = 1.0
        self.camera_pan = [0.0, 0.0]

    def _load_model(self, model_name: str) -> dict[str, Any]:
        if model_name in self._model_cache:
            return self._model_cache[model_name]

        model = getModel(f"chess:models/{model_name}")
        parent = model.get("parent")
        if parent:
            parent_model = getModel(parent)
            merged = dict(parent_model)
            merged["textures"] = dict(parent_model.get("textures", {}))
            merged["textures"].update(model.get("textures", {}))
            merged["elements"] = model.get("elements", parent_model.get("elements", []))
            model = merged

        self._model_cache[model_name] = model
        return model

    @staticmethod
    def _value(point: dict[str, float], axis: str) -> float:
        return point[axis]

    @staticmethod
    def _rotate_point(
        point: tuple[float, float, float],
        rotation: dict[str, Any] | None,
    ) -> tuple[float, float, float]:
        """Aplica la rotación Minecraft de un elemento alrededor de su origen."""
        if not rotation:
            return point

        axis = rotation.get("axis")
        if axis not in ("x", "y", "z"):
            return point

        origin = tuple(float(value) for value in rotation.get("origin", (8, 8, 8)))
        angle = math.radians(float(rotation.get("angle", 0)))
        cosine = math.cos(angle)
        sine = math.sin(angle)
        relative = [point[index] - origin[index] for index in range(3)]

        if rotation.get("rescale"):
            # Es el factor usado para que un cubo rotado conserve su tamaño
            # aparente en los modelos de bloques.
            rescale = 1 / (abs(cosine) + abs(sine))
            if axis == "x":
                relative[1] *= rescale
                relative[2] *= rescale
            elif axis == "y":
                relative[0] *= rescale
                relative[2] *= rescale
            else:
                relative[0] *= rescale
                relative[1] *= rescale

        x, y, z = relative
        if axis == "x":
            rotated = (x, y * cosine - z * sine, y * sine + z * cosine)
        elif axis == "y":
            rotated = (x * cosine + z * sine, y, -x * sine + z * cosine)
        else:
            rotated = (x * cosine - y * sine, x * sine + y * cosine, z)

        return tuple(rotated[index] + origin[index] for index in range(3))

    def _project(self, point: tuple[float, float, float], center: tuple[float, float], scale: float) -> tuple[int, int]:
        x, y, z = point
        # Cámara elevada mirando desde el frente: conserva la forma 3D sin
        # requerir OpenGL y mantiene cada pieza dentro de su casilla.
        x -= 8
        z -= 8
        cos_yaw = math.cos(self.camera_yaw)
        sin_yaw = math.sin(self.camera_yaw)
        rotated_x = x * cos_yaw - z * sin_yaw
        rotated_z = x * sin_yaw + z * cos_yaw
        screen_x = center[0] + rotated_x * scale * self.camera_zoom
        screen_y = (center[1] + rotated_z * scale * self.camera_elevation * self.camera_zoom
                    - y * scale * 0.9 * self.camera_zoom)
        return round(screen_x), round(screen_y)

    def _camera_depth(self, x: float, z: float) -> float:
        x -= 4
        z -= 4
        return x * math.sin(self.camera_yaw) + z * math.cos(self.camera_yaw)

    def _camera_point_depth(self, point: tuple[float, float, float]) -> float:
        """Profundidad considerando posición horizontal y altura."""
        x, height, z = point
        # Los modelos usan una escala 0..16 por pieza; 16 unidades equivalen
        # a la altura de una casilla.
        local_x = x / 16 - 0.5
        local_z = z / 16 - 0.5
        return (
            local_x * math.sin(self.camera_yaw)
            + local_z * math.cos(self.camera_yaw)
            + (height / 16) * (self.camera_elevation / 0.9)
        )

    def _texture_color(self, texture_name: str, uv: tuple[float, float, float, float]) -> tuple[int, int, int]:
        key = (texture_name, uv)
        if key in self._color_cache:
            return self._color_cache[key]

        texture = self._texture_cache.get(texture_name)
        if texture is None:
            texture = getTexture(texture_name, "models")
            self._texture_cache[texture_name] = texture

        u_start = max(0, min(texture.get_width() - 1, round(min(uv[0], uv[2]) / 16 * texture.get_width())))
        u_end = max(0, min(texture.get_width() - 1, round(max(uv[0], uv[2]) / 16 * texture.get_width())))
        v_start = max(0, min(texture.get_height() - 1, round(min(uv[1], uv[3]) / 16 * texture.get_height())))
        v_end = max(0, min(texture.get_height() - 1, round(max(uv[1], uv[3]) / 16 * texture.get_height())))

        samples = []
        for sample_u in range(u_start, u_end + 1, max(1, (u_end - u_start) // 3 or 1)):
            for sample_v in range(v_start, v_end + 1, max(1, (v_end - v_start) // 3 or 1)):
                color = texture.get_at((sample_u, sample_v))
                if len(color) < 4 or color.a > 20:
                    samples.append((color.r, color.g, color.b))

        if samples:
            result = tuple(round(sum(color[channel] for color in samples) / len(samples)) for channel in range(3))
        else:
            result = (180, 180, 180)
        self._color_cache[key] = result
        return result

    def _texture_data(self, texture_name: str) -> tuple[np.ndarray, np.ndarray]:
        cached = self._texture_data_cache.get(texture_name)
        if cached is not None:
            return cached
        texture = self._texture_cache.get(texture_name)
        if texture is None:
            texture = getTexture(texture_name, "models")
            self._texture_cache[texture_name] = texture
        data = pygame.surfarray.array3d(texture)
        alpha = pygame.surfarray.array_alpha(texture)
        self._texture_data_cache[texture_name] = (data, alpha)
        return data, alpha

    def _faces_for_element(self, element: dict[str, Any], texture_name: str) -> list[_Face]:
        start = tuple(float(value) for value in element["from"])
        end = tuple(float(value) for value in element["to"])
        coordinates = {
            "x": (start[0], end[0]),
            "y": (start[1], end[1]),
            "z": (start[2], end[2]),
        }
        faces = []
        for name, face in element.get("faces", {}).items():
            axes = self._face_axes.get(name)
            if axes is None:
                continue
            if "uv" not in face:
                continue

            fixed_axis, first_axis, second_axis = axes
            fixed_name, fixed_value = fixed_axis
            first_name, first_direction = first_axis
            second_name, second_direction = second_axis
            fixed = coordinates[fixed_name][fixed_value]
            first = coordinates[first_name]
            second = coordinates[second_name]
            corners = [
                {fixed_name: fixed, first_name: first[0], second_name: second[0]},
                {fixed_name: fixed, first_name: first[1], second_name: second[0]},
                {fixed_name: fixed, first_name: first[1], second_name: second[1]},
                {fixed_name: fixed, first_name: first[0], second_name: second[1]},
            ]
            if first_direction < 0:
                corners.reverse()
            if second_direction < 0:
                corners.reverse()
            points = tuple(
                self._rotate_point((corner["x"], corner["y"], corner["z"]), element.get("rotation"))
                for corner in corners
            )
            uv_values = tuple(float(value) for value in face["uv"])
            u1, v1, u2, v2 = uv_values
            uv_points = []
            for corner in corners:
                if name in ("north", "south"):
                    first_ratio = (corner["x"] - start[0]) / (end[0] - start[0] or 1)
                    second_ratio = (corner["y"] - start[1]) / (end[1] - start[1] or 1)
                elif name in ("west", "east"):
                    first_ratio = (corner["z"] - start[2]) / (end[2] - start[2] or 1)
                    second_ratio = (corner["y"] - start[1]) / (end[1] - start[1] or 1)
                else:
                    first_ratio = (corner["x"] - start[0]) / (end[0] - start[0] or 1)
                    second_ratio = (corner["z"] - start[2]) / (end[2] - start[2] or 1)
                uv_points.append((u1 + (u2 - u1) * first_ratio, v1 + (v2 - v1) * second_ratio))
            uv_rotation = int(face.get("rotation", 0))
            depth = sum(self._camera_point_depth(point) for point in points) / 4
            faces.append(_Face(points, tuple(uv_points), uv_rotation, 1.0, depth))
        return faces

    def draw_piece(
        self,
        window: pygame.Surface,
        piece: Any,
        center: tuple[float, float],
        square_size: float | None = None,
    ) -> None:
        pixels = pygame.surfarray.pixels3d(window)
        zbuffer = np.full((window.get_height(), window.get_width()), -np.inf, dtype=np.float32)
        for _, polygon, texture_data, uv, uv_rotation, depths in self._project_piece_faces(piece, center, square_size):
            self._draw_face_zbuffer(pixels, zbuffer, polygon, depths, texture_data, uv, uv_rotation)
        del pixels

    @staticmethod
    def _draw_face_zbuffer(
        pixels: Any,
        zbuffer: np.ndarray,
        polygon: list[tuple[int, int]],
        depths: list[float],
        texture_data: tuple[np.ndarray, np.ndarray],
        uv: tuple[tuple[float, float], ...],
        uv_rotation: int,
    ) -> None:
        """Pinta una cara usando su UV y alpha reales por píxel."""
        width, height = pixels.shape[:2]
        texture, alpha = texture_data
        texture_width, texture_height = texture.shape[:2]
        uv_points = list(uv)
        center_u = sum(point[0] for point in uv_points) / len(uv_points)
        center_v = sum(point[1] for point in uv_points) / len(uv_points)
        for _ in range((uv_rotation % 360) // 90):
            uv_points = [
                (center_u - (v - center_v), center_v + (u - center_u))
                for u, v in uv_points
            ]

        for indexes in ((0, 1, 2), (0, 2, 3)):
            triangle = [polygon[index] for index in indexes]
            triangle_depths = [depths[index] for index in indexes]
            triangle_uv = [uv_points[index] for index in indexes]
            x_values = [point[0] for point in triangle]
            y_values = [point[1] for point in triangle]
            x_min = max(0, min(x_values))
            x_max = min(width - 1, max(x_values))
            y_min = max(0, min(y_values))
            y_max = min(height - 1, max(y_values))
            if x_min > x_max or y_min > y_max:
                continue

            grid_x, grid_y = np.meshgrid(
                np.arange(x_min, x_max + 1, dtype=np.float32),
                np.arange(y_min, y_max + 1, dtype=np.float32),
            )
            x0, y0 = triangle[0]
            x1, y1 = triangle[1]
            x2, y2 = triangle[2]
            denominator = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(denominator) < 1e-6:
                continue
            weight_0 = ((y1 - y2) * (grid_x - x2) + (x2 - x1) * (grid_y - y2)) / denominator
            weight_1 = ((y2 - y0) * (grid_x - x2) + (x0 - x2) * (grid_y - y2)) / denominator
            weight_2 = 1 - weight_0 - weight_1
            inside = (weight_0 >= -0.001) & (weight_1 >= -0.001) & (weight_2 >= -0.001)
            depth = weight_0 * triangle_depths[0] + weight_1 * triangle_depths[1] + weight_2 * triangle_depths[2]
            texture_u = weight_0 * triangle_uv[0][0] + weight_1 * triangle_uv[1][0] + weight_2 * triangle_uv[2][0]
            texture_v = weight_0 * triangle_uv[0][1] + weight_1 * triangle_uv[1][1] + weight_2 * triangle_uv[2][1]
            texture_x_float = np.clip(texture_u / 16 * (texture_width - 1), 0, texture_width - 1)
            texture_y_float = np.clip(texture_v / 16 * (texture_height - 1), 0, texture_height - 1)
            x0_texture = texture_x_float.astype(np.int32)
            y0_texture = texture_y_float.astype(np.int32)
            x1_texture = np.minimum(x0_texture + 1, texture_width - 1)
            y1_texture = np.minimum(y0_texture + 1, texture_height - 1)
            x_weight = (texture_x_float - x0_texture)[..., None]
            y_weight = (texture_y_float - y0_texture)[..., None]

            def sample_texture(source: np.ndarray) -> np.ndarray:
                top = source[x0_texture, y0_texture] * (1 - x_weight) + source[x1_texture, y0_texture] * x_weight
                bottom = source[x0_texture, y1_texture] * (1 - x_weight) + source[x1_texture, y1_texture] * x_weight
                return top * (1 - y_weight) + bottom * y_weight

            source_alpha = sample_texture(alpha.astype(np.float32)[..., None])[..., 0]
            current_depth = zbuffer[y_min:y_max + 1, x_min:x_max + 1]
            # Los modelos tienen elementos muy cercanos/coplanares. Un
            # epsilon demasiado pequeño produce z-fighting en forma de rayas.
            visible = inside & (source_alpha > 0) & (depth > current_depth + 0.02)
            current_depth[visible] = depth[visible]
            region = pixels[x_min:x_max + 1, y_min:y_max + 1]
            source_color = sample_texture(texture.astype(np.float32))
            destination_color = region.transpose(1, 0, 2).astype(np.float32)
            opacity = (source_alpha.astype(np.float32) / 255)[..., None]
            blended = source_color * opacity + destination_color * (1 - opacity)
            region[visible.T] = blended.astype(np.uint8)[visible]

    def _project_piece_faces(
        self,
        piece: Any,
        center: tuple[float, float],
        square_size: float | None = None,
        depth_offset: float = 0.0,
    ) -> list[tuple[float, list[tuple[int, int]], tuple[np.ndarray, np.ndarray], tuple[tuple[float, float], ...], int, list[float]]]:
        """Prepara las caras proyectadas para poder ordenarlas globalmente."""
        piece_name = piece.__class__.__name__.lower()
        color_name = piece.color.name.removeprefix("Color.").lower()
        # Las piezas marcadas como inválidas usan RED/GRAY en la lógica del
        # tablero, pero no tienen un modelo JSON propio. Se conserva el color
        # original para seleccionar el modelo blanco o negro correspondiente.
        if color_name not in ("white", "black"):
            original_color = getattr(piece, "ColorOG", piece.color)
            color_name = original_color.name.removeprefix("Color.").lower()
        model_name = f"{piece_name}_{color_name}"
        model = self._load_model(model_name)
        # La textura de una pieza se determina por su propio modelo raíz;
        # así un parent negro no puede arrastrar accidentalmente la textura
        # blanca de otra variante.
        texture_name = f"chess:models/{model_name}"
        is_black = color_name == "black"
        scale = (self.square_size if square_size is None else square_size) / 16
        faces = self._face_geometry_cache.get(model_name)
        if faces is None:
            faces = []
            for element in model.get("elements", []):
                faces.extend(self._faces_for_element(element, texture_name))
            self._face_geometry_cache[model_name] = faces

        projected_faces = []
        texture_data = self._texture_data(texture_name)
        for face in faces:
            # Luz ambiente mínima: una textura oscura no convierte toda la
            # cara en un polígono negro cuando cambia el ángulo de cámara.
            model_points = [
                (16 - point[0], point[1], 16 - point[2]) if is_black else point
                for point in face.points
            ]
            polygon = [self._project(point, center, scale) for point in model_points]
            depths = [
                depth_offset + self._camera_point_depth(point)
                for point in model_points
            ]
            projected_faces.append((
                sum(depths) / len(depths),
                polygon,
                texture_data,
                face.uv,
                face.uv_rotation,
                depths,
            ))
        return projected_faces

    def _project_board_point(
        self,
        point: tuple[float, float, float],
        origin: tuple[float, float],
        scale: float,
    ) -> tuple[int, int]:
        """Proyecta coordenadas mundiales (x, altura, z) a la ventana."""
        x, height, z = point
        # La cámara gira alrededor del centro del tablero (4, 4).
        x -= 4
        z -= 4
        cos_yaw = math.cos(self.camera_yaw)
        sin_yaw = math.sin(self.camera_yaw)
        rotated_x = x * cos_yaw - z * sin_yaw
        rotated_z = x * sin_yaw + z * cos_yaw
        return (
            round(origin[0] + rotated_x * scale * self.camera_zoom),
            round(origin[1] + rotated_z * scale * self.camera_elevation * self.camera_zoom
                  - height * scale * 0.9 * self.camera_zoom),
        )

    def orbit(self, horizontal: float, vertical: float) -> None:
        """Rota la cámara con el movimiento del mouse."""
        self.camera_yaw += horizontal * 0.01
        self.camera_elevation = max(0.12, min(1.25, self.camera_elevation + vertical * 0.006))

    def pan(self, horizontal: float, vertical: float) -> None:
        """Desplaza la cámara en pantalla."""
        self.camera_pan[0] += horizontal
        self.camera_pan[1] += vertical

    def zoom(self, amount: float) -> None:
        """Acerca o aleja la cámara."""
        self.camera_zoom = max(0.45, min(2.2, self.camera_zoom + amount))

    def reset_camera(self) -> None:
        self.camera_yaw = 0.7853981634
        self.camera_elevation = 0.45
        self.camera_zoom = 1.0
        self.camera_pan = [0.0, 0.0]

    def draw_coordinates(
        self,
        window: pygame.Surface,
        origin: tuple[float, float],
        scale: float,
    ) -> None:
        """Dibuja coordenadas sobre los bordes de la plataforma 3D."""
        font = pygame.font.Font(None, 28)
        for column in range(8):
            point = self._project_board_point((column + 0.5, 0.04, 8.32), origin, scale)
            label = font.render(chr(ord("a") + column), True, (235, 235, 235))
            window.blit(label, label.get_rect(center=(point[0], point[1])))
        for row in range(8):
            point = self._project_board_point((-0.32, 0.04, row + 0.5), origin, scale)
            label = font.render(str(8 - row), True, (235, 235, 235))
            window.blit(label, label.get_rect(center=(point[0], point[1])))

    def draw_board(self, window: pygame.Surface, board: Any, offset: tuple[int, int]) -> None:
        """Dibuja una escena 3D completa con plataforma, casillas y piezas."""
        board_state = tuple(
            (
                box.position.row,
                box.position.col,
                type(box.piece).__name__ if box.piece is not None else None,
                box.piece.color.name if box.piece is not None else None,
            )
            for row in board.board
            for box in row
        )
        cache_key = (
            window.get_size(),
            board_state,
            round(self.camera_yaw, 5),
            round(self.camera_elevation, 5),
            round(self.camera_zoom, 5),
            round(self.camera_pan[0], 2),
            round(self.camera_pan[1], 2),
        )
        if self._render_cache_key == cache_key and self._render_cache_surface is not None:
            window.blit(self._render_cache_surface, (0, 0))
            return

        window.fill((24, 31, 31))
        scale = min(58.0, (window.get_width() - 120) / (16 * 0.9))
        origin = (
            window.get_width() / 2 + self.camera_pan[0],
            window.get_height() * 0.46 + self.camera_pan[1],
        )
        board_depth = 0.55
        border = 0.42

        # Base gruesa de la plataforma: cuatro caras laterales y la tapa.
        slab_top = [
            self._project_board_point((x, 0, z), origin, scale)
            for x, z in ((-border, -border), (8 + border, -border),
                         (8 + border, 8 + border), (-border, 8 + border))
        ]
        slab_bottom = [
            self._project_board_point((x, -board_depth, z), origin, scale)
            for x, z in ((-border, -border), (8 + border, -border),
                         (8 + border, 8 + border), (-border, 8 + border))
        ]
        side_colors = ((55, 36, 23), (65, 43, 27), (45, 30, 20), (75, 49, 29))
        for index, color in enumerate(side_colors):
            following = (index + 1) % 4
            pygame.draw.polygon(
                window,
                color,
                [
                    slab_top[index],
                    slab_top[following],
                    slab_bottom[following],
                    slab_bottom[index],
                ],
            )
        pygame.draw.polygon(window, (92, 60, 34), slab_top)

        # Casillas como planos inclinados, no como rectángulos de pantalla.
        for row, boxes in enumerate(board.board):
            for column, box in enumerate(boxes):
                tile = [
                    self._project_board_point((column, 0.015, row), origin, scale),
                    self._project_board_point((column + 1, 0.015, row), origin, scale),
                    self._project_board_point((column + 1, 0.015, row + 1), origin, scale),
                    self._project_board_point((column, 0.015, row + 1), origin, scale),
                ]
                pygame.draw.polygon(window, box.getColor(), tile)
                pygame.draw.lines(window, (30, 30, 30), True, tile, 1)

        # El orden por profundidad evita que las piezas traseras tapen a las delanteras.
        pieces = [box for row in board.board for box in row if box.piece is not None]
        all_faces = []
        zbuffer = np.full((window.get_height(), window.get_width()), -np.inf, dtype=np.float32)
        for box in sorted(
            pieces,
            key=lambda item: self._camera_depth(item.position.col + 0.5, item.position.row + 0.5),
        ):
            center = self._project_board_point(
                (box.position.col + 0.5, 0, box.position.row + 0.5),
                origin,
                scale,
            )
            all_faces.extend(
                self._project_piece_faces(
                    box.piece,
                    center,
                    square_size=scale,
                    depth_offset=self._camera_depth(
                        box.position.col + 0.5,
                        box.position.row + 0.5,
                    ),
                )
            )

        pixels = pygame.surfarray.pixels3d(window)
        for _, polygon, texture_data, uv, uv_rotation, depths in all_faces:
            self._draw_face_zbuffer(
                pixels,
                zbuffer,
                polygon,
                depths,
                texture_data,
                uv,
                uv_rotation,
            )
        del pixels

        self.draw_coordinates(window, origin, scale)
        self._render_cache_key = cache_key
        self._render_cache_surface = window.copy()
