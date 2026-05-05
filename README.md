# 🗳️ Bharat Votex
**AI-Powered Biometric Voting System**
*Final Year B.Tech Project — Artificial Intelligence & Machine Learning*

---

## 📌 Project Overview

Bharat Votex is a secure, AI-powered electronic voting system that uses **facial recognition** and **liveness detection** to authenticate voters via their laptop webcam — eliminating impersonation and duplicate voting.

### Key Features
- 🔍 **AI Face Recognition** — dlib-based 128-dimensional face encoding matching
- 👁️ **Liveness Detection** — MediaPipe Eye Aspect Ratio (EAR) to prevent photo spoofing
- 🔒 **One Vote Per Voter** — database flag + session management
- 🔐 **Vote Encryption** — SHA-256 hash per vote for audit trail
- 📊 **Live Results Dashboard** — real-time Chart.js bar chart
- 🛡️ **Admin Panel** — register voters with face capture

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Backend | Python 3.10+, Flask |
| AI/ML | face_recognition, OpenCV, MediaPipe |
| Database | SQLite (via Python sqlite3) |
| Charts | Chart.js (CDN) |

---

## 📁 Project Structure

```
bharat_votex/
├── app.py                     ← Flask entry point (all API routes)
├── requirements.txt           ← Python dependencies
├── README.md
│
├── templates/
│   ├── index.html             ← Login page (Voter ID entry)
│   ├── verify.html            ← Biometric scan (webcam)
│   ├── vote.html              ← Voting booth (candidate selection)
│   ├── results.html           ← Live results with bar chart
│   └── admin.html             ← Admin panel (voter registration)
│
├── static/
│   └── css/style.css          ← All UI styles
│
├── ai/
│   ├── face_auth.py           ← Face registration + verification
│   └── liveness.py            ← EAR-based liveness detection
│
├── database/
│   └── db.py                  ← SQLite models + queries
│
└── voter_faces/               ← Stored face encodings (.pkl files)
```

---

## 🚀 Setup & Run

### Step 1 — Prerequisites
- Python 3.10 or higher
- `cmake` installed (required by dlib for face_recognition)
  - Ubuntu/Debian: `sudo apt install cmake`
  - macOS: `brew install cmake`
  - Windows: Install from https://cmake.org/download/

### Step 2 — Install dependencies
```bash
cd bharat_votex
pip install -r requirements.txt
```

> ⚠️ `face_recognition` installs `dlib` which compiles C++ code. This may take 5–10 minutes.

### Step 3 — Run the server
```bash
python app.py
```

### Step 4 — Open in browser
```
http://127.0.0.1:5000
```

---

## 🎮 Demo Walkthrough

### Register a voter (Admin Panel)
1. Go to `http://127.0.0.1:5000/admin`
2. Enter Voter ID (e.g. `VTR001`) and Name
3. Click **Register Voter Face** — your face will be captured

### Cast a vote
1. Go to `http://127.0.0.1:5000`
2. Enter the Voter ID you registered
3. Complete the face scan on the verification page
4. Select a candidate and submit

### View live results
- Go to `http://127.0.0.1:5000/results`
- Auto-refreshes every 5 seconds

---

## 🧠 AI/ML Concepts Used

| Concept | Implementation |
|---------|---------------|
| Face Detection | HOG + SVM (dlib via face_recognition) |
| Face Encoding | Deep metric learning → 128-D vector |
| Face Matching | Euclidean distance (threshold = 0.5) |
| Liveness Detection | Eye Aspect Ratio via MediaPipe landmarks |
| Anti-spoofing | EAR range check to detect printed photos |

---

## 🔐 Security Features

- Each voter has a `has_voted` database flag — prevents double voting
- Votes stored as SHA-256 hashes — tamper-evident audit trail
- Face encoding stored as serialized numpy array — not raw photos
- Session management via Flask secret key
- Liveness detection prevents photo/video-based spoofing

---

## 📈 Possible Enhancements (for extra marks)

- [ ] OTP via email as second factor (`smtplib`)
- [ ] AES encryption for stored votes
- [ ] CNN model for spoof detection (trained on real vs printed faces)
- [ ] Blockchain-based vote storage
- [ ] Mobile-responsive UI improvements
- [ ] Voter turnout analytics dashboard

---

## 👨‍💻 Author

**Project:** Bharat Votex
**Degree:** B.Tech — Artificial Intelligence & Machine Learning
**Year:** Final Year (2025–26)
