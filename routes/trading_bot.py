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

        if (observation_candles[0]["volume"] < observation_candles[1]["volume"] < observation_candles[2]["volume"]):
            if (observation_candles[0]["close"] < observation_candles[1]["close"] < observation_candles[2]["close"]):
                dict["decision"] = "LONG"
                dict["diff"] = observation_candles[2]["close"] - observation_candles[0]["close"]
            elif (observation_candles[0]["close"] > observation_candles[1]["close"] > observation_candles[2]["close"]):
                dict["decision"] = "SHORT"
                dict["diff"] = observation_candles[0]["close"] - observation_candles[2]["close"]
                # TODO: sort by price diff & select 50 best. can add other indicators

        dict["id"] = index["id"]
        lst.append(dict)
    
    # Filter lst to top 50 by 'diff' value
    lst = sorted(lst, key=lambda d: d.get('diff', float('-inf')), reverse=True)[:50]
    for d in lst:
        d.pop('diff', None)

    print(lst)
    return json.dumps(lst)
