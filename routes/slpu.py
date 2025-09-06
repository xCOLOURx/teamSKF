import logging
import re
from collections import deque
from flask import request, Response
from routes import app

logger = logging.getLogger(__name__)


# ---------- Helpers ----------

def coord_to_square(x, y, cols, rows, cell, minx, miny):
    """
    Convert (x,y) SVG coordinate into 1-based boustrophedon square index.
    Start: bottom-left, End: top-left.
    """
    X = x - minx
    Y = y - miny

    col = X // cell
    row_from_top = Y // cell
    row_from_bottom = rows - 1 - row_from_top

    if row_from_bottom % 2 == 0:  # left-to-right row
        return row_from_bottom * cols + col + 1
    else:  # right-to-left row
        return row_from_bottom * cols + (cols - col)


def parse_board(svg_text):
    """
    Parse board size and jumps from the SVG.
    """
    # Extract viewBox
    vb = re.search(r'viewBox="\s*(-?\d+)\s+(-?\d+)\s+(\d+)\s+(\d+)\s*"', svg_text)
    if not vb:
        raise ValueError("viewBox missing")
    minx, miny, W, H = map(int, vb.groups())

    # Extract cell size from <pattern>
    pat = re.search(r'<pattern[^>]*id="grid"[^>]*width="(\d+)"[^>]*height="(\d+)"', svg_text)
    if not pat:
        raise ValueError("grid pattern missing")
    cell = int(pat.group(1))

    cols = W // cell
    rows = H // cell

    # Extract snakes & ladders
    jumps = {}
    for line in re.findall(r'<line [^>]*/>', svg_text):
        x1 = int(re.search(r'x1="(\d+)"', line).group(1))
        y1 = int(re.search(r'y1="(\d+)"', line).group(1))
        x2 = int(re.search(r'x2="(\d+)"', line).group(1))
        y2 = int(re.search(r'y2="(\d+)"', line).group(1))
        s = coord_to_square(x1, y1, cols, rows, cell, minx, miny)
        e = coord_to_square(x2, y2, cols, rows, cell, minx, miny)
        jumps[s] = e

    return cols, rows, cell, minx, miny, jumps


# ---------- Game rules ----------

def apply_roll(pos, die, roll, final_sq, jumps):
    """
    Move a player given current position, die type, and roll.
    die: 0=regular, 1=power-of-two
    """
    if die == 0:  # regular die
        step = roll
        new_die = 1 if roll == 6 else 0
    else:  # power-of-two die
        if roll == 1:
            step = 2
            new_die = 0
        else:
            step = 1 << roll  # 2^roll
            new_die = 1

    new_pos = pos + step
    if new_pos > final_sq:
        new_pos = final_sq - (new_pos - final_sq)
    new_pos = jumps.get(new_pos, new_pos)
    return new_pos, new_die


# ---------- Solver: BFS ensuring Player 2 wins ----------

def solve_player2(cols, rows, jumps):
    final_sq = cols * rows
    # State: (p1, p2, die1, die2, turn, history)
    start = (0, 0, 0, 0, 0, "")  # both before start, both regular dice, turn=0 (P1)
    queue = deque([start])
    visited = set()

    while queue:
        p1, p2, d1, d2, turn, hist = queue.popleft()

        # Win/loss checks
        if p2 == final_sq:
            return hist
        if p1 == final_sq:
            continue

        key = (p1, p2, d1, d2, turn)
        if key in visited:
            continue
        visited.add(key)

        if turn == 0:  # Player 1's turn
            for r in range(1, 7):
                np1, nd1 = apply_roll(p1, d1, r, final_sq, jumps)
                queue.append((np1, p2, nd1, d2, 1, hist + str(r)))
        else:  # Player 2's turn
            for r in range(1, 7):
                np2, nd2 = apply_roll(p2, d2, r, final_sq, jumps)
                queue.append((p1, np2, d1, nd2, 0, hist + str(r)))

    # Fallback (should not happen under given constraints)
    return "1"


# ---------- Flask route ----------

@app.route('/slpu', methods=['POST'])
def slpu():
    svg_input = request.data.decode("utf-8", errors="ignore")
    logging.info("Received SVG (truncated): %s", svg_input[:200])

    cols, rows, cell, minx, miny, jumps = parse_board(svg_input)
    rolls = solve_player2(cols, rows, jumps)

    result_svg = f'<svg xmlns="http://www.w3.org/2000/svg"><text>{rolls}</text></svg>'
    logging.info("My result: %s", result_svg)

    return Response(result_svg, mimetype="image/svg+xml")
