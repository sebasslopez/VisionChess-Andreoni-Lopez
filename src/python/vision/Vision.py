import cv2
import numpy as np
import threading
import time

from .detect_board import BoardDetector
from .detect_pieces import PieceDetector


class Vision:
    DEFAULT = "." * 64

    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.detection_history = []
        self.detection_history_limit = 60
        self.stabilization_history_limit = 15
        self.current_detection = ""
        self.pending_detection = ""
        self.pending_detection_count = 0
        self.detection_interval = 1 / 12
        self.board_detection_interval = 12
        self.board_detection_frames = 0
        self.latest_detection = ""
        self.latest_frame = None
        self.detection_lock = threading.Lock()
        self.frame_lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.capture_thread = None
        self.detection_thread = None
        self.board_detector = BoardDetector()
        self.piece_detector = PieceDetector()
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    @staticmethod
    def _waiting_frame():
        frame = np.zeros((1100, 1100, 3), dtype="uint8")
        cv2.putText(frame, "Esperando tablero...", (240, 420), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame

    def run(self):
        cv2.namedWindow("Tablero", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Tablero", 1100, 1100)
        try:
            while True:
                ret, frame = self.cap.read()
                if not ret:
                    break
                transformed_frame = self.board_detector.run(frame)
                if transformed_frame is None:
                    display_frame = self._waiting_frame()
                else:
                    positions = self._stabilize_detection(self.piece_detector.run(transformed_frame, True))
                    print(positions)
                    display_frame = transformed_frame
                cv2.imshow("Tablero", display_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("r"):
                    self.board_detector.reset()
                elif key == ord("q"):
                    break
        finally:
            self.cap.release()
            cv2.destroyAllWindows()

    def detect(self) -> str:
        self._start_detection_thread()
        with self.detection_lock:
            return self.latest_detection

    def _start_detection_thread(self):
        if self.detection_thread is not None and self.detection_thread.is_alive():
            return
        self.stop_event.clear()
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
        self.detection_thread = threading.Thread(target=self._detect_loop, daemon=True)
        self.detection_thread.start()

    def _capture_loop(self):
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if ret:
                with self.frame_lock:
                    self.latest_frame = frame
            else:
                self.stop_event.wait(0.01)

    def _detect_loop(self):
        while not self.stop_event.is_set():
            started = time.perf_counter()
            with self.frame_lock:
                frame = None if self.latest_frame is None else self.latest_frame.copy()
            if frame is None:
                self.stop_event.wait(0.01)
                continue
            with self.state_lock:
                detect_board = (self.board_detector.previous_quadrilateral is None or self.board_detection_frames >= self.board_detection_interval)
                transformed_frame = self.board_detector.run(frame, detect_board)
                if detect_board:
                    self.board_detection_frames = 0
                else:
                    self.board_detection_frames += 1
                if transformed_frame is None:
                    stable_detection = ""
                    self.board_detection_frames = 0
                else:
                    stable_detection = self._stabilize_detection(self.piece_detector.run(transformed_frame))
            with self.detection_lock:
                self.latest_detection = stable_detection
            remaining = self.detection_interval - (time.perf_counter() - started)
            if remaining > 0:
                self.stop_event.wait(remaining)

    def _stabilize_detection(self, board: str) -> str:
        if board == "" or not isinstance(board, str) or len(board) != 64:
            return ""
        if board == self.pending_detection:
            self.pending_detection_count += 1
        else:
            self.pending_detection = board
            self.pending_detection_count = 1
        self.detection_history.append(board)
        if len(self.detection_history) > self.detection_history_limit:
            self.detection_history.pop(0)
        stable_board = []
        for index in range(64):
            counts = {}
            for detection in self.detection_history[-self.stabilization_history_limit:]:
                piece = detection[index]
                counts[piece] = counts.get(piece, 0) + 1
            selected = max(counts, key=counts.get)
            if selected == ".":
                pieces = [piece for piece, count in counts.items() if piece != "." and count >= 3]
                if pieces:
                    selected = max(pieces, key=counts.get)
            stable_board.append(selected)
        stable_detection = "".join(stable_board)
        if not self.current_detection:
            self.current_detection = stable_detection
        if (board != self.current_detection and self.pending_detection_count >= 2):
            self.current_detection = board
            self.detection_history = [board]
            return board
        self.current_detection = stable_detection
        return stable_detection

    def stop(self):
        self.stop_event.set()
        if self.detection_thread is not None and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=1)
        if self.capture_thread is not None and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=1)
        self.cap.release()
        cv2.destroyAllWindows()

    def reset(self):
        with self.state_lock:
            self.board_detector.reset()
            self.board_detection_frames = 0
            self.detection_history.clear()
            self.current_detection = ""
            self.pending_detection = ""
            self.pending_detection_count = 0
        with self.detection_lock:
            self.latest_detection = ""


if __name__ == "__main__":
    Vision().run()
