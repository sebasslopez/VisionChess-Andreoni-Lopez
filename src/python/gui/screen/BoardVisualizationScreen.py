import pygame
import threading
from chess import Board as boar
from chess.Position import Position
from .screen import Screen
from vision.Vision import Vision
from utils.ModelRenderer import ModelRenderer


class BoardVisualizationScreen(Screen):
    def __init__(self, size: tuple[int, int]):
        super().__init__(size, None)
        Position.OFFSET_X = self.BOARD_MARGIN
        Position.OFFSET_Y = self.BOARD_MARGIN
        self.vision = Vision()
        self.model_renderer = ModelRenderer()
        self.board: boar.Board | None = None
        self.lastDetectedBoard = ""
        self.loading_dots = 1
        self.loading_tick = 0
        self.camera_drag_button = None
        self.last_mouse_position = None
        self._render_lock = threading.Lock()
        self._render_event = threading.Event()
        self._render_stop = threading.Event()
        self._render_request = None
        self._render_surface = None
        self._render_generation = 0
        self._last_render_request = None
        self._render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self._render_thread.start()

    def _render_loop(self):
        while not self._render_stop.is_set():
            self._render_event.wait(0.1)
            self._render_event.clear()
            if self._render_stop.is_set():
                break
            with self._render_lock:
                request = self._render_request
            if request is None:
                continue

            board_state, size, generation = request
            try:
                rendered_board = boar.Board(False, board_state, turns=False)
                surface = pygame.Surface(size)
                with self._render_lock:
                    self.model_renderer.draw_board(surface, rendered_board, (0, 0))
                    if generation == self._render_generation:
                        self._render_surface = surface
            except (RuntimeError, pygame.error):
                # La ventana puede cerrarse mientras el hilo termina.
                if self._render_stop.is_set():
                    break

    def _queue_render(self, board_state: str, size: tuple[int, int]):
        request = (board_state, size, self._render_generation)
        if request == self._last_render_request:
            return
        self._last_render_request = request
        with self._render_lock:
            self._render_request = request
        self._render_event.set()

    def _camera_changed(self):
        self._render_generation += 1
        self._last_render_request = None

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
            self.lastDetectedBoard = detected_board
        elif self.board is not None and len(detected_board) == 64 and detected_board != self.lastDetectedBoard:
            self.board.updateBoard(detected_board)
            self.lastDetectedBoard = detected_board
        if self.board is not None:
            self._queue_render(self.board.actual, window.get_size())
            with self._render_lock:
                rendered_surface = self._render_surface
            if rendered_surface is not None:
                window.blit(rendered_surface, (0, 0))
            else:
                font = pygame.font.Font(None, 36)
                text = font.render("Renderizando tablero...", True, (255, 255, 255))
                window.blit(text, text.get_rect(center=window.get_rect().center))
        else:
            font = pygame.font.Font(None, 48)
            text = font.render("Cargando" + "." * self.loading_dots, True, (255, 255, 255))
            text_rect = text.get_rect(center=window.get_rect().center)
            window.blit(text, text_rect)
            self.loading_tick += 1
            if self.loading_tick >= 5:
                self.loading_tick = 0
                self.loading_dots = self.loading_dots % 3 + 1

    def update(self, window: pygame.Surface, size: tuple[int, int]):
        super().clear(window)
        self.display(window)
        pygame.display.flip()

    def handle_event(self, event: pygame.event.Event):
        """Controla la cámara 3D sin convertir la vista en un tablero jugable."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            self.camera_drag_button = event.button
            self.last_mouse_position = event.pos
            return
        if event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
            self.camera_drag_button = None
            self.last_mouse_position = None
            return
        if event.type == pygame.MOUSEMOTION and self.camera_drag_button is not None:
            if self.last_mouse_position is None:
                self.last_mouse_position = event.pos
                return
            previous_x, previous_y = self.last_mouse_position
            delta_x = event.pos[0] - previous_x
            delta_y = event.pos[1] - previous_y
            if self.camera_drag_button == 1:
                with self._render_lock:
                    self.model_renderer.orbit(delta_x, delta_y)
            else:
                with self._render_lock:
                    self.model_renderer.pan(delta_x, delta_y)
            self._camera_changed()
            self.last_mouse_position = event.pos
            return
        if event.type == pygame.MOUSEWHEEL:
            with self._render_lock:
                self.model_renderer.zoom(event.y * 0.08)
            self._camera_changed()
            return
        if event.type == pygame.KEYDOWN:
            self.handleKeyPress(event.key)

    def handleKeyPress(self, key: int):
        if key == pygame.K_v and self.board is not None:
            self.board.acceptInvalidMoves()
            return
        if key == pygame.K_r:
            self.vision.reset()
            self.board = None
            self.lastDetectedBoard = ""
            self.loading_dots = 1
            self.loading_tick = 0
            return
        if key == pygame.K_LEFT:
            with self._render_lock:
                self.model_renderer.orbit(-12, 0)
            self._camera_changed()
            return
        if key == pygame.K_RIGHT:
            with self._render_lock:
                self.model_renderer.orbit(12, 0)
            self._camera_changed()
            return
        if key == pygame.K_UP:
            with self._render_lock:
                self.model_renderer.orbit(0, -12)
            self._camera_changed()
            return
        if key == pygame.K_DOWN:
            with self._render_lock:
                self.model_renderer.orbit(0, 12)
            self._camera_changed()
            return
        if key in (
            pygame.K_EQUALS,
            getattr(pygame, "K_PLUS", -1),
            getattr(pygame, "K_KP_PLUS", -1),
        ):
            with self._render_lock:
                self.model_renderer.zoom(0.08)
            self._camera_changed()
            return
        if key == pygame.K_MINUS:
            with self._render_lock:
                self.model_renderer.zoom(-0.08)
            self._camera_changed()
            return
        if key == pygame.K_HOME:
            with self._render_lock:
                self.model_renderer.reset_camera()
            self._camera_changed()
            return
        super().handleKeyPress(key)

    def stop(self):
        self._render_stop.set()
        self._render_event.set()
        if self._render_thread.is_alive():
            self._render_thread.join(timeout=1)
