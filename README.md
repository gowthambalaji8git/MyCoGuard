# MyCoGuard (MCG) — Mushroom Health & Safety Analyzer

Upload a photo of a mushroom, get an instant reference match, a **Healthy /
Unhealthy / Poisonous** safety status, and a downloadable PDF report — all
behind a username/password login.

Built with **Python (Flask)** on the backend, **HTML/CSS/JS** on the
frontend, and **SQLite** for storage. No external services or API keys
required — it runs entirely on your machine.

---

## 1. Setup

```bash
# 1. create and activate a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. (re)build the reference dataset — only needed once, or if you edit
#    build_dataset.py / the data/ folder
python build_dataset.py

# 4. run the app
python app.py
```

Open **http://127.0.0.1:5000** — you'll land on the login page. Click
**"Create an account"** to register, then log in and upload a mushroom photo.

## 2. Project structure

```
mycoguard/
├── app.py                 # Flask routes: auth, upload, analyze, reports
├── classifier.py           # Image analysis engine (see "How analysis works")
├── database.py             # SQLite helpers (users + saved reports)
├── report_generator.py     # Builds the downloadable PDF report
├── build_dataset.py         # One-time script: builds mushroom_info.json
├── mushroom_info.json       # Reference knowledge base (25 species)
├── reference_features.json  # Cached image "fingerprints" for matching
├── requirements.txt
├── data/                    # Your original labelled photo set (kept for reference)
├── static/
│   ├── css/style.css        # Mushroom-themed design system
│   ├── js/main.js           # Upload dropzone + preview
│   └── img/
│       ├── logo.png         # Your MCG logo
│       ├── dataset/         # Cleaned copies of the reference photos
│       └── uploads/         # User-uploaded photos land here
├── templates/               # login, register, forgot/reset password,
│                             # dashboard, result, history
├── reports/                 # Generated PDF reports land here
└── instance/mycoguard.db    # SQLite database (created on first run)
```

## 3. How the analysis works (today)

`classifier.py` extracts a lightweight colour + texture "fingerprint" (an
HSV colour histogram plus a coarse edge-energy signal) from the uploaded
photo, then compares it — via cosine similarity — against pre-computed
fingerprints for all 25 reference species bundled in `data/Mushroom Data`.
The closest match's category (**Healthy/Edible**, **Unhealthy/Inedible**, or
**Poisonous**) becomes the report's status, with a confidence score and the
next-closest candidates shown for transparency.

This keeps the app dependency-light (`numpy` + `Pillow`, no GPU, no model
download) so it runs anywhere immediately. It is a solid MVP baseline, but
it is **not a trained neural network** and should not be treated as a
certified identification tool — see the safety notice in every report.

## 4. Login & security notes

- Passwords are hashed with Werkzeug's `generate_password_hash` (never
  stored in plain text).
- "Forgot password" is a 2-step, security-question based flow (no email
  server required for this demo) — see `SECURITY_QUESTIONS` in `app.py`.
- Sessions use Flask's signed cookies; set a real `MCG_SECRET_KEY`
  environment variable before deploying anywhere beyond localhost.

## 5. Future improvements (roadmap)

Ideas to grow this from an MVP into a production app, roughly in order of
impact:

1. **Real deep-learning classifier** — swap `classifier.py`'s histogram
   matcher for a fine-tuned CNN (MobileNetV3/EfficientNet via TensorFlow or
   PyTorch) trained on a much larger labelled mushroom dataset, for real
   species-level accuracy. Every other file only calls `analyze_image()`,
   so this is a drop-in swap.
2. **GPS + season context** — use location and time of year to narrow
   candidate species (many look-alikes don't overlap in range/season).
3. **Multi-photo scans** — let users upload cap, gills *and* stem/spore
   print photos for a single, more confident report.
4. **Email-based password reset** with a real SMTP/transactional-email
   provider and expiring reset tokens, plus optional 2FA.
5. **Community verification** — let experienced users / mycologists review
   and confirm uncertain scans.
6. **Offline mobile app** — wrap the classifier in a small on-device model
   (TensorFlow Lite / Core ML) for use in the field with no signal.
7. **Shareable report links** and team/family accounts for foraging groups.
8. **Admin dashboard** to expand the reference species library over time.

## 6. Safety disclaimer

MyCoGuard is a reference and educational tool. It does **not** replace
identification by a qualified mycologist or poison control authority. Never
eat a wild mushroom based on this app's output. If poisoning is suspected,
contact emergency medical services or a poison center immediately.
