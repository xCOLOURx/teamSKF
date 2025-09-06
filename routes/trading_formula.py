import json
import logging
import re
import math
from flask import request, jsonify
from routes import app

logger = logging.getLogger(__name__)

def latex_to_python(formula: str, variables: dict) -> str:
    expr = formula

    # Strip $$ or $ wrappers
    expr = re.sub(r"\$\$|\$", "", expr)

    # Remove leading assignment like "Fee =" or "VaR ="
    expr = re.sub(r"^[A-Za-z_][A-Za-z0-9_]*\s*=", "", expr)

    # Replace \text{Var} with Var
    expr = re.sub(r"\\text\{([^}]*)\}", r"\1", expr)

    # Normalize variable names: E[R_m] -> E_R_m
    expr = expr.replace("[", "_").replace("]", "").replace("{", "").replace("}", "")

    # Operators
    expr = expr.replace(r"\times", "*")
    expr = expr.replace(r"\cdot", "*")
    expr = expr.replace(r"\max", "max")
    expr = expr.replace(r"\min", "min")
    expr = expr.replace(r"\log", "math.log")

    # Exponentials: e^x -> math.exp(x)
    expr = re.sub(r"e\^(\w+)", r"math.exp(\1)", expr)
    expr = re.sub(r"e\^\(([^)]+)\)", r"math.exp(\1)", expr)

    # Fractions: \frac{a}{b} -> (a)/(b)
    def frac_repl(m):
        return f"({m.group(1)})/({m.group(2)})"
    expr = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", frac_repl, expr)

    # Summations: \sum_{i=1}^{n} expr
    def sum_repl(m):
        var = m.group(1)
        lower = m.group(2)
        upper = m.group(3)
        body = m.group(4)
        return f"(sum(({body}) for {var} in range(int({lower}), int({upper})+1)))"
    expr = re.sub(r"\\sum_\{([a-zA-Z])=(\d+)\}\^\{([^}]*)\}([^ ]+)", sum_repl, expr)

    # Replace variable names safely (sorted by length to avoid partial matches)
    for var in sorted(variables.keys(), key=len, reverse=True):
        expr = re.sub(rf"\b{re.escape(var)}\b", f"variables['{var}']", expr)

    return expr


@app.route('/trading-formula', methods=['POST'])
def trading_formula():
    try:
        testcases = request.get_json(force=True)
        results = []

        for case in testcases:
            formula = case.get("formula", "")
            variables = case.get("variables", {})

            # Convert formula to Python expression
            python_expr = latex_to_python(formula, variables)

            try:
                # Evaluate safely
                result = eval(
                    python_expr,
                    {"math": math, "max": max, "min": min, "sum": sum, "range": range},
                    {"variables": variables}
                )
                result = round(float(result), 4)
            except Exception as e:
                logger.error(f"Error evaluating {case['name']}: {e}")
                result = None

            results.append({"result": result})

        return jsonify(results)

    except Exception as e:
        logger.error(f"Trading formula error: {e}")
        return jsonify({"error": str(e)}), 400
