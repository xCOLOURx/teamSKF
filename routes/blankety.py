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

    # Implementation here:
    answers = []
    for series in data["series"]:
        best_imputed = None
        best_score = float('inf')
        null_mask = [x is None for x in series]
        # Try several smoothing fractions and pick the best for each series
        for frac in [0.15, 0.25, 0.35, 0.5]:
            imputed = impute_nulls_adaptive(series, frac=frac)
            # Use variance of imputed values at nulls as a proxy for stability
            score = np.nanvar(imputed[null_mask])
            if score < best_score:
                best_score = score
                best_imputed = imputed
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