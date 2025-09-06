from bisect import bisect_left, bisect_right
import json
import logging

from flask import request

from routes import app
import networkx as nx

logger = logging.getLogger(__name__)


@app.route('/investigate', methods=['POST'])
def universal_bureau_surv():
    
    data = request.get_json(silent=True)
    logger.info(data)
    res = []
    try:
        network_list = data["networks"]
    except:
        network_list = eval(request.get_data().decode())
    print(network_list)
    for network in network_list:
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
        
        
    return {"networks": res}
    
    
# [{'networkId': '68456992-3fd6-4983-a35e-1f0a90f15c25', 'network': [{'spy1': 'Tony Stark', 'spy2': 'Natasha Romanoff'}, {'spy1': 'Tony Stark', 'spy2': 'Steve Rogers'}, {'spy1': 'Natasha Romanoff', 'spy2': 'Steve Rogers'}]}, {'networkId': 'fee2ea9d-7af5-4133-b1f4-7222373026ef', 'network': [{'spy1': 'Reed Richards', 'spy2': 'Ben Grimm'}, {'spy1': 'Sue Storm', 'spy2': 'Ben Grimm'}, {'spy1': 'Johnny Storm', 'spy2': 'Ben Grimm'}, {'spy1': 'Johnny Storm', 'spy2': 'Sue Storm'}]}, {'networkId': '3fd489bc-3710-491e-82ab-e78b67da9543', 'network': [{'spy1': 'Erik Lensherr', 'spy2': 'Scott Summers'}, {'spy1': 'Scott Summers', 'spy2': 'Ororo Munroe'}, {'spy1': 'Charles Xavier', 'spy2': 'Ororo Munroe'}, {'spy1': 'Scott Summers', 'spy2': 'Jean Grey'}, {'spy1': 'Ororo Munroe', 'spy2': 'Jean Grey'}]}]