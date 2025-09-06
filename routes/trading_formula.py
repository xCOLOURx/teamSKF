import json
import logging
import re
import math
import argparse
from flask import request, jsonify
from routes import app

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _read_group(s: str, start: int):
    """
    Read a balanced {...} or (...) group starting at index `start`.
    Returns (content, next_index). If not a group, returns (None, start).
    """
    if start >= len(s) or s[start] not in "{(":
        return None, start
    open_ch = s[start]
    close_ch = "}" if open_ch == "{" else ")"
    depth = 0
    j = start
    while j < len(s):
        c = s[j]
        if c == open_ch:
            depth += 1
        elif c == close_ch:
            depth -= 1
            if depth == 0:
                # content excludes the outer braces/parens
                return s[start + 1 : j], j + 1
        j += 1
    # Unbalanced; treat as no group
    return None, start


def _replace_fractions(expr: str) -> str:
    """
    Replace all \frac{num}{den} with ((num)/(den)) using balanced group parsing.
    Handles nested \frac and \text inside.
    """
    i = 0
    out = []
    while i < len(expr):
        if expr.startswith(r"\frac", i):
            j = i + len(r"\frac")
            # skip spaces
            while j < len(expr) and expr[j].isspace():
                j += 1
            # numerator must be a {group}
            num, j2 = _read_group(expr, j)
            if num is None:
                # not a well-formed \frac; emit literally and continue
                out.append("frac")
                i = j
                continue
            # skip spaces
            k = j2
            while k < len(expr) and expr[k].isspace():
                k += 1
            den, k2 = _read_group(expr, k)
            if den is None:
                out.append("frac")
                i = j2
                continue
            out.append(f"(({num})/({den}))")
            i = k2
        else:
            out.append(expr[i])
            i += 1
    return "".join(out)


def _read_ungrouped_body(s: str, start: int) -> tuple[str, int]:
    """
    Read a body expression starting at `start` until the next top-level + or -,
    or end of string. Tracks nesting to avoid cutting inside parentheses.
    """
    depth = 0
    j = start
    while j < len(s):
        c = s[j]
        if c in "({":
            depth += 1
        elif c in ")}":
            depth = max(0, depth - 1)
        elif depth == 0 and c in "+-":
            break
        j += 1
    return s[start:j].strip(), j


def _replace_sums(expr: str) -> str:
    """
    Replace \sum_{i=1}^{n} <body> with:
      (sum((<body>) for i in range(int(1), int(n)+1)))
    Supports body in { ... } or ( ... ) or ungrouped token up to next top-level + or -.
    """
    i = 0
    out = []
    L = len(expr)
    while i < L:
        if expr.startswith(r"\sum_", i):
            j = i + len(r"\sum_")
            # parse lower limit group {i=1}
            lower_group, j2 = _read_group(expr, j)
            if lower_group is None or "=" not in lower_group:
                out.append("sum")
                i = j
                continue
            var, lower = lower_group.split("=", 1)
            var = var.strip()
            lower = lower.strip()

            # expect ^{upper}
            if j2 >= L or expr[j2] != "^":
                out.append("sum")
                i = j2
                continue
            j3 = j2 + 1
            upper_group, j4 = _read_group(expr, j3)
            if upper_group is None:
                out.append("sum")
                i = j3
                continue
            upper = upper_group.strip()

            # read body
            # skip spaces
            j5 = j4
            while j5 < L and expr[j5].isspace():
                j5 += 1

            if j5 < L and expr[j5] in "{(":
                body, j6 = _read_group(expr, j5)
            else:
                body, j6 = _read_ungrouped_body(expr, j5)

            out.append(f"(sum(({body}) for {var} in range(int({lower}), int({upper})+1)))")
            i = j6
        else:
            out.append(expr[i])
            i += 1
    return "".join(out)

# ---------- LaTeX -> Python ----------

