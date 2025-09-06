from bisect import bisect_left, bisect_right
import json
import logging

from flask import request

from routes import app

logger = logging.getLogger(__name__)



    
@app.route('/ticketing-agent', methods=['POST'])
def ticketing_agent():
    data = request.get_json(silent=True)
    customers = data["customers"]
    concerts = data["concerts"]
    priority = data["priority"]
    ans = {}
    for customer in customers:
        vip_bonus = 100 if customer["vip_status"] else 0
        points = {concert["name"]:vip_bonus for concert in concerts}
        if (customer["credit_card"] in priority):
            points[priority[customer["credit_card"]]] += 50
        ax, ay = customer["location"][0], customer["location"][1]
        for concert in concerts:
            bx,by = concert["booking_center_location"][0], concert["booking_center_location"][1]
            dist = abs(ax-bx) + abs(ay-by)
            points[concert["name"]] += max(0, 30 - 5*(dist-2))
        ans[customer["name"]] = max(points.items(), key=lambda x: x[1])[0]
    return ans
        
    # dist 2 = 30 points
    # dist 3 = 25 points
    # dist 4 = 20 points
    # dist 5 = 15 points
    # dist 6 = 10 points
    # dist 7 = 5 points
    # dist 8 = 0 points
                 

