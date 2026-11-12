"""Detección directa del tablero usando el modelo YOLO.

Este módulo es independiente de :mod:`detect_board`. No intenta decidir si las
detecciones forman un cuadrilátero ni conserva el resultado de frames previos:
devuelve exactamente las detecciones que entrega YOLO.
"""

from pathlib import Path
from typing import Any

import cv2
from ultralytics import YOLO


class DirectBoardDetector:
    """Ejecuta ``board.pt`` directamente sobre una imagen o frame."""

    def __init__(self, model_path: str | Path | None = None, image_size: int = 640):
        if model_path is None:
            model_path = Path(__file__).resolve().parent / "models" / "board.pt"

        self.model = YOLO(str(model_path))
        self.image_size = image_size

    def detect(self, frame: Any) -> list[dict[str, Any]]:
        """Devuelve todas las detecciones generadas por YOLO para ``frame``.

        ``conf=0.0`` evita descartar detecciones por confianza en este módulo.
        No se aplican filtros por clase, cantidad, posición, solapamiento o
        forma del tablero.
        """
        result = self.model.predict(
            source=frame,
            imgsz=self.image_size,
            conf=0.0,
            iou=1.0,
            max_det=30000,
            verbose=False,
        )[0]

        boxes = result.boxes
        detections = []
        names = self.model.names
        for box, confidence, class_id in zip(
            boxes.xyxy.cpu().tolist(),
            boxes.conf.cpu().tolist(),
            boxes.cls.cpu().tolist(),
        ):
            class_id = int(class_id)
            class_name = names[class_id] if isinstance(names, list) else names.get(class_id, str(class_id))
            detections.append(
                {
                    "box": box,
                    "confidence": float(confidence),
                    "class_id": class_id,
                    "class_name": class_name,
                }
            )
        return detections

    def annotate(
        self,
        frame: Any,
        detections: list[dict[str, Any]] | None = None,
        min_confidence: float = 0.25,
    ) -> Any:
        """Dibuja las detecciones visibles sobre ``frame``.

        El umbral solo afecta el dibujo. ``detect()`` sigue devolviendo todas
        las detecciones producidas por YOLO.
        """
        if detections is None:
            detections = self.detect(frame)

        for detection in detections:
            if detection["confidence"] < min_confidence:
                continue
            x1, y1, x2, y2 = (round(value) for value in detection["box"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                f'{detection["class_name"]} {detection["confidence"]:.3f}',
                (x1, max(20, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (0, 255, 0),
                2,
            )
        return frame

    def run(
        self,
        frame: Any,
        draw: bool = False,
        draw_min_confidence: float = 0.25,
    ) -> list[dict[str, Any]]:
        """Detecta el tablero; opcionalmente dibuja las cajas sobre ``frame``."""
        detections = self.detect(frame)
        if draw:
            self.annotate(frame, detections, min_confidence=draw_min_confidence)
        return detections

    def run_camera(self, camera_index: int = 0) -> None:
        """Muestra la cámara y recuadra cada detección de YOLO.

        Se cierra presionando ``q``.
        """
        camera = cv2.VideoCapture(camera_index)
        if not camera.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara {camera_index}")

        try:
            while True:
                ok, frame = camera.read()
                if not ok:
                    break

                detections = self.run(frame, draw=True, draw_min_confidence=0.25)
                visible_detections = sum(
                    detection["confidence"] >= 0.25 for detection in detections
                )
                cv2.putText(
                    frame,
                    f"Detecciones: {visible_detections} | Q: salir",
                    (15, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    (0, 255, 0),
                    2,
                )
                cv2.imshow("Deteccion directa del tablero", frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
        finally:
            camera.release()
            cv2.destroyAllWindows()


if __name__ == "__main__":
    detector = DirectBoardDetector()
    detector.run_camera()
