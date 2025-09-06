from bisect import bisect_left, bisect_right
import json
import logging

from flask import request

from routes import app
import networkx as nx

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
    dp = [None for _ in range(T+1)]
    dp[0] = (0, ())
    end_times = [task["end"] for task in tasks]
    prev_task = []
    for task in tasks:
        s = task["start"]
        pos = bisect_right(end_times, s)
        prev_task.append(pos)
    # print(prev_task)
    
    for i,task in enumerate(tasks, start=1):

        dp[i] = dp[prev_task[i-1]] 
        dp[i] = (dp[i][0] + task["score"], dp[i][1] + (task,))

        if (dp[i][0] < dp[i-1][0]):
            dp[i] = dp[i-1]
    
    edges = []
    for station in subway:
        u, v = station["connection"]
        edge = (u, v, {"weight": station["fee"]})
        edges.append(edge)
    # print(edges)
    G = nx.Graph()
    G.add_edges_from(edges)
    length = dict(nx.floyd_warshall(G, weight="weight"))
    max_score, ts = dp[T]
    curr = starting_station
    min_fee = 0
    for i in range(len(ts)):
        v = ts[i]["station"]
        min_fee += length[curr][v]
        curr = v
    min_fee += length[curr][starting_station]
    schedule = [t["name"] for t in ts]
    # print(max_score, min_fee, schedule)
    ans = {
        "max_score": max_score,
        "min_fee" : min_fee,
        "schedule": schedule
    }
    return json.dumps(ans)
    
