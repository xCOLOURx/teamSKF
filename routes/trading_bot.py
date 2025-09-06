import json
import logging

from flask import request

from routes import app

logger = logging.getLogger(__name__)


@app.route('/trading-bot', methods=['POST'])
def trading_bot():
    data = request.get_json()
    lst = []
    for index in data:
        dict = {}
        previous_candles = index["previous_candles"]
        observation_candles = index["observation_candles"]

        # Entry at first observation_candle close, exit at last observation_candle close
        entry_price = observation_candles[0]["close"]
        exit_price = observation_candles[-1]["close"]

        # If price increased, LONG; else SHORT
        dict["decision"] = "LONG" if exit_price > entry_price else "SHORT"
        dict["id"] = index["id"]
        lst.append(dict)
    print(lst)
    return json.dumps(lst)
