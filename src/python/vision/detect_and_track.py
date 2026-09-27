import cv2
import numpy as np

CAMERA_ID = 0
BOARD_SIZE = 800
VIEW_MARGIN = 120
VIEW_SIZE = BOARD_SIZE + VIEW_MARGIN * 2
MIN_LINE_LENGTH = 180
MAX_FAILURES = 20
MIN_TRACK_POINTS = 20
MAX_TRACK_ERROR = 35
DEBUG = False
REDETECT_INTERVAL = 3
REDETECT_DISTANCE = 120
MIN_GRID_SCORE = 2
REDETECT_SCORE_MARGIN = 0.35
GRID_TRACK_POINTS = 120

def order_points(p):
    p = np.asarray(p, dtype=np.float32)
    r = np.zeros((4, 2), dtype=np.float32)
    s = p.sum(axis=1)
    d = np.diff(p, axis=1).reshape(-1)
    r[0] = p[np.argmin(s)]
    r[1] = p[np.argmin(d)]
    r[2] = p[np.argmax(s)]
    r[3] = p[np.argmax(d)]
    return r

def corner_distance(a, b):
    return float(np.mean(np.linalg.norm(a - b, axis=1)))

def validate_current_board(frame, corners):
    if corners is None:
        return False, -999
    score = grid_intersection_score(frame, corners)

    return score >= MIN_GRID_SCORE, score

def line_intersection(a, b):
    x1, y1, x2, y2 = a
    x3, y3, x4, y4 = b
    den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(den) < 1e-6: return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / den
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / den
    return np.array([px, py], dtype=np.float32)

def detect_side_lines(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(gray, 25, 110)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    lines = cv2.HoughLinesP(edges,1,np.pi / 720,threshold=35,minLineLength=MIN_LINE_LENGTH,maxLineGap=35)
    if lines is None: return None
    h, w = gray.shape
    horizontal = []
    vertical = []
    for line in lines:
        x1, y1, x2, y2 = map(float,line)
        length = np.hypot(x2 - x1,y2 - y1)
        if length < MIN_LINE_LENGTH: continue
        angle = np.degrees(np.arctan2(y2 - y1,x2 - x1))
        while angle <= -90: angle += 180
        while angle > 90: angle -= 180
        cx = (x1 + x2) / 2
        cy = (y1 + y2) / 2
        if abs(angle) < 8:
            if 0.08 * h < cy < 0.94 * h: horizontal.append({"line": (x1, y1, x2, y2),"length": length,"cx": cx,"cy": cy,"angle": angle})
        elif abs(angle) > 82:
            if 0.04 * w < cx < 0.90 * w: vertical.append({"line": (x1, y1, x2, y2),"length": length,"cx": cx,"cy": cy,"angle": angle})
    if not horizontal or not vertical: return None
    def score_top(x):
        y = x["cy"]
        position = abs(y - 0.15 * h)
        return x["length"] - position * 2.0
    def score_bottom(x):
        y = x["cy"]
        position = abs(y - 0.86 * h)
        return x["length"] - position * 1.5
    def score_left(x):
        x_pos = x["cx"]
        position = abs(x_pos - 0.10 * w)
        return x["length"] - position * 2.0
    def score_right(x):
        x_pos = x["cx"]
        position = abs(x_pos - 0.75 * w)
        return x["length"] - position * 1.5
    top_candidates = [x for x in horizontal if 0.08 * h < x["cy"] < 0.30 * h]
    bottom_candidates = [x for x in horizontal if 0.68 * h < x["cy"] < 0.96 * h]
    left_candidates = [x for x in vertical if 0.04 * w < x["cx"] < 0.25 * w]
    right_candidates = [x for x in vertical if 0.65 * w < x["cx"] < 0.90 * w]
    if not top_candidates or not bottom_candidates or not left_candidates or not right_candidates: return None
    top = max(top_candidates,key=score_top)
    bottom = max(bottom_candidates,key=score_bottom)
    left = max(left_candidates,key=score_left)
    right = max(right_candidates,key=score_right)
    return top["line"],right["line"],bottom["line"],left["line"]

def get_line_data(frame):
    gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray,(5, 5),0)
    edges = cv2.Canny(gray,25,110)
    lines = cv2.HoughLinesP(edges,1,np.pi / 720,threshold=35,minLineLength=120,maxLineGap=35)
    if lines is None:return [], []
    h, w = gray.shape
    horizontal = []
    vertical = []
    for l in lines:
        x1, y1, x2, y2 = map(float,l)
        length = np.hypot(x2 - x1,y2 - y1)
        angle = np.degrees(np.arctan2(y2 - y1,x2 - x1))
        while angle <= -90:angle += 180
        while angle > 90:angle -= 180
        cx = (x1 + x2) * 0.5
        cy = (y1 + y2) * 0.5
        if abs(angle) < 18:
            horizontal.append({"line": (x1, y1, x2, y2),"length": length,"cx": cx,"cy": cy,"angle": angle})
        elif abs(angle) > 68:
            vertical.append({"line": (x1, y1, x2, y2),"length": length,"cx": cx,"cy": cy,"angle": angle})
    return horizontal, vertical

