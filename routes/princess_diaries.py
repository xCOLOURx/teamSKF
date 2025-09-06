from bisect import bisect_left, bisect_right
import json
import logging

from flask import request

from routes import app
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

logger = logging.getLogger(__name__)


@app.route('/princess-diaries', methods=['POST'])
def princess_diaries():
    data = request.get_json()
    # logging.info("data sent for evaluation {}".format(data))
    tasks: list = data.get("tasks")
    subway = data.get("subway")
    starting_station = int(data.get("starting_station"))
    T = len(tasks)
    # print(tasks)
    # print(subway)
    # print(starting_station)
    
    tasks.sort(key=lambda t: t["end"])
    
    end_times = [task["end"] for task in tasks]
    prev_task = []
    for task in tasks:
        s = task["start"]
        pos = bisect_right(end_times, s)
        prev_task.append(pos)
    # print(prev_task)
    
    
    dp = [(0, tuple()) for _ in range(T+1)]
    for i,task in enumerate(tasks, start=1):

        dp[i] = dp[prev_task[i-1]] 
        dp[i] = (dp[i][0] + task["score"], dp[i][1] + (task,))

        if (dp[i][0] < dp[i-1][0]):
            dp[i] = dp[i-1]
    
    row_id, col_id, weights = [], [], []
    V = 0
    for station in subway:
        u, v = station["connection"]
        V = max(V, u, v)
        row_id.append(u)
        col_id.append(v)
        weights.append(station["fee"])
        row_id.append(v)
        col_id.append(u)
        weights.append(station["fee"])
    V += 1
    sparse = csr_matrix((weights, (row_id, col_id)), shape=(V, V), dtype=int)
    dists = shortest_path(sparse)
    max_score, ts = dp[T]
    curr = starting_station
    min_fee = 0
    for i in range(len(ts)):
        v = ts[i]["station"]
        min_fee += dists[curr][v]
        curr = v
    min_fee += dists[curr][starting_station]
    schedule = [t["name"] for t in ts]
    # print(max_score, min_fee, schedule)
    ans = {
        "max_score": max_score,
        "min_fee" : int(min_fee),
        "schedule": schedule
    }
    return json.dumps(ans)
    
