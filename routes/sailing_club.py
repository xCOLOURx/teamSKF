from bisect import bisect_left, bisect_right
import json
import logging

from flask import request

from routes import app

logger = logging.getLogger(__name__)


def part1(inp):
    inp.sort()
    cl, cr = inp[0][0], inp[0][1]
    
    n = len(inp)
    ans = []
    for i in range(1,n):
        if (inp[i][0] <= cr):
            cr = max(cr, inp[i][1])
        else:
            ans.append((cl, cr))
            cl = inp[i][0]
            cr = inp[i][1]
    ans.append((cl, cr))
    return ans

def part2(inp):
    inp.sort(key=lambda x: (x[1], x[0]))
    n = len(inp)
    l = 0
    ans = 0
    curr = 0
    for r in range(n):
        while l < r and inp[l][1] < inp[r][0]:
            curr -= 1
            l += 1
        curr += 1
        ans = max(curr, ans)
    return ans
    
@app.route('/', methods=['POST'])
def sailing_club():
    data = request.get_json(silent=True)
    sols = []
    for testcase in data["testCases"]:
        inp = testcase["input"]
        sols.append({
            "id": testcase["id"],
            "sortedMergedSlots": part1(inp),
            "minBoatsNeeded": part2(inp)
        })
    return {"solutions": sols}
                