def get_candidate_lines(lines, side, frame_shape):
    h, w = frame_shape[:2]
    candidates = []
    for x in lines:
        if side == "top":
            if x["cy"] > h * 0.32:continue
        elif side == "bottom":
            if x["cy"] < h * 0.60:continue
        elif side == "left":
            if x["cx"] > w * 0.30:continue
        elif side == "right":
            if x["cx"] < w * 0.60:continue
        candidates.append(x)
    candidates.sort(key=lambda x: x["length"],reverse=True)
    result = []
    for candidate in candidates:
        duplicate = False
        for previous in result:
            if side in ("top", "bottom"): distance = abs(candidate["cy"] - previous["cy"])
            else: distance = abs(candidate["cx"] -previous["cx"])
            if distance < 8:
                duplicate = True
                break
        if not duplicate:result.append(candidate)
        if len(result) >= 6: break
    return result

def quad_from_lines(top,right,bottom,left):
    tl = line_intersection(top["line"],left["line"])
    tr = line_intersection(top["line"],right["line"])
    br = line_intersection(bottom["line"],right["line"])
    bl = line_intersection(bottom["line"],left["line"])
    if any(p is None for p in [tl, tr, br, bl]):return None
    quad = order_points(np.float32([tl, tr, br, bl]))
    return quad

def quad_valid(corners, frame_shape):
    if corners is None:
        return False
    h, w = frame_shape[:2]
    area = abs(cv2.contourArea(corners))
    if area < w * h * 0.15:
        return False
    if not cv2.isContourConvex(corners):
        return False
    tl, tr, br, bl = corners
    top = np.linalg.norm(tr - tl)
    bottom = np.linalg.norm(br - bl)
    left = np.linalg.norm(bl - tl)
    right = np.linalg.norm(br - tr)
    if min(top, bottom, left, right) < 100:
        return False
    if top / bottom < 0.55:
        return False
    if top / bottom > 1.80:
        return False
    if left / right < 0.55:
        return False
    if left / right > 1.80:
        return False
    if np.any(corners[:, 0] < -30):
        return False
    if np.any(corners[:, 0] > w + 30):
        return False
    if np.any(corners[:, 1] < -30):
        return False
    if np.any(corners[:, 1] > h + 30):
        return False
    return True

def grid_intersection_score(frame, corners):
    SIZE = 400
    dst = np.float32([[0, 0], [SIZE - 1, 0], [SIZE - 1, SIZE - 1], [0, SIZE - 1]])
    H = cv2.getPerspectiveTransform(corners.astype(np.float32), dst)
    board = cv2.warpPerspective(frame, H, (SIZE, SIZE))
    gray = cv2.cvtColor(board, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    gx = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
    gy = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))
    vertical = np.percentile(gx, 70, axis=0)
    horizontal = np.percentile(gy, 70, axis=1)
    vertical = cv2.GaussianBlur(vertical.reshape(1, -1), (1, 11), 0).reshape(-1)
    horizontal = cv2.GaussianBlur(horizontal.reshape(-1, 1), (11, 1), 0).reshape(-1)
    def periodic_score(profile):
        n = len(profile)
        expected = np.linspace(0, n - 1, 9)
        values = []
        for p in expected:
            radius = int(n * 0.035)
            a = max(0, int(p) - radius)
            b = min(n, int(p) + radius + 1)
            if b <= a:
                continue
            values.append(np.max(profile[a:b]))
        if len(values) != 9:
            return 0
        values = np.asarray(values)
        background = np.median(profile)
        strength = np.mean(values) - background
        spread = np.std(profile) + 1
        return strength / spread
    sx = periodic_score(vertical)
    sy = periodic_score(horizontal)
    score = sx + sy
    return score

