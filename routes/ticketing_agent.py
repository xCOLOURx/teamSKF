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
    
    
                

