from ultralytics import YOLO
import cv2
import math
import numpy as np
from pathlib import Path


class BoardDetector:
    """Detecta el tablero y devuelve una vista cenital sin abrir ventanas."""

    def __init__(self, model_path=None, board_size=800, margin=150):
        if model_path is None:
            model_path = Path(__file__).resolve().parent / "models" / "board.pt"
        self.model = YOLO(str(model_path))
        self.board_size = board_size
        self.margin = margin
        self.previous_quadrilateral = None

    @staticmethod
    def _iou(box_a, box_b):
        ax1, ay1, ax2, ay2 = box_a
        bx1, by1, bx2, by2 = box_b
        width, height = max(0, min(ax2, bx2) - max(ax1, bx1)), max(0, min(ay2, by2) - max(ay1, by1))
        intersection = width * height
        if intersection == 0:
            return 0
        return intersection / ((ax2 - ax1) * (ay2 - ay1) + (bx2 - bx1) * (by2 - by1) - intersection)

    def _remove_overlapping_detections(self, detections):
        selected = []
        for detection in sorted(detections, key=lambda item: item["confidence"], reverse=True):
            if all(self._iou(detection["box"], chosen["box"]) == 0 for chosen in selected):
                selected.append(detection)
        return selected

    @staticmethod
    def _order_points(points):
        center_x = sum(x for x, _ in points) / len(points)
        center_y = sum(y for _, y in points) / len(points)
        return sorted(points, key=lambda point: math.atan2(point[1] - center_y, point[0] - center_x))

    @staticmethod
    def _area(points):
        return abs(sum(points[i][0] * points[(i + 1) % 4][1] - points[(i + 1) % 4][0] * points[i][1] for i in range(4)) / 2)

    def _is_valid_quadrilateral(self, points):
        if points is None or len(points) != 4 or self._area(points) == 0:
            return False
        cross_products = []
        for i in range(4):
            current, following, next_point = points[i], points[(i + 1) % 4], points[(i + 2) % 4]
            vector_a = (following[0] - current[0], following[1] - current[1])
            vector_b = (next_point[0] - following[0], next_point[1] - following[1])
            cross_products.append(vector_a[0] * vector_b[1] - vector_a[1] * vector_b[0])
        return all(value > 0 for value in cross_products) or all(value < 0 for value in cross_products)

    def _is_similar_quadrilateral(self, current, previous):
        previous_area = self._area(previous)
        if previous_area == 0 or not 0.75 <= self._area(current) / previous_area <= 1.25:
            return False
        previous_width = max(x for x, _ in previous) - min(x for x, _ in previous)
        previous_height = max(y for _, y in previous) - min(y for _, y in previous)
        current_width = max(x for x, _ in current) - min(x for x, _ in current)
        current_height = max(y for _, y in current) - min(y for _, y in current)
        if previous_width == 0 or previous_height == 0:
            return False
        displacement = max(math.hypot((current[i][0] - previous[i][0]) / previous_width, (current[i][1] - previous[i][1]) / previous_height) for i in range(4))
        return (displacement <= 0.12 and 0.85 <= current_width / previous_width <= 1.15 and 0.85 <= current_height / previous_height <= 1.15)

    def _create_board_view(self, frame, quadrilateral):
        canvas_size = self.board_size + 2 * self.margin
        source = np.array(quadrilateral, dtype="float32")
        destination = np.array([(self.margin, self.margin), (self.margin + self.board_size, self.margin), (self.margin + self.board_size, self.margin + self.board_size), (self.margin, self.margin + self.board_size)], dtype="float32")
        transform = cv2.getPerspectiveTransform(source, destination)
        board_view = cv2.warpPerspective(frame, transform, (canvas_size, canvas_size))
        cell_size = self.board_size / 8
        """for i in range(9):
            position = round(self.margin + i * cell_size)
            cv2.line(board_view, (position, self.margin), (position, self.margin + self.board_size), (0, 255, 0), 1)
            cv2.line(board_view, (self.margin, position), (self.margin + self.board_size, position), (0, 255, 0), 1)
        """
        return board_view

    def reset(self):
        """Olvida las esquinas actuales para forzar un cálculo nuevo."""
        self.previous_quadrilateral = None

    def run(self, frame):
        """Devuelve el frame transformado, o None mientras faltan esquinas."""
        results = self.model(frame, imgsz=(640, 640), verbose=False)
        detections = [{"box": box, "confidence": confidence} for box, confidence in zip(results[0].boxes.xyxy.cpu().tolist(), results[0].boxes.conf.cpu().tolist())]
        detections = self._remove_overlapping_detections(detections)[:4]
        points = [(round((item["box"][0] + item["box"][2]) / 2), round((item["box"][1] + item["box"][3]) / 2)) for item in detections]
        quadrilateral = self._order_points(points) if len(points) == 4 else None
        if self._is_valid_quadrilateral(quadrilateral):
            if self.previous_quadrilateral is None or self._is_similar_quadrilateral(quadrilateral, self.previous_quadrilateral):
                self.previous_quadrilateral = quadrilateral
        if self.previous_quadrilateral is None:
            return None
        return self._create_board_view(frame, self.previous_quadrilateral)
