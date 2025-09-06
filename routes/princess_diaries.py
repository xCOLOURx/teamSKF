import json
import logging

from flask import request

from routes import app

logger = logging.getLogger(__name__)


@app.route('/princess-diaries', methods=['POST'])
def princess_diaries():
    data = request.get_json()
    logging.info("data sent for evaluation {}".format(data))
    tasks = data.get("tasks")
    subway = data.get("subway")
    starting_station = int(data.get("starting_station"))
    print(tasks)
    print(subway)
    print(starting_station)
