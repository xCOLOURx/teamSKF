from bisect import bisect_left, bisect_right
import json
import logging

from flask import request

from routes import app

logger = logging.getLogger(__name__)


def bf(ratios, goods):
    
    
    n = len(goods)
    adjL = [{} for _ in range(n)]
    for u,v,w in ratios:
        u = int(u)
        v = int(v)
        if (v not in adjL[u] or w > adjL[u][v]):
            adjL[u][v] = w
    
    ans = None
    for source in range(n):
        dist = [0.0 for _ in range(n)]
        pred = [None for _ in range(n)]
        dist[source] = 1.0
        for _ in range(n-1):
            for u,v,w in ratios:
                u = int(u)
                v = int(v)
                if dist[u]*w > dist[v]:
                    dist[v] = dist[u]*w
                    pred[v] = u
        for u,v,w in ratios:
            u = int(u)
            v = int(v)
            if dist[u]*w > dist[v]:
                pred[v] = u
                vis = [False for _ in range(n)]
                vis[v] = True
                while not vis[u]:
                    vis[u] = True
                    u = pred[u]
                cycle = [u]
                v = pred[u]
                res = adjL[v][u]
                while v != u:
                    cycle.append(v)
                    res *= adjL[pred[v]][v]
                    v = pred[v]
                cycle.append(u)
                cycle.reverse()
                if (not ans or ans[0] < res):
                    ans = (res, cycle)
    
            
    return { "path": [goods[u] for u in ans[1]], "gain": (ans[0]-1.0)*100 }

@app.route('/The-Ink-Archive', methods=['POST'])
def ink_archive():
    
    data = request.get_json(silent=True)
    part1_ans = bf(data[0]["ratios"], data[0]["goods"])
    # print(part1_ans)
    part2_ans = bf(data[1]["ratios"], data[1]["goods"])
    # print(part2_ans)
    
    
    return [part1_ans, part2_ans]
    
    
