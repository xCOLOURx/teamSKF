import json
import logging

from flask import request

from routes import app

logger = logging.getLogger(__name__)


@app.route('/trading-bot', methods=['POST'])
def trading_bot():
    data = request.get_json()
    lst_strict = []
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
                dict["id"] = index["id"]
            elif (previous_candles[2]["close"] > observation_candles[0]["close"] > observation_candles[1]["close"] > observation_candles[2]["close"]):
                dict["decision"] = "SHORT"
                dict["diff"] = observation_candles[0]["close"] - observation_candles[2]["close"]
                dict["id"] = index["id"]

        lst_strict.append(dict)

    lst_strict = [d for d in lst_strict if d] # Remove empty dicts

    # # TODO: For the remaining balance, take a more lax condition
    # lst_lax = []
    # for index in data:
    #     dict = {}
    #     title = index["title"]
    #     previous_candles = index["previous_candles"]
    #     observation_candles = index["observation_candles"]

    #     # Taken a stricter condition
    #     if (observation_candles[0]["volume"] < observation_candles[1]["volume"] < observation_candles[2]["volume"]):
    #         if (observation_candles[0]["close"] < observation_candles[1]["close"] < observation_candles[2]["close"]):
    #             dict["decision"] = "LONG"
    #             dict["diff"] = observation_candles[2]["close"] - observation_candles[0]["close"]
    #             dict["id"] = index["id"]
    #         elif (observation_candles[0]["close"] > observation_candles[1]["close"] > observation_candles[2]["close"]):
    #             dict["decision"] = "SHORT"
    #             dict["diff"] = observation_candles[0]["close"] - observation_candles[2]["close"]
    #             dict["id"] = index["id"]

    #     lst_lax.append(dict)
    
    # # Remove indexes in lst_lax that are already in lst_strict by matching 'id'
    # strict_ids = {d['id'] for d in lst_strict if 'id' in d}
    # lst_lax = [d for d in lst_lax if d.get('id') not in strict_ids]
    # # Now filter lst_lax to top 50 by 'diff' value
    # lst_lax = sorted(lst_lax, key=lambda d: d.get('diff', float('-inf')), reverse=True)[:(50-len(lst_strict))]

    # lst = lst_strict + lst_lax
    
    lst = lst_strict

    for d in lst:
        d.pop('diff', None)
    
    print(f"Number of potential trades after filtering top 50: {len(lst)}")
    print(lst)

    return json.dumps(lst)