def detect_playing_area(frame):
    horizontal, vertical = get_line_data(frame)
    if not horizontal or not vertical:
        return None
    top_lines = get_candidate_lines(horizontal, "top", frame.shape)
    bottom_lines = get_candidate_lines(horizontal, "bottom", frame.shape)
    left_lines = get_candidate_lines(vertical, "left", frame.shape)
    right_lines = get_candidate_lines(vertical, "right", frame.shape)
    if not all([top_lines, bottom_lines, left_lines, right_lines]):
        return None
    best_quad = None
    best_score = -999
    for top in top_lines:
        for bottom in bottom_lines:
            if bottom["cy"] - top["cy"] < frame.shape[0] * 0.40:
                continue
            for left in left_lines:
                for right in right_lines:
                    if right["cx"] - left["cx"] < frame.shape[1] * 0.40:
                        continue
                    corners = quad_from_lines(top, right, bottom, left)
                    if not quad_valid(corners, frame.shape):
                        continue
                    score = grid_intersection_score(frame, corners)
                    center = np.mean(corners, axis=0)
                    image_center = np.array([frame.shape[1] / 2, frame.shape[0] / 2])
                    center_distance = np.linalg.norm(center - image_center)
                    score -= (center_distance / max(frame.shape[:2])) * 0.5
                    if score > best_score:
                        best_score = score
                        best_quad = corners
    if best_quad is None or best_score < MIN_GRID_SCORE:
        return None
    return best_quad
def grid_geometry_score(frame, corners):
    size = 400
    board, _ = warp_from_corners(frame, corners, size)
    gray = cv2.cvtColor(board, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    gx = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3))
    gy = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3))
    px = np.percentile(gx, 75, axis=0)
    py = np.percentile(gy, 75, axis=1)
    def score(profile):
        peaks = []
        threshold = np.percentile(profile, 65)
        for i in range(5, len(profile) - 5):
            if profile[i] >= threshold and profile[i] == np.max(profile[i-5:i+6]):
                peaks.append(i)
        if len(peaks) < 9:
            return -999
        best = -999
        expected = len(profile) / 8
        for start in peaks:
            positions = [start]
            for n in range(1, 9):
                target = start + n * expected
                candidates = [p for p in peaks if abs(p - target) < expected * 0.20]
                if not candidates:
                    break
                positions.append(min(candidates, key=lambda p: abs(p - target)))
            if len(positions) != 9:
                continue
            distances = np.diff(positions)
            regularity = np.std(distances) / np.mean(distances)
            if regularity < 0.12:
                best = max(best, 1.0 - regularity)
        return best
    sx = score(px)
    sy = score(py)
    if sx < 0 or sy < 0:
        return -999
    return sx + sy

def redetect_near_board(frame, current_corners):
    horizontal, vertical = get_line_data(frame)
    if not horizontal or not vertical:
        return None, -999
    def local(lines, side, a, b):
        expected_angle = np.degrees(np.arctan2(b[1] - a[1], b[0] - a[0]))
        result = []
        for candidate in get_candidate_lines(lines, side, frame.shape):
            midpoint = np.array([candidate["cx"], candidate["cy"]], dtype=np.float32)
            direction = b - a
            offset = midpoint - a
            distance = abs(direction[0] * offset[1] - direction[1] * offset[0]) / max(np.linalg.norm(direction), 1)
            angle = abs(candidate["angle"] - expected_angle) % 180
            angle = min(angle, 180 - angle)
            if distance <= REDETECT_DISTANCE and angle <= 18:
                result.append(candidate)
        result.sort(key=lambda x: x["length"], reverse=True)
        return result[:4]

    tl, tr, br, bl = current_corners
    top_lines = local(horizontal, "top", tl, tr)
    bottom_lines = local(horizontal, "bottom", bl, br)
    left_lines = local(vertical, "left", tl, bl)
    right_lines = local(vertical, "right", tr, br)
    if not all([top_lines, bottom_lines, left_lines, right_lines]):
        return None, -999
    best_quad = None
    best_score = -999999
    best_grid_score = -999
    for top in top_lines:
        for bottom in bottom_lines:
            if bottom["cy"] - top["cy"] < frame.shape[0] * 0.40:
                continue
            for left in left_lines:
                for right in right_lines:
                    if right["cx"] - left["cx"] < frame.shape[1] * 0.40:
                        continue
                    quad = quad_from_lines(top, right, bottom, left)
                    if not quad_valid(quad, frame.shape):
                        continue
                    distance = corner_distance(quad, current_corners)
                    if distance > REDETECT_DISTANCE:
                        continue
                    score = grid_intersection_score(frame, quad)
                    if score < MIN_GRID_SCORE:
                        continue
                    ranked_score = score - distance * 0.015
                    if ranked_score > best_score:
                        best_score = ranked_score
                        best_grid_score = score
                        best_quad = quad
    if best_quad is None:
        return None, -999
    return best_quad, best_grid_score

