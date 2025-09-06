import json
import logging

import re

from flask import request

from routes import app

logger = logging.getLogger(__name__)


@app.route('/trading-formula', methods=['POST'])
def trading_formula():
    data = request.get_json()
    logging.info("data sent for evaluation {}".format(data))

    # input_value = data.get("input")
    # result = input_value * input_value
    # data = json.load(open('test_inputs/trading_formula.json'))

    answers = []
    for item in data:
        result = compute_formula(item['formula'], item['variables'])
        print(f"{item['name']} result: {result}")
        answers.append({"result": result})

    # logging.info("My result :{}".format(result))
    return json.dumps(answers)

def compute_formula(formula, variables):
    formula = formula.replace('$$', '')  # Remove LaTeX math mode
    # Replace LaTeX variable names with their values
    for var, val in variables.items():
        formula = re.sub(rf'\\text\{{{var}\}}', str(val), formula)
    # Replace LaTeX operators
    formula = formula.replace(r'\times', '*')
    formula = formula.replace(r'\max', 'max')
    # Replace LaTeX fraction (handles both single and double backslash)
    formula = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1)/(\2)', formula)
    formula = re.sub(r'\frac\{([^{}]+)\}\{([^{}]+)\}', r'(\1)/(\2)', formula)
    # Remove 'Fee =' part
    expr = formula.split('=')[1].strip()
    # Evaluate the expression
    val = eval(expr)
    dp_val = "{:.4f}".format(val)
    return dp_val