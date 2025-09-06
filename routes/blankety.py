import json
import logging

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

from flask import request

from routes import app

logger = logging.getLogger(__name__)


@app.route('/blankety', methods=['POST'])
def blankety():
    data = request.get_json()
    logging.info("data sent for evaluation {}".format(data))

    answers = []
    for series in data["series"]:
        arr = np.array([x if x is not None else np.nan for x in series], dtype=float)
        x = np.arange(len(arr))
        mask = ~np.isnan(arr)
        null_mask = np.isnan(arr)

        # Candidate models
        candidates = []

        # Polynomial fits (degrees 1, 2, 3)
        for deg in [1, 2, 3]:
            try:
                coeffs = np.polyfit(x[mask], arr[mask], deg)
                poly = np.poly1d(coeffs)
                pred = arr.copy()
                pred[null_mask] = poly(x[null_mask])
                candidates.append((pred, np.nanvar(pred[null_mask])))
            except Exception:
                pass

        # Trigonometric fit (sinusoidal)
        try:
            from scipy.optimize import curve_fit
            def sin_func(x, A, w, phi, c):
                return A * np.sin(w * x + phi) + c
            popt, _ = curve_fit(sin_func, x[mask], arr[mask], p0=[1, 1, 0, 0])
            pred = arr.copy()
            pred[null_mask] = sin_func(x[null_mask], *popt)
            candidates.append((pred, np.nanvar(pred[null_mask])))
        except Exception:
            pass

        # Exponential fit
        try:
            def exp_func(x, a, b, c):
                return a * np.exp(b * x) + c
            popt, _ = curve_fit(exp_func, x[mask], arr[mask], p0=[1, 0.01, 0])
            pred = arr.copy()
            pred[null_mask] = exp_func(x[null_mask], *popt)
            candidates.append((pred, np.nanvar(pred[null_mask])))
        except Exception:
            pass

        # LOESS + cubic spline (as before)
        for frac in [0.15, 0.25, 0.35, 0.5]:
            try:
                imputed = impute_nulls_adaptive(series, frac=frac)
                candidates.append((imputed, np.nanvar(imputed[null_mask])))
            except Exception:
                pass

        # Select best candidate by lowest variance at nulls
        if candidates:
            best_imputed = min(candidates, key=lambda tup: tup[1])[0]
        else:
            best_imputed = arr.copy()
            best_imputed[null_mask] = 0
        answers.append(best_imputed.tolist())

    result = {"answer": answers}

    logging.info("My result :{}".format(result))
    return json.dumps(result)

# Smoothing function (rolling mean)

# LOESS smoothing (local polynomial regression)
def loess_smooth(series, frac=0.3):
    from statsmodels.nonparametric.smoothers_lowess import lowess
    arr = np.array([x if x is not None else np.nan for x in series], dtype=float)
    x = np.arange(len(arr))
    mask = ~np.isnan(arr)
    smoothed = lowess(arr[mask], x[mask], frac=frac, return_sorted=False)
    result = arr.copy()
    result[mask] = smoothed
    return result

# Cubic spline regression for imputation

# Improved imputation: combine LOESS and cubic spline
def impute_nulls_adaptive(series, frac=0.3):
    arr = np.array([x if x is not None else np.nan for x in series], dtype=float)
    smoothed = loess_smooth(arr, frac=frac)
    x = np.arange(len(arr))
    mask = ~np.isnan(smoothed)
    spline = CubicSpline(x[mask], smoothed[mask])
    imputed = arr.copy()
    null_mask = np.isnan(arr)
    imputed[null_mask] = spline(x[null_mask])
    return imputed

# # Test input
# {
#     "series": [
#         [0.10, null, 0.30, null, 0.52],
#         [0.20, null, 0.60, null, 1.04]
#     ]
# }