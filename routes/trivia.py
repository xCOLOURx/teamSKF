import json
import logging

from flask import request

from routes import app

logger = logging.getLogger(__name__)


@app.route('/trivia', methods=['GET'])
def evaluate():
    data = {  "answers": [4, 1, 2, 2, 3, 4, 1, 5, 4, 3, 3, 3, 4, 1, 2, 1, 1, 2, 2, 1, 2, 2, 3, 4, 2] }
    logging.info("My result :{}".format(data))
    return json.dumps(data)
