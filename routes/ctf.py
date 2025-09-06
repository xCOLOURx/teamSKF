from bisect import bisect_left, bisect_right
import json
import logging

from flask import request, send_file

from routes import app

logger = logging.getLogger(__name__)



    
@app.route('/payload_homework', methods=['GET'])
def homework():
    return send_file("../static/payload_homework")
    
    
@app.route('/payload_malicious', methods=['GET'])
def malicious():
    return send_file("../static/payload_malicious")
    

