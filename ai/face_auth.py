"""
Bharat Votex — Face Authentication Module
Uses face_recognition library (dlib-based) for voter identity verification.
"""

import os
import pickle
import numpy as np
from PIL import Image
import io

ENCODINGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "voter_faces")
os.makedirs(ENCODINGS_DIR, exist_ok=True)

TOLERANCE = 0.55


def _load_image_array(frame_bytes: bytes):
    try:
        pil_img = Image.open(io.BytesIO(frame_bytes))
        pil_img = pil_img.convert("RGB")
        rgb = np.array(pil_img, dtype=np.uint8)
        print(f"[face_auth] Image OK — shape: {rgb.shape}, dtype: {rgb.dtype}")
        return rgb
    except Exception as e:
        print(f"[face_auth] PIL failed: {e}")

    try:
        import cv2
        nparr = np.frombuffer(frame_bytes, np.uint8)
        bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if bgr is not None:
            rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.uint8)
            print(f"[face_auth] OpenCV fallback OK — shape: {rgb.shape}")
            return rgb
    except Exception as e2:
        print(f"[face_auth] OpenCV fallback failed: {e2}")

    return None


def _preprocess_image(rgb: np.ndarray) -> np.ndarray:
    import cv2
    h, w = rgb.shape[:2]

    if w < 300:
        scale = 300 / w
        rgb = cv2.resize(rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_LINEAR)

    if w > 1280:
        scale = 1280 / w
        rgb = cv2.resize(rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    try:
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        bgr = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    except Exception as e:
        print(f"[face_auth] CLAHE skipped: {e}")

    # ✅ KEY FIX — ensure uint8 contiguous array for dlib/face_recognition
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
    return rgb


def _encoding_path(voter_id: str) -> str:
    return os.path.join(ENCODINGS_DIR, f"{voter_id}.pkl")


def register_face(voter_id: str, frame_bytes: bytes):
    try:
        import face_recognition
    except ImportError:
        return False, "face_recognition not installed."

    rgb = _load_image_array(frame_bytes)
    if rgb is None:
        return False, "Could not decode image. Please try again."

    rgb = _preprocess_image(rgb)
    # ✅ Extra safety before passing to dlib
    rgb = np.ascontiguousarray(rgb, dtype=np.uint8)

    print(f"[face_auth] Before face_locations — shape: {rgb.shape}, dtype: {rgb.dtype}, contiguous: {rgb.flags['C_CONTIGUOUS']}")

    face_locations = face_recognition.face_locations(rgb, model="hog", number_of_times_to_upsample=2)
    print(f"[face_auth] Register — faces found: {len(face_locations)}")

    if len(face_locations) == 0:
        face_locations = face_recognition.face_locations(rgb, model="hog", number_of_times_to_upsample=3)
        print(f"[face_auth] Register retry — faces found: {len(face_locations)}")

    if len(face_locations) == 0:
        return False, "No face detected. Please ensure good lighting and face centered in oval."

    if len(face_locations) > 1:
        return False, "Multiple faces detected. Only one person should be in frame."

    encodings = face_recognition.face_encodings(rgb, face_locations)
    if not encodings:
        return False, "Could not extract face features. Try again with better lighting."

    with open(_encoding_path(voter_id), "wb") as f:
        pickle.dump(encodings[0], f)

    print(f"[face_auth] Registered voter: {voter_id}")
    return True, "Face registered successfully."


def verify_face(voter_id: str, frame_bytes: bytes):
    enc_path = _encoding_path(voter_id)
    if not os.path.exists(enc_path):
        return False, 0.0, "No face registered for this voter ID. Please contact admin."

    try:
        import face_recognition
    except ImportError:
        return True, 0.85, "Demo mode: bypassing face check."

    rgb = _load_image_array(frame_bytes)
    if rgb is None:
        return False, 0.0, "Could not decode image. Please try again."

    rgb = _preprocess_image(rgb)
    # ✅ Extra safety before passing to dlib
    rgb = np.ascontiguousarray(rgb, dtype=np.uint8)

    face_locations = face_recognition.face_locations(rgb, model="hog", number_of_times_to_upsample=2)
    print(f"[face_auth] Verify — faces found: {len(face_locations)}")

    if len(face_locations) == 0:
        face_locations = face_recognition.face_locations(rgb, model="hog", number_of_times_to_upsample=3)

    if len(face_locations) == 0:
        return False, 0.0, "No face detected. Please look directly at the camera."

    live_encodings = face_recognition.face_encodings(rgb, face_locations)
    if not live_encodings:
        return False, 0.0, "Could not process face. Please try again."

    with open(enc_path, "rb") as f:
        stored_encoding = pickle.load(f)

    distance = face_recognition.face_distance([stored_encoding], live_encodings[0])[0]
    confidence = round(float(1.0 - distance), 3)
    match = bool(distance <= TOLERANCE)

    print(f"[face_auth] distance={distance:.3f}, confidence={confidence:.3f}, match={match}")

    if match:
        return True, confidence, "Identity verified successfully."
    else:
        return False, confidence, f"Face does not match. Confidence: {confidence:.0%}. Try again in better lighting."