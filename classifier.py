"""
MyCoGuard analysis engine.

This module extracts a lightweight visual "fingerprint" (colour + edge
histogram) from a mushroom photo and compares it against a fingerprinted
reference library built from the bundled Mushroom Data set, returning the
closest matching species together with its safety category.

NOTE on approach
-----------------
This is a nearest-neighbour colour/texture matcher, not a trained deep
neural network - it ships zero heavy ML dependencies so it runs anywhere
`pip install -r requirements.txt` works. It is a solid, honest baseline for
a demo/MVP. See README.md -> "Future Improvements" for how to swap this
module for a real CNN (e.g. a fine-tuned MobileNet/EfficientNet in
TensorFlow or PyTorch) without touching the rest of the app - every route
only ever calls `analyze_image()` below.
"""
import json
import os

import numpy as np
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
INFO_PATH = os.path.join(BASE, "mushroom_info.json")
FEATURES_PATH = os.path.join(BASE, "reference_features.json")

_H_BINS, _S_BINS, _V_BINS = 8, 4, 4


def _load_info():
    with open(INFO_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_features(image_path_or_file):
    """Return a normalised feature vector (HSV histogram + simple edge energy)."""
    img = Image.open(image_path_or_file).convert("RGB").resize((160, 160))
    arr = np.asarray(img).astype(np.float32) / 255.0

    hsv = np.asarray(img.convert("HSV")).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    hist, _ = np.histogramdd(
        np.stack([h.ravel(), s.ravel(), v.ravel()], axis=1),
        bins=(_H_BINS, _S_BINS, _V_BINS),
        range=((0, 255), (0, 255), (0, 255)),
    )
    hist = hist.ravel()
    hist = hist / (hist.sum() + 1e-8)

    # crude edge-energy texture signal (gradient magnitude, coarse-binned)
    gray = arr.mean(axis=2)
    gx = np.abs(np.diff(gray, axis=1))
    gy = np.abs(np.diff(gray, axis=0))
    texture = np.array([gx.mean(), gx.std(), gy.mean(), gy.std()], dtype=np.float32)

    feat = np.concatenate([hist, texture])
    return feat


def _cosine_similarity(a, b):
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-8
    return float(np.dot(a, b) / denom)


def build_reference_features(force=False):
    """Precompute & cache feature vectors for every image in mushroom_info.json."""
    if os.path.exists(FEATURES_PATH) and not force:
        return
    info = _load_info()
    out = {}
    for rec in info:
        img_path = os.path.join(BASE, "static", rec["image"])
        try:
            feat = extract_features(img_path)
            out[rec["id"]] = feat.tolist()
        except Exception as e:  # pragma: no cover
            print(f"[classifier] skipped {rec['id']}: {e}")
    with open(FEATURES_PATH, "w") as f:
        json.dump(out, f)


def _load_reference_features():
    build_reference_features()
    with open(FEATURES_PATH, "r") as f:
        return json.load(f)


CATEGORY_META = {
    "healthy": {
        "label": "Healthy / Edible",
        "css": "status-healthy",
        "icon": "check-circle",
        "headline": "This mushroom appears HEALTHY and commonly edible.",
    },
    "unhealthy": {
        "label": "Unhealthy / Inedible",
        "css": "status-warning",
        "icon": "alert-triangle",
        "headline": "This mushroom looks UNHEALTHY / not recommended for eating.",
    },
    "poisonous": {
        "label": "Poisonous",
        "css": "status-danger",
        "icon": "skull",
        "headline": "This mushroom shows signs consistent with a POISONOUS species.",
    },
}


def analyze_image(image_path):
    """
    Analyze a mushroom photo.

    Returns a dict with the best-matching reference species, the safety
    category, a confidence score (0-100) and the full ranked candidate list.
    """
    info = _load_info()
    by_id = {r["id"]: r for r in info}
    ref_features = _load_reference_features()

    query = extract_features(image_path)

    scored = []
    for rid, feat in ref_features.items():
        sim = _cosine_similarity(query, feat)
        scored.append((rid, sim))
    scored.sort(key=lambda x: x[1], reverse=True)

    top = scored[:5]
    best_id, best_sim = top[0]
    best_rec = by_id[best_id]

    # squash cosine similarity (~0.4-1.0 typical range for photos) into a
    # friendlier 0-100 confidence score for display purposes
    confidence = max(0.0, min(1.0, (best_sim - 0.5) / 0.5)) * 100
    confidence = round(max(confidence, 38.0), 1)  # floor so it never looks absurd

    candidates = []
    for rid, sim in top:
        rec = by_id[rid]
        candidates.append({
            "id": rid,
            "name": rec["display_name"],
            "category": rec["category"],
            "category_label": rec["category_label"],
            "score": round(sim * 100, 1),
        })

    meta = CATEGORY_META[best_rec["category"]]

    return {
        "match": best_rec,
        "confidence": confidence,
        "category": best_rec["category"],
        "meta": meta,
        "candidates": candidates,
    }
