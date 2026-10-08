"""Week 4 baselines for HIT-UAV vehicle detection (hituav-vehicle-v0.2).

Information boundary for every method: the single grayscale IR frame only
(no altitude / angle / date / filename features).
"""
import json
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

VEH = {1, 3}          # Car, OtherVehicle -> vehicle  (W3 vehicle_map_v0.2)
DONTCARE = 4          # ignore region at evaluation
TEST_DATES = ["20210121", "20210123"]
VAL_DATES = ["20210119"]
RAW_URL = "https://raw.githubusercontent.com/suojiashun/HIT-UAV-Infrared-Thermal-Dataset/main/normal_json/"


def load_dataset(data_dir):
    data_dir = Path(data_dir)
    im, an = [], []
    for s in ["train", "val", "test"]:
        j = json.load(open(data_dir / "normal_json" / f"{s}.json", encoding="utf-8"))
        for i in j["images"]:
            i["official_split"] = s
        im += j["images"]; an += j["annotation"]
    im = pd.DataFrame(im); an = pd.DataFrame(an)
    p = im.filename.str.replace(".jpg", "", regex=False).str.split("_", expand=True)
    im["daynight"] = p[0].astype(int).map({0: "day", 1: "night"})
    im["altitude_m"] = p[1].astype(int); im["angle_deg"] = p[2].astype(int)
    im["flight_group"] = im.date_captured + "_" + im.daynight + "_" + im.altitude_m.astype(str) + "_" + im.angle_deg.astype(str)
    im["split"] = np.where(im.date_captured.isin(TEST_DATES), "test", np.where(im.date_captured.isin(VAL_DATES), "val", "train"))
    an[["x", "y", "w", "h"]] = pd.DataFrame(an.bbox.tolist(), index=an.index)
    return im, an


def ensure_images(im, data_dir):
    """Download the HIT-UAV frames that are missing locally (images are not committed to git)."""
    import urllib.request
    img_dir = Path(data_dir) / "images"; img_dir.mkdir(parents=True, exist_ok=True)
    missing = [r for r in im.itertuples() if not (img_dir / r.filename).exists()]
    for r in missing:
        urllib.request.urlretrieve(RAW_URL + f"{r.official_split}/{r.filename}", img_dir / r.filename)
    return len(missing)


# ------------------------------------------------------------------ classical detectors

_K3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))


def _boxes_from_mask(mask, score_map, size_rule, polarity):
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    out = []
    for k in range(1, n):
        x, y, w, h, area = stats[k]
        if not size_rule(w, h):
            continue
        blob = lab[y:y + h, x:x + w] == k
        out.append(dict(x=int(x), y=int(y), w=int(w), h=int(h), score=float(score_map[y:y + h, x:x + w][blob].mean()),
                        polarity=polarity, fill=float(area) / (w * h)))
    return out


def otsu_cca(gray, size_rule):
    """Baseline 1 (W2 current baseline): global Otsu on raw intensity, hot (bright) pixels = target, CCA."""
    _, m = cv2.threshold(gray, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, _K3)
    z = (gray.astype(np.float32) - gray.mean()) / (gray.std() + 1e-6)   # score = brightness above frame mean
    return _boxes_from_mask(m, z, size_rule, +1)


def local_contrast_proposals(gray, size_rule, k=2.0, bg_ksize=41, close=3):
    """Proposal stage of Baseline 2: |I - local background| in both polarities (hot or cold objects)."""
    g = gray.astype(np.float32)
    bg = cv2.blur(g, (bg_ksize, bg_ksize))
    d = g - bg
    s = d.std() + 1e-6
    out = []
    for pol in (+1, -1):
        m = (pol * d > k * s).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, _K3)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close)))
        out += _boxes_from_mask(m, pol * d / s, size_rule, pol)
    return out


from skimage.feature import hog as _skhog


def proposal_features(gray, b, pad=0.25):
    """HOG of the padded crop + simple geometry / contrast features."""
    H, W = gray.shape
    x, y, w, h = b['x'], b['y'], b['w'], b['h']
    px, py = int(w * pad), int(h * pad)
    x0, y0, x1, y1 = max(0, x - px), max(0, y - py), min(W, x + w + px), min(H, y + h + py)
    crop = gray[y0:y1, x0:x1]
    if max(w, h) > min(w, h):     # rotate to landscape so orientation does not dominate
        crop = crop if w >= h else crop.T
    c = cv2.resize(np.ascontiguousarray(crop), (32, 32), interpolation=cv2.INTER_AREA)
    hog = _skhog(c, orientations=9, pixels_per_cell=(8, 8), cells_per_block=(2, 2), feature_vector=True)
    inner = gray[y:y + h, x:x + w].astype(np.float32)
    ring = gray[y0:y1, x0:x1].astype(np.float32)
    geo = [np.log(w * h), max(w, h) / max(1, min(w, h)), b['fill'], b['polarity'], b['score'],
           (inner.mean() - ring.mean()) / (ring.std() + 1e-6), inner.std() / 255.0]
    return np.concatenate([hog, geo]).astype(np.float32)


# ------------------------------------------------------------------ evaluation (same for all methods)

IOU_T = 0.5


