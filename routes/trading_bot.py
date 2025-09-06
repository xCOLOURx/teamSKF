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
        if observation_candles[-1]["close"] > previous_candles[-1]["close"]:
            dict["decision"] = "LONG"
        elif sum(candle["closed"] for candle in observation_candles[-3:]) > sum(candle["closed"] for candle in previous_candles[-3:]):
            dict["decision"] = "LONG"
        else:
            dict["decision"] = "SHORT"

        dict["decision"] = "LONG" if observation_candles[-1]["close"] > previous_candles[-1]["close"] else "SHORT"
        dict["id"] = index["id"]
        lst.append(dict)
    
    print(lst)

    # logging.info("My result :{}".format(result))
    return json.dumps(lst)