def warp_from_corners(frame, corners, size=BOARD_SIZE):
    dst = np.float32([[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]])
    H = cv2.getPerspectiveTransform(corners.astype(np.float32), dst)
    warped = cv2.warpPerspective(frame, H, (size, size))
    return warped, H

def create_tracking_points(gray, corners):
    board, H = warp_from_corners(gray, corners, BOARD_SIZE)
    points = []
    cell = BOARD_SIZE / 8
    for row in range(9):
        for col in range(9):
            x = col * cell
            y = row * cell
            for ox, oy in [(-8, 0), (8, 0), (0, -8), (0, 8)]:
                px = x + ox
                py = y + oy
                if 0 <= px < BOARD_SIZE and 0 <= py < BOARD_SIZE:
                    points.append([px, py])
    points = np.float32(points).reshape(-1, 1, 2)
    H_inv = np.linalg.inv(H)
    return cv2.perspectiveTransform(points, H_inv).astype(np.float32)

def track_board(previous_gray, current_gray, previous_points, corners):
    if previous_points is None or len(previous_points) < MIN_TRACK_POINTS:
        return None, None, None
    current_points, status, error = cv2.calcOpticalFlowPyrLK(previous_gray, current_gray, previous_points, None, winSize=(31, 31), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 25, 0.01))
    if current_points is None:
        return None, None, None
    old = previous_points.reshape(-1, 2)
    new = current_points.reshape(-1, 2)
    status = status.reshape(-1)
    error = error.reshape(-1)
    valid = (status == 1) & (error < MAX_TRACK_ERROR)
    old = old[valid]
    new = new[valid]
    if len(new) < MIN_TRACK_POINTS:
        return None, None, None
    backward, status_back, error_back = cv2.calcOpticalFlowPyrLK(current_gray, previous_gray, new.reshape(-1, 1, 2), None, winSize=(31, 31), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 25, 0.01))
    if backward is None:
        return None, None, None
    backward = backward.reshape(-1, 2)
    status_back = status_back.reshape(-1)
    error_back = error_back.reshape(-1)
    fb_error = np.linalg.norm(old - backward, axis=1)
    valid = (status_back == 1) & (error_back < MAX_TRACK_ERROR) & (fb_error < 2.0)
    old = old[valid]
    new = new[valid]
    if len(new) < MIN_TRACK_POINTS:
        return None, None, None
    H, mask = cv2.findHomography(old, new, cv2.RANSAC, 3.0)
    if H is None or mask is None:
        return None, None, None
    mask = mask.reshape(-1).astype(bool)
    if np.sum(mask) < MIN_TRACK_POINTS:
        return None, None, None
    old_inliers = old[mask]
    new_inliers = new[mask]
    board_width = max(np.linalg.norm(corners[1] - corners[0]), np.linalg.norm(corners[2] - corners[3]))
    board_height = max(np.linalg.norm(corners[3] - corners[0]), np.linalg.norm(corners[2] - corners[1]))
    if np.ptp(old_inliers[:, 0]) < board_width * 0.30:
        return None, None, None
    if np.ptp(old_inliers[:, 1]) < board_height * 0.30:
        return None, None, None
    predicted = cv2.perspectiveTransform(old.reshape(-1, 1, 2), H).reshape(-1, 2)
    reprojection_error = np.linalg.norm(predicted - new, axis=1)
    good = reprojection_error < 4.0
    if np.sum(good) < MIN_TRACK_POINTS:
        return None, None, None
    new_corners = cv2.perspectiveTransform(corners.reshape(-1, 1, 2), H).reshape(4, 2)
    old_area = abs(cv2.contourArea(corners))
    new_area = abs(cv2.contourArea(new_corners))
    if old_area < 1:
        return None, None, None
    area_ratio = new_area / old_area
    if area_ratio < 0.80 or area_ratio > 1.25:
        return None, None, None
    movement = np.mean([np.linalg.norm(new_corners[i] - corners[i]) for i in range(4)])
    if movement > 100:
        return None, None, None
    return new_corners, new, H

