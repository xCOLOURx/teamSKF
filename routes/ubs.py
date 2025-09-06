from bisect import bisect_left, bisect_right
import json
import logging

from flask import request

from routes import app
import networkx as nx

logger = logging.getLogger(__name__)


@app.route('/investigate', methods=['POST'])
def universal_bureau_surv():
    data = request.get_json()
    print(data)
    res = []
    for network in data["networks"]:
        ans = {"networkId": network["networkId"]}
        
        edges = set()
        for edge in network["network"]:
            edges.add((edge["spy1"], edge["spy2"]))
        G = nx.Graph()
        G.add_edges_from(edges)
        bridges = nx.bridges(G)
        for u,v in bridges:
            edges.discard((u,v))
            edges.discard((v,u))
        ans["extraChannels"] = []
        for u,v in edges:
            ans["extraChannels"].append({"spy1": u, "spy2": v})
        res.append(ans)
        
        
    return json.dumps({"networks": res})