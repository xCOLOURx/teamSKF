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
        title = index["title"]
        previous_candles = index["previous_candles"]
        observation_candles = index["observation_candles"]

        if (observation_candles[0]["volume"] < observation_candles[2]["volume"]):
            if (observation_candles[0]["close"] < observation_candles[2]["close"]):
                dict["decision"] = "LONG"
            else:
                dict["decision"] = "SHORT"
        else:
            if (observation_candles[0]["close"] < observation_candles[2]["close"]):
                dict["decision"] = "SHORT"
            else:
                dict["decision"] = "LONG"

        if ("buy" in title.lower()) or ("long" in title.lower()) or ("bull" in title.lower()) or ("bullish" in title.lower()) or ("moon" in title.lower()) or ("rocket" in title.lower()) or ("pump" in title.lower()):
            dict["decision"] = "LONG"
        elif ("sell" in title.lower()) or ("short" in title.lower()) or ("bear" in title.lower()) or ("bearish" in title.lower()) or ("dump" in title.lower()) or ("crash" in title.lower()) or ("down" in title.lower()):
            dict["decision"] = "SHORT"
        
        dict["id"] = index["id"]
        lst.append(dict)
    print(lst)
    return json.dumps(lst)
