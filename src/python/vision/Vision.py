import cv2
import numpy as np

from detect_board import BoardDetector
from detect_pieces import PieceDetector


class Vision:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.board_detector = BoardDetector()
        self.piece_detector = PieceDetector()
        self.cap = cv2.VideoCapture(self.camera_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    @staticmethod
    def _waiting_frame():
        frame = np.zeros((1100, 1100, 3), dtype="uint8")
        cv2.putText(frame, "Esperando tablero...", (240, 420),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        return frame

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        cv2.namedWindow("Tablero", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Tablero", 1100, 1100)
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                transformed_frame = self.board_detector.run(frame)
                if transformed_frame is None:
                    display_frame = self._waiting_frame()
                else:
                    positions = self.piece_detector.run(transformed_frame)
                    print(positions)
                    display_frame = transformed_frame
                cv2.imshow("Tablero", display_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("r"):
                    self.board_detector.reset()
                elif key == ord("q"):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

    def detect(self) -> str:
        ret, frame = self.cap.read()
        if not ret:
            return ""
        transformed_frame = self.board_detector.run(frame)
        if transformed_frame is None:
            return ""
        else:
            board = self.piece_detector.run(transformed_frame)
            #print(positions)
            return board

    def stop(self):
        self.cap.release()
        cv2.destroyAllWindows()

    def reset(self):
        self.board_detector.reset()

if __name__ == "__main__":
    Vision().run()
