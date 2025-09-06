import json
import logging
from flask import request, jsonify
from routes import app
from sympy import symbols
from sympy.parsing.latex import parse_latex

logger = logging.getLogger(__name__)


@app.route('/trading-formula', methods=['POST'])
def trading_formula():
    try:
        testcases = request.get_json(force=True)
        results = []

        for case in testcases:
            formula = case.get("formula", "")
            variables = case.get("variables", {})

            try:
                # Clean LaTeX: remove $$, $, and left-hand "Fee ="
                clean_formula = formula.replace("$$", "").replace("$", "")
                if "=" in clean_formula:
                    clean_formula = clean_formula.split("=", 1)[1]

                # Parse into SymPy expression
                expr = parse_latex(clean_formula)

                # Substitute variable values
                sym_subs = {}
                for var, val in variables.items():
                    sym = symbols(var.replace("[", "_").replace("]", ""))
                    sym_subs[sym] = val

                result = expr.subs(sym_subs).evalf()
                result = round(float(result), 4)

            except Exception as e:
                logger.error(f"Error evaluating {case.get('name')}: {e}")
                result = None

            results.append({"result": result})

        return jsonify(results)

    except Exception as e:
        logger.error(f"Trading formula error: {e}")
        return jsonify({"error": str(e)}), 400
