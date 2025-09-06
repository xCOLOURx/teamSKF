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

        # Taken a stricter condition
        if (previous_candles[2]["volume"] < observation_candles[0]["volume"] < observation_candles[1]["volume"] < observation_candles[2]["volume"]):
            if (previous_candles[2]["close"] < observation_candles[0]["close"] < observation_candles[1]["close"] < observation_candles[2]["close"]):
                dict["decision"] = "LONG"
                dict["diff"] = observation_candles[2]["close"] - observation_candles[0]["close"]
            elif (previous_candles[2]["close"] > observation_candles[0]["close"] > observation_candles[1]["close"] > observation_candles[2]["close"]):
                dict["decision"] = "SHORT"
                dict["diff"] = observation_candles[0]["close"] - observation_candles[2]["close"]
        
        dict["id"] = index["id"]
        lst.append(dict)

        # TODO: For the remaining balance, take a more lax condition
    
    # # Filter lst to top 50 by 'diff' value
    # lst = sorted(lst, key=lambda d: d.get('diff', float('-inf')), reverse=True)[:50]
    
    for d in lst:
        d.pop('diff', None)
    
    print(f"Number of potential trades after filtering top 50: {len(lst)}")
    print(lst)

    return json.dumps(lst)