def latex_to_python(formula: str, variables: dict) -> str:
    expr = formula.strip()

    # Remove $$ / $ wrappers
    expr = re.sub(r"^\s*\$\$|\$\$\s*$", "", expr)
    expr = re.sub(r"^\s*\$|\$\s*$", "", expr)

    # Drop leading assignment (e.g., "Fee =")
    expr = re.sub(r"^[A-Za-z_][A-Za-z0-9_]*\s*=", "", expr).strip()

    # Handle \frac BEFORE touching braces/backslashes
    expr = _replace_fractions(expr)

    # Handle \sum BEFORE removing braces/backslashes
    expr = _replace_sums(expr)

    # \text{Var} -> Var
    expr = re.sub(r"\\text\{([^}]*)\}", r"\1", expr)

    # Normalize bracketed variable names: E[R_m] -> E_R_m
    expr = expr.replace("[", "_").replace("]", "")

    # LaTeX operators/functions
    expr = expr.replace(r"\times", "*").replace(r"\cdot", "*")
    expr = expr.replace(r"\max", "max").replace(r"\min", "min")
    expr = expr.replace(r"\log", "math.log").replace(r"\ln", "math.log")

    # Exponentials: e^{...} or e^x -> math.exp(...)
    expr = re.sub(r"e\^\{([^}]*)\}", r"math.exp(\1)", expr)
    expr = re.sub(r"e\^\(([^)]*)\)", r"math.exp(\1)", expr)
    expr = re.sub(r"(?<![A-Za-z0-9_])e\^([A-Za-z0-9_\.]+)", r"math.exp(\1)", expr)

    # Convert remaining LaTeX power '^' to Python '**'
    # (after handling e^.. to avoid turning it into math.exp**)
    expr = expr.replace("^", "**")

    # Now it's safe to drop LaTeX grouping braces
    expr = expr.replace("{", "").replace("}", "")

    # Remove any remaining backslashes (e.g., \sigma_p -> sigma_p)
    expr = expr.replace("\\", "")

    # Finally, replace variable names with dict lookups (longest first to avoid partial collisions)
    for var in sorted(variables.keys(), key=len, reverse=True):
        expr = re.sub(rf"\b{re.escape(var)}\b", f"variables['{var}']", expr)

    return expr.strip()


@app.route('/trading-formula', methods=['POST'])
def trading_formula():
    try:
        testcases = request.get_json(force=True)
        results = []

        for case in testcases:
            formula = case.get("formula", "")
            variables = case.get("variables", {})

            python_expr = latex_to_python(formula, variables)

            try:
                result = eval(
                    python_expr,
                    {"math": math, "max": max, "min": min, "sum": sum, "range": range},
                    {"variables": variables}
                )
                result = f"{float(result):.4f}"
            except Exception as e:
                logger.error(f"Error evaluating {case.get('name')}: {python_expr} :: {e}")
                result = None

            results.append({"result": result})

        return jsonify(results)

    except Exception as e:
        logger.error(f"Trading formula error: {e}")
        return jsonify({"error": str(e)}), 400


# def run_local_tests():
#     """Run a few local testcases without Flask server"""
#     tests = [
#         {
#             "name": "test1",
#             "formula": r"Fee = \text{TradeAmount} \times \text{BrokerageRate} + \text{FixedCharge}",
#             "variables": {
#                 "TradeAmount": 10000.0,
#                 "BrokerageRate": 0.0025,
#                 "FixedCharge": 10.0,
#             },
#         },
#         {
#             "name": "test2",
#             "formula": r"Fee = \max(\text{TradeAmount} \times \text{BrokerageRate}, \text{MinimumFee})",
#             "variables": {"TradeAmount": 1000.0, "BrokerageRate": 0.003, "MinimumFee": 15.0},
#         },
#         {
#             "name": "test3",
#             "formula": r"Fee = \frac{\text{TradeAmount} - \text{Discount}}{\text{ConversionRate}}",
#             "variables": {"TradeAmount": 11300.0, "Discount": 500.0, "ConversionRate": 1.2},
#         },
#         {
#             "name": "test17",
#             "formula": r"SR = \frac{E[R_p]-R_f}{\sigma_p}",
#             "variables": {"E_R_p": 0.1, "R_f": 0.02, "sigma_p": 0.15},
#         },
#     ]

#     for case in tests:
#         try:
#             expr = latex_to_python(case["formula"], case["variables"])
#             result = eval(
#                 expr,
#                 {"math": math, "max": max, "min": min, "sum": sum, "range": range},
#                 {"variables": case["variables"]}
#             )
#             print(f"{case['name']}: {float(result):.4f}")
#         except Exception as e:
#             print(f"{case['name']} failed: {e}")


# if __name__ == "__main__":
#     parser = argparse.ArgumentParser()
#     parser.add_argument("--test", action="store_true", help="Run local testcases")
#     args = parser.parse_args()

    
    run_local_tests()

