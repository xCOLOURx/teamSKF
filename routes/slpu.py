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
    Square 1 = bottom-left, Square W*H = top-left.
    """
    X = x - minx
    Y = y - miny

    col = X // cell
    row_from_top = Y // cell
    row_from_bottom = rows - 1 - row_from_top  # 0 = bottom row

    if row_from_bottom % 2 == 0:  # left-to-right
        idx = row_from_bottom * cols + col + 1
    else:  # right-to-left
        idx = row_from_bottom * cols + (cols - col)

    return int(idx)


def parse_board(svg_text):
    """Parse board size and jumps from the SVG."""
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

    return cols, rows, jumps


def apply_roll(pos, die, roll, final_sq, jumps):
    """Move a player given current position, die type, and roll."""
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

    # Apply snake/ladder jump
    new_pos = jumps.get(new_pos, new_pos)
    return new_pos, new_die


# ---------- Path Finder ----------

def find_path(cols, rows, jumps):
    """Find an optimal path to the final square, recording rolls."""
    final_sq = cols * rows
    start = (0, 0, "")  # pos, die, rolls
    queue = deque([start])
    visited = set()

    while queue:
        pos, die, rolls = queue.popleft()
        if pos == final_sq:
            return rolls

        if (pos, die) in visited:
            continue
        visited.add((pos, die))

        for r in range(1, 7):
            new_pos, new_die = apply_roll(pos, die, r, final_sq, jumps)
            queue.append((new_pos, new_die, rolls + str(r)))

    return "1"  # fallback, shouldn't happen


# ---------- Player 2 win strategy ----------

def make_player2_win(optimal_rolls, cols, rows, jumps):
    """
    Modify the final move so:
    - P1 overshoots and misses.
    - P2 lands exactly on the final square.
    """
    final_sq = cols * rows

    # Play out Player 1 until just before the last move
    p1, d1 = 0, 0
    for r in map(int, optimal_rolls[:-1]):
        p1, d1 = apply_roll(p1, d1, r, final_sq, jumps)

    # Replace last roll with overshoot (safe bump)
    last_r = int(optimal_rolls[-1])
    overshoot_r = last_r + 2 if last_r < 6 else 1

    p1_rolls = optimal_rolls[:-1] + str(overshoot_r)
    p2_rolls = optimal_rolls

    result = []
    for x, y in zip(p1_rolls, p2_rolls):
        result.append(x)
        result.append(y)
    return "".join(str(r) for r in result)
 


# ---------- Flask route ----------

@app.route('/slpu', methods=['POST'])
def slpu():
    svg_input = request.data.decode("utf-8", errors="ignore")
    logging.info("Received SVG (truncated): %s", svg_input[:200])

    cols, rows, jumps = parse_board(svg_input)

    # Final square = W * H
    final_sq = cols * rows
    logging.info("Board size: %dx%d, final square: %d", cols, rows, final_sq)

    # Find optimal path to last square
    optimal_rolls = find_path(cols, rows, jumps)

    # Adjust to ensure Player 2 wins
    rolls = make_player2_win(optimal_rolls, cols, rows, jumps)

    result_svg = f'<svg xmlns="http://www.w3.org/2000/svg"><text>{rolls}</text></svg>'
    logging.info("My result: %s", result_svg)

    return Response(result_svg, mimetype="image/svg+xml")


# if __name__ == "__main__":
#     with open("example.svg", "r", encoding="utf-8") as f:
#         svg_text = f.read()

#         cols, rows, jumps = parse_board(svg_text)

#         # Final square = W * H
#         final_sq = cols * rows
#         logging.info("Board size: %dx%d, final square: %d", cols, rows, final_sq)

#         # Find optimal path to last square
#         optimal_rolls = find_path(cols, rows, jumps)

#         # Adjust to ensure Player 2 wins
#         rolls = make_player2_win(optimal_rolls, cols, rows, jumps)

#         result_svg = f'<svg xmlns="http://www.w3.org/2000/svg"><text>{rolls}</text></svg>'
#         logging.info("My result: %s", result_svg)

#         print(rolls)