def get_64_squares(corners):
    dst = np.float32([[0, 0], [BOARD_SIZE, 0], [BOARD_SIZE, BOARD_SIZE], [0, BOARD_SIZE]])
    H = cv2.getPerspectiveTransform(corners.astype(np.float32), dst)
    squares = []
    for row in range(8):
        for col in range(8):
            x1 = col * BOARD_SIZE / 8
            y1 = row * BOARD_SIZE / 8
            x2 = (col + 1) * BOARD_SIZE / 8
            y2 = (row + 1) * BOARD_SIZE / 8
            square = np.float32([[x1, y1], [x2, y1], [x2, y2], [x1, y2]])
            square = cv2.perspectiveTransform(square.reshape(-1, 1, 2), H).reshape(4, 2)
            squares.append(square)
    return squares

def create_board_view(frame, corners):
    destination = np.float32([
        [VIEW_MARGIN, VIEW_MARGIN],
        [VIEW_MARGIN + BOARD_SIZE, VIEW_MARGIN],
        [VIEW_MARGIN + BOARD_SIZE, VIEW_MARGIN + BOARD_SIZE],
        [VIEW_MARGIN, VIEW_MARGIN + BOARD_SIZE]
    ])
    H = cv2.getPerspectiveTransform(corners.astype(np.float32), destination)
    view = cv2.warpPerspective(frame, H, (VIEW_SIZE, VIEW_SIZE))
    for i in range(9):
        x = int(VIEW_MARGIN + i * BOARD_SIZE / 8)
        cv2.line(view, (x, VIEW_MARGIN), (x, VIEW_MARGIN + BOARD_SIZE), (0, 255, 0), 2)
    for i in range(9):
        y = int(VIEW_MARGIN + i * BOARD_SIZE / 8)
        cv2.line(view, (VIEW_MARGIN, y), (VIEW_MARGIN + BOARD_SIZE, y), (0, 255, 0), 2)
    return view

cap = cv2.VideoCapture(CAMERA_ID)
if not cap.isOpened():
    raise RuntimeError("No se pudo abrir la cámara")
playing_corners = None
predicted_corners = None
tracking_points = None
previous_gray = None
tracking = False
frame_count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_count += 1
    if not tracking:
        corners = detect_playing_area(frame)
        if corners is not None:
            points = create_tracking_points(gray, corners)
            if points is not None and len(points) >= MIN_TRACK_POINTS:
                playing_corners = corners
                predicted_corners = corners.copy()
                tracking_points = points
                previous_gray = gray.copy()
                tracking = True
    else:
        new_corners, _, H = track_board(previous_gray, gray, tracking_points, predicted_corners)
        if new_corners is not None:
            predicted_corners = new_corners
            tracking_points = cv2.perspectiveTransform(tracking_points, H).astype(np.float32)
        else:
            predicted_corners = playing_corners.copy()
            tracking_points = create_tracking_points(gray, playing_corners)
        if frame_count % REDETECT_INTERVAL == 0:
            current_valid, current_score = validate_current_board(frame, playing_corners)
            candidate, candidate_score = redetect_near_board(frame, playing_corners)
            if candidate is not None and (not current_valid or candidate_score > current_score + REDETECT_SCORE_MARGIN):
                playing_corners = candidate
                predicted_corners = candidate.copy()
                fresh_points = create_tracking_points(gray, playing_corners)
                if fresh_points is not None and len(fresh_points) >= MIN_TRACK_POINTS:
                    tracking_points = fresh_points
        previous_gray = gray.copy()
    if tracking and playing_corners is not None:
        cv2.polylines(frame, [playing_corners.astype(np.int32)], True, (0, 255, 0), 3)
        if DEBUG:
            for p in playing_corners:
                x, y = p.astype(int)
                cv2.circle(frame, (x, y), 6, (0, 0, 255), -1)
        view = create_board_view(frame, playing_corners)
        #cv2.imshow("64 casillas", view)
        cv2.putText(frame, "TABLERO DETECTADO", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "BUSCANDO TABLERO...", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    cv2.imshow("Camara",frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):break
cap.release()
cv2.destroyAllWindows()
