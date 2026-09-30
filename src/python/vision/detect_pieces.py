from sympy.strategies.core import switch
from torch._export.db import case
from ultralytics import YOLO
import cv2


class PieceDetector:
    """Detecta piezas sobre la vista cenital del tablero."""

    def __init__(self, model_path="models/pieces.pt", board_size=800, margin=150):
        self.model = YOLO(model_path)
        self.board_size = board_size
        self.margin = margin
        self.overlap_threshold = 0.95

    @staticmethod
    def _intersection_over_union(box_a, box_b):
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        intersection_width = max(0, min(ax2, bx2) - max(ax1, bx1))
        intersection_height = max(0, min(ay2, by2) - max(ay1, by1))
        intersection_area = intersection_width * intersection_height
        if intersection_area == 0:
            return 0
        area_a = (ax2 - ax1) * (ay2 - ay1)
        area_b = (bx2 - bx1) * (by2 - by1)
        return intersection_area / (area_a + area_b - intersection_area)

    def _remove_duplicate_detections(self, detections):
        selected = []
        for detection in sorted(detections, key=lambda item: item["confidence"], reverse=True):
            if all(
                self._intersection_over_union(detection["box"], chosen["box"])
                <= self.overlap_threshold
                for chosen in selected
            ):
                selected.append(detection)
        return self._remove_same_square_detections(selected)

    def _square_name(self, x, y):
        cell_size = self.board_size / 8
        column = int((x - self.margin) / cell_size)
        row = int((y - self.margin) / cell_size)
        if not 0 <= column < 8 or not 0 <= row < 8:
            return None
        return f"{chr(ord('a') + column)}{8 - row}"

    def _remove_same_square_detections(self, detections):
        """Conserva la detección más confiable de cada casilla."""
        selected = []
        occupied_squares = set()
        for detection in sorted(detections, key=lambda item: item["confidence"], reverse=True):
            x1, y1, x2, y2 = detection["box"]
            square = self._square_name((x1 + x2) / 2, (max(y1,y2)+(y1-y2)/4))
            if square is not None and square in occupied_squares:
                continue
            selected.append(detection)
            if square is not None:
                occupied_squares.add(square)
        return selected

    def traducePieces(self,detections):
        board = ["."] * 64
        for d in detections:
            x1, y1, x2, y2 = d["box"]
            type = ""
            match d["class_id"]:
                case 0: type = "b"
                case 1: type = "k"
                case 2: type = "n"
                case 3: type = "p"
                case 4: type = "q"
                case 5: type = "r"
                case 6: type = "B"
                case 7: type = "K"
                case 8: type = "N"
                case 9: type = "P"
                case 10: type = "Q"
                case 11: type = "R"
            box = self.getBoxNumber((x1 + x2) / 2, (max(y1,y2)+(y1-y2)/4))
            if box != -1: board[box] = type
        return "".join(board)

    #{0: 'Black-bishop', 1: 'Black-king', 2: 'Black-knight', 3: 'Black-pawn', 4: 'Black-queen', 5: 'Black-rook', 6: 'White-bishop', 7: 'White-king', 8: 'White-knight', 9: 'White-pawn', 10: 'White-queen', 11: 'White-rook'}

    def getBoxNumber(self,x, y):
        cell_size = self.board_size / 8
        column = int((x - self.margin) / cell_size)
        row = int((y - self.margin) / cell_size)
        if not 0 <= column < 8 or not 0 <= row < 8:
            return -1
        return column + row*8

    def run(self, frame):
        """Anota `frame` y devuelve las piezas detectadas junto a sus casillas."""
        results = self.model(frame, imgsz=640)
        detections = [
            {"box": box, "confidence": confidence, "class_id": class_id}
            for box, confidence, class_id in zip(
                results[0].boxes.xyxy.cpu().tolist(),
                results[0].boxes.conf.cpu().tolist(),
                results[0].boxes.cls.cpu().tolist(),
            )
        ]
        positions = []
        detections = self._remove_duplicate_detections(detections)
        prom = 0
        count = 0
        for detection in detections:
            x1, y1, x2, y2 = detection["box"]
            top_left, bottom_right = (round(x1), round(y1)), (round(x2), round(y2))
            piece_name = self.model.names[int(detection["class_id"])]
            square = self._square_name((x1 + x2) / 2, (max(y1,y2)+(y1-y2)/4))
            squaren = self.getBoxNumber((x1 + x2) / 2, (max(y1,y2)+(y1-y2)/4))
            cv2.rectangle(frame, top_left, bottom_right, (255, 0, 0), 2)
            cv2.putText(frame, f"{piece_name} {detection['confidence']:.2f}",
                        (top_left[0], max(20, top_left[1] - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 0, 0), 2)
            if square is not None:
                conf = detection["confidence"]
                positions.append(
                    f"{piece_name}: {square},{squaren} ({conf:.2f})"
                )
                prom += conf
                count += 1
        print(prom)
        print(", ".join(positions) if positions else "Sin piezas detectadas")
        return self.traducePieces(detections)