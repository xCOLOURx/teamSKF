import json
import logging

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from statsmodels.nonparametric.smoothers_lowess import lowess

from flask import request

from routes import app

logger = logging.getLogger(__name__)


@app.route('/blankety', methods=['POST'])
def blankety():
    data = request.get_json()
    return {
        "answer": [impute_series(series) for series in data["series"]]
    }

def impute_series(series, frac=0.05):
    arr = np.array([x if x is not None else np.nan for x in series], dtype=float)
    x = np.arange(len(arr))
    mask = ~np.isnan(arr)
    # Denoise with LOESS
    smoothed = lowess(arr[mask], x[mask], frac=frac, return_sorted=False)
    arr_smooth = arr.copy()
    arr_smooth[mask] = smoothed
    # Spline fit to denoised data
    spline = CubicSpline(x[mask], arr_smooth[mask])
    arr_imputed = arr.copy()
    null_mask = np.isnan(arr)
    arr_imputed[null_mask] = spline(x[null_mask])
    # Clamp to finite values
    arr_imputed = np.nan_to_num(arr_imputed, nan=0.0, posinf=np.max(arr_smooth[mask]), neginf=np.min(arr_smooth[mask]))
    return arr_imputed.tolist()