import json
import logging

from flask import request

from routes import app

logger = logging.getLogger(__name__)


@app.route('/blankety', methods=['POST'])
def blankety():
    data = request.get_json()
    logging.info("data sent for evaluation {}".format(data))
    input_value = data.get("input")

    # Implementation here:
    result = input_value

    logging.info("My result :{}".format(result))
    return json.dumps(result)

# Rules
# 1. Replace all nulls
# 2. Signal is function (e.g. linear/quad, periodic, short-memory dependency) + noise
# 3. Local regression, spline fits, state-space models, or autoregressive smoothing
# 4. Return exactly 100 lists of length 1000

# import numpy as np
# import pandas as pd
# from typing import Optional, Union

# def smooth_series(series: Union[pd.Series, np.ndarray], window: int = 5) -> np.ndarray:
#     """
#     Smooth a series using a rolling mean.
#     Args:
#         series: Input series (pandas Series or numpy array)
#         window: Window size for rolling mean
#     Returns:
#         Smoothed numpy array
#     """
#     if isinstance(series, pd.Series):
#         return series.rolling(window, min_periods=1, center=True).mean().to_numpy()
#     else:
#         return pd.Series(series).rolling(window, min_periods=1, center=True).mean().to_numpy()

# def regress_series(x: np.ndarray, y: np.ndarray, degree: int = 1) -> np.poly1d:
#     """
#     Fit a polynomial regression to the data.
#     Args:
#         x: Independent variable (1D array)
#         y: Dependent variable (1D array)
#         degree: Degree of polynomial
#     Returns:
#         np.poly1d object representing the fitted polynomial
#     """
#     mask = ~np.isnan(y)
#     coeffs = np.polyfit(x[mask], y[mask], degree)
#     return np.poly1d(coeffs)