def iou_matrix(a, b):
    """a: (n,4) xywh, b: (m,4) xywh -> (n,m) IoU"""
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    ax1, ay1, ax2, ay2 = a[:, 0], a[:, 1], a[:, 0] + a[:, 2], a[:, 1] + a[:, 3]
    bx1, by1, bx2, by2 = b[:, 0], b[:, 1], b[:, 0] + b[:, 2], b[:, 1] + b[:, 3]
    iw = np.clip(np.minimum(ax2[:, None], bx2[None]) - np.maximum(ax1[:, None], bx1[None]), 0, None)
    ih = np.clip(np.minimum(ay2[:, None], by2[None]) - np.maximum(ay1[:, None], by1[None]), 0, None)
    inter = iw * ih
    ua = (a[:, 2] * a[:, 3])[:, None] + (b[:, 2] * b[:, 3])[None] - inter
    return inter / np.maximum(ua, 1e-9)


def ioa_pred(a, b):
    """fraction of each pred box a covered by box b"""
    if len(a) == 0 or len(b) == 0:
        return np.zeros((len(a), len(b)))
    ax1, ay1, ax2, ay2 = a[:, 0], a[:, 1], a[:, 0] + a[:, 2], a[:, 1] + a[:, 3]
    bx1, by1, bx2, by2 = b[:, 0], b[:, 1], b[:, 0] + b[:, 2], b[:, 1] + b[:, 3]
    iw = np.clip(np.minimum(ax2[:, None], bx2[None]) - np.maximum(ax1[:, None], bx1[None]), 0, None)
    ih = np.clip(np.minimum(ay2[:, None], by2[None]) - np.maximum(ay1[:, None], by1[None]), 0, None)
    return iw * ih / np.maximum((a[:, 2] * a[:, 3])[:, None], 1e-9)


def match(preds, gt, dontcare, image_ids):
    """Greedy matching per image (score desc). Returns
    pred_df with columns tp (1/0) and ignored, gt_df with matched_score (max score of matching pred, NaN if never matched)."""
    preds = preds[preds.image_id.isin(image_ids)].sort_values('score', ascending=False).copy()
    gt = gt[gt.image_id.isin(image_ids)].copy()
    preds['tp'] = 0; preds['ignored'] = False; preds['best_iou'] = 0.0
    gt['matched_score'] = np.nan
    pg = dict(tuple(preds.groupby('image_id')))
    gg = dict(tuple(gt.groupby('image_id')))
    dg = dict(tuple(dontcare[dontcare.image_id.isin(image_ids)].groupby('image_id')))
    for iid in image_ids:
        P = pg.get(iid); G = gg.get(iid); D = dg.get(iid)
        if P is None:
            continue
        pb = P[['x', 'y', 'w', 'h']].values.astype(float)
        used = np.zeros(0 if G is None else len(G), bool)
        ious = iou_matrix(pb, G[['x', 'y', 'w', 'h']].values.astype(float)) if G is not None else np.zeros((len(P), 0))
        dc = ioa_pred(pb, D[['x', 'y', 'w', 'h']].values.astype(float)).max(1) if D is not None else np.zeros(len(P))
        for k, idx in enumerate(P.index):
            if ious.shape[1]:
                cand = np.where(~used, ious[k], -1)
                j = int(cand.argmax())
                preds.at[idx, 'best_iou'] = ious[k].max()
                if cand[j] >= IOU_T:
                    used[j] = True
                    preds.at[idx, 'tp'] = 1
                    gt.at[G.index[j], 'matched_score'] = P.at[idx, 'score']
                    continue
            if dc[k] >= 0.5:
                preds.at[idx, 'ignored'] = True
    return preds, gt


def average_precision(preds, n_gt):
    p = preds[~preds.ignored].sort_values('score', ascending=False)
    if n_gt == 0 or len(p) == 0:
        return 0.0
    tp = p.tp.values; fp = 1 - tp
    ctp, cfp = np.cumsum(tp), np.cumsum(fp)
    rec = ctp / n_gt; prec = ctp / np.maximum(ctp + cfp, 1e-9)
    mrec = np.concatenate([[0], rec, [1]]); mpre = np.concatenate([[0], prec, [0]])
    for i in range(len(mpre) - 2, -1, -1):
        mpre[i] = max(mpre[i], mpre[i + 1])
    idx = np.where(mrec[1:] != mrec[:-1])[0]
    return float(np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1]))


def at_threshold(preds, gt, n_images, t):
    p = preds[(~preds.ignored) & (preds.score >= t)]
    tp = int(p.tp.sum()); fp = int(len(p) - tp); n_gt = len(gt)
    rec = tp / n_gt if n_gt else 0.0
    prec = tp / (tp + fp) if tp + fp else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return dict(recall=rec, miss_rate=1 - rec, precision=prec, f1=f1, fp_per_100_frames=100 * fp / n_images, tp=tp, fp=fp, n_gt=n_gt)


def best_f1_threshold(preds, gt, n_images):
    """Threshold policy (same for all methods): pick score threshold that maximises F1 on Validation."""
    scores = np.unique(preds[~preds.ignored].score.values)
    if len(scores) > 400:
        scores = np.quantile(scores, np.linspace(0, 1, 400))
    best = (0, scores.min() if len(scores) else 0)
    for t in scores:
        f = at_threshold(preds, gt, n_images, t)['f1']
        if f > best[0]:
            best = (f, t)
    return float(best[1])
