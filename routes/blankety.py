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
        imputed = impute_nulls_with_spline(series, window=3)
        answers.append(imputed.tolist())

    result = {"answer": answers}

    logging.info("My result :{}".format(result))
    return json.dumps(result)

# Smoothing function (rolling mean)
def smooth_series(series, window=3):
    arr = np.array([x if x is not None else np.nan for x in series], dtype=float)
    return pd.Series(arr).rolling(window, min_periods=1, center=True).mean().to_numpy()

# Cubic spline regression for imputation
def impute_nulls_with_spline(series, window=3):
    arr = np.array([x if x is not None else np.nan for x in series], dtype=float)
    smoothed = smooth_series(arr, window)
    x = np.arange(len(arr))
    mask = ~np.isnan(smoothed)
    # Fit cubic spline to smoothed, non-null data
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