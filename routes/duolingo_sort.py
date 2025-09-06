from bisect import bisect_left, bisect_right
import json
import logging

from flask import request

from routes import app
from text_to_num import text2num
import zahlwort2num as w2n
from cnc import convert

logger = logging.getLogger(__name__)


def roman_to_int(s):
    roman_values = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50,
        'C': 100, 'D': 500, 'M': 1000
    }
    
    total = 0
    prev_value = 0
    
    for char in reversed(s):
        value = roman_values[char]
        if value < prev_value:
            total -= value
        else:
            total += value
        prev_value = value
    
    return total

def english_to_int(s):
    return text2num(s, "en")

def trad_ch_to_int(s):
    res = convert.chinese2number(s)
    assert set(convert.number2chinese(int(res), language="T", forceErLian="forceNot")).issubset(s)
    return res

def simp_ch_to_int(s):
    res = convert.chinese2number(s)
    
    assert set(convert.number2chinese(int(res), language="S", forceErLian="forceNot")).issubset(s)
    return res

def german_to_int(s):
    return w2n.convert(s)

CONVERSIONS = [
    (int, 5), (roman_to_int, 0), (english_to_int, 1), 
    (trad_ch_to_int, 2), (simp_ch_to_int, 3),
    (german_to_int, 4), ]


@app.route('/duolingo-sort', methods=['POST'])
def duolingo_sort():
    data = request.get_data(as_text=True)
    # print(data)
    data = json.loads(data)
    # logger.info(data)
    inp = data["challengeInput"]["unsortedList"]
    lis = []
    for num in inp:
        for conv, priority in CONVERSIONS:
            try:
                lis.append((conv(num), priority, num))
                break
            except:
                pass
        else:
            logger.info(num)
    # print(lis)
    if (data["part"] == "ONE"):
        res = {
            "sortedList": [str(x) for x,_,_ in sorted(lis)]
        }
    else:
        res = {
            "sortedList": [x for _,_,x in sorted(lis)]
        }
    # logger.info(sorted(lis))
    return res
                

