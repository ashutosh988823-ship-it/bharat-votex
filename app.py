"""
Bharat Votex — AI-Powered Biometric Voting System
Main Flask Application
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import base64
import json
import numpy as np
from datetime import datetime
from database.db import init_db, get_voter, mark_voted, cast_vote, get_results, add_voter
from ai.face_auth import register_face, verify_face
from ai.liveness import check_liveness

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Initialize DB on startup
init_db()


def decode_frame(frame_b64: str):
    """
    Safely decode a base64 image string to raw bytes.
    Handles both raw base64 and data URL formats.
    Returns bytes or None.
    """
    try:
        # Strip data URL prefix if present (e.g. "data:image/jpeg;base64,...")
        if "," in frame_b64:
            frame_b64 = frame_b64.split(",", 1)[1]

        # Fix padding
        frame_b64 += "=" * (-len(frame_b64) % 4)

        frame_bytes = base64.b64decode(frame_b64)

        # Validate it decodes to a real image
        import cv2
        nparr = np.frombuffer(frame_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            print("[ERROR] cv2.imdecode returned None — invalid image bytes")
            return None

        print(f"[DEBUG] Image decoded OK — shape: {img.shape}, dtype: {img.dtype}")
        return frame_bytes

    except Exception as e:
        print(f"[ERROR] decode_frame failed: {e}")
        return None


# ─────────────────────────────────────────────
# Pages
# ─────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/verify")
def verify():
    if "voter_id" not in session:
        return redirect(url_for("index"))
    return render_template("verify.html", voter_id=session["voter_id"])


@app.route("/vote")
def vote():
    if not session.get("authenticated"):
        return redirect(url_for("index"))
    return render_template("vote.html", voter_id=session["voter_id"])


@app.route("/results")
def results():
    return render_template("results.html")


@app.route("/admin")
def admin():
    return render_template("admin.html")


# ─────────────────────────────────────────────
# API Routes
# ─────────────────────────────────────────────

@app.route("/api/login", methods=["POST"])
def api_login():
    """Step 1: Voter enters their Voter ID."""
    data = request.get_json()
    voter_id = data.get("voter_id", "").strip().upper()

    voter = get_voter(voter_id)
    if not voter:
        return jsonify({"success": False, "message": "Voter ID not found. Please check your ID."}), 404

    if voter["has_voted"]:
        return jsonify({"success": False, "message": "You have already cast your vote. Thank you!"}), 403

    session["voter_id"] = voter_id
    session["authenticated"] = False
    return jsonify({"success": True, "name": voter["name"], "message": "Voter ID verified. Please complete biometric scan."})


@app.route("/api/biometric/verify", methods=["POST"])
def api_biometric_verify():
    """Step 2: Verify face + liveness."""
    if "voter_id" not in session:
        return jsonify({"success": False, "message": "Session expired. Please login again."}), 401

    data = request.get_json()
    frame_b64 = data.get("frame")
    if not frame_b64:
        return jsonify({"success": False, "message": "No image received."}), 400

    voter_id = session["voter_id"]

    frame_bytes = decode_frame(frame_b64)
    if frame_bytes is None:
        return jsonify({"success": False, "message": "Could not decode image. Please try again."}), 400

    # Liveness check first
    try:
        is_live, liveness_msg = check_liveness(frame_bytes)
        print(f"[DEBUG] Liveness: {is_live} — {liveness_msg}")
        if not is_live:
            return jsonify({"success": False, "message": f"Liveness check failed: {liveness_msg}"}), 400
    except Exception as e:
        print(f"[WARN] Liveness check exception (skipping): {e}")
        # Don't block voting if liveness crashes — just log it

    # Face recognition
    try:
        match, confidence, face_msg = verify_face(voter_id, frame_bytes)
        print(f"[DEBUG] Face match: {match}, confidence: {confidence}, msg: {face_msg}")
    except Exception as e:
        print(f"[ERROR] verify_face crashed: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": f"Face verification error: {str(e)}"}), 500

    if not match:
        return jsonify({"success": False, "message": f"Face not recognized: {face_msg}", "confidence": confidence}), 401

    session["authenticated"] = True
    return jsonify({
        "success": True,
        "message": "Identity verified! Welcome, voter.",
        "confidence": confidence
    })


@app.route("/api/vote/cast", methods=["POST"])
def api_cast_vote():
    """Step 3: Cast the vote."""
    if not session.get("authenticated"):
        return jsonify({"success": False, "message": "Not authenticated."}), 401

    voter_id = session["voter_id"]
    voter = get_voter(voter_id)

    if voter["has_voted"]:
        return jsonify({"success": False, "message": "Vote already cast."}), 403

    data = request.get_json()
    candidate = data.get("candidate")
    if not candidate:
        return jsonify({"success": False, "message": "No candidate selected."}), 400

    cast_vote(candidate)
    mark_voted(voter_id)
    session.clear()

    return jsonify({"success": True, "message": "Your vote has been recorded securely. Thank you!"})


@app.route("/api/results", methods=["GET"])
def api_results():
    """Get live vote results."""
    results = get_results()
    return jsonify({"success": True, "results": results})


@app.route("/api/admin/register", methods=["POST"])
def api_register_voter():
    """Admin: Register a new voter with face."""
    data = request.get_json()
    voter_id = data.get("voter_id", "").strip().upper()
    name = data.get("name", "").strip()
    frame_b64 = data.get("frame")

    if not all([voter_id, name, frame_b64]):
        return jsonify({"success": False, "message": "Missing required fields."}), 400

    frame_bytes = decode_frame(frame_b64)
    if frame_bytes is None:
        return jsonify({"success": False, "message": "Could not decode image. Please try again."}), 400

    # Register face encoding
    try:
        success, msg = register_face(voter_id, frame_bytes)
        print(f"[DEBUG] register_face: success={success}, msg={msg}")
    except Exception as e:
        print(f"[ERROR] register_face crashed: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"success": False, "message": f"Face registration error: {str(e)}"}), 500

    if not success:
        return jsonify({"success": False, "message": msg}), 400

    # Add to DB
    add_voter(voter_id, name)
    return jsonify({"success": True, "message": f"Voter {name} registered successfully."})


@app.route("/api/admin/voters", methods=["GET"])
def api_voters():
    """Admin: Get all voters."""
    from database.db import get_all_voters
    voters = get_all_voters()
    return jsonify({"success": True, "voters": voters})


if __name__ == "__main__":
    print("=" * 50)
    print("  Bharat Votex — Starting Server")
    print("  Visit: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)