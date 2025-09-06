import json
import logging

from flask import request

from routes import app

logger = logging.getLogger(__name__)


@app.route('/trading-bot', methods=['POST'])
def trading_bot():
    data = request.get_json()
    # logging.info("data sent for evaluation {}".format(data))

    # result = input_value * input_value
    
    lst = []
    for index in data:
        dict = {}
        previous_candles = index["previous_candles"]
        observation_candles = index["observation_candles"]

        # Strategy
        # 1. if later close > previous close, LONG
        #    else
        # 2.    if sum of last 3 closes in observation > sum of last 3 closes in previous, LONG
        # 3. else SHORT
        # TODO: incorporate volume
        # 
        if observation_candles[-1]["close"] > previous_candles[-1]["close"]:
            dict["decision"] = "LONG"
        elif sum(candle["close"] for candle in observation_candles[-3:]) > sum(candle["close"] for candle in previous_candles[-3:]):
            dict["decision"] = "LONG"
        else:
            dict["decision"] = "SHORT"

        dict["decision"] = "LONG" if observation_candles[-1]["close"] > previous_candles[-1]["close"] else "SHORT"
        dict["id"] = index["id"]
        lst.append(dict)
    
    print(lst)

    # logging.info("My result :{}".format(result))
    return json.dumps(lst)
