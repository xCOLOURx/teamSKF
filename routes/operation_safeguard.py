from bisect import bisect_left, bisect_right
import json
import logging

from flask import request

from routes import app

logger = logging.getLogger(__name__)

def mirror_words(s):
    return " ".join(map(lambda x: x[::-1], s.split(" ")))

def encode_mirror_alphabet(s):
    res = []
    for c in s:
        if (c.isupper()):
            res.append(chr(25-ord(c)+2*ord('A')))
        elif(c.islower()):
            res.append(chr(25-ord(c)+2*ord('a')))
        else:
            res.append(c)
    return "".join(res)

def toggle_case(s):
    res = []
    for c in s:
        if (c.isupper()):
            res.append(c.lower())
        elif (c.islower()):
            res.append(c.upper())
        else:
            res.append(c)
    return "".join(res)

def swap_pairs(s):
    res = []
    for i in range(0,len(s), 2):
        if (i+1 < len(s)):
            res.append(s[i+1])
        res.append(s[i])
    return ''.join(res)

def encode_index_parity(s):
    res = []
    j = (len(s)+1)//2
    i = 0
    while j < len(s):
        res.append(s[i])
        res.append(s[j])
        i += 1
        j += 1
    if (len(s)%2 == 1):
        res.append(s[i])
    return "".join(res)

VOWELS = set("aeiouAEIOU")
def double_consonants(s):
    i = 0
    res = []
    while i < len(s):
        if (s[i].isalpha() and s[i] not in VOWELS):
            i+=1
        res.append(s[i])    
        i += 1
    return "".join(res)


OPERATIONS = {
    "mirror_words(": mirror_words,
    "encode_mirror_alphabet(": encode_mirror_alphabet,
    "toggle_case(": toggle_case,
    "swap_pairs(": swap_pairs,
    "encode_index_parity(": encode_index_parity,
    "double_consonants(": double_consonants
}
@app.route('/operation-safeguard', methods=['POST'])
def operation_safeguard():
    data = request.get_json(silent=True)
    logger.info(data)
    chal1 = data["challenge_one"]
    chal1_ans = chal1["transformed_encrypted_word"]
    for trans in reversed(chal1["transformations"]):
        while trans != "x":
            i = trans.find('(')+1
            op = OPERATIONS[trans[:i]]
            chal1_ans = op(chal1_ans)
            trans = trans[i:-1]
    print(chal1_ans)
    
    chal2 = data["challenge_two"]
    logging.info(chal2)
    return {"challenge_one": chal1_ans}
                

