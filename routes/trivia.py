import json
import logging

from flask import request

from routes import app

logger = logging.getLogger(__name__)


@app.route('/trivia', methods=['GET'])
def evaluate():
    data = {  "answers": [4, ]};
    logging.info("My result :{}".format(data))
    return json.dumps(data)
