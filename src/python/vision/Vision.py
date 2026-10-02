import cv2
import numpy as np

from .detect_board import BoardDetector
from .detect_pieces import PieceDetector


class Vision:
    DEFAULT = "." * 64

    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.detection_history = []
        self.detection_history_limit = 60
        self.current_detection = ""
        self.pending_detection = ""
        self.pending_detection_count = 0
        self.board_detector = BoardDetector()
        self.piece_detector = PieceDetector()
        self.cap = cv2.VideoCapture(self.camera_index)
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
                    positions = self._stabilize_detection(self.piece_detector.run(transformed_frame))
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
        ret, frame = self.cap.read()
        if not ret:
            return ""
        transformed_frame = self.board_detector.run(frame)
        if transformed_frame is None: return ""
        else:
            board = self.piece_detector.run(transformed_frame)
            return self._stabilize_detection(board)

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
            for detection in self.detection_history:
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
        if (board != self.current_detection
                and self.pending_detection_count >= 3):
            self.current_detection = board
            self.detection_history = [board]
            return board
        self.current_detection = stable_detection
        return stable_detection

    def stop(self):
        self.cap.release()
        cv2.destroyAllWindows()

    def reset(self):
        self.board_detector.reset()
        self.detection_history.clear()
        self.current_detection = ""
        self.pending_detection = ""
        self.pending_detection_count = 0


if __name__ == "__main__":
    Vision().run()